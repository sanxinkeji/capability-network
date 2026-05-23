from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auctions.constants import (
    ERR_AUCTION_ALREADY_JOINED,
    ERR_AUCTION_BID_NOT_FOUND,
    ERR_AUCTION_BID_OVER_BUDGET,
    ERR_AUCTION_FORBIDDEN,
    ERR_AUCTION_INSUFFICIENT_PARTICIPANTS,
    ERR_AUCTION_INTENT_HAS_DEAL,
    ERR_AUCTION_INTENT_NOT_AGENT,
    ERR_AUCTION_INVALID_STATUS,
    ERR_AUCTION_NOT_FOUND,
    ERR_AUCTION_NOT_PARTICIPANT,
    ERR_AUCTION_OFFER_INVALID,
    ERR_AUCTION_PARTICIPANT_LIMIT,
    MAX_AUCTION_PARTICIPANTS,
    AuctionStatus,
)
from app.auctions.models import Auction, AuctionBid, AuctionParticipant
from app.auctions.schemas import (
    AuctionBidResponse,
    AuctionParticipantResponse,
    AuctionResponse,
)
from app.auctions.state_machine import assert_auction_transition, intent_status_for_auction
from app.auth.schemas import CurrentUser, raise_auth_error
from app.deals.service import create_deal_for_auction, intent_has_deal
from app.intents.constants import ERR_INTENT_NOT_FOUND, IntentChannel, IntentStatus
from app.intents.models import Intent
from app.intents.schemas import parse_tags_payload
from app.matching.models import MatchLog
from app.offers.constants import OfferStatus
from app.offers.models import Offer
from app.offers.schemas import parse_tags_payload as parse_offer_tags


def _auction_to_response(
    auction: Auction,
    *,
    intent: Intent,
    participants: list[AuctionParticipant],
    bids: list[AuctionBid],
) -> AuctionResponse:
    return AuctionResponse(
        id=auction.id,
        intent_id=auction.intent_id,
        status=AuctionStatus(auction.status),
        budget_cents=intent.budget_cents,
        currency=intent.currency,
        selected_bid_id=auction.selected_bid_id,
        deal_id=auction.deal_id,
        participant_count=len(participants),
        participants=[
            AuctionParticipantResponse(
                id=item.id,
                offer_id=item.offer_id,
                user_id=item.user_id,
                match_log_id=item.match_log_id,
                joined_at=item.joined_at.isoformat(),
            )
            for item in participants
        ],
        bids=[
            AuctionBidResponse(
                id=item.id,
                participant_id=item.participant_id,
                offer_id=item.offer_id,
                user_id=item.user_id,
                amount_cents=item.amount_cents,
                created_at=item.created_at.isoformat(),
            )
            for item in bids
        ],
        created_at=auction.created_at.isoformat(),
        updated_at=auction.updated_at.isoformat(),
    )


async def _get_intent_or_404(db: AsyncSession, intent_id: UUID) -> Intent:
    result = await db.execute(select(Intent).where(Intent.id == intent_id))
    intent = result.scalar_one_or_none()
    if intent is None:
        raise_auth_error(code=ERR_INTENT_NOT_FOUND, message="intent not found", http_status=404)
    return intent


async def _get_auction_or_404(db: AsyncSession, auction_id: UUID) -> Auction:
    result = await db.execute(select(Auction).where(Auction.id == auction_id))
    auction = result.scalar_one_or_none()
    if auction is None:
        raise_auth_error(code=ERR_AUCTION_NOT_FOUND, message="auction not found", http_status=404)
    return auction


async def _get_auction_bundle(
    db: AsyncSession, auction_id: UUID
) -> tuple[Auction, Intent, list[AuctionParticipant], list[AuctionBid]]:
    auction = await _get_auction_or_404(db, auction_id)
    intent = await _get_intent_or_404(db, auction.intent_id)

    participants_result = await db.execute(
        select(AuctionParticipant)
        .where(AuctionParticipant.auction_id == auction.id)
        .order_by(AuctionParticipant.joined_at.asc())
    )
    participants = list(participants_result.scalars().all())

    bids_result = await db.execute(
        select(AuctionBid)
        .where(AuctionBid.auction_id == auction.id)
        .order_by(AuctionBid.amount_cents.asc(), AuctionBid.created_at.asc())
    )
    bids = list(bids_result.scalars().all())
    return auction, intent, participants, bids


