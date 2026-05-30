from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.constants import (
    DEFAULT_PAGE_SIZE,
    ERR_ADMIN_SELF_SUSPEND,
    ERR_ADMIN_USER_NOT_FOUND,
    MAX_PAGE_SIZE,
)
from app.admin.schemas import (
    AdminStatsResponse,
    AgentStatsResponse,
    DashboardAnalyticsResponse,
    OpsHealthResponse,
    PaymentStatsResponse,
)
from app.auth.constants import ApiKeyStatus, KycLevel, UserStatus
from app.auth.models import ApiKey, User
from app.auth.schemas import CurrentUser, UserProfile, raise_auth_error
from app.auth.service import get_user_by_id, user_to_profile
from app.deals.constants import DealStatus
from app.deals.models import Deal, DealExtension
from app.deals.schemas import DealResponse
from app.deals.service import _deal_to_response, get_deal
from app.intents.constants import IntentStatus
from app.intents.models import Intent
from app.intents.schemas import intent_to_response
from app.offers.constants import OfferStatus
from app.offers.models import Offer
from app.offers.schemas import offer_to_response
from app.platform.announcements import PlatformAnnouncement
from app.platform.schemas import PaymentConfigInfo
from app.platform.service import get_payment_config_info, log_admin_action
from app.core.health import probe_database, probe_redis
from app.shop.models import ShopApplication
from app.wallets.constants import LedgerEntryType, WithdrawStatus
from app.wallets.models import PaymentOrder, Wallet, WalletLedger, WithdrawRequest


