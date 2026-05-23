import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import CurrentUser, raise_auth_error
from app.deals.constants import (
    AUTO_CONFIRM_AMOUNT_THRESHOLD_CENTS,
    AUTO_CONFIRM_DELAY_HOURS,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    PER_QUERY_CHANNEL,
    WEBHOOK_EVENT_STATUS_CHANGED,
    DealStatus,
    ERR_DEAL_CREATE_INVALID,
    ERR_DEAL_DELIVERY_REQUIRED,
    ERR_DEAL_DISPUTE_REASON_REQUIRED,
    ERR_DEAL_FORBIDDEN,
    ERR_DEAL_INVALID_STATUS,
    ERR_DEAL_MATCH_LOG_NOT_FOUND,
    ERR_DEAL_NOT_FOUND,
    ERR_DEAL_PAIR_MISMATCH,
    ERR_DEAL_VERSION_CONFLICT,
    ERR_DEAL_NOT_PENDING,
    ERR_DEAL_REFUND_FORBIDDEN,
)
from app.deals.models import Deal, DealExtension
from app.deals.schemas import (
    DealConfirmRequest,
    DealCreateRequest,
    DealDeliverRequest,
    DealDisputeRequest,
    DealResponse,
)
from app.deals.agent_delivery import (
    is_agent_auto_delivered,
    offer_channel_is_agent,
)
from app.deals.state_machine import assert_transition
from app.deals import tasks as deal_tasks
from app.deals import wallet_adapter
from app.deals.webhooks import dispatch_event
from app.intents.constants import IntentStatus
from app.intents.models import Intent
from app.intents.schemas import parse_tags_payload
from app.matching.models import MatchLog
from app.offers.constants import OfferStatus
from app.offers.models import Offer

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_dt(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _deal_to_response(deal: Deal, ext: DealExtension | None) -> DealResponse:
    return DealResponse(
        id=deal.id,
        offer_id=deal.offer_id,
        intent_id=deal.intent_id,
        buyer_id=deal.buyer_id,
        seller_id=deal.seller_id,
        amount_cents=deal.amount_cents,
        currency=deal.currency,
        status=DealStatus(deal.status),
        auto_confirm=ext.auto_confirm if ext else False,
        match_log_id=ext.match_log_id if ext else None,
        delivery_payload_url=ext.delivery_payload_url if ext else None,
        delivery_text=ext.delivery_text if ext else None,
        dispute_reason=deal.dispute_reason,
        refund_amount_cents=deal.refund_amount_cents,
        auto_confirm_deadline=(
            ext.auto_confirm_deadline.isoformat() if ext and ext.auto_confirm_deadline else None
        ),
        agent_auto_delivered=is_agent_auto_delivered(ext.delivery_text if ext else None),
        created_at=deal.created_at.isoformat(),
        updated_at=deal.updated_at.isoformat(),
        completed_at=deal.completed_at.isoformat() if deal.completed_at else None,
    )


async def _get_deal_bundle(
    db: AsyncSession, deal_id: UUID
) -> tuple[Deal, DealExtension | None]:
    result = await db.execute(select(Deal).where(Deal.id == deal_id))
    deal = result.scalar_one_or_none()
    if deal is None:
        raise_auth_error(code=ERR_DEAL_NOT_FOUND, message="deal not found", http_status=404)

    ext_result = await db.execute(select(DealExtension).where(DealExtension.deal_id == deal_id))
    ext = ext_result.scalar_one_or_none()
    return deal, ext


def _ensure_participant(deal: Deal, current: CurrentUser) -> None:
    if current.id not in (deal.buyer_id, deal.seller_id) and current.role != "admin":
        raise_auth_error(code=ERR_DEAL_FORBIDDEN, message="deal access denied", http_status=403)


def _check_version(deal: Deal, expected_updated_at: datetime | None) -> None:
    if expected_updated_at is None:
        return
    if _normalize_dt(deal.updated_at) != _normalize_dt(expected_updated_at):
        raise_auth_error(
            code=ERR_DEAL_VERSION_CONFLICT,
            message="deal was modified by another request",
            http_status=409,
        )


async def _emit_status_changed(deal: Deal, *, from_status: str, to_status: str) -> None:
    await dispatch_event(
        event=WEBHOOK_EVENT_STATUS_CHANGED,
        payload={
            "deal_id": str(deal.id),
            "from_status": from_status,
            "to_status": to_status,
            "buyer_id": str(deal.buyer_id),
            "seller_id": str(deal.seller_id),
            "amount_cents": deal.amount_cents,
            "currency": deal.currency,
        },
    )


def _resolve_auto_confirm(*, channel: str, amount_cents: int) -> bool:
    return channel == PER_QUERY_CHANNEL and amount_cents < AUTO_CONFIRM_AMOUNT_THRESHOLD_CENTS


async def _resolve_intent_offer(
    db: AsyncSession, payload: DealCreateRequest
) -> tuple[Intent, Offer, UUID | None]:
    match_log_id: UUID | None = None

    if payload.match_log_id is not None:
        log_result = await db.execute(select(MatchLog).where(MatchLog.id == payload.match_log_id))
        match_log = log_result.scalar_one_or_none()
        if match_log is None:
            raise_auth_error(
                code=ERR_DEAL_MATCH_LOG_NOT_FOUND,
                message="match log not found",
                http_status=404,
            )
        intent_id = match_log.intent_id
        offer_id = match_log.offer_id
        match_log_id = match_log.id
    else:
        intent_id = payload.intent_id  # type: ignore[assignment]
        offer_id = payload.offer_id  # type: ignore[assignment]

    intent_result = await db.execute(select(Intent).where(Intent.id == intent_id))
    intent = intent_result.scalar_one_or_none()
    if intent is None:
        raise_auth_error(code=ERR_DEAL_NOT_FOUND, message="intent not found", http_status=404)

    offer_result = await db.execute(select(Offer).where(Offer.id == offer_id))
    offer = offer_result.scalar_one_or_none()
    if offer is None:
        raise_auth_error(code=ERR_DEAL_NOT_FOUND, message="offer not found", http_status=404)

    if payload.match_log_id is None and (intent.id != intent_id or offer.id != offer_id):
        raise_auth_error(
            code=ERR_DEAL_PAIR_MISMATCH,
            message="intent and offer pair mismatch",
            http_status=422,
        )

    return intent, offer, match_log_id


async def intent_has_deal(db: AsyncSession, intent_id: UUID) -> bool:
    result = await db.execute(select(Deal.id).where(Deal.intent_id == intent_id).limit(1))
    return result.scalar_one_or_none() is not None


async def create_deal_for_auction(
    db: AsyncSession,
    *,
    current: CurrentUser,
    intent: Intent,
    offer: Offer,
    match_log_id: UUID | None,
    amount_cents: int,
) -> Deal:
    if intent.user_id != current.id:
        raise_auth_error(code=ERR_DEAL_FORBIDDEN, message="only buyer can create deal", http_status=403)

    if await intent_has_deal(db, intent.id):
        raise_auth_error(
            code=ERR_DEAL_CREATE_INVALID,
            message="intent already has a deal",
            http_status=409,
        )

    if offer.status != OfferStatus.PUBLISHED:
        raise_auth_error(
            code=ERR_DEAL_CREATE_INVALID,
            message="offer must be published",
            http_status=409,
        )

    if offer.user_id == intent.user_id:
        raise_auth_error(
            code=ERR_DEAL_CREATE_INVALID,
            message="buyer and seller must be different users",
            http_status=422,
        )

    if amount_cents > intent.budget_cents or offer.currency != intent.currency:
        raise_auth_error(
            code=ERR_DEAL_CREATE_INVALID,
            message="bid amount or currency incompatible with intent",
            http_status=422,
        )

    intent_meta = parse_tags_payload(intent.tags)
    channel = str(intent_meta.get("channel", "human"))
    auto_confirm = _resolve_auto_confirm(channel=channel, amount_cents=amount_cents)

    deal = Deal(
        offer_id=offer.id,
        intent_id=intent.id,
        buyer_id=intent.user_id,
        seller_id=offer.user_id,
        amount_cents=amount_cents,
        currency=offer.currency,
        status=DealStatus.PENDING,
    )
    db.add(deal)
    await db.flush()

    extension = DealExtension(
        deal_id=deal.id,
        match_log_id=match_log_id,
        auto_confirm=auto_confirm,
    )
    db.add(extension)
    await db.flush()
    await db.refresh(deal)
    return deal


async def create_deal(
    db: AsyncSession,
    *,
    current: CurrentUser,
    payload: DealCreateRequest,
) -> DealResponse:
    intent, offer, match_log_id = await _resolve_intent_offer(db, payload)

    if intent.user_id != current.id:
        raise_auth_error(code=ERR_DEAL_FORBIDDEN, message="only buyer can create deal", http_status=403)

    if await intent_has_deal(db, intent.id):
        raise_auth_error(
            code=ERR_DEAL_CREATE_INVALID,
            message="intent already has a deal",
            http_status=409,
        )

    if intent.status in (
        IntentStatus.AUCTIONING,
        IntentStatus.SELECTED,
        IntentStatus.DEAL,
    ):
        raise_auth_error(
            code=ERR_DEAL_CREATE_INVALID,
            message="intent is in auction flow; use auction select instead",
            http_status=409,
        )

    if intent.status not in (IntentStatus.OPEN, IntentStatus.MATCHED, IntentStatus.MATCHING):
        raise_auth_error(
            code=ERR_DEAL_CREATE_INVALID,
            message="intent is not open for deal creation",
            http_status=409,
        )

    if offer.status != OfferStatus.PUBLISHED:
        raise_auth_error(
            code=ERR_DEAL_CREATE_INVALID,
            message="offer must be published",
            http_status=409,
        )

    if offer.user_id == intent.user_id:
        raise_auth_error(
            code=ERR_DEAL_CREATE_INVALID,
            message="buyer and seller must be different users",
            http_status=422,
        )

    if offer.price_cents > intent.budget_cents or offer.currency != intent.currency:
        raise_auth_error(
            code=ERR_DEAL_CREATE_INVALID,
            message="offer price or currency incompatible with intent",
            http_status=422,
        )

    intent_meta = parse_tags_payload(intent.tags)
    channel = str(intent_meta.get("channel", "human"))
    auto_confirm = _resolve_auto_confirm(channel=channel, amount_cents=offer.price_cents)

    deal = Deal(
        offer_id=offer.id,
        intent_id=intent.id,
        buyer_id=intent.user_id,
        seller_id=offer.user_id,
        amount_cents=offer.price_cents,
        currency=offer.currency,
        status=DealStatus.PENDING,
    )
    db.add(deal)
    await db.flush()

    extension = DealExtension(
        deal_id=deal.id,
        match_log_id=match_log_id,
        auto_confirm=auto_confirm,
    )
    db.add(extension)
    intent.status = IntentStatus.MATCHED

    await db.commit()
    await db.refresh(deal)
    await db.refresh(extension)

    await _emit_status_changed(deal, from_status=DealStatus.PENDING, to_status=deal.status)
    logger.info(
        "deal created: id=%s status=pending auto_confirm=%s",
        deal.id,
        auto_confirm,
    )
    return _deal_to_response(deal, extension)


async def _apply_delivery(
    db: AsyncSession,
    deal: Deal,
    ext: DealExtension | None,
    *,
    text: str | None,
    payload_url: str | None,
) -> DealExtension:
    assert_transition(deal.status, DealStatus.DELIVERED)
    deal.status = DealStatus.DELIVERED

    if ext is None:
        ext = DealExtension(deal_id=deal.id, auto_confirm=False)
        db.add(ext)

    ext.delivery_payload_url = payload_url
    ext.delivery_text = text

    if ext.auto_confirm:
        await _complete_deal(db, deal, ext, trigger="auto_on_deliver")
    else:
        deadline = deal_tasks.schedule_auto_confirm(deal.id, delay_hours=AUTO_CONFIRM_DELAY_HOURS)
        ext.auto_confirm_deadline = deadline

    return ext


async def auto_deliver_deal(
    db: AsyncSession,
    *,
    deal_id: UUID,
    delivery_text: str,
    payload_url: str | None = None,
) -> DealResponse | None:
    """Agent 通道：由外部 Agent 提交真实交付内容。"""
    deal, ext = await _get_deal_bundle(db, deal_id)
    if deal.status != DealStatus.IN_PROGRESS:
        return None

    offer = (
        await db.execute(select(Offer).where(Offer.id == deal.offer_id))
    ).scalar_one_or_none()
    if offer is None or not offer_channel_is_agent(offer):
        return None

    from_status = deal.status
    ext = await _apply_delivery(db, deal, ext, text=delivery_text, payload_url=payload_url)

    await db.flush()
    await db.refresh(deal)
    await db.refresh(ext)
    await _emit_status_changed(deal, from_status=from_status, to_status=deal.status)
    logger.info("agent auto-delivered: deal_id=%s offer_id=%s", deal.id, offer.id)
    return _deal_to_response(deal, ext)


async def pay_deal(
    db: AsyncSession,
    *,
    deal_id: UUID,
    current: CurrentUser,
) -> DealResponse:
    deal, ext = await _get_deal_bundle(db, deal_id)

    if current.id != deal.buyer_id:
        raise_auth_error(code=ERR_DEAL_FORBIDDEN, message="only buyer can pay", http_status=403)

    if deal.status != DealStatus.PENDING:
        raise_auth_error(
            code=ERR_DEAL_NOT_PENDING,
            message="deal must be in pending status to pay",
            http_status=409,
        )

    try:
        await wallet_adapter.freeze(
            db,
            user_id=deal.buyer_id,
            deal_id=deal.id,
            amount=deal.amount_cents,
        )
    except Exception:
        await db.rollback()
        raise

    from_status = deal.status
    assert_transition(from_status, DealStatus.PAID)
    deal.status = DealStatus.PAID
    assert_transition(deal.status, DealStatus.IN_PROGRESS)
    deal.status = DealStatus.IN_PROGRESS

    await db.commit()
    await db.refresh(deal)
    if ext:
        await db.refresh(ext)

    await _emit_status_changed(deal, from_status=from_status, to_status=deal.status)
    logger.info("deal paid: id=%s frozen=%s status=%s", deal.id, deal.amount_cents, deal.status)
    return _deal_to_response(deal, ext)


async def get_deal(
    db: AsyncSession,
    *,
    deal_id: UUID,
    current: CurrentUser,
) -> DealResponse:
    deal, ext = await _get_deal_bundle(db, deal_id)
    _ensure_participant(deal, current)
    return _deal_to_response(deal, ext)


async def list_deals(
    db: AsyncSession,
    *,
    current: CurrentUser,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> dict:
    page = max(page, 1)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

    participant_filter = or_(Deal.buyer_id == current.id, Deal.seller_id == current.id)
    total = (
        await db.execute(select(func.count()).select_from(Deal).where(participant_filter))
    ).scalar_one()

    result = await db.execute(
        select(Deal)
        .where(participant_filter)
        .order_by(Deal.created_at.desc())
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


async def deliver_deal(
    db: AsyncSession,
    *,
    deal_id: UUID,
    current: CurrentUser,
    payload: DealDeliverRequest,
) -> DealResponse:
    deal, ext = await _get_deal_bundle(db, deal_id)
    _ensure_participant(deal, current)

    if current.id != deal.seller_id:
        raise_auth_error(code=ERR_DEAL_FORBIDDEN, message="only seller can deliver", http_status=403)

    if not payload.payload_url and not payload.text:
        raise_auth_error(
            code=ERR_DEAL_DELIVERY_REQUIRED,
            message="payload_url or text is required",
            http_status=422,
        )

    from_status = deal.status
    ext = await _apply_delivery(
        db,
        deal,
        ext,
        text=payload.text,
        payload_url=payload.payload_url,
    )

    await db.commit()
    await db.refresh(deal)
    await db.refresh(ext)

    await _emit_status_changed(deal, from_status=from_status, to_status=deal.status)
    return _deal_to_response(deal, ext)


async def confirm_deal(
    db: AsyncSession,
    *,
    deal_id: UUID,
    current: CurrentUser,
    payload: DealConfirmRequest | None = None,
) -> DealResponse:
    deal, ext = await _get_deal_bundle(db, deal_id)
    _ensure_participant(deal, current)

    if current.id != deal.buyer_id and current.role != "admin":
        raise_auth_error(code=ERR_DEAL_FORBIDDEN, message="only buyer can confirm", http_status=403)

    _check_version(deal, payload.expected_updated_at if payload else None)

    if deal.status != DealStatus.DELIVERED:
        raise_auth_error(
            code=ERR_DEAL_INVALID_STATUS,
            message="deal must be in delivered status to confirm",
            http_status=409,
        )

    from_status = deal.status
    await _complete_deal(db, deal, ext, trigger="buyer_confirm")
    await db.commit()
    await db.refresh(deal)
    if ext:
        await db.refresh(ext)

    await _emit_status_changed(deal, from_status=from_status, to_status=deal.status)
    return _deal_to_response(deal, ext)


async def auto_confirm_deal(db: AsyncSession, *, deal_id: UUID) -> DealResponse | None:
    deal, ext = await _get_deal_bundle(db, deal_id)
    if deal.status != DealStatus.DELIVERED:
        return None

    from_status = deal.status
    await _complete_deal(db, deal, ext, trigger="auto_confirm_timeout")
    await db.commit()
    await db.refresh(deal)
    if ext:
        await db.refresh(ext)

    await _emit_status_changed(deal, from_status=from_status, to_status=deal.status)
    return _deal_to_response(deal, ext)


async def _complete_deal(
    db: AsyncSession,
    deal: Deal,
    ext: DealExtension | None,
    *,
    trigger: str,
) -> None:
    assert_transition(deal.status, DealStatus.COMPLETED)
    deal_tasks.cancel_auto_confirm(deal.id)

    await wallet_adapter.settle(db, deal_id=deal.id)

    deal.status = DealStatus.COMPLETED
    deal.completed_at = _utc_now()
    if ext:
        ext.auto_confirm_deadline = None

    logger.info("deal settled: id=%s trigger=%s", deal.id, trigger)


async def dispute_deal(
    db: AsyncSession,
    *,
    deal_id: UUID,
    current: CurrentUser,
    payload: DealDisputeRequest,
) -> DealResponse:
    deal, ext = await _get_deal_bundle(db, deal_id)
    _ensure_participant(deal, current)

    if deal.status not in (DealStatus.IN_PROGRESS, DealStatus.DELIVERED):
        raise_auth_error(
            code=ERR_DEAL_INVALID_STATUS,
            message="deal cannot be disputed in current status",
            http_status=409,
        )

    if not payload.dispute_reason.strip():
        raise_auth_error(
            code=ERR_DEAL_DISPUTE_REASON_REQUIRED,
            message="dispute_reason is required",
            http_status=422,
        )

    from_status = deal.status
    assert_transition(from_status, DealStatus.DISPUTED)
    deal.status = DealStatus.DISPUTED
    deal.dispute_reason = payload.dispute_reason.strip()
    deal_tasks.cancel_auto_confirm(deal.id)

    if ext is None:
        ext = DealExtension(deal_id=deal.id, auto_confirm=False)
        db.add(ext)
    ext.disputed_by_id = current.id
    if current.id == deal.seller_id:
        ext.negotiated_refund = True
    ext.auto_confirm_deadline = None

    await db.commit()
    await db.refresh(deal)
    if ext:
        await db.refresh(ext)

    await _emit_status_changed(deal, from_status=from_status, to_status=deal.status)
    logger.info("deal disputed: id=%s funds remain frozen", deal.id)
    return _deal_to_response(deal, ext)


async def refund_deal(
    db: AsyncSession,
    *,
    deal_id: UUID,
    current: CurrentUser,
) -> DealResponse:
    deal, ext = await _get_deal_bundle(db, deal_id)

    if not _can_refund(deal, ext, current):
        raise_auth_error(
            code=ERR_DEAL_REFUND_FORBIDDEN,
            message="refund requires admin or negotiated buyer refund after seller dispute",
            http_status=403,
        )

    if deal.status != DealStatus.DISPUTED:
        raise_auth_error(
            code=ERR_DEAL_INVALID_STATUS,
            message="only disputed deals can be refunded",
            http_status=409,
        )

    from_status = deal.status
    assert_transition(from_status, DealStatus.REFUNDED)

    await wallet_adapter.unfreeze(
        db,
        user_id=deal.buyer_id,
        deal_id=deal.id,
        amount=deal.amount_cents,
    )

    deal.status = DealStatus.REFUNDED
    deal.refund_amount_cents = deal.amount_cents
    deal.completed_at = _utc_now()
    deal_tasks.cancel_auto_confirm(deal.id)

    await db.commit()
    await db.refresh(deal)
    if ext:
        await db.refresh(ext)

    await _emit_status_changed(deal, from_status=from_status, to_status=deal.status)
    return _deal_to_response(deal, ext)


def _can_refund(deal: Deal, ext: DealExtension | None, current: CurrentUser) -> bool:
    if current.role == "admin":
        return True
    if (
        current.id == deal.buyer_id
        and ext is not None
        and ext.negotiated_refund
        and ext.disputed_by_id == deal.seller_id
    ):
        return True
    return False
