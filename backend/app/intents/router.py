from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.core.database import get_db
from app.intents.constants import IntentStatus
from app.intents.parser import parse_intent_text
from app.intents.schemas import IntentCreateRequest, IntentParseRequest
from app.intents.service import create_intent, get_intent, list_intents
from app.schemas.response import success

router = APIRouter(prefix="/intents", tags=["intents"])


@router.post("")
async def create_intent_endpoint(
    payload: IntentCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    intent = await create_intent(db, current=current, payload=payload)
    return success(intent.model_dump())


@router.post("/parse")
async def parse_intent_endpoint(payload: IntentParseRequest):
    parsed = await parse_intent_text(payload.text)
    return success(parsed.model_dump(mode="json"))


@router.get("")
async def list_intents_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
    status: IntentStatus | None = Query(default=None),
):
    intents = await list_intents(db, status=str(status) if status else None, current=current)
    return success([item.model_dump() for item in intents])


@router.get("/{intent_id}")
async def get_intent_endpoint(
    intent_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    intent = await get_intent(db, intent_id=intent_id, current=current)
    return success(intent.model_dump())
