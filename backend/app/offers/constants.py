from enum import StrEnum


class OfferChannel(StrEnum):
    HUMAN = "human"
    AGENT = "agent"


class BillingModel(StrEnum):
    PER_USE = "per_use"
    PER_QUERY = "per_query"
    PER_HOUR = "per_hour"


class OfferStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    PAUSED = "paused"


# offers 模块错误码（42000–42999）
ERR_OFFER_NOT_FOUND = 42001
ERR_OFFER_FORBIDDEN = 42002
ERR_OFFER_INVALID_STATUS = 42003
ERR_OFFER_PUBLISH_INCOMPLETE = 42004