def _utc_today_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _announcement_to_dict(row: PlatformAnnouncement) -> dict:
    return {
        "id": row.id,
        "title": row.title,
        "content": row.content,
        "status": row.status,
        "notify_mode": row.notify_mode,
        "audience": row.audience,
        "starts_at": row.starts_at.isoformat() if row.starts_at else None,
        "ends_at": row.ends_at.isoformat() if row.ends_at else None,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


async def get_platform_stats(db: AsyncSession) -> AdminStatsResponse:
    users_total = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    deals_total = (await db.execute(select(func.count()).select_from(Deal))).scalar_one()

    in_progress_statuses = (
        DealStatus.PAID,
        DealStatus.IN_PROGRESS,
        DealStatus.DELIVERED,
    )
    deals_in_progress = (
        await db.execute(
            select(func.count()).select_from(Deal).where(Deal.status.in_(in_progress_statuses))
        )
    ).scalar_one()
    deals_disputed = (
        await db.execute(
            select(func.count()).select_from(Deal).where(Deal.status == DealStatus.DISPUTED)
        )
    ).scalar_one()

    today_start = _utc_today_start()
    users_today = (
        await db.execute(
            select(func.count()).select_from(User).where(User.created_at >= today_start)
        )
    ).scalar_one()
    deals_today = (
        await db.execute(
            select(func.count()).select_from(Deal).where(Deal.created_at >= today_start)
        )
    ).scalar_one()

    offers_published = (
        await db.execute(
            select(func.count()).select_from(Offer).where(Offer.status == "published")
        )
    ).scalar_one()
    intents_open = (
        await db.execute(
            select(func.count()).select_from(Intent).where(Intent.status == "open")
        )
    ).scalar_one()

    deposits = (
        await db.execute(
            select(func.coalesce(func.sum(WalletLedger.amount_cents), 0)).where(
                WalletLedger.entry_type == LedgerEntryType.DEPOSIT
            )
        )
    ).scalar_one()
    payments = (
        await db.execute(
            select(func.coalesce(func.sum(WalletLedger.amount_cents), 0)).where(
                WalletLedger.entry_type == LedgerEntryType.PAYMENT,
                WalletLedger.amount_cents > 0,
            )
        )
    ).scalar_one()
    commission = (
        await db.execute(
            select(func.coalesce(func.sum(func.abs(WalletLedger.amount_cents)), 0)).where(
                WalletLedger.entry_type == LedgerEntryType.FEE
            )
        )
    ).scalar_one()

    withdrawals_pending = (
        await db.execute(
            select(func.count()).select_from(WithdrawRequest).where(
                WithdrawRequest.status == WithdrawStatus.PENDING
            )
        )
    ).scalar_one()

    kyc_pending = (
        await db.execute(
            select(func.count()).select_from(User).where(
                User.kyc_level == KycLevel.L0,
                User.kyc_real_name.is_not(None),
                User.kyc_id_number.is_not(None),
            )
        )
    ).scalar_one()

    shop_applications_pending = (
        await db.execute(
            select(func.count()).select_from(ShopApplication).where(ShopApplication.status == "pending")
        )
    ).scalar_one()

    agent_keys_active = (
        await db.execute(
            select(func.count()).select_from(ApiKey).where(ApiKey.status == ApiKeyStatus.ACTIVE)
        )
    ).scalar_one()
    agent_users_total = (
        await db.execute(select(func.count(func.distinct(ApiKey.user_id))).select_from(ApiKey))
    ).scalar_one()

    return AdminStatsResponse(
        users_total=users_total,
        deals_total=deals_total,
        deals_in_progress=deals_in_progress,
        deals_disputed=deals_disputed,
        users_today=users_today,
        deals_today=deals_today,
        offers_published=offers_published,
        intents_open=intents_open,
        wallet_deposits_cents=int(deposits or 0),
        wallet_payments_cents=int(payments or 0),
        wallet_commission_cents=int(commission or 0),
        withdrawals_pending=int(withdrawals_pending or 0),
        kyc_pending=int(kyc_pending or 0),
        shop_applications_pending=int(shop_applications_pending or 0),
        agent_keys_active=int(agent_keys_active or 0),
        agent_users_total=int(agent_users_total or 0),
    )


async def get_payment_stats(db: AsyncSession, *, days: int = 7) -> PaymentStatsResponse:
    days = max(1, min(days, 90))
    today_start = _utc_today_start()
    range_start = today_start - timedelta(days=days - 1)

    paid_filter = PaymentOrder.status == "paid"

    today_income = (
        await db.execute(
            select(func.coalesce(func.sum(PaymentOrder.amount_cents), 0)).where(
                paid_filter, PaymentOrder.paid_at >= today_start
            )
        )
    ).scalar_one()
    today_orders = (
        await db.execute(
            select(func.count()).select_from(PaymentOrder).where(
                paid_filter, PaymentOrder.paid_at >= today_start
            )
        )
    ).scalar_one()

    total_income = (
        await db.execute(
            select(func.coalesce(func.sum(PaymentOrder.amount_cents), 0)).where(paid_filter)
        )
    ).scalar_one()
    total_orders = (
        await db.execute(select(func.count()).select_from(PaymentOrder).where(paid_filter))
    ).scalar_one()

    avg_amount = int(total_income / total_orders) if total_orders else 0

    day_col = func.date_trunc("day", PaymentOrder.paid_at).label("day")
    daily_rows = (
        await db.execute(
            select(
                day_col,
                func.coalesce(func.sum(PaymentOrder.amount_cents), 0).label("income_cents"),
                func.count().label("order_count"),
            )
            .where(paid_filter, PaymentOrder.paid_at >= range_start)
            .group_by(day_col)
            .order_by(day_col)
        )
    ).all()
    daily_map = {
        row.day.date().isoformat(): {
            "date": row.day.date().isoformat(),
            "income_cents": int(row.income_cents or 0),
            "order_count": int(row.order_count or 0),
        }
        for row in daily_rows
        if row.day is not None
    }
    daily: list[dict] = []
    for i in range(days):
        day = (range_start + timedelta(days=i)).date().isoformat()
        daily.append(
            daily_map.get(day, {"date": day, "income_cents": 0, "order_count": 0})
        )

    channel_rows = (
        await db.execute(
            select(
                PaymentOrder.channel,
                func.coalesce(func.sum(PaymentOrder.amount_cents), 0).label("amount_cents"),
                func.count().label("order_count"),
            )
            .where(paid_filter)
            .group_by(PaymentOrder.channel)
            .order_by(func.sum(PaymentOrder.amount_cents).desc())
        )
    ).all()
    channels = [
        {
            "channel": row.channel,
            "amount_cents": int(row.amount_cents or 0),
            "order_count": int(row.order_count or 0),
        }
        for row in channel_rows
    ]

    top_rows = (
        await db.execute(
            select(
                User.email,
                User.display_name,
                func.coalesce(func.sum(PaymentOrder.amount_cents), 0).label("amount_cents"),
            )
            .join(User, User.id == PaymentOrder.user_id)
            .where(paid_filter)
            .group_by(User.id, User.email, User.display_name)
            .order_by(func.sum(PaymentOrder.amount_cents).desc())
            .limit(10)
        )
    ).all()
    top_users = [
        {
            "email": row.email,
            "display_name": row.display_name,
            "amount_cents": int(row.amount_cents or 0),
        }
        for row in top_rows
    ]

    return PaymentStatsResponse(
        today_income_cents=int(today_income or 0),
        today_orders=int(today_orders or 0),
        total_income_cents=int(total_income or 0),
        total_orders=int(total_orders or 0),
        avg_amount_cents=avg_amount,
        daily=daily,
        channels=channels,
        top_users=top_users,
    )


def _build_daily_count_series(
    rows: list,
    *,
    days: int,
    range_start: datetime,
) -> list[dict]:
    daily_map = {
        row.day.date().isoformat(): int(row.count or 0)
        for row in rows
        if row.day is not None
    }
    series: list[dict] = []
    for i in range(days):
        day = (range_start + timedelta(days=i)).date().isoformat()
        series.append({"date": day, "count": daily_map.get(day, 0)})
    return series


async def get_dashboard_analytics(
    db: AsyncSession, *, days: int = 7
) -> DashboardAnalyticsResponse:
    days = max(1, min(days, 90))
    today_start = _utc_today_start()
    range_start = today_start - timedelta(days=days - 1)

    stats = await get_platform_stats(db)
    payment = await get_payment_stats(db, days=days)

    deal_status_rows = (
        await db.execute(select(Deal.status, func.count()).group_by(Deal.status))
    ).all()
    deals_by_status = [{"status": row[0], "count": int(row[1])} for row in deal_status_rows]

    user_day_col = func.date_trunc("day", User.created_at).label("day")
    user_daily_rows = (
        await db.execute(
            select(user_day_col, func.count().label("count"))
            .where(User.created_at >= range_start)
            .group_by(user_day_col)
            .order_by(user_day_col)
        )
    ).all()
    daily_users = _build_daily_count_series(user_daily_rows, days=days, range_start=range_start)

    deal_day_col = func.date_trunc("day", Deal.created_at).label("day")
    deal_daily_rows = (
        await db.execute(
            select(deal_day_col, func.count().label("count"))
            .where(Deal.created_at >= range_start)
            .group_by(deal_day_col)
            .order_by(deal_day_col)
        )
    ).all()
    daily_deals = _build_daily_count_series(deal_daily_rows, days=days, range_start=range_start)

    ledger_rows = (
        await db.execute(
            select(
                WalletLedger.entry_type,
                func.coalesce(func.sum(func.abs(WalletLedger.amount_cents)), 0).label(
                    "amount_cents"
                ),
                func.count().label("entry_count"),
            )
            .where(WalletLedger.created_at >= range_start)
            .group_by(WalletLedger.entry_type)
            .order_by(func.sum(func.abs(WalletLedger.amount_cents)).desc())
        )
    ).all()
    ledger_by_type = [
        {
            "entry_type": row.entry_type,
            "amount_cents": int(row.amount_cents or 0),
            "entry_count": int(row.entry_count or 0),
        }
        for row in ledger_rows
    ]

    top_active_rows = (
        await db.execute(
            select(
                User.email,
                User.display_name,
                func.count().label("deal_count"),
            )
            .join(Deal, Deal.buyer_id == User.id)
            .where(Deal.created_at >= range_start)
            .group_by(User.id, User.email, User.display_name)
            .order_by(func.count().desc())
            .limit(12)
        )
    ).all()
    top_active_users = [
        {
            "email": row.email,
            "display_name": row.display_name,
            "deal_count": int(row.deal_count or 0),
        }
        for row in top_active_rows
    ]

    return DashboardAnalyticsResponse(
        stats=stats,
        payment=payment,
        deals_by_status=deals_by_status,
        daily_users=daily_users,
        daily_deals=daily_deals,
        ledger_by_type=ledger_by_type,
        top_active_users=top_active_users,
    )


async def get_ops_health(db: AsyncSession) -> OpsHealthResponse:
    stats = await get_platform_stats(db)
    payment = await get_payment_config_info(db)

    completed = (
        await db.execute(
            select(func.count()).select_from(Deal).where(Deal.status == DealStatus.COMPLETED)
        )
    ).scalar_one()
    total_deals = stats.deals_total or 0
    completion_rate = (completed / total_deals * 100) if total_deals else 100.0
    disputed_rate = (stats.deals_disputed / total_deals * 100) if total_deals else 0.0
    sla_percent = completion_rate

    health = 100
    health -= min(stats.deals_disputed * 8, 35)
    health -= min(stats.withdrawals_pending * 3, 25)
    if stats.deals_in_progress > 20:
        health -= 10
    health_score = max(0, min(100, int(health)))

    if health_score >= 80:
        health_label = "healthy"
    elif health_score >= 55:
        health_label = "risk"
    else:
        health_label = "critical"

    db_ok, db_detail = await probe_database(db)
    redis_ok, redis_detail = await probe_redis()
    payment_resource = _payment_resource(payment)

    resources = [
        {"name": "API 服务", "status": "normal", "value": "运行中"},
        {
            "name": "数据库",
            "status": "normal" if db_ok else "error",
            "value": db_detail,
        },
        {
            "name": "Redis",
            "status": "normal" if redis_ok else "error",
            "value": redis_detail,
        },
        payment_resource,
        {
            "name": "Agent 接入",
            "status": "normal" if stats.agent_keys_active else "idle",
            "value": f"{stats.agent_keys_active} 活跃 Key",
        },
    ]

    return OpsHealthResponse(
        health_score=health_score,
        health_label=health_label,
        sla_percent=round(sla_percent, 2),
        disputed_rate=round(disputed_rate, 2),
        completion_rate=round(completion_rate, 2),
        pending_withdrawals=stats.withdrawals_pending,
        deals_in_progress=stats.deals_in_progress,
        agent_keys_active=stats.agent_keys_active,
        agent_users_total=stats.agent_users_total,
        resources=resources,
    )


def _payment_resource(payment: PaymentConfigInfo) -> dict:
    provider_labels = {
        "wechat": "微信",
        "alipay": "支付宝",
        "test": "测试",
    }
    provider = payment.payment_provider
    label = provider_labels.get(provider, provider)

    if not payment.payment_enabled:
        return {"name": "支付通道", "status": "idle", "value": "支付已关闭"}

    configured_flags = {
        "wechat": payment.wechat_configured,
        "alipay": payment.alipay_configured,
        "test": True,
    }
    configured = configured_flags.get(provider, False)
    if provider not in configured_flags:
        configured = any(
            (
                payment.wechat_configured,
                payment.alipay_configured,
                payment.easypay_configured,
                payment.stripe_configured,
            )
        )

    if configured:
        return {"name": "支付通道", "status": "normal", "value": f"{label} 已配置"}

    return {"name": "支付通道", "status": "warning", "value": f"{label} 未配置"}


async def list_users(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    status: str | None = None,
    search: str | None = None,
) -> dict:
    page = max(page, 1)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

    query = select(User, Wallet.balance_cents).outerjoin(Wallet, Wallet.user_id == User.id)
    count_query = select(func.count()).select_from(User)

    if status:
        query = query.where(User.status == status)
        count_query = count_query.where(User.status == status)

    if search and search.strip():
        term = f"%{search.strip()}%"
        search_filter = or_(User.email.ilike(term), User.display_name.ilike(term))
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(
        query.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = result.all()

    items = []
    for user, balance_cents in rows:
        profile = user_to_profile(user).model_dump()
        profile["wallet_balance_cents"] = int(balance_cents or 0)
        items.append(profile)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def update_user_status(
    db: AsyncSession,
    *,
    user_id: UUID,
    status: UserStatus,
    current: CurrentUser,
) -> UserProfile:
    if user_id == current.id and status != UserStatus.ACTIVE:
        raise_auth_error(
            code=ERR_ADMIN_SELF_SUSPEND,
            message="admin cannot suspend themselves",
            http_status=422,
        )

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise_auth_error(
            code=ERR_ADMIN_USER_NOT_FOUND,
            message="user not found",
            http_status=404,
        )

    user.status = status
    await db.commit()
    await db.refresh(user)
    return user_to_profile(user)


async def list_all_deals(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    status: str | None = None,
) -> dict:
    page = max(page, 1)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

    query = select(Deal)
    count_query = select(func.count()).select_from(Deal)

    if status:
        query = query.where(Deal.status == status)
        count_query = count_query.where(Deal.status == status)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(
        query.order_by(Deal.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    deals = result.scalars().all()

    ext_map: dict[UUID, DealExtension] = {}
    if deals:
        deal_ids = [deal.id for deal in deals]
        ext_result = await db.execute(
            select(DealExtension).where(DealExtension.deal_id.in_(deal_ids))
        )
        ext_map = {ext.deal_id: ext for ext in ext_result.scalars().all()}

    return {
        "items": [
            _deal_to_response(deal, ext_map.get(deal.id)).model_dump() for deal in deals
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def get_deal_admin(
    db: AsyncSession,
    *,
    deal_id: UUID,
    current: CurrentUser,
) -> DealResponse:
    return await get_deal(db, deal_id=deal_id, current=current)


async def list_all_offers(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    status: str | None = None,
) -> dict:
    page = max(page, 1)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

    query = select(Offer)
    count_query = select(func.count()).select_from(Offer)
    if status:
        query = query.where(Offer.status == status)
        count_query = count_query.where(Offer.status == status)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(
        query.order_by(Offer.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    offers = result.scalars().all()
    return {
        "items": [offer_to_response(o).model_dump() for o in offers],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def list_all_intents(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    status: str | None = None,
) -> dict:
    page = max(page, 1)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

    query = select(Intent)
    count_query = select(func.count()).select_from(Intent)
    if status:
        query = query.where(Intent.status == status)
        count_query = count_query.where(Intent.status == status)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(
        query.order_by(Intent.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    intents = result.scalars().all()
    return {
        "items": [intent_to_response(i).model_dump() for i in intents],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def admin_update_offer_status(
    db: AsyncSession,
    *,
    offer_id: UUID,
    status: str,
    admin_id: UUID,
) -> dict:
    if status not in (OfferStatus.PUBLISHED, OfferStatus.PAUSED):
        raise_auth_error(code=47004, message="status must be published or paused", http_status=400)

    result = await db.execute(select(Offer).where(Offer.id == offer_id))
    offer = result.scalar_one_or_none()
    if offer is None:
        raise_auth_error(code=47005, message="offer not found", http_status=404)

    offer.status = status
    await log_admin_action(
        db,
        admin_id=admin_id,
        action="update_offer_status",
        target_type="offer",
        target_id=str(offer_id),
        detail=status,
    )
    await db.commit()
    await db.refresh(offer)
    return offer_to_response(offer).model_dump()


async def admin_update_intent_status(
    db: AsyncSession,
    *,
    intent_id: UUID,
    status: str,
    admin_id: UUID,
) -> dict:
    if status != IntentStatus.CLOSED:
        raise_auth_error(code=47006, message="admin can only close intents", http_status=400)

    result = await db.execute(select(Intent).where(Intent.id == intent_id))
    intent = result.scalar_one_or_none()
    if intent is None:
        raise_auth_error(code=47007, message="intent not found", http_status=404)

    intent.status = IntentStatus.CLOSED
    await log_admin_action(
        db,
        admin_id=admin_id,
        action="close_intent",
        target_type="intent",
        target_id=str(intent_id),
        detail=None,
    )
    await db.commit()
    await db.refresh(intent)
    return intent_to_response(intent).model_dump()


async def list_announcements(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    status: str | None = None,
    search: str | None = None,
) -> dict:
    page = max(page, 1)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

    query = select(PlatformAnnouncement)
    count_query = select(func.count()).select_from(PlatformAnnouncement)

    if status:
        query = query.where(PlatformAnnouncement.status == status)
        count_query = count_query.where(PlatformAnnouncement.status == status)

    if search and search.strip():
        term = f"%{search.strip()}%"
        search_filter = or_(
            PlatformAnnouncement.title.ilike(term),
            PlatformAnnouncement.content.ilike(term),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(
        query.order_by(PlatformAnnouncement.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = result.scalars().all()
    return {
        "items": [_announcement_to_dict(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def create_announcement(
    db: AsyncSession,
    *,
    admin_id: UUID,
    payload: dict,
) -> dict:
    row = PlatformAnnouncement(**payload)
    db.add(row)
    await log_admin_action(
        db,
        admin_id=admin_id,
        action="create_announcement",
        target_type="announcement",
        target_id=None,
        detail=row.title,
    )
    await db.commit()
    await db.refresh(row)
    return _announcement_to_dict(row)


async def update_announcement(
    db: AsyncSession,
    *,
    announcement_id: int,
    admin_id: UUID,
    payload: dict,
) -> dict:
    result = await db.execute(
        select(PlatformAnnouncement).where(PlatformAnnouncement.id == announcement_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise_auth_error(code=47008, message="announcement not found", http_status=404)

    for key, value in payload.items():
        setattr(row, key, value)

    await log_admin_action(
        db,
        admin_id=admin_id,
        action="update_announcement",
        target_type="announcement",
        target_id=str(announcement_id),
        detail=row.title,
    )
    await db.commit()
    await db.refresh(row)
    return _announcement_to_dict(row)


async def delete_announcement(
    db: AsyncSession,
    *,
    announcement_id: int,
    admin_id: UUID,
) -> None:
    result = await db.execute(
        select(PlatformAnnouncement).where(PlatformAnnouncement.id == announcement_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise_auth_error(code=47008, message="announcement not found", http_status=404)

    title = row.title
    await db.delete(row)
    await log_admin_action(
        db,
        admin_id=admin_id,
        action="delete_announcement",
        target_type="announcement",
        target_id=str(announcement_id),
        detail=title,
    )
    await db.commit()


async def get_agent_stats(db: AsyncSession) -> AgentStatsResponse:
    keys_total = (await db.execute(select(func.count()).select_from(ApiKey))).scalar_one()
    keys_active = (
        await db.execute(
            select(func.count()).select_from(ApiKey).where(ApiKey.status == ApiKeyStatus.ACTIVE)
        )
    ).scalar_one()
    keys_revoked = (
        await db.execute(
            select(func.count()).select_from(ApiKey).where(ApiKey.status == ApiKeyStatus.REVOKED)
        )
    ).scalar_one()
    keys_rotated = (
        await db.execute(
            select(func.count()).select_from(ApiKey).where(ApiKey.status == ApiKeyStatus.ROTATED)
        )
    ).scalar_one()
    users_with_keys = (
        await db.execute(select(func.count(func.distinct(ApiKey.user_id))).select_from(ApiKey))
    ).scalar_one()
    return AgentStatsResponse(
        keys_total=int(keys_total or 0),
        keys_active=int(keys_active or 0),
        keys_revoked=int(keys_revoked or 0),
        keys_rotated=int(keys_rotated or 0),
        users_with_keys=int(users_with_keys or 0),
    )


async def list_admin_api_keys(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    status: str | None = None,
    search: str | None = None,
) -> dict:
    page = max(page, 1)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

    query = select(ApiKey, User).join(User, User.id == ApiKey.user_id)
    count_query = select(func.count()).select_from(ApiKey).join(User, User.id == ApiKey.user_id)

    if status:
        query = query.where(ApiKey.status == status)
        count_query = count_query.where(ApiKey.status == status)

    if search:
        term = f"%{search.strip()}%"
        filt = or_(
            User.email.ilike(term),
            User.display_name.ilike(term),
            ApiKey.platform_user_id.ilike(term),
            ApiKey.name.ilike(term),
            ApiKey.key_prefix.ilike(term),
        )
        query = query.where(filt)
        count_query = count_query.where(filt)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(
        query.order_by(ApiKey.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = result.all()
    return {
        "items": [
            {
                "id": str(key.id),
                "user_id": str(user.id),
                "user_email": user.email,
                "user_display_name": user.display_name,
                "platform_user_id": key.platform_user_id,
                "name": key.name,
                "key_prefix": key.key_prefix,
                "status": key.status,
                "created_at": key.created_at.isoformat(),
            }
            for key, user in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def admin_revoke_api_key(
    db: AsyncSession,
    *,
    key_id: UUID,
    admin_id: UUID,
) -> dict:
    result = await db.execute(
        select(ApiKey, User)
        .join(User, User.id == ApiKey.user_id)
        .where(ApiKey.id == key_id, ApiKey.status == ApiKeyStatus.ACTIVE)
    )
    row = result.one_or_none()
    if row is None:
        raise_auth_error(code=40401, message="api key not found", http_status=404)

    api_key, user = row
    api_key.status = ApiKeyStatus.REVOKED
    await log_admin_action(
        db,
        admin_id=admin_id,
        action="revoke_api_key",
        target_type="api_key",
        target_id=str(key_id),
        detail=f"{user.email} / {api_key.platform_user_id}",
    )
    await db.commit()
    await db.refresh(api_key)
    return {
        "id": str(api_key.id),
        "user_id": str(user.id),
        "user_email": user.email,
        "user_display_name": user.display_name,
        "platform_user_id": api_key.platform_user_id,
        "name": api_key.name,
        "key_prefix": api_key.key_prefix,
        "status": api_key.status,
        "created_at": api_key.created_at.isoformat(),
    }
