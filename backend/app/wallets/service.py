from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.schemas import raise_auth_error
from app.core.config import settings
from app.deals.models import Deal
from app.wallets.constants import (
    DEFAULT_COMMISSION_RATE,
    ERR_WALLET_ALREADY_SETTLED,
    ERR_WALLET_DEAL_NOT_FOUND,
    ERR_WALLET_FREEZE_NOT_FOUND,
    ERR_WALLET_INSUFFICIENT_BALANCE,
    ERR_WALLET_INSUFFICIENT_FROZEN,
    ERR_WALLET_INVALID_AMOUNT,
    ERR_WALLET_PAYMENT_NOT_CONFIGURED,
    ERR_WALLET_PAYMENT_ORDER_INVALID,
    ERR_WALLET_PAYMENT_ORDER_NOT_FOUND,
    ERR_WALLET_WITHDRAW_INVALID,
    ERR_WALLET_WITHDRAW_NOT_FOUND,
    LedgerEntryType,
    PaymentOrderStatus,
    WithdrawStatus,
)
from app.wallets.models import PaymentOrder, Wallet, WalletLedger, WithdrawRequest
from app.platform.enforcement import require_wallet_enabled
from app.platform.service import get_commission_rate, get_or_create_settings, log_admin_action
from app.wallets.payment_provider import (
    PaymentProviderError,
    get_payment_provider,
    platform_payment_config_from_row,
)
from app.wallets.schemas import (
    DepositOrderResponse,
    FreezeResult,
    LedgerEntryResponse,
    SettleResult,
    UnfreezeResult,
    WalletResponse,
    WithdrawRequestResponse,
)

def wallet_to_response(wallet: Wallet, *, points_non_withdrawable: int) -> WalletResponse:
    return WalletResponse(
        id=wallet.id,
        user_id=wallet.user_id,
        balance_available=wallet.balance_available,
        balance_frozen=wallet.balance_frozen,
        points_non_withdrawable=points_non_withdrawable,
        currency=wallet.currency,
        created_at=wallet.created_at.isoformat(),
        updated_at=wallet.updated_at.isoformat(),
    )


async def get_points_balance(db: AsyncSession, wallet_id: UUID) -> int:
    result = await db.execute(
        select(func.coalesce(func.sum(WalletLedger.amount_cents), 0)).where(
            WalletLedger.wallet_id == wallet_id,
            WalletLedger.entry_type.in_(
                [LedgerEntryType.POINTS_CREDIT, LedgerEntryType.POINTS_DEBIT]
            ),
        )
    )
    return int(result.scalar_one())


async def get_or_create_wallet(db: AsyncSession, user_id: UUID) -> Wallet:
    result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
    wallet = result.scalar_one_or_none()
    if wallet is not None:
        return wallet

    wallet = Wallet(user_id=user_id)
    db.add(wallet)
    await db.flush()
    return wallet


async def _get_wallet_for_update(db: AsyncSession, user_id: UUID) -> Wallet:
    result = await db.execute(
        select(Wallet).where(Wallet.user_id == user_id).with_for_update()
    )
    wallet = result.scalar_one_or_none()
    if wallet is None:
        wallet = Wallet(user_id=user_id)
        db.add(wallet)
        await db.flush()
        result = await db.execute(
            select(Wallet).where(Wallet.id == wallet.id).with_for_update()
        )
        wallet = result.scalar_one()
    return wallet


async def _append_ledger(
    db: AsyncSession,
    *,
    wallet_id: UUID,
    deal_id: UUID | None,
    entry_type: LedgerEntryType,
    amount_cents: int,
    balance_after: int,
    description: str | None = None,
) -> WalletLedger:
    entry = WalletLedger(
        wallet_id=wallet_id,
        deal_id=deal_id,
        entry_type=str(entry_type),
        amount_cents=amount_cents,
        balance_after=balance_after,
        description=description,
    )
    db.add(entry)
    return entry


def ledger_to_response(entry: WalletLedger) -> LedgerEntryResponse:
    return LedgerEntryResponse(
        id=entry.id,
        wallet_id=entry.wallet_id,
        deal_id=entry.deal_id,
        entry_type=entry.entry_type,
        amount_cents=entry.amount_cents,
        balance_after=entry.balance_after,
        description=entry.description,
        created_at=entry.created_at.isoformat(),
    )


async def get_my_wallet(db: AsyncSession, *, user_id: UUID) -> WalletResponse:
    wallet = await get_or_create_wallet(db, user_id)
    points = await get_points_balance(db, wallet.id)
    return wallet_to_response(wallet, points_non_withdrawable=points)


