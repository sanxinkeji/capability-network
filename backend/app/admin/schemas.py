from datetime import datetime

from pydantic import BaseModel, Field

from app.auth.constants import UserStatus


class AdminStatsResponse(BaseModel):
    users_total: int
    deals_total: int
    deals_in_progress: int
    deals_disputed: int
    users_today: int
    deals_today: int
    offers_published: int = 0
    intents_open: int = 0
    wallet_deposits_cents: int = 0
    wallet_payments_cents: int = 0
    wallet_commission_cents: int = 0
    withdrawals_pending: int = 0
    kyc_pending: int = 0
    shop_applications_pending: int = 0
    agent_keys_active: int = 0
    agent_users_total: int = 0


class AdminKycAction(BaseModel):
    action: str = Field(description="approve | reject")
    admin_note: str | None = None


class AdminUserStatusUpdate(BaseModel):
    status: UserStatus = Field(description="active or suspended")


class AdminWithdrawAction(BaseModel):
    action: str = Field(description="approve | reject | complete")
    admin_note: str | None = None
    provider_ref: str | None = None


class AdminPaymentOrderAction(BaseModel):
    action: str = Field(description="refund")
    admin_note: str | None = None


class AdminOfferStatusUpdate(BaseModel):
    status: str = Field(description="published | paused")


class AdminIntentStatusUpdate(BaseModel):
    status: str = Field(description="closed")


class AdminUserCredit(BaseModel):
    amount_cents: int = Field(ge=1)
    note: str | None = None


class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    status: str
    notify_mode: str
    audience: str
    starts_at: str | None
    ends_at: str | None
    created_at: str
    updated_at: str


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    content: str = ""
    status: str = Field(default="draft", pattern="^(draft|active)$")
    notify_mode: str = Field(default="popup", pattern="^(popup|banner)$")
    audience: str = Field(default="all", max_length=32)
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class AnnouncementUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=256)
    content: str | None = None
    status: str | None = Field(default=None, pattern="^(draft|active)$")
    notify_mode: str | None = Field(default=None, pattern="^(popup|banner)$")
    audience: str | None = Field(default=None, max_length=32)
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class PaymentStatsResponse(BaseModel):
    today_income_cents: int
    today_orders: int
    total_income_cents: int
    total_orders: int
    avg_amount_cents: int
    daily: list[dict]
    channels: list[dict]
    top_users: list[dict]


class DashboardAnalyticsResponse(BaseModel):
    stats: AdminStatsResponse
    payment: PaymentStatsResponse
    deals_by_status: list[dict]
    daily_users: list[dict]
    daily_deals: list[dict]
    ledger_by_type: list[dict]
    top_active_users: list[dict]


class OpsHealthResponse(BaseModel):
    health_score: int
    health_label: str
    sla_percent: float
    disputed_rate: float
    completion_rate: float
    pending_withdrawals: int
    deals_in_progress: int
    agent_keys_active: int = 0
    agent_users_total: int = 0
    resources: list[dict]


class AgentStatsResponse(BaseModel):
    keys_total: int
    keys_active: int
    keys_revoked: int
    keys_rotated: int
    users_with_keys: int


class AdminApiKeyItem(BaseModel):
    id: str
    user_id: str
    user_email: str
    user_display_name: str
    platform_user_id: str
    name: str | None
    key_prefix: str
    status: str
    created_at: str