async def _get_or_create_auction(db: AsyncSession, intent: Intent) -> Auction:
    result = await db.execute(select(Auction).where(Auction.intent_id == intent.id))
    auction = result.scalar_one_or_none()
    if auction is not None:
        return auction

    auction = Auction(intent_id=intent.id, status=AuctionStatus.OPEN)
    db.add(auction)
    await db.flush()
    return auction


def _ensure_agent_intent(intent: Intent) -> None:
    meta = parse_tags_payload(intent.tags)
    channel = str(meta.get("channel", IntentChannel.HUMAN))
    if channel != IntentChannel.AGENT:
        raise_auth_error(
            code=ERR_AUCTION_INTENT_NOT_AGENT,
            message="auction is only available for agent channel intents",
            http_status=422,
        )


def _validate_offer_for_intent(intent: Intent, offer: Offer) -> None:
    if offer.status != OfferStatus.PUBLISHED:
        raise_auth_error(
            code=ERR_AUCTION_OFFER_INVALID,
            message="offer must be published",
            http_status=409,
        )
    if offer.category != intent.category or offer.currency != intent.currency:
        raise_auth_error(
            code=ERR_AUCTION_OFFER_INVALID,
            message="offer category or currency incompatible with intent",
            http_status=422,
        )
    offer_meta = parse_offer_tags(offer.tags)
    intent_meta = parse_tags_payload(intent.tags)
    if str(offer_meta.get("channel")) != str(intent_meta.get("channel")):
        raise_auth_error(
            code=ERR_AUCTION_OFFER_INVALID,
            message="offer channel incompatible with intent",
            http_status=422,
        )
    if offer.price_cents > intent.budget_cents:
        raise_auth_error(
            code=ERR_AUCTION_OFFER_INVALID,
            message="offer price exceeds intent budget",
            http_status=422,
        )


async def _sync_auction_status(
    db: AsyncSession,
    auction: Auction,
    intent: Intent,
    target: AuctionStatus,
) -> None:
    current = AuctionStatus(auction.status)
    if current == target:
        return
    assert_auction_transition(current, target)
    auction.status = target
    intent.status = intent_status_for_auction(target)


async def get_auction_by_intent(
    db: AsyncSession,
    *,
    intent_id: UUID,
    current: CurrentUser,
) -> AuctionResponse:
    intent = await _get_intent_or_404(db, intent_id)
    if intent.user_id != current.id and current.role != "admin":
        participant_check = await db.execute(
            select(AuctionParticipant.id)
            .join(Auction, Auction.id == AuctionParticipant.auction_id)
            .where(Auction.intent_id == intent_id, AuctionParticipant.user_id == current.id)
            .limit(1)
        )
        if participant_check.scalar_one_or_none() is None:
            raise_auth_error(code=ERR_AUCTION_FORBIDDEN, message="auction access denied", http_status=403)

    result = await db.execute(select(Auction).where(Auction.intent_id == intent_id))
    auction = result.scalar_one_or_none()
    if auction is None:
        raise_auth_error(code=ERR_AUCTION_NOT_FOUND, message="auction not found", http_status=404)

    _, _, participants, bids = await _get_auction_bundle(db, auction.id)
    return _auction_to_response(auction, intent=intent, participants=participants, bids=bids)


async def get_auction(
    db: AsyncSession,
    *,
    auction_id: UUID,
    current: CurrentUser,
) -> AuctionResponse:
    auction, intent, participants, bids = await _get_auction_bundle(db, auction_id)
    if intent.user_id != current.id and current.role != "admin":
        if not any(item.user_id == current.id for item in participants):
            raise_auth_error(code=ERR_AUCTION_FORBIDDEN, message="auction access denied", http_status=403)
    return _auction_to_response(auction, intent=intent, participants=participants, bids=bids)


