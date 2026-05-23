from app.deals.constants import DealStatus

TERMINAL_STATUSES = frozenset(
    {DealStatus.COMPLETED, DealStatus.REFUNDED, DealStatus.CANCELLED}
)

ALLOWED_TRANSITIONS: dict[DealStatus, frozenset[DealStatus]] = {
    DealStatus.PENDING: frozenset({DealStatus.PAID, DealStatus.CANCELLED}),
    DealStatus.PAID: frozenset({DealStatus.IN_PROGRESS, DealStatus.CANCELLED, DealStatus.REFUNDED}),
    DealStatus.IN_PROGRESS: frozenset(
        {DealStatus.DELIVERED, DealStatus.DISPUTED, DealStatus.CANCELLED}
    ),
    DealStatus.DELIVERED: frozenset({DealStatus.COMPLETED, DealStatus.DISPUTED}),
    DealStatus.DISPUTED: frozenset(
        {DealStatus.COMPLETED, DealStatus.REFUNDED, DealStatus.IN_PROGRESS}
    ),
    DealStatus.COMPLETED: frozenset(),
    DealStatus.REFUNDED: frozenset(),
    DealStatus.CANCELLED: frozenset(),
}


def can_transition(from_status: str, to_status: str) -> bool:
    try:
        source = DealStatus(from_status)
        target = DealStatus(to_status)
    except ValueError:
        return False
    return target in ALLOWED_TRANSITIONS.get(source, frozenset())


def assert_transition(from_status: str, to_status: str) -> None:
    if not can_transition(from_status, to_status):
        from app.auth.schemas import raise_auth_error
        from app.deals.constants import ERR_DEAL_INVALID_STATUS

        raise_auth_error(
            code=ERR_DEAL_INVALID_STATUS,
            message=f"cannot transition deal from '{from_status}' to '{to_status}'",
            http_status=409,
        )
