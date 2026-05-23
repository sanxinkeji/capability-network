from app.auctions.constants import AuctionStatus, ERR_AUCTION_INVALID_STATUS
from app.auth.schemas import raise_auth_error
from app.intents.constants import IntentStatus


ALLOWED_TRANSITIONS: dict[AuctionStatus, set[AuctionStatus]] = {
    AuctionStatus.OPEN: {AuctionStatus.MATCHED},
    AuctionStatus.MATCHED: {AuctionStatus.AUCTIONING},
    AuctionStatus.AUCTIONING: {AuctionStatus.SELECTED},
    AuctionStatus.SELECTED: {AuctionStatus.DEAL},
    AuctionStatus.DEAL: set(),
}

INTENT_STATUS_FOR_AUCTION: dict[AuctionStatus, IntentStatus] = {
    AuctionStatus.OPEN: IntentStatus.OPEN,
    AuctionStatus.MATCHED: IntentStatus.MATCHED,
    AuctionStatus.AUCTIONING: IntentStatus.AUCTIONING,
    AuctionStatus.SELECTED: IntentStatus.SELECTED,
    AuctionStatus.DEAL: IntentStatus.DEAL,
}


def assert_auction_transition(current: AuctionStatus, target: AuctionStatus) -> None:
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise_auth_error(
            code=ERR_AUCTION_INVALID_STATUS,
            message=f"auction cannot transition from {current} to {target}",
            http_status=409,
        )


def intent_status_for_auction(status: AuctionStatus) -> IntentStatus:
    return INTENT_STATUS_FOR_AUCTION[status]
