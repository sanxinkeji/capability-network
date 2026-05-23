from uuid import UUID

from pydantic import BaseModel, Field

from app.auctions.constants import AuctionStatus


class AuctionJoinRequest(BaseModel):
    offer_id: UUID
    match_log_id: UUID | None = None


class AuctionBidRequest(BaseModel):
    amount_cents: int = Field(ge=1, description="出价金额（分），须 ≤ intent 预算")


class AuctionSelectRequest(BaseModel):
    bid_id: UUID


class AuctionParticipantResponse(BaseModel):
    id: UUID
    offer_id: UUID
    user_id: UUID
    match_log_id: UUID | None = None
    joined_at: str


class AuctionBidResponse(BaseModel):
    id: UUID
    participant_id: UUID
    offer_id: UUID
    user_id: UUID
    amount_cents: int
    created_at: str


class AuctionResponse(BaseModel):
    id: UUID
    intent_id: UUID
    status: AuctionStatus
    budget_cents: int
    currency: str
    selected_bid_id: UUID | None = None
    deal_id: UUID | None = None
    participant_count: int
    participants: list[AuctionParticipantResponse]
    bids: list[AuctionBidResponse]
    created_at: str
    updated_at: str