async def join_auction(
    db: AsyncSession,
    *,
    intent_id: UUID,
    current: CurrentUser,
    offer_id: UUID,
    match_log_id: UUID | None = None,
) -> AuctionResponse:
    intent = await _get_intent_or_404(db, intent_id)
    _ensure_agent_intent(intent)

    if await intent_has_deal(db, intent.id):
        raise_auth_error(
            code=ERR_AUCTION_INTENT_HAS_DEAL,
            message="intent already has a deal",
            http_status=409,
        )

    status = IntentStatus(intent.status)
    if status not in (IntentStatus.OPEN, IntentStatus.MATCHED):
        raise_auth_error(
            code=ERR_AUCTION_INVALID_STATUS,
            message="intent is not accepting auction participants",
            http_status=409,
        )

    offer_result = await db.execute(select(Offer).where(Offer.id == offer_id))
    offer = offer_result.scalar_one_or_none()
    if offer is None:
        raise_auth_error(code=ERR_AUCTION_OFFER_INVALID, message="offer not found", http_status=404)

    if offer.user_id != current.id:
        raise_auth_error(code=ERR_AUCTION_FORBIDDEN, message="only offer owner can join", http_status=403)

    if offer.user_id == intent.user_id:
        raise_auth_error(
            code=ERR_AUCTION_OFFER_INVALID,
            message="buyer and seller must be different users",
            http_status=422,
        )

    _validate_offer_for_intent(intent, offer)

    if match_log_id is not None:
        log_result = await db.execute(select(MatchLog).where(MatchLog.id == match_log_id))
        match_log = log_result.scalar_one_or_none()
        if match_log is None or match_log.intent_id != intent.id or match_log.offer_id != offer.id:
            raise_auth_error(
                code=ERR_AUCTION_OFFER_INVALID,
                message="match log does not match intent and offer",
                http_status=422,
            )

    auction = await _get_or_create_auction(db, intent)
    auction_status = AuctionStatus(auction.status)
    if auction_status not in (AuctionStatus.OPEN, AuctionStatus.MATCHED):
        raise_auth_error(
            code=ERR_AUCTION_INVALID_STATUS,
            message="auction is not accepting new participants",
            http_status=409,
        )

    existing = await db.execute(
        select(AuctionParticipant).where(
            AuctionParticipant.auction_id == auction.id,
            AuctionParticipant.offer_id == offer.id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise_auth_error(
            code=ERR_AUCTION_ALREADY_JOINED,
            message="offer already joined this auction",
            http_status=409,
        )

    count_result = await db.execute(
        select(func.count()).select_from(AuctionParticipant).where(
            AuctionParticipant.auction_id == auction.id
        )
    )
    participant_count = int(count_result.scalar_one())
    if participant_count >= MAX_AUCTION_PARTICIPANTS:
        raise_auth_error(
            code=ERR_AUCTION_PARTICIPANT_LIMIT,
            message=f"auction participant limit reached ({MAX_AUCTION_PARTICIPANTS})",
            http_status=422,
        )

    participant = AuctionParticipant(
        auction_id=auction.id,
        offer_id=offer.id,
        user_id=current.id,
        match_log_id=match_log_id,
    )
    db.add(participant)
    await db.flush()

    new_count = participant_count + 1
    if new_count >= 2 and auction_status == AuctionStatus.OPEN:
        await _sync_auction_status(db, auction, intent, AuctionStatus.MATCHED)

    await db.commit()
    await db.refresh(auction)
    _, _, participants, bids = await _get_auction_bundle(db, auction.id)
    return _auction_to_response(auction, intent=intent, participants=participants, bids=bids)


async def start_auction(
    db: AsyncSession,
    *,
    intent_id: UUID,
    current: CurrentUser,
) -> AuctionResponse:
    intent = await _get_intent_or_404(db, intent_id)
    if intent.user_id != current.id:
        raise_auth_error(code=ERR_AUCTION_FORBIDDEN, message="only intent owner can start auction", http_status=403)

    _ensure_agent_intent(intent)

    if await intent_has_deal(db, intent.id):
        raise_auth_error(
            code=ERR_AUCTION_INTENT_HAS_DEAL,
            message="intent already has a deal",
            http_status=409,
        )

    result = await db.execute(select(Auction).where(Auction.intent_id == intent_id))
    auction = result.scalar_one_or_none()
    if auction is None:
        raise_auth_error(code=ERR_AUCTION_NOT_FOUND, message="auction not found", http_status=404)

    participants_result = await db.execute(
        select(AuctionParticipant).where(AuctionParticipant.auction_id == auction.id)
    )
    participants = list(participants_result.scalars().all())
    if len(participants) < 2:
        raise_auth_error(
            code=ERR_AUCTION_INSUFFICIENT_PARTICIPANTS,
            message="at least 2 participants required to start auction",
            http_status=422,
        )

    await _sync_auction_status(db, auction, intent, AuctionStatus.AUCTIONING)
    await db.commit()
    await db.refresh(auction)

    bids_result = await db.execute(
        select(AuctionBid).where(AuctionBid.auction_id == auction.id).order_by(AuctionBid.created_at.asc())
    )
    bids = list(bids_result.scalars().all())
    return _auction_to_response(auction, intent=intent, participants=participants, bids=bids)


async def submit_bid(
    db: AsyncSession,
    *,
    auction_id: UUID,
    current: CurrentUser,
    amount_cents: int,
) -> AuctionResponse:
    auction, intent, participants, _ = await _get_auction_bundle(db, auction_id)

    if AuctionStatus(auction.status) != AuctionStatus.AUCTIONING:
        raise_auth_error(
            code=ERR_AUCTION_INVALID_STATUS,
            message="auction is not accepting bids",
            http_status=409,
        )

    participant = next((item for item in participants if item.user_id == current.id), None)
    if participant is None:
        raise_auth_error(code=ERR_AUCTION_NOT_PARTICIPANT, message="not an auction participant", http_status=403)

    if amount_cents > intent.budget_cents:
        raise_auth_error(
            code=ERR_AUCTION_BID_OVER_BUDGET,
            message="bid amount exceeds intent budget",
            http_status=422,
        )

    bid = AuctionBid(
        auction_id=auction.id,
        participant_id=participant.id,
        offer_id=participant.offer_id,
        user_id=current.id,
        amount_cents=amount_cents,
    )
    db.add(bid)
    await db.commit()
    await db.refresh(auction)

    _, _, participants, bids = await _get_auction_bundle(db, auction.id)
    return _auction_to_response(auction, intent=intent, participants=participants, bids=bids)


async def select_bid(
    db: AsyncSession,
    *,
    auction_id: UUID,
    current: CurrentUser,
    bid_id: UUID,
) -> AuctionResponse:
    auction, intent, participants, bids = await _get_auction_bundle(db, auction_id)

    if intent.user_id != current.id:
        raise_auth_error(code=ERR_AUCTION_FORBIDDEN, message="only intent owner can select bid", http_status=403)

    if AuctionStatus(auction.status) != AuctionStatus.AUCTIONING:
        raise_auth_error(
            code=ERR_AUCTION_INVALID_STATUS,
            message="auction is not in bidding phase",
            http_status=409,
        )

    bid = next((item for item in bids if item.id == bid_id), None)
    if bid is None:
        raise_auth_error(code=ERR_AUCTION_BID_NOT_FOUND, message="bid not found", http_status=404)

    await _sync_auction_status(db, auction, intent, AuctionStatus.SELECTED)
    auction.selected_bid_id = bid.id

    participant = next((item for item in participants if item.id == bid.participant_id), None)
    if participant is None:
        raise_auth_error(code=ERR_AUCTION_BID_NOT_FOUND, message="bid participant not found", http_status=404)

    offer_result = await db.execute(select(Offer).where(Offer.id == bid.offer_id))
    offer = offer_result.scalar_one()

    deal = await create_deal_for_auction(
        db,
        current=current,
        intent=intent,
        offer=offer,
        match_log_id=participant.match_log_id,
        amount_cents=bid.amount_cents,
    )

    await _sync_auction_status(db, auction, intent, AuctionStatus.DEAL)
    auction.deal_id = deal.id

    await db.commit()
    await db.refresh(auction)

    _, _, participants, bids = await _get_auction_bundle(db, auction.id)
    response = _auction_to_response(auction, intent=intent, participants=participants, bids=bids)
    return response
