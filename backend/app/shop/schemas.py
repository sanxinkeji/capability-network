from uuid import UUID

from pydantic import BaseModel, Field


class ShopApplicationSubmitRequest(BaseModel):
    shop_name: str = Field(min_length=2, max_length=100)
    agent_platform: str = Field(pattern=r"^(openclaw|hermes|other)$")
    description: str = Field(min_length=10, max_length=2000)


class ShopApplicationResponse(BaseModel):
    id: UUID
    shop_name: str
    agent_platform: str
    description: str
    status: str
    review_note: str | None
    created_at: str
    reviewed_at: str | None

    model_config = {"from_attributes": True}


class ShopApplicationStatusResponse(BaseModel):
    has_application: bool
    is_seller: bool
    application: ShopApplicationResponse | None = None


class AdminShopApplicationItem(BaseModel):
    user_id: UUID
    email: str
    display_name: str
    shop_name: str
    agent_platform: str
    description: str
    status: str
    review_note: str | None
    created_at: str
    reviewed_at: str | None


class ShopApplicationRejectRequest(BaseModel):
    review_note: str = Field(min_length=1, max_length=500)
