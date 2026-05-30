from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.core.database import get_db
from app.offers.constants import OfferChannel, OfferStatus
from app.offers.schemas import OfferCreateRequest, OfferUpdateRequest
from app.offers.service import (
    create_offer,
    get_marketplace_offer,
    get_offer,
    list_marketplace_offers,
    list_offers,
    publish_offer,
    update_offer,
)
from app.platform.enforcement import require_marketplace_enabled
from app.platform.service import get_or_create_settings
from app.schemas.response import success

router = APIRouter(prefix="/offers", tags=["offers"])


@router.post("")
async def create_offer_endpoint(
    payload: OfferCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    offer = await create_offer(db, current=current, payload=payload)
    return success(offer.model_dump())


@router.get("")
async def list_offers_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
    category: str | None = None,
    channel: OfferChannel | None = None,
    status: OfferStatus | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    data = await list_offers(
        db,
        current=current,
        category=category,
        channel=str(channel) if channel else None,
        status=str(status) if status else None,
        page=page,
        page_size=page_size,
    )
    return success(data)


@router.get("/marketplace")
async def list_marketplace_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
    category: str | None = None,
    channel: OfferChannel | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    settings = await get_or_create_settings(db)
    require_marketplace_enabled(settings)
    data = await list_marketplace_offers(
        db,
        current=current,
        category=category,
        channel=str(channel) if channel else None,
        page=page,
        page_size=page_size,
    )
    return success(data)


@router.get("/marketplace/{offer_id}")
async def get_marketplace_offer_endpoint(
    offer_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    settings = await get_or_create_settings(db)
    require_marketplace_enabled(settings)
    data = await get_marketplace_offer(db, offer_id=offer_id, current=current)
    return success(data)


@router.get("/{offer_id}")
async def get_offer_endpoint(
    offer_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    offer = await get_offer(db, offer_id=offer_id, current=current)
    return success(offer.model_dump())


@router.patch("/{offer_id}")
async def update_offer_endpoint(
    offer_id: UUID,
    payload: OfferUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    offer = await update_offer(db, offer_id=offer_id, current=current, payload=payload)
    return success(offer.model_dump())


@router.post("/{offer_id}/publish")
async def publish_offer_endpoint(
    offer_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    offer = await publish_offer(db, offer_id=offer_id, current=current)
    return success(offer.model_dump())
