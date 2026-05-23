from enum import StrEnum


class IntentChannel(StrEnum):
    HUMAN = "human"
    AGENT = "agent"


class IntentSettlement(StrEnum):
    FIAT = "fiat"
    POINTS = "points"


class IntentStatus(StrEnum):
    OPEN = "open"
    MATCHING = "matching"
    MATCHED = "matched"
    AUCTIONING = "auctioning"
    SELECTED = "selected"
    DEAL = "deal"
    CLOSED = "closed"


INTENT_CREATED_QUEUE = "intent.created"

# intents 模块错误码（43000–43999）
ERR_INTENT_NOT_FOUND = 43001
ERR_INTENT_FORBIDDEN = 43002
ERR_INTENT_INVALID_STATUS = 43003
ERR_INTENT_PARSE_FAILED = 43004
