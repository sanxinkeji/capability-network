from enum import StrEnum


class KycLevel(StrEnum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"


class CallerType(StrEnum):
    HUMAN = "human"
    AGENT = "agent"


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class UserStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class ApiKeyStatus(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"
    ROTATED = "rotated"


# Auth-specific error codes (41000–41999)
ERR_INVALID_CREDENTIALS = 41001
ERR_ACCOUNT_SUSPENDED = 41002
ERR_REFRESH_TOKEN_INVALID = 41003
ERR_REFRESH_TOKEN_EXPIRED = 41004
ERR_API_KEY_INVALID = 41005
ERR_KYC_INSUFFICIENT = 41006
ERR_KYC_ALREADY_VERIFIED = 41010
ERR_KYC_PENDING = 41011
ERR_KYC_ID_DUPLICATE = 41012
ERR_KYC_NOT_FOUND = 41013
ERR_KYC_INVALID = 41014
ERR_LOGIN_LOCKED = 41009
ERR_EMAIL_NOT_VERIFIED = 41016
ERR_EMAIL_VERIFICATION_INVALID = 41017
ERR_EMAIL_VERIFICATION_EXPIRED = 41018
ERR_RATE_LIMIT = 42901

API_KEY_PREFIX = "cnk_"
PHONE_EMAIL_DOMAIN = "phone.capability.network"
