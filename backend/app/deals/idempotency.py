import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deals.constants import IDEMPOTENCY_TTL_HOURS
from app.deals.models import DealIdempotency
from app.deals.schemas import DealResponse

TypeHandler = Callable[[], Awaitable[DealResponse]]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def execute_idempotent(
    db: AsyncSession,
    *,
    idempotency_key: str | None,
    operation: str,
    deal_id: UUID | None,
    actor_id: UUID,
    handler: TypeHandler,
) -> DealResponse:
    if not idempotency_key:
        return await handler()

    now = _utc_now()
    result = await db.execute(
        select(DealIdempotency).where(
            DealIdempotency.idempotency_key == idempotency_key,
            DealIdempotency.operation == operation,
            DealIdempotency.deal_id == deal_id,
            DealIdempotency.expires_at > now,
        )
    )
    cached = result.scalar_one_or_none()
    if cached is not None:
        return DealResponse.model_validate_json(cached.response_json)

    response = await handler()

    record = DealIdempotency(
        idempotency_key=idempotency_key,
        operation=operation,
        deal_id=deal_id,
        actor_id=actor_id,
        response_json=response.model_dump_json(),
        expires_at=now + timedelta(hours=IDEMPOTENCY_TTL_HOURS),
    )
    db.add(record)
    await db.commit()
    return response


async def purge_expired(db: AsyncSession) -> int:
    now = _utc_now()
    result = await db.execute(
        select(DealIdempotency).where(DealIdempotency.expires_at <= now)
    )
    rows = result.scalars().all()
    for row in rows:
        await db.delete(row)
    if rows:
        await db.commit()
    return len(rows)
