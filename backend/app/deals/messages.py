"""订单会话消息：支付后聊天、Agent 主动沟通。"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import CurrentUser, raise_auth_error
from app.deals.agent_delivery import offer_channel_is_agent
from app.deals.constants import (
    WEBHOOK_EVENT_MESSAGE_CREATED,
    DealMessageKind,
    DealMessageSenderRole,
    DealStatus,
    ERR_DEAL_FORBIDDEN,
    ERR_DEAL_MESSAGE_CLOSED,
    ERR_DEAL_MESSAGE_EMPTY,
    ERR_DEAL_NOT_FOUND,
)
from app.deals.models import Deal, DealExtension, DealMessage
from app.deals.schemas import DealMessageCreateRequest, DealMessageListResponse, DealMessageResponse
from app.deals.webhooks import dispatch_event
from app.intents.models import Intent
from app.offers.models import Offer

logger = logging.getLogger(__name__)

CHAT_WRITABLE_STATUSES = frozenset(
    {
        DealStatus.IN_PROGRESS,
        DealStatus.DELIVERED,
        DealStatus.DISPUTED,
    }
)


def _message_to_response(message: DealMessage) -> DealMessageResponse:
    return DealMessageResponse(
        id=message.id,
        deal_id=message.deal_id,
        sender_role=message.sender_role,
        sender_id=message.sender_id,
        body=message.body,
        kind=message.kind,
        created_at=message.created_at.isoformat(),
    )


async def _get_deal_or_404(db: AsyncSession, deal_id: UUID) -> Deal:
    deal = (await db.execute(select(Deal).where(Deal.id == deal_id))).scalar_one_or_none()
    if deal is None:
        raise_auth_error(code=ERR_DEAL_NOT_FOUND, message="deal not found", http_status=404)
    return deal


def _ensure_participant(deal: Deal, current: CurrentUser) -> None:
    if current.id not in (deal.buyer_id, deal.seller_id) and current.role != "admin":
        raise_auth_error(code=ERR_DEAL_FORBIDDEN, message="deal access denied", http_status=403)


def _resolve_sender_role(deal: Deal, current: CurrentUser) -> DealMessageSenderRole:
    if current.id == deal.buyer_id:
        return DealMessageSenderRole.BUYER
    if current.id == deal.seller_id:
        if current.caller_type == "agent":
            return DealMessageSenderRole.AGENT
        return DealMessageSenderRole.SELLER
    raise_auth_error(code=ERR_DEAL_FORBIDDEN, message="deal access denied", http_status=403)


async def _emit_message_created(message: DealMessage, *, deal: Deal) -> None:
    await dispatch_event(
        event=WEBHOOK_EVENT_MESSAGE_CREATED,
        payload={
            "deal_id": str(deal.id),
            "message_id": str(message.id),
            "sender_role": message.sender_role,
            "sender_id": str(message.sender_id) if message.sender_id else None,
            "kind": message.kind,
            "body": message.body,
            "buyer_id": str(deal.buyer_id),
            "seller_id": str(deal.seller_id),
            "deal_status": deal.status,
        },
    )


async def _insert_message(
    db: AsyncSession,
    *,
    deal: Deal,
    sender_role: DealMessageSenderRole | str,
    body: str,
    sender_id: UUID | None = None,
    kind: DealMessageKind | str = DealMessageKind.TEXT,
    emit_webhook: bool = True,
) -> DealMessage:
    text = body.strip()
    if not text:
        raise_auth_error(code=ERR_DEAL_MESSAGE_EMPTY, message="message body is required", http_status=422)

    message = DealMessage(
        deal_id=deal.id,
        sender_role=str(sender_role),
        sender_id=sender_id,
        body=text,
        kind=str(kind),
    )
    db.add(message)
    await db.flush()
    if emit_webhook:
        await _emit_message_created(message, deal=deal)
    return message


def _agent_greeting(*, offer: Offer, intent: Intent) -> str:
    desc = (intent.description or "").strip()
    desc_line = f"\n\n需求摘要：{desc}" if desc else ""
    return (
        f"你好！我是「{offer.title}」的智能助手 🦞\n"
        f"已收到你的订单：{intent.title}{desc_line}\n\n"
        "为了更好地为你交付，请补充：\n"
        "1. 具体格式与字数要求\n"
        "2. 截止时间\n"
        "3. 参考资料或特殊说明（如有）\n\n"
        "收到后我会立即开始处理。"
    )


def _demo_delivery_text(*, offer: Offer, intent: Intent, buyer_note: str) -> str:
    return (
        f"【{offer.title} · 演示交付】\n\n"
        f"需求：{intent.title}\n"
        f"你的补充：{buyer_note.strip() or '（无额外说明）'}\n\n"
        "---\n"
        "这是平台演示交付物。接入 OpenClaw 后，此处将替换为 Agent 真实产出（文档/PDF/链接等）。"
    )


async def bootstrap_chat_on_pay(
    db: AsyncSession,
    *,
    deal: Deal,
) -> list[DealMessage]:
    """支付成功后初始化订单会话。"""
    offer = (await db.execute(select(Offer).where(Offer.id == deal.offer_id))).scalar_one_or_none()
    intent = (await db.execute(select(Intent).where(Intent.id == deal.intent_id))).scalar_one_or_none()
    if offer is None or intent is None:
        return []

    messages: list[DealMessage] = []
    messages.append(
        await _insert_message(
            db,
            deal=deal,
            sender_role=DealMessageSenderRole.SYSTEM,
            body="✅ 支付成功！资金已托管在平台，履约完成后才会结算给商家。",
            emit_webhook=False,
        )
    )

    if offer_channel_is_agent(offer):
        messages.append(
            await _insert_message(
                db,
                deal=deal,
                sender_role=DealMessageSenderRole.AGENT,
                body=_agent_greeting(offer=offer, intent=intent),
                sender_id=deal.seller_id,
                emit_webhook=False,
            )
        )
    else:
        messages.append(
            await _insert_message(
                db,
                deal=deal,
                sender_role=DealMessageSenderRole.SYSTEM,
                body="商家已收到通知，可在本页沟通需求与交付进度。",
                emit_webhook=False,
            )
        )

    for message in messages:
        await _emit_message_created(message, deal=deal)

    return messages


async def append_delivery_message(
    db: AsyncSession,
    *,
    deal: Deal,
    delivery_text: str,
    payload_url: str | None = None,
    sender_role: DealMessageSenderRole = DealMessageSenderRole.AGENT,
) -> DealMessage:
    body = delivery_text.strip()
    if payload_url:
        body = f"{body}\n\n📎 交付物：{payload_url}" if body else f"📎 交付物：{payload_url}"
    return await _insert_message(
        db,
        deal=deal,
        sender_role=sender_role,
        body=body or "交付已完成，请验收。",
        sender_id=deal.seller_id,
        kind=DealMessageKind.DELIVERY,
    )


async def notify_delivery_in_chat(
    db: AsyncSession,
    *,
    deal: Deal,
    delivery_text: str,
    payload_url: str | None = None,
) -> DealMessage | None:
    offer = (await db.execute(select(Offer).where(Offer.id == deal.offer_id))).scalar_one_or_none()
    if offer is None:
        return None
    role = (
        DealMessageSenderRole.AGENT
        if offer_channel_is_agent(offer)
        else DealMessageSenderRole.SELLER
    )
    return await append_delivery_message(
        db,
        deal=deal,
        delivery_text=delivery_text,
        payload_url=payload_url,
        sender_role=role,
    )


async def list_deal_messages(
    db: AsyncSession,
    *,
    deal_id: UUID,
    current: CurrentUser,
) -> DealMessageListResponse:
    deal = await _get_deal_or_404(db, deal_id)
    _ensure_participant(deal, current)

    total = (
        await db.execute(
            select(func.count()).select_from(DealMessage).where(DealMessage.deal_id == deal_id)
        )
    ).scalar_one()

    result = await db.execute(
        select(DealMessage)
        .where(DealMessage.deal_id == deal_id)
        .order_by(DealMessage.created_at.asc(), DealMessage.id.asc())
    )
    items = [_message_to_response(row) for row in result.scalars().all()]
    return DealMessageListResponse(items=items, total=int(total))


async def post_deal_message(
    db: AsyncSession,
    *,
    deal_id: UUID,
    current: CurrentUser,
    payload: DealMessageCreateRequest,
) -> DealMessageResponse:
    deal = await _get_deal_or_404(db, deal_id)
    _ensure_participant(deal, current)

    if deal.status not in CHAT_WRITABLE_STATUSES:
        raise_auth_error(
            code=ERR_DEAL_MESSAGE_CLOSED,
            message="deal chat is closed for this status",
            http_status=409,
        )

    sender_role = _resolve_sender_role(deal, current)
    message = await _insert_message(
        db,
        deal=deal,
        sender_role=sender_role,
        body=payload.body,
        sender_id=current.id,
    )

    if sender_role == DealMessageSenderRole.BUYER and deal.status == DealStatus.IN_PROGRESS:
        await _maybe_demo_agent_flow(db, deal=deal, buyer_note=payload.body.strip())

    await db.commit()
    await db.refresh(message)
    return _message_to_response(message)


async def _maybe_demo_agent_flow(
    db: AsyncSession,
    *,
    deal: Deal,
    buyer_note: str,
) -> None:
    """演示：买家补充细节后，Agent 回复并自动交付（无需外部 OpenClaw）。"""
    offer = (await db.execute(select(Offer).where(Offer.id == deal.offer_id))).scalar_one_or_none()
    intent = (await db.execute(select(Intent).where(Intent.id == deal.intent_id))).scalar_one_or_none()
    if offer is None or intent is None or not offer_channel_is_agent(offer):
        return

    buyer_count = (
        await db.execute(
            select(func.count())
            .select_from(DealMessage)
            .where(
                DealMessage.deal_id == deal.id,
                DealMessage.sender_role == DealMessageSenderRole.BUYER,
            )
        )
    ).scalar_one()
    if int(buyer_count) != 1:
        return

    await _insert_message(
        db,
        deal=deal,
        sender_role=DealMessageSenderRole.AGENT,
        body="收到你的补充信息，我开始为你处理，请稍候… 🦞",
        sender_id=deal.seller_id,
        emit_webhook=False,
    )

    from app.deals.service import auto_deliver_deal

    delivery_text = _demo_delivery_text(offer=offer, intent=intent, buyer_note=buyer_note)
    delivered = await auto_deliver_deal(
        db,
        deal_id=deal.id,
        delivery_text=delivery_text,
    )
    if delivered is None:
        return

    logger.info("demo agent flow completed: deal_id=%s", deal.id)


async def post_agent_message_internal(
    db: AsyncSession,
    *,
    deal_id: UUID,
    current: CurrentUser,
    body: str,
    kind: DealMessageKind | str = DealMessageKind.TEXT,
) -> DealMessageResponse:
    """MCP / Agent 以卖方身份发消息。"""
    deal = await _get_deal_or_404(db, deal_id)
    if current.id != deal.seller_id and current.role != "admin":
        raise_auth_error(code=ERR_DEAL_FORBIDDEN, message="only seller can post agent messages", http_status=403)

    if deal.status not in CHAT_WRITABLE_STATUSES:
        raise_auth_error(
            code=ERR_DEAL_MESSAGE_CLOSED,
            message="deal chat is closed for this status",
            http_status=409,
        )

    message = await _insert_message(
        db,
        deal=deal,
        sender_role=DealMessageSenderRole.AGENT,
        body=body,
        sender_id=deal.seller_id,
        kind=kind,
    )
    await db.commit()
    await db.refresh(message)
    return _message_to_response(message)
