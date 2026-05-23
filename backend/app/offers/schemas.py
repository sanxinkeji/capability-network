from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from app.offers.constants import BillingModel, OfferChannel, OfferStatus


class OfferCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    category: str = Field(min_length=1, max_length=64)
    channel: OfferChannel
    billing_model: BillingModel
    price_cents: int = Field(ge=0)
    currency: str = Field(default="CNY", min_length=3, max_length=3)
    budget_min_cents: int | None = Field(default=None, ge=0)
    budget_max_cents: int | None = Field(default=None, ge=0)
    delivery_description: str | None = None
    acceptance_sample_url: HttpUrl | str | None = None

    @model_validator(mode="after")
    def validate_budget_range(self) -> "OfferCreateRequest":
        if (
            self.budget_min_cents is not None
            and self.budget_max_cents is not None
            and self.budget_min_cents > self.budget_max_cents
        ):
            raise ValueError("budget_min_cents must be less than or equal to budget_max_cents")
        return self


class OfferUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    category: str | None = Field(default=None, min_length=1, max_length=64)
    channel: OfferChannel | None = None
    billing_model: BillingModel | None = None
    price_cents: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    budget_min_cents: int | None = Field(default=None, ge=0)
    budget_max_cents: int | None = Field(default=None, ge=0)
    delivery_description: str | None = None
    acceptance_sample_url: HttpUrl | str | None = None
    status: OfferStatus | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: OfferStatus | None) -> OfferStatus | None:
        if value == OfferStatus.PUBLISHED:
            raise ValueError("use POST /offers/{id}/publish to publish an offer")
        return value

    @model_validator(mode="after")
    def validate_budget_range(self) -> "OfferUpdateRequest":
        if (
            self.budget_min_cents is not None
            and self.budget_max_cents is not None
            and self.budget_min_cents > self.budget_max_cents
        ):
            raise ValueError("budget_min_cents must be less than or equal to budget_max_cents")
        return self


class OfferResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: str
    category: str
    channel: OfferChannel
    billing_model: BillingModel
    price_cents: int
    currency: str
    budget_min_cents: int | None
    budget_max_cents: int | None
    delivery_description: str | None
    acceptance_sample_url: str | None
    status: OfferStatus
    embedding: list[float] | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


def build_tags_payload(
    *,
    channel: OfferChannel,
    billing_model: BillingModel,
    budget_min_cents: int | None,
    budget_max_cents: int | None,
    delivery_description: str | None,
    acceptance_sample_url: str | None,
) -> dict[str, Any]:
    return {
        "channel": channel,
        "billing_model": billing_model,
        "budget_min_cents": budget_min_cents,
        "budget_max_cents": budget_max_cents,
        "delivery_description": delivery_description,
        "acceptance_sample_url": str(acceptance_sample_url) if acceptance_sample_url else None,
        "embedding": None,
    }


def parse_tags_payload(tags: dict[str, Any] | list[Any] | None) -> dict[str, Any]:
    if not tags or isinstance(tags, list):
        return {}
    return tags


def offer_to_response(offer) -> OfferResponse:
    meta = parse_tags_payload(offer.tags)
    return OfferResponse(
        id=offer.id,
        user_id=offer.user_id,
        title=offer.title,
        description=offer.description,
        category=offer.category,
        channel=OfferChannel(meta.get("channel", OfferChannel.HUMAN)),
        billing_model=BillingModel(meta.get("billing_model", BillingModel.PER_USE)),
        price_cents=offer.price_cents,
        currency=offer.currency,
        budget_min_cents=meta.get("budget_min_cents"),
        budget_max_cents=meta.get("budget_max_cents"),
        delivery_description=meta.get("delivery_description"),
        acceptance_sample_url=meta.get("acceptance_sample_url"),
        status=OfferStatus(offer.status),
        embedding=meta.get("embedding"),
        created_at=offer.created_at.isoformat(),
        updated_at=offer.updated_at.isoformat(),
    )
