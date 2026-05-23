from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import CurrentUser, raise_auth_error
from app.intents.constants import (
    ERR_INTENT_FORBIDDEN,
    ERR_INTENT_NOT_FOUND,
    IntentStatus,
)
from app.intents.events import publish_intent_created
from app.intents.models import Intent
from app.intents.schemas import (
    IntentCreateRequest,
    IntentResponse,
    build_tags_payload,
    intent_to_response,
)


def _ensure_owner(intent: Intent, current: CurrentUser) -> None:
    if intent.user_id != current.id:
        raise_auth_error(code=ERR_INTENT_FORBIDDEN, message="intent access denied", http_status=403)


async def create_intent(
    db: AsyncSession,
    *,
    current: CurrentUser,
    payload: IntentCreateRequest,
) -> IntentResponse:
    intent = Intent(
        user_id=current.id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        budget_cents=payload.budget_max,
        currency=payload.currency.upper(),
        status=IntentStatus.OPEN,
        tags=build_tags_payload(
            channel=payload.channel,
            settlement=payload.settlement,
            deadline=payload.deadline,
            acceptance_criteria=payload.acceptance_criteria,
        ),
    )
    db.add(intent)
    await db.commit()
    await db.refresh(intent)

    await publish_intent_created(
        intent_id=intent.id,
        user_id=intent.user_id,
        status=intent.status,
    )

    return intent_to_response(intent)


async def get_intent(
    db: AsyncSession,
    *,
    intent_id: UUID,
    current: CurrentUser | None = None,
) -> IntentResponse:
    intent = await _get_intent_or_404(db, intent_id)
    if current is not None:
        _ensure_owner(intent, current)
    return intent_to_response(intent)


async def list_intents(
    db: AsyncSession,
    *,
    status: str | None = None,
    current: CurrentUser | None = None,
) -> list[IntentResponse]:
    query = select(Intent).order_by(Intent.created_at.desc())

    if status:
        query = query.where(Intent.status == status)
    if current is not None:
        query = query.where(Intent.user_id == current.id)

    result = await db.execute(query)
    intents = result.scalars().all()
    return [intent_to_response(item) for item in intents]


async def attach_mock_match(
    db: AsyncSession,
    *,
    intent_id: UUID,
    current: CurrentUser,
) -> IntentResponse:
    intent = await _get_intent_or_404(db, intent_id)
    _ensure_owner(intent, current)

    meta = dict(intent.tags or {})
    meta["match_id"] = str(uuid4())
    intent.tags = meta
    intent.status = IntentStatus.MATCHED
    await db.commit()
    await db.refresh(intent)
    return intent_to_response(intent)


async def _get_intent_or_404(db: AsyncSession, intent_id: UUID) -> Intent:
    result = await db.execute(select(Intent).where(Intent.id == intent_id))
    intent = result.scalar_one_or_none()
    if intent is None:
        raise_auth_error(code=ERR_INTENT_NOT_FOUND, message="intent not found", http_status=404)
    return intent