async def list_wallet_ledger(
    db: AsyncSession,
    *,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    wallet = await get_or_create_wallet(db, user_id)
    query = select(WalletLedger).where(WalletLedger.wallet_id == wallet.id)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(WalletLedger.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    entries = result.scalars().all()

    return {
        "items": [ledger_to_response(entry).model_dump() for entry in entries],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def redeem_recharge_card(
    db: AsyncSession,
    *,
    user_id: UUID,
    code_str: str,
) -> WalletResponse:
    from app.platform.codes import redeem_recharge_code

    code = await redeem_recharge_code(db, user_id=user_id, code_str=code_str)
    wallet = await _get_wallet_for_update(db, user_id)
    wallet.balance_available += code.value_cents or 0
    await _append_ledger(
        db,
        wallet_id=wallet.id,
        deal_id=None,
        entry_type=LedgerEntryType.DEPOSIT,
        amount_cents=code.value_cents or 0,
        balance_after=wallet.balance_available,
        description=f"recharge card {code.code}",
    )
    await db.commit()
    await db.refresh(wallet)
    points = await get_points_balance(db, wallet.id)
    return wallet_to_response(wallet, points_non_withdrawable=points)


async def credit_wallet(
    db: AsyncSession,
    *,
    user_id: UUID,
    amount_cents: int,
    description: str,
    provider_ref: str,
) -> WalletResponse:
    """支付确认后入账（幂等由 payment_order 状态保证）。"""
    if amount_cents <= 0:
        raise_auth_error(
            code=ERR_WALLET_INVALID_AMOUNT,
            message="credit amount must be positive",
            http_status=422,
        )

    wallet = await _get_wallet_for_update(db, user_id)
    wallet.balance_available += amount_cents
    await _append_ledger(
        db,
        wallet_id=wallet.id,
        deal_id=None,
        entry_type=LedgerEntryType.DEPOSIT,
        amount_cents=amount_cents,
        balance_after=wallet.balance_available,
        description=description,
    )
    await db.commit()
    await db.refresh(wallet)
    points = await get_points_balance(db, wallet.id)
    return wallet_to_response(wallet, points_non_withdrawable=points)


def _utc_today_start() -> datetime:
    now = datetime.now(UTC)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


async def _enforce_user_daily_payment_limits(
    db: AsyncSession,
    *,
    user_id: UUID,
    amount_cents: int,
    platform,
) -> None:
    today_start = _utc_today_start()
    active_statuses = (PaymentOrderStatus.PENDING, PaymentOrderStatus.PAID)

    if platform.max_daily_payment_count is not None:
        today_count = (
            await db.execute(
                select(func.count())
                .select_from(PaymentOrder)
                .where(
                    PaymentOrder.user_id == user_id,
                    PaymentOrder.created_at >= today_start,
                    PaymentOrder.status.in_(active_statuses),
                )
            )
        ).scalar_one()
        if today_count >= platform.max_daily_payment_count:
            raise_auth_error(
                code=ERR_WALLET_INVALID_AMOUNT,
                message=f"daily payment count limit exceeded (max {platform.max_daily_payment_count})",
                http_status=422,
            )

    if platform.payment_daily_limit_cents is not None:
        paid_today = (
            await db.execute(
                select(func.coalesce(func.sum(PaymentOrder.amount_cents), 0)).where(
                    PaymentOrder.user_id == user_id,
                    PaymentOrder.status == PaymentOrderStatus.PAID,
                    PaymentOrder.paid_at >= today_start,
                )
            )
        ).scalar_one()
        pending_today = (
            await db.execute(
                select(func.coalesce(func.sum(PaymentOrder.amount_cents), 0)).where(
                    PaymentOrder.user_id == user_id,
                    PaymentOrder.status == PaymentOrderStatus.PENDING,
                    PaymentOrder.created_at >= today_start,
                )
            )
        ).scalar_one()
        projected = int(paid_today or 0) + int(pending_today or 0) + amount_cents
        if projected > platform.payment_daily_limit_cents:
            raise_auth_error(
                code=ERR_WALLET_INVALID_AMOUNT,
                message=f"daily payment amount limit exceeded (max {platform.payment_daily_limit_cents} cents)",
                http_status=422,
            )


def _payment_order_to_response(
    order: PaymentOrder,
    *,
    wallet: WalletResponse | None = None,
    provider: str,
) -> DepositOrderResponse:
    return DepositOrderResponse(
        id=order.id,
        amount_cents=order.amount_cents,
        currency=order.currency,
        channel=order.channel,
        status=order.status,
        provider=provider,
        provider_ref=order.provider_ref,
        pay_url=order.pay_url,
        expires_at=order.expires_at.isoformat() if order.expires_at else None,
        paid_at=order.paid_at.isoformat() if order.paid_at else None,
        created_at=order.created_at.isoformat(),
        wallet=wallet,
    )


async def create_deposit_order(
    db: AsyncSession,
    *,
    user_id: UUID,
    amount_cents: int,
    channel: str,
) -> DepositOrderResponse:
    platform = await get_or_create_settings(db)
    require_wallet_enabled(platform)
    channel = channel.lower()
    if not platform.payment_enabled:
        raise_auth_error(code=ERR_WALLET_PAYMENT_NOT_CONFIGURED, message="payment is disabled", http_status=503)
    if channel == "wechat" and not platform.payment_wechat_enabled:
        raise_auth_error(code=ERR_WALLET_PAYMENT_NOT_CONFIGURED, message="wechat pay is disabled", http_status=503)
    if channel == "alipay" and not platform.payment_alipay_enabled:
        raise_auth_error(code=ERR_WALLET_PAYMENT_NOT_CONFIGURED, message="alipay is disabled", http_status=503)
    if channel == "stripe" and not platform.stripe_enabled:
        raise_auth_error(code=ERR_WALLET_PAYMENT_NOT_CONFIGURED, message="stripe is disabled", http_status=503)

    if amount_cents < platform.min_deposit_cents:
        raise_auth_error(
            code=ERR_WALLET_INVALID_AMOUNT,
            message=f"minimum deposit is {platform.min_deposit_cents} cents",
            http_status=422,
        )
    if platform.max_deposit_cents is not None and amount_cents > platform.max_deposit_cents:
        raise_auth_error(
            code=ERR_WALLET_INVALID_AMOUNT,
            message=f"maximum deposit is {platform.max_deposit_cents} cents",
            http_status=422,
        )

    pending_count = (
        await db.execute(
            select(func.count())
            .select_from(PaymentOrder)
            .where(
                PaymentOrder.user_id == user_id,
                PaymentOrder.status == PaymentOrderStatus.PENDING,
            )
        )
    ).scalar_one()
    if pending_count >= platform.max_pending_payment_orders:
        raise_auth_error(
            code=ERR_WALLET_INVALID_AMOUNT,
            message=f"too many pending payment orders (max {platform.max_pending_payment_orders})",
            http_status=422,
        )

    await _enforce_user_daily_payment_limits(
        db,
        user_id=user_id,
        amount_cents=amount_cents,
        platform=platform,
    )

    pay_config = platform_payment_config_from_row(platform)
    try:
        provider = get_payment_provider(channel, config=pay_config)
    except PaymentProviderError as exc:
        raise_auth_error(
            code=ERR_WALLET_PAYMENT_NOT_CONFIGURED,
            message=str(exc),
            http_status=503,
        )

    wallet = await get_or_create_wallet(db, user_id)
    order = PaymentOrder(
        user_id=user_id,
        amount_cents=amount_cents,
        currency=wallet.currency,
        channel=channel.lower(),
        status=PaymentOrderStatus.PENDING,
        provider_ref=f"cn_tmp_{uuid4().hex[:20]}",
        expires_at=datetime.now(UTC) + timedelta(minutes=platform.payment_order_timeout_minutes),
    )
    db.add(order)
    await db.flush()

    try:
        result = await provider.create_deposit(
            user_id=user_id,
            order_id=order.id,
            amount_cents=amount_cents,
            currency=wallet.currency,
        )
    except PaymentProviderError as exc:
        await db.rollback()
        raise_auth_error(
            code=ERR_WALLET_PAYMENT_NOT_CONFIGURED,
            message=str(exc),
            http_status=503,
        )

    order.provider_ref = result.provider_ref
    order.pay_url = result.pay_url

    wallet_response: WalletResponse | None = None
    paid_instant = result.status == "paid"
    if paid_instant:
        order.status = PaymentOrderStatus.PAID
        order.paid_at = datetime.now(UTC)
        wallet = await _get_wallet_for_update(db, user_id)
        wallet.balance_available += amount_cents
        await _append_ledger(
            db,
            wallet_id=wallet.id,
            deal_id=None,
            entry_type=LedgerEntryType.DEPOSIT,
            amount_cents=amount_cents,
            balance_after=wallet.balance_available,
            description=f"deposit {result.provider} ref={result.provider_ref}",
        )

    await db.commit()
    await db.refresh(order)
    if paid_instant:
        wallet = await get_or_create_wallet(db, user_id)
        points = await get_points_balance(db, wallet.id)
        wallet_response = wallet_to_response(wallet, points_non_withdrawable=points)
    return _payment_order_to_response(order, wallet=wallet_response, provider=result.provider)


async def get_deposit_order(
    db: AsyncSession,
    *,
    user_id: UUID,
    order_id: UUID,
) -> DepositOrderResponse:
    result = await db.execute(
        select(PaymentOrder).where(PaymentOrder.id == order_id, PaymentOrder.user_id == user_id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise_auth_error(
            code=ERR_WALLET_PAYMENT_ORDER_NOT_FOUND,
            message="payment order not found",
            http_status=404,
        )
    return _payment_order_to_response(order, provider=order.channel)


async def complete_deposit_by_provider_ref(
    db: AsyncSession,
    *,
    provider_ref: str,
    amount_cents: int,
) -> DepositOrderResponse | None:
    result = await db.execute(
        select(PaymentOrder).where(PaymentOrder.provider_ref == provider_ref).with_for_update()
    )
    order = result.scalar_one_or_none()
    if order is None:
        return None
    if order.status == PaymentOrderStatus.PAID:
        return _payment_order_to_response(order, provider=order.channel)
    if amount_cents != order.amount_cents:
        raise_auth_error(
            code=ERR_WALLET_PAYMENT_ORDER_INVALID,
            message="payment amount mismatch",
            http_status=422,
        )

    order.status = PaymentOrderStatus.PAID
    order.paid_at = datetime.now(UTC)

    wallet = await _get_wallet_for_update(db, order.user_id)
    wallet.balance_available += order.amount_cents
    await _append_ledger(
        db,
        wallet_id=wallet.id,
        deal_id=None,
        entry_type=LedgerEntryType.DEPOSIT,
        amount_cents=order.amount_cents,
        balance_after=wallet.balance_available,
        description=f"deposit {order.channel} ref={provider_ref}",
    )
    await db.commit()
    await db.refresh(order)
    points = await get_points_balance(db, wallet.id)
    wallet_response = wallet_to_response(wallet, points_non_withdrawable=points)
    return _payment_order_to_response(order, wallet=wallet_response, provider=order.channel)


async def handle_payment_notify(
    db: AsyncSession,
    *,
    channel: str,
    payload: bytes,
    headers: dict[str, str],
) -> bool:
    platform = await get_or_create_settings(db)
    pay_config = platform_payment_config_from_row(platform)
    try:
        provider = get_payment_provider(channel, config=pay_config)
    except PaymentProviderError:
        return False

    notify = await provider.verify_notify(payload=payload, headers=headers)
    if notify is None or notify.status != "paid":
        return False

    result = await complete_deposit_by_provider_ref(
        db,
        provider_ref=notify.provider_ref,
        amount_cents=notify.amount_cents,
    )
    return result is not None


def _withdraw_to_response(record: WithdrawRequest, wallet: WalletResponse) -> WithdrawRequestResponse:
    return WithdrawRequestResponse(
        id=record.id,
        amount_cents=record.amount_cents,
        status=record.status,
        payout_method=record.payout_method,
        payout_account=record.payout_account,
        payout_name=record.payout_name,
        admin_note=record.admin_note,
        provider_ref=record.provider_ref,
        created_at=record.created_at.isoformat(),
        processed_at=record.processed_at.isoformat() if record.processed_at else None,
        wallet=wallet,
    )


async def create_withdraw_request(
    db: AsyncSession,
    *,
    user_id: UUID,
    amount_cents: int,
    payout_method: str,
    payout_account: str,
    payout_name: str,
) -> WithdrawRequestResponse:
    platform = await get_or_create_settings(db)
    if amount_cents < platform.min_withdraw_cents:
        raise_auth_error(
            code=ERR_WALLET_INVALID_AMOUNT,
            message=f"minimum withdraw is {platform.min_withdraw_cents} cents",
            http_status=422,
        )
    if amount_cents > platform.max_withdraw_cents:
        raise_auth_error(
            code=ERR_WALLET_INVALID_AMOUNT,
            message=f"maximum withdraw is {platform.max_withdraw_cents} cents",
            http_status=422,
        )

    wallet = await _get_wallet_for_update(db, user_id)
    if wallet.balance_available < amount_cents:
        raise_auth_error(
            code=ERR_WALLET_INSUFFICIENT_BALANCE,
            message="insufficient available balance to withdraw",
            http_status=422,
        )

    wallet.balance_available -= amount_cents
    record = WithdrawRequest(
        user_id=user_id,
        amount_cents=amount_cents,
        status=WithdrawStatus.PENDING,
        payout_method=payout_method.lower(),
        payout_account=payout_account.strip(),
        payout_name=payout_name.strip(),
    )
    db.add(record)
    await db.flush()

    await _append_ledger(
        db,
        wallet_id=wallet.id,
        deal_id=None,
        entry_type=LedgerEntryType.WITHDRAW,
        amount_cents=-amount_cents,
        balance_after=wallet.balance_available,
        description=f"withdraw request {record.id} pending",
    )

    await db.commit()
    await db.refresh(wallet)
    await db.refresh(record)
    points = await get_points_balance(db, wallet.id)
    return _withdraw_to_response(record, wallet_to_response(wallet, points_non_withdrawable=points))


async def list_my_withdrawals(
    db: AsyncSession,
    *,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    query = select(WithdrawRequest).where(WithdrawRequest.user_id == user_id)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    result = await db.execute(
        query.order_by(WithdrawRequest.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    records = result.scalars().all()
    wallet = await get_my_wallet(db, user_id=user_id)
    return {
        "items": [
            _withdraw_to_response(record, wallet).model_dump()
            for record in records
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def list_admin_withdrawals(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> dict:
    query = select(WithdrawRequest)
    if status:
        query = query.where(WithdrawRequest.status == status)
    else:
        query = query.where(
            WithdrawRequest.status.in_(
                [
                    WithdrawStatus.PENDING,
                    WithdrawStatus.APPROVED,
                    WithdrawStatus.PROCESSING,
                ]
            )
        )
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    result = await db.execute(
        query.order_by(WithdrawRequest.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    records = result.scalars().all()
    return {
        "items": [
            {
                "id": str(r.id),
                "user_id": str(r.user_id),
                "amount_cents": r.amount_cents,
                "status": r.status,
                "payout_method": r.payout_method,
                "payout_account": r.payout_account,
                "payout_name": r.payout_name,
                "admin_note": r.admin_note,
                "provider_ref": r.provider_ref,
                "created_at": r.created_at.isoformat(),
                "processed_at": r.processed_at.isoformat() if r.processed_at else None,
            }
            for r in records
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def list_admin_deposit_orders(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    channel: str | None = None,
    search: str | None = None,
) -> dict:
    query = select(PaymentOrder, User.email, User.display_name).join(
        User, User.id == PaymentOrder.user_id
    )
    count_query = select(func.count()).select_from(PaymentOrder).join(
        User, User.id == PaymentOrder.user_id
    )

    if status:
        query = query.where(PaymentOrder.status == status)
        count_query = count_query.where(PaymentOrder.status == status)
    if channel:
        query = query.where(PaymentOrder.channel == channel)
        count_query = count_query.where(PaymentOrder.channel == channel)
    if search and search.strip():
        term = f"%{search.strip()}%"
        search_filter = or_(
            PaymentOrder.provider_ref.ilike(term),
            User.email.ilike(term),
            User.display_name.ilike(term),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(
        query.order_by(PaymentOrder.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = result.all()
    return {
        "items": [
            {
                "id": str(o.id),
                "user_id": str(o.user_id),
                "user_email": email,
                "user_display_name": display_name,
                "amount_cents": o.amount_cents,
                "currency": o.currency,
                "channel": o.channel,
                "status": o.status,
                "provider_ref": o.provider_ref,
                "pay_url": o.pay_url,
                "created_at": o.created_at.isoformat(),
                "paid_at": o.paid_at.isoformat() if o.paid_at else None,
            }
            for o, email, display_name in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def admin_credit_user_wallet(
    db: AsyncSession,
    *,
    user_id: UUID,
    amount_cents: int,
    admin_id: UUID,
    note: str | None = None,
) -> dict:
    provider_ref = f"admin_credit_{uuid4().hex[:16]}"
    wallet = await credit_wallet(
        db,
        user_id=user_id,
        amount_cents=amount_cents,
        description=note or "admin manual credit",
        provider_ref=provider_ref,
    )
    await log_admin_action(
        db,
        admin_id=admin_id,
        action="credit_wallet",
        target_type="user",
        target_id=str(user_id),
        detail=f"{amount_cents}:{note or ''}",
    )
    await db.commit()
    return wallet.model_dump()


async def list_admin_ledger(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    entry_type: str | None = None,
) -> dict:
    query = select(WalletLedger)
    if entry_type:
        query = query.where(WalletLedger.entry_type == entry_type)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    result = await db.execute(
        query.order_by(WalletLedger.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    entries = result.scalars().all()
    return {
        "items": [ledger_to_response(entry).model_dump() for entry in entries],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def admin_process_withdraw(
    db: AsyncSession,
    *,
    withdraw_id: UUID,
    action: str,
    admin_note: str | None = None,
    provider_ref: str | None = None,
    admin_id: UUID | None = None,
) -> dict:
    result = await db.execute(
        select(WithdrawRequest).where(WithdrawRequest.id == withdraw_id).with_for_update()
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise_auth_error(
            code=ERR_WALLET_WITHDRAW_NOT_FOUND,
            message="withdraw request not found",
            http_status=404,
        )

    now = datetime.now(UTC)
    action = action.lower()

    if action == "reject":
        if record.status not in (WithdrawStatus.PENDING, WithdrawStatus.APPROVED):
            raise_auth_error(code=ERR_WALLET_WITHDRAW_INVALID, message="cannot reject", http_status=409)
        wallet = await _get_wallet_for_update(db, record.user_id)
        wallet.balance_available += record.amount_cents
        await _append_ledger(
            db,
            wallet_id=wallet.id,
            deal_id=None,
            entry_type=LedgerEntryType.DEPOSIT,
            amount_cents=record.amount_cents,
            balance_after=wallet.balance_available,
            description=f"withdraw {record.id} rejected refund",
        )
        record.status = WithdrawStatus.REJECTED
        record.admin_note = admin_note
        record.processed_at = now
    elif action == "approve":
        if record.status != WithdrawStatus.PENDING:
            raise_auth_error(code=ERR_WALLET_WITHDRAW_INVALID, message="cannot approve", http_status=409)
        record.status = WithdrawStatus.APPROVED
        record.admin_note = admin_note
    elif action == "complete":
        if record.status not in (WithdrawStatus.APPROVED, WithdrawStatus.PROCESSING, WithdrawStatus.PENDING):
            raise_auth_error(code=ERR_WALLET_WITHDRAW_INVALID, message="cannot complete", http_status=409)
        record.status = WithdrawStatus.COMPLETED
        record.provider_ref = provider_ref
        record.admin_note = admin_note
        record.processed_at = now
    else:
        raise_auth_error(code=ERR_WALLET_WITHDRAW_INVALID, message="invalid action", http_status=400)

    if admin_id is not None:
        await log_admin_action(
            db,
            admin_id=admin_id,
            action=f"withdraw_{action}",
            target_type="withdraw",
            target_id=str(withdraw_id),
            detail=admin_note,
        )

    await db.commit()
    await db.refresh(record)
    return {
        "id": str(record.id),
        "status": record.status,
        "admin_note": record.admin_note,
        "provider_ref": record.provider_ref,
        "processed_at": record.processed_at.isoformat() if record.processed_at else None,
    }


async def admin_refund_deposit_order(
    db: AsyncSession,
    *,
    order_id: UUID,
    admin_id: UUID,
    admin_note: str | None = None,
) -> dict:
    result = await db.execute(
        select(PaymentOrder).where(PaymentOrder.id == order_id).with_for_update()
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise_auth_error(
            code=ERR_WALLET_PAYMENT_ORDER_NOT_FOUND,
            message="payment order not found",
            http_status=404,
        )
    if order.status != PaymentOrderStatus.PAID:
        raise_auth_error(
            code=ERR_WALLET_PAYMENT_ORDER_INVALID,
            message="only paid orders can be refunded",
            http_status=409,
        )

    wallet = await _get_wallet_for_update(db, order.user_id)
    if wallet.balance_available < order.amount_cents:
        raise_auth_error(
            code=ERR_WALLET_INSUFFICIENT_BALANCE,
            message="user balance insufficient for refund",
            http_status=422,
        )

    wallet.balance_available -= order.amount_cents
    await _append_ledger(
        db,
        wallet_id=wallet.id,
        deal_id=None,
        entry_type=LedgerEntryType.REFUND,
        amount_cents=-order.amount_cents,
        balance_after=wallet.balance_available,
        description=f"admin refund payment order {order.id} ref={order.provider_ref}",
    )
    order.status = PaymentOrderStatus.REFUNDED

    await log_admin_action(
        db,
        admin_id=admin_id,
        action="payment_order_refund",
        target_type="payment_order",
        target_id=str(order_id),
        detail=admin_note,
    )

    await db.commit()
    await db.refresh(order)
    return {
        "id": str(order.id),
        "status": order.status,
        "amount_cents": order.amount_cents,
        "provider_ref": order.provider_ref,
        "admin_note": admin_note,
    }


# 兼容测试：直接入账（不经过支付网关）
async def recharge(
    db: AsyncSession,
    *,
    user_id: UUID,
    amount_cents: int,
    points_cents: int = 0,
    provider=None,
) -> WalletResponse:
    wallet = await _get_wallet_for_update(db, user_id)

    if amount_cents > 0:
        wallet.balance_available += amount_cents
        await _append_ledger(
            db,
            wallet_id=wallet.id,
            deal_id=None,
            entry_type=LedgerEntryType.DEPOSIT,
            amount_cents=amount_cents,
            balance_after=wallet.balance_available,
            description="test credit",
        )

    points = await get_points_balance(db, wallet.id)
    if points_cents > 0:
        points += points_cents
        await _append_ledger(
            db,
            wallet_id=wallet.id,
            deal_id=None,
            entry_type=LedgerEntryType.POINTS_CREDIT,
            amount_cents=points_cents,
            balance_after=points,
            description="points credit",
        )

    await db.commit()
    await db.refresh(wallet)
    points = await get_points_balance(db, wallet.id)
    return wallet_to_response(wallet, points_non_withdrawable=points)


async def _get_freeze_split(db: AsyncSession, wallet_id: UUID, deal_id: UUID) -> tuple[int, int]:
    result = await db.execute(
        select(WalletLedger).where(
            WalletLedger.wallet_id == wallet_id,
            WalletLedger.deal_id == deal_id,
            WalletLedger.entry_type.in_([LedgerEntryType.FREEZE, LedgerEntryType.POINTS_DEBIT]),
        )
    )
    from_points = 0
    from_available = 0
    for entry in result.scalars():
        if entry.entry_type == LedgerEntryType.POINTS_DEBIT:
            from_points += abs(entry.amount_cents)
        elif entry.entry_type == LedgerEntryType.FREEZE:
            from_available += abs(entry.amount_cents)
    return from_points, from_available


async def freeze(
    db: AsyncSession,
    *,
    user_id: UUID,
    deal_id: UUID,
    amount: int,
) -> FreezeResult:
    if amount <= 0:
        raise_auth_error(
            code=ERR_WALLET_INVALID_AMOUNT,
            message="freeze amount must be positive",
            http_status=422,
        )

    wallet = await _get_wallet_for_update(db, user_id)
    points = await get_points_balance(db, wallet.id)
    total_spendable = points + wallet.balance_available

    if total_spendable < amount:
        raise_auth_error(
            code=ERR_WALLET_INSUFFICIENT_BALANCE,
            message="insufficient balance to freeze",
            http_status=422,
        )

    from_points = min(points, amount)
    from_available = amount - from_points

    if from_points > 0:
        new_points = points - from_points
        await _append_ledger(
            db,
            wallet_id=wallet.id,
            deal_id=deal_id,
            entry_type=LedgerEntryType.POINTS_DEBIT,
            amount_cents=-from_points,
            balance_after=new_points,
            description=f"freeze deal {deal_id} points portion",
        )

    if from_available > 0:
        wallet.balance_available -= from_available
        await _append_ledger(
            db,
            wallet_id=wallet.id,
            deal_id=deal_id,
            entry_type=LedgerEntryType.FREEZE,
            amount_cents=-from_available,
            balance_after=wallet.balance_available,
            description=f"freeze deal {deal_id} available portion",
        )

    wallet.balance_frozen += amount
    await db.commit()
    await db.refresh(wallet)

    return FreezeResult(
        deal_id=deal_id,
        wallet_id=wallet.id,
        amount_cents=amount,
        from_points_cents=from_points,
        from_available_cents=from_available,
        balance_frozen_after=wallet.balance_frozen,
    )


async def unfreeze(
    db: AsyncSession,
    *,
    user_id: UUID,
    deal_id: UUID,
    amount: int | None = None,
) -> UnfreezeResult:
    wallet = await _get_wallet_for_update(db, user_id)
    from_points, from_available = await _get_freeze_split(db, wallet.id, deal_id)
    total_frozen = from_points + from_available

    if total_frozen == 0:
        raise_auth_error(
            code=ERR_WALLET_FREEZE_NOT_FOUND,
            message=f"no freeze record for deal {deal_id}",
            http_status=404,
        )

    if amount is not None and amount != total_frozen:
        raise_auth_error(
            code=ERR_WALLET_INVALID_AMOUNT,
            message="partial unfreeze is not supported",
            http_status=422,
        )

    release_amount = amount if amount is not None else total_frozen
    if wallet.balance_frozen < release_amount:
        raise_auth_error(
            code=ERR_WALLET_INSUFFICIENT_FROZEN,
            message="insufficient frozen balance",
            http_status=422,
        )

    points = await get_points_balance(db, wallet.id)

    if from_points > 0:
        points += from_points
        await _append_ledger(
            db,
            wallet_id=wallet.id,
            deal_id=deal_id,
            entry_type=LedgerEntryType.POINTS_CREDIT,
            amount_cents=from_points,
            balance_after=points,
            description=f"unfreeze deal {deal_id} points portion",
        )

    if from_available > 0:
        wallet.balance_available += from_available
        await _append_ledger(
            db,
            wallet_id=wallet.id,
            deal_id=deal_id,
            entry_type=LedgerEntryType.UNFREEZE,
            amount_cents=from_available,
            balance_after=wallet.balance_available,
            description=f"unfreeze deal {deal_id} available portion",
        )

    wallet.balance_frozen -= release_amount
    await db.commit()
    await db.refresh(wallet)

    return UnfreezeResult(
        deal_id=deal_id,
        wallet_id=wallet.id,
        amount_cents=release_amount,
        to_points_cents=from_points,
        to_available_cents=from_available,
        balance_frozen_after=wallet.balance_frozen,
    )


async def _is_deal_settled(db: AsyncSession, deal_id: UUID) -> bool:
    result = await db.execute(
        select(WalletLedger.id).where(
            WalletLedger.deal_id == deal_id,
            WalletLedger.entry_type == LedgerEntryType.PAYMENT,
            WalletLedger.amount_cents > 0,
        )
    )
    return result.scalar_one_or_none() is not None


async def settle(db: AsyncSession, *, deal_id: UUID) -> SettleResult:
    result = await db.execute(select(Deal).where(Deal.id == deal_id))
    deal = result.scalar_one_or_none()
    if deal is None:
        raise_auth_error(
            code=ERR_WALLET_DEAL_NOT_FOUND,
            message="deal not found",
            http_status=404,
        )

    if await _is_deal_settled(db, deal_id):
        raise_auth_error(
            code=ERR_WALLET_ALREADY_SETTLED,
            message="deal already settled",
            http_status=409,
        )

    amount = deal.amount_cents
    commission_rate = await get_commission_rate(db)
    commission = int(amount * commission_rate)
    seller_net = amount - commission

    buyer_wallet = await _get_wallet_for_update(db, deal.buyer_id)
    seller_wallet = await _get_wallet_for_update(db, deal.seller_id)

    if buyer_wallet.balance_frozen < amount:
        raise_auth_error(
            code=ERR_WALLET_INSUFFICIENT_FROZEN,
            message="buyer frozen balance insufficient for settlement",
            http_status=422,
        )

    buyer_wallet.balance_frozen -= amount

    await _append_ledger(
        db,
        wallet_id=buyer_wallet.id,
        deal_id=deal_id,
        entry_type=LedgerEntryType.PAYMENT,
        amount_cents=-amount,
        balance_after=buyer_wallet.balance_available,
        description=f"settle deal {deal_id} payment",
    )
    await _append_ledger(
        db,
        wallet_id=buyer_wallet.id,
        deal_id=deal_id,
        entry_type=LedgerEntryType.FEE,
        amount_cents=-commission,
        balance_after=buyer_wallet.balance_available,
        description=f"settle deal {deal_id} commission {commission} cents",
    )

    seller_wallet.balance_available += seller_net
    await _append_ledger(
        db,
        wallet_id=seller_wallet.id,
        deal_id=deal_id,
        entry_type=LedgerEntryType.PAYMENT,
        amount_cents=seller_net,
        balance_after=seller_wallet.balance_available,
        description=f"settle deal {deal_id} net after {commission} fee",
    )

    await db.commit()
    await db.refresh(buyer_wallet)
    await db.refresh(seller_wallet)

    return SettleResult(
        deal_id=deal_id,
        amount_cents=amount,
        commission_cents=commission,
        seller_net_cents=seller_net,
        buyer_wallet_id=buyer_wallet.id,
        seller_wallet_id=seller_wallet.id,
    )
