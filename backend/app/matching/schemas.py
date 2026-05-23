from uuid import UUID

from pydantic import BaseModel, Field


class MatchRunRequest(BaseModel):
    intent_id: UUID
    top_n: int = Field(default=10, ge=1, le=100)


class MatchCandidateResponse(BaseModel):
    match_log_id: UUID
    offer_id: UUID
    title: str
    description: str
    category: str
    channel: str
    price_cents: int
    currency: str
    match_score: float
    rank: int
    recommend_auto: bool
    score_breakdown: dict[str, float | bool]


class MatchRunResponse(BaseModel):
    intent_id: UUID
    algorithm: str
    total_candidates: int
    candidates: list[MatchCandidateResponse]
