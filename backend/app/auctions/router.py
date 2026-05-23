from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.auctions.schemas import AuctionBidRequest, AuctionJoinRequest, AuctionSelectRequest
from app.auctions.service import (
    get_auction,
    get_auction_by_intent,
    join_auction,
    select_bid,
    start_auction,
    submit_bid,
)
from app.core.database import get_db
from app.platform.enforcement import require_matching_enabled
from app.platform.service import get_or_create_settings
from app.schemas.response import success

router = APIRouter(tags=["auctions"])


@router.get("/intents/{intent_id}/auction")
async def get_intent_auction_endpoint(
    intent_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    settings = await get_or_create_settings(db)
    require_matching_enabled(settings)
    auction = await get_auction_by_intent(db, intent_id=intent_id, current=current)
    return success(auction.model_dump())


@router.post("/intents/{intent_id}/auction/join")
async def join_auction_endpoint(
    intent_id: UUID,
    payload: AuctionJoinRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    settings = await get_or_create_settings(db)
    require_matching_enabled(settings)
    auction = await join_auction(
        db,
        intent_id=intent_id,
        current=current,
        offer_id=payload.offer_id,
        match_log_id=payload.match_log_id,
    )
    return success(auction.model_dump())


@router.post("/intents/{intent_id}/auction/start")
async def start_auction_endpoint(
    intent_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    settings = await get_or_create_settings(db)
    require_matching_enabled(settings)
    auction = await start_auction(db, intent_id=intent_id, current=current)
    return success(auction.model_dump())


@router.get("/auctions/{auction_id}")
async def get_auction_endpoint(
    auction_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    settings = await get_or_create_settings(db)
    require_matching_enabled(settings)
    auction = await get_auction(db, auction_id=auction_id, current=current)
    return success(auction.model_dump())


@router.post("/auctions/{auction_id}/bid")
async def submit_bid_endpoint(
    auction_id: UUID,
    payload: AuctionBidRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    settings = await get_or_create_settings(db)
    require_matching_enabled(settings)
    auction = await submit_bid(
        db,
        auction_id=auction_id,
        current=current,
        amount_cents=payload.amount_cents,
    )
    return success(auction.model_dump())


@router.post("/auctions/{auction_id}/select")
async def select_bid_endpoint(
    auction_id: UUID,
    payload: AuctionSelectRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    settings = await get_or_create_settings(db)
    require_matching_enabled(settings)
    auction = await select_bid(
        db,
        auction_id=auction_id,
        current=current,
        bid_id=payload.bid_id,
    )
    return success(auction.model_dump())
