from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class GeneratePlatformCodesRequest(BaseModel):
    code_type: str = Field(pattern="^(invite|recharge)$")
    count: int = Field(ge=1, le=500)
    expires_at: datetime | None = None
    value_cents: int | None = Field(default=None, ge=1)


class RedeemCodeRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)


class PlatformCodeResponse(BaseModel):
    id: str
    code: str
    code_type: str
    value_cents: int | None
    expires_at: str | None
    used_at: str | None
    used_by_id: str | None
    batch_id: str
    status: str
    created_at: str
