from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.core.database import get_db
from app.matching.schemas import MatchRunRequest
from app.matching.service import run_matching
from app.platform.enforcement import require_matching_enabled
from app.platform.service import get_or_create_settings
from app.schemas.response import success

router = APIRouter(prefix="/matching", tags=["matching"])


@router.post("/run")
async def run_matching_endpoint(
    payload: MatchRunRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    settings = await get_or_create_settings(db)
    require_matching_enabled(settings)
    result = await run_matching(
        db,
        intent_id=payload.intent_id,
        current=current,
        top_n=payload.top_n,
    )
    return success(result.model_dump())
