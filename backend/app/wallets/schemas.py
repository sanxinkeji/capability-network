from uuid import UUID

from pydantic import BaseModel, Field


class WalletResponse(BaseModel):
    id: UUID
    user_id: UUID
    balance_available: int
    balance_frozen: int
    points_non_withdrawable: int
    currency: str
    created_at: str
    updated_at: str


class CreateDepositOrderRequest(BaseModel):
    amount_cents: int = Field(gt=0, description="充值金额（分）")
    channel: str = Field(description="支付渠道：wechat | alipay")


class DepositOrderResponse(BaseModel):
    id: UUID
    amount_cents: int
    currency: str
    channel: str
    status: str
    provider: str
    provider_ref: str
    pay_url: str | None
    expires_at: str | None
    paid_at: str | None
    created_at: str
    wallet: WalletResponse | None = None


class LedgerEntryResponse(BaseModel):
    id: UUID
    wallet_id: UUID
    deal_id: UUID | None
    entry_type: str
    amount_cents: int
    balance_after: int
    description: str | None
    created_at: str


class WithdrawRequestPayload(BaseModel):
    amount_cents: int = Field(gt=0, description="提现金额（分）")
    payout_method: str = Field(description="alipay | wechat | bank")
    payout_account: str = Field(min_length=1, max_length=512, description="收款账号")
    payout_name: str = Field(min_length=1, max_length=128, description="收款人姓名")


class WithdrawRequestResponse(BaseModel):
    id: UUID
    amount_cents: int
    status: str
    payout_method: str
    payout_account: str
    payout_name: str
    admin_note: str | None
    provider_ref: str | None
    created_at: str
    processed_at: str | None
    wallet: WalletResponse


class AdminWithdrawAction(BaseModel):
    action: str = Field(description="approve | reject | complete")
    admin_note: str | None = None
    provider_ref: str | None = Field(default=None, description="打款流水号（complete 时填写）")


class FreezeResult(BaseModel):
    deal_id: UUID
    wallet_id: UUID
    amount_cents: int
    from_points_cents: int
    from_available_cents: int
    balance_frozen_after: int


class SettleResult(BaseModel):
    deal_id: UUID
    amount_cents: int
    commission_cents: int
    seller_net_cents: int
    buyer_wallet_id: UUID
    seller_wallet_id: UUID


class UnfreezeResult(BaseModel):
    deal_id: UUID
    wallet_id: UUID
    amount_cents: int
    to_points_cents: int
    to_available_cents: int
    balance_frozen_after: int
