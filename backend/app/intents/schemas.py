from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.intents.constants import IntentChannel, IntentSettlement, IntentStatus


def default_settlement_for_channel(channel: IntentChannel) -> IntentSettlement:
    return IntentSettlement.FIAT if channel == IntentChannel.HUMAN else IntentSettlement.POINTS


class IntentCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    category: str = Field(min_length=1, max_length=64)
    channel: IntentChannel = IntentChannel.HUMAN
    settlement: IntentSettlement | None = None
    budget_max: int = Field(ge=0, description="预算上限，单位：分")
    currency: str = Field(default="CNY", min_length=3, max_length=3)
    deadline: datetime | None = None
    acceptance_criteria: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def apply_settlement_default(self) -> "IntentCreateRequest":
        if self.settlement is None:
            self.settlement = default_settlement_for_channel(self.channel)
        return self

    @model_validator(mode="after")
    def validate_settlement_strategy(self) -> "IntentCreateRequest":
        expected = default_settlement_for_channel(self.channel)
        if self.settlement != expected:
            raise ValueError(
                f"settlement must be '{expected}' for channel '{self.channel}'"
            )
        return self


class IntentParseRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class IntentParseResponse(BaseModel):
    title: str
    description: str
    category: str
    channel: IntentChannel
    settlement: IntentSettlement
    budget_max: int
    currency: str
    deadline: datetime | None
    acceptance_criteria: dict[str, Any]
    parsed_by: str = Field(description="llm | rules")


class IntentResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: str
    category: str
    channel: IntentChannel
    settlement: IntentSettlement
    budget_max: int
    currency: str
    deadline: str | None
    acceptance_criteria: dict[str, Any]
    status: IntentStatus
    match_id: UUID | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


def build_tags_payload(
    *,
    channel: IntentChannel,
    settlement: IntentSettlement,
    deadline: datetime | None,
    acceptance_criteria: dict[str, Any],
    match_id: UUID | None = None,
) -> dict[str, Any]:
    return {
        "channel": channel,
        "settlement": settlement,
        "deadline": deadline.isoformat() if deadline else None,
        "acceptance_criteria": acceptance_criteria,
        "match_id": str(match_id) if match_id else None,
    }


def parse_tags_payload(tags: dict[str, Any] | list[Any] | None) -> dict[str, Any]:
    if not tags or isinstance(tags, list):
        return {}
    return tags


def intent_to_response(intent) -> IntentResponse:
    meta = parse_tags_payload(intent.tags)
    match_id_raw = meta.get("match_id")
    match_id: UUID | None = None
    if match_id_raw:
        try:
            match_id = UUID(str(match_id_raw))
        except ValueError:
            match_id = None
    return IntentResponse(
        id=intent.id,
        user_id=intent.user_id,
        title=intent.title,
        description=intent.description,
        category=intent.category,
        channel=IntentChannel(meta.get("channel", IntentChannel.HUMAN)),
        settlement=IntentSettlement(meta.get("settlement", IntentSettlement.FIAT)),
        budget_max=intent.budget_cents,
        currency=intent.currency,
        deadline=meta.get("deadline"),
        acceptance_criteria=meta.get("acceptance_criteria") or {},
        status=IntentStatus(intent.status),
        match_id=match_id,
        created_at=intent.created_at.isoformat(),
        updated_at=intent.updated_at.isoformat(),
    )
