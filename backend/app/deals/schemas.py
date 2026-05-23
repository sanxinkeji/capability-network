from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.deals.constants import DealStatus


class DealCreateRequest(BaseModel):
    intent_id: UUID | None = None
    offer_id: UUID | None = None
    match_log_id: UUID | None = None

    @model_validator(mode="after")
    def validate_create_keys(self) -> "DealCreateRequest":
        by_pair = self.intent_id is not None and self.offer_id is not None
        by_log = self.match_log_id is not None
        if by_pair == by_log:
            raise ValueError("provide either (intent_id + offer_id) or match_log_id, not both")
        return self


class DealDeliverRequest(BaseModel):
    payload_url: str | None = Field(default=None, max_length=512)
    text: str | None = None

    @model_validator(mode="after")
    def require_delivery_payload(self) -> "DealDeliverRequest":
        if not self.payload_url and not self.text:
            raise ValueError("payload_url or text is required")
        return self


class DealDisputeRequest(BaseModel):
    dispute_reason: str = Field(min_length=1, max_length=2000)


class DealConfirmRequest(BaseModel):
    expected_updated_at: datetime | None = Field(
        default=None,
        description="乐观锁：客户端持有的 updated_at，冲突时返回 40901",
    )


class DealResponse(BaseModel):
    id: UUID
    offer_id: UUID
    intent_id: UUID
    buyer_id: UUID
    seller_id: UUID
    amount_cents: int
    currency: str
    status: DealStatus
    auto_confirm: bool
    match_log_id: UUID | None = None
    delivery_payload_url: str | None = None
    delivery_text: str | None = None
    dispute_reason: str | None = None
    refund_amount_cents: int | None = None
    auto_confirm_deadline: str | None = None
    agent_auto_delivered: bool = False
    created_at: str
    updated_at: str
    completed_at: str | None = None

    model_config = {"from_attributes": True}


class WebhookRegisterRequest(BaseModel):
    url: str = Field(min_length=8, max_length=512)
    events: list[str] = Field(default_factory=lambda: ["deals.status_changed"])
    secret: str | None = Field(default=None, max_length=128)


class WebhookRegistrationResponse(BaseModel):
    id: UUID
    url: str
    events: list[str]
    created_at: str
