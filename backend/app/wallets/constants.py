from enum import StrEnum


class LedgerEntryType(StrEnum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    FREEZE = "freeze"
    UNFREEZE = "unfreeze"
    PAYMENT = "payment"
    REFUND = "refund"
    FEE = "fee"
    POINTS_CREDIT = "points_credit"
    POINTS_DEBIT = "points_debit"


DEFAULT_COMMISSION_RATE = 0.10

# wallets 模块错误码（46000–46999）
ERR_WALLET_NOT_FOUND = 46001
ERR_WALLET_INSUFFICIENT_BALANCE = 46002
ERR_WALLET_INSUFFICIENT_FROZEN = 46003
ERR_WALLET_ALREADY_SETTLED = 46004
ERR_WALLET_DEAL_NOT_FOUND = 46005
ERR_WALLET_INVALID_AMOUNT = 46006
ERR_WALLET_FREEZE_NOT_FOUND = 46007
ERR_WALLET_PAYMENT_NOT_CONFIGURED = 46008
ERR_WALLET_PAYMENT_ORDER_NOT_FOUND = 46009
ERR_WALLET_PAYMENT_ORDER_INVALID = 46010
ERR_WALLET_WITHDRAW_NOT_FOUND = 46011
ERR_WALLET_WITHDRAW_INVALID = 46012


class PaymentOrderStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    EXPIRED = "expired"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentChannel(StrEnum):
    WECHAT = "wechat"
    ALIPAY = "alipay"


class WithdrawStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"


class PayoutMethod(StrEnum):
    ALIPAY = "alipay"
    WECHAT = "wechat"
    BANK = "bank"
