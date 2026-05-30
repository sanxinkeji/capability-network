from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.core.database import get_db
from app.deals.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.deals.idempotency import execute_idempotent
from app.deals.schemas import (
    DealConfirmRequest,
    DealCreateRequest,
    DealDeliverRequest,
    DealDisputeRequest,
    DealBuyFromOfferRequest,
    DealMessageCreateRequest,
    WebhookRegisterRequest,
    WebhookRegistrationResponse,
)
from app.deals.service import (
    buy_from_offer,
    confirm_deal,
    create_deal,
    deliver_deal,
    dispute_deal,
    get_deal,
    list_deals,
    pay_deal,
    refund_deal,
)
from app.deals.messages import list_deal_messages, post_deal_message
from app.deals.webhooks import list_webhooks, register_webhook
from app.schemas.response import success

router = APIRouter(prefix="/deals", tags=["deals"])


@router.post("/webhooks")
async def register_webhook_endpoint(
    payload: WebhookRegisterRequest,
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    registration = register_webhook(
        user_id=current.id,
        url=payload.url,
        events=payload.events,
        secret=payload.secret,
    )
    response = WebhookRegistrationResponse(
        id=registration.id,
        url=registration.url,
        events=registration.events,
        created_at=registration.created_at.isoformat(),
    )
    return success(response.model_dump())


@router.get("/webhooks")
async def list_webhooks_endpoint(
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    registrations = list_webhooks(user_id=current.id)
    items = [
        WebhookRegistrationResponse(
            id=item.id,
            url=item.url,
            events=item.events,
            created_at=item.created_at.isoformat(),
        ).model_dump()
        for item in registrations
    ]
    return success(items)


@router.post("")
async def create_deal_endpoint(
    payload: DealCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    deal = await execute_idempotent(
        db,
        idempotency_key=idempotency_key,
        operation="create",
        deal_id=None,
        actor_id=current.id,
        handler=lambda: create_deal(db, current=current, payload=payload),
    )
    return success(deal.model_dump())


@router.get("")
async def list_deals_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
):
    data = await list_deals(db, current=current, page=page, page_size=page_size)
    return success(data)


@router.post("/buy-from-offer")
async def buy_from_offer_endpoint(
    payload: DealBuyFromOfferRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    result = await buy_from_offer(
        db,
        current=current,
        offer_id=payload.offer_id,
        buyer_note=payload.buyer_note,
    )
    return success(result.model_dump())


@router.get("/{deal_id}/messages")
async def list_deal_messages_endpoint(
    deal_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    data = await list_deal_messages(db, deal_id=deal_id, current=current)
    return success(data.model_dump())


@router.post("/{deal_id}/messages")
async def post_deal_message_endpoint(
    deal_id: UUID,
    payload: DealMessageCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    message = await post_deal_message(db, deal_id=deal_id, current=current, payload=payload)
    return success(message.model_dump())


@router.get("/{deal_id}")
async def get_deal_endpoint(
    deal_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    deal = await get_deal(db, deal_id=deal_id, current=current)
    return success(deal.model_dump())


@router.post("/{deal_id}/pay")
async def pay_deal_endpoint(
    deal_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    deal = await execute_idempotent(
        db,
        idempotency_key=idempotency_key,
        operation="pay",
        deal_id=deal_id,
        actor_id=current.id,
        handler=lambda: pay_deal(db, deal_id=deal_id, current=current),
    )
    return success(deal.model_dump())


@router.post("/{deal_id}/deliver")
async def deliver_deal_endpoint(
    deal_id: UUID,
    payload: DealDeliverRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    deal = await execute_idempotent(
        db,
        idempotency_key=idempotency_key,
        operation="deliver",
        deal_id=deal_id,
        actor_id=current.id,
        handler=lambda: deliver_deal(db, deal_id=deal_id, current=current, payload=payload),
    )
    return success(deal.model_dump())


@router.post("/{deal_id}/confirm")
async def confirm_deal_endpoint(
    deal_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
    payload: DealConfirmRequest | None = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    deal = await execute_idempotent(
        db,
        idempotency_key=idempotency_key,
        operation="confirm",
        deal_id=deal_id,
        actor_id=current.id,
        handler=lambda: confirm_deal(db, deal_id=deal_id, current=current, payload=payload),
    )
    return success(deal.model_dump())


@router.post("/{deal_id}/dispute")
async def dispute_deal_endpoint(
    deal_id: UUID,
    payload: DealDisputeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    deal = await execute_idempotent(
        db,
        idempotency_key=idempotency_key,
        operation="dispute",
        deal_id=deal_id,
        actor_id=current.id,
        handler=lambda: dispute_deal(db, deal_id=deal_id, current=current, payload=payload),
    )
    return success(deal.model_dump())


@router.post("/{deal_id}/refund")
async def refund_deal_endpoint(
    deal_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    deal = await execute_idempotent(
        db,
        idempotency_key=idempotency_key,
        operation="refund",
        deal_id=deal_id,
        actor_id=current.id,
        handler=lambda: refund_deal(db, deal_id=deal_id, current=current),
    )
    return success(deal.model_dump())
