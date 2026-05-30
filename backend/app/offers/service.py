from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import CurrentUser, raise_auth_error
from app.offers.constants import (
    ERR_OFFER_FORBIDDEN,
    ERR_OFFER_INVALID_STATUS,
    ERR_OFFER_NOT_FOUND,
    ERR_OFFER_PUBLISH_INCOMPLETE,
    OfferStatus,
)
from app.offers.models import Offer
from app.offers.schemas import (
    OfferCreateRequest,
    OfferResponse,
    OfferUpdateRequest,
    build_tags_payload,
    offer_to_response,
    parse_tags_payload,
)


def _ensure_owner(offer: Offer, current: CurrentUser) -> None:
    if offer.user_id != current.id:
        raise_auth_error(code=ERR_OFFER_FORBIDDEN, message="offer access denied", http_status=403)


async def create_offer(
    db: AsyncSession,
    *,
    current: CurrentUser,
    payload: OfferCreateRequest,
) -> OfferResponse:
    from app.auth.service import get_user_by_id
    from app.shop.service import require_seller

    user = await get_user_by_id(db, current.id)
    if user is None:
        raise_auth_error(code=ERR_OFFER_FORBIDDEN, message="user not found", http_status=403)
    require_seller(user)

    offer = Offer(
        user_id=current.id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        price_cents=payload.price_cents,
        currency=payload.currency.upper(),
        status=OfferStatus.DRAFT,
        tags=build_tags_payload(
            channel=payload.channel,
            billing_model=payload.billing_model,
            budget_min_cents=payload.budget_min_cents,
            budget_max_cents=payload.budget_max_cents,
            delivery_description=payload.delivery_description,
            acceptance_sample_url=payload.acceptance_sample_url,
        ),
    )
    db.add(offer)
    await db.commit()
    await db.refresh(offer)
    return offer_to_response(offer)


async def get_offer(
    db: AsyncSession,
    *,
    offer_id: UUID,
    current: CurrentUser,
) -> OfferResponse:
    offer = await _get_offer_or_404(db, offer_id)
    _ensure_owner(offer, current)
    return offer_to_response(offer)


async def update_offer(
    db: AsyncSession,
    *,
    offer_id: UUID,
    current: CurrentUser,
    payload: OfferUpdateRequest,
) -> OfferResponse:
    offer = await _get_offer_or_404(db, offer_id)
    _ensure_owner(offer, current)

    updates = payload.model_dump(exclude_unset=True)
    meta = parse_tags_payload(offer.tags)

    scalar_fields = {"title", "description", "category", "price_cents", "currency", "status"}
    meta_fields = {
        "channel",
        "billing_model",
        "budget_min_cents",
        "budget_max_cents",
        "delivery_description",
        "acceptance_sample_url",
    }

    for field in scalar_fields:
        if field in updates:
            value = updates[field]
            if field == "currency" and value is not None:
                value = value.upper()
            if field == "status" and value is not None:
                value = str(value)
            setattr(offer, field, value)

    for field in meta_fields:
        if field in updates:
            value = updates[field]
            if field == "acceptance_sample_url" and value is not None:
                value = str(value)
            meta[field] = value

    offer.tags = meta
    await db.commit()
    await db.refresh(offer)
    return offer_to_response(offer)


def _apply_offer_filters(
    query,
    *,
    category: str | None = None,
    channel: str | None = None,
    status: str | None = None,
):
    if category:
        query = query.where(Offer.category == category)
    if status:
        query = query.where(Offer.status == status)
    if channel:
        query = query.where(Offer.tags["channel"].as_string() == channel)
    return query


async def _paginate_offers(
    db: AsyncSession,
    query,
    *,
    page: int,
    page_size: int,
) -> dict:
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(Offer.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    offers = result.scalars().all()

    return {
        "items": [offer_to_response(offer).model_dump() for offer in offers],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def list_offers(
    db: AsyncSession,
    *,
    current: CurrentUser,
    category: str | None = None,
    channel: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    query = select(Offer).where(Offer.user_id == current.id)
    query = _apply_offer_filters(query, category=category, channel=channel, status=status)
    return await _paginate_offers(db, query, page=page, page_size=page_size)


async def list_marketplace_offers(
    db: AsyncSession,
    *,
    current: CurrentUser,
    category: str | None = None,
    channel: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    query = select(Offer).where(
        Offer.status == OfferStatus.PUBLISHED,
        Offer.user_id != current.id,
    )
    query = _apply_offer_filters(query, category=category, channel=channel)
    return await _paginate_offers(db, query, page=page, page_size=page_size)


async def get_marketplace_offer(
    db: AsyncSession,
    *,
    offer_id: UUID,
    current: CurrentUser,
) -> dict:
    from app.auth.models import User

    offer = await _get_offer_or_404(db, offer_id)
    if offer.status != OfferStatus.PUBLISHED:
        raise_auth_error(
            code=ERR_OFFER_INVALID_STATUS,
            message="offer is not published",
            http_status=404,
        )
    if offer.user_id == current.id:
        raise_auth_error(code=ERR_OFFER_FORBIDDEN, message="cannot buy own offer", http_status=403)

    seller = (
        await db.execute(select(User).where(User.id == offer.user_id))
    ).scalar_one_or_none()
    payload = offer_to_response(offer).model_dump()
    payload["seller_display_name"] = seller.display_name if seller else None
    return payload


async def publish_offer(
    db: AsyncSession,
    *,
    offer_id: UUID,
    current: CurrentUser,
) -> OfferResponse:
    offer = await _get_offer_or_404(db, offer_id)
    _ensure_owner(offer, current)

    if offer.status not in {OfferStatus.DRAFT, OfferStatus.PAUSED}:
        raise_auth_error(
            code=ERR_OFFER_INVALID_STATUS,
            message=f"cannot publish offer in status '{offer.status}'",
            http_status=409,
        )

    meta = parse_tags_payload(offer.tags)
    required_meta = ("channel", "billing_model")
    missing = [field for field in required_meta if not meta.get(field)]
    if missing or not offer.title or not offer.description or not offer.category:
        raise_auth_error(
            code=ERR_OFFER_PUBLISH_INCOMPLETE,
            message="offer is incomplete and cannot be published",
            http_status=422,
        )

    offer.status = OfferStatus.PUBLISHED
    await db.commit()
    await db.refresh(offer)
    return offer_to_response(offer)


async def _get_offer_or_404(db: AsyncSession, offer_id: UUID) -> Offer:
    result = await db.execute(select(Offer).where(Offer.id == offer_id))
    offer = result.scalar_one_or_none()
    if offer is None:
        raise_auth_error(code=ERR_OFFER_NOT_FOUND, message="offer not found", http_status=404)
    return offer
