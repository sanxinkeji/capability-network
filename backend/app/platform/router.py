from typing import Annotated



from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession



from app.core.database import get_db

from app.platform.service import get_public_platform_settings

from app.schemas.response import success



router = APIRouter(prefix="/platform", tags=["platform"])





@router.get("/settings")

async def public_platform_settings(

    db: Annotated[AsyncSession, Depends(get_db)],

):

    settings = await get_public_platform_settings(db)

    return success(settings.model_dump())

