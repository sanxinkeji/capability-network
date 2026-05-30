from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependencies import require_admin
from app.auth.dependencies import get_current_human
from app.auth.models import User
from app.auth.schemas import CurrentUser
from app.core.database import get_db
from app.schemas.response import success
from app.shop.schemas import ShopApplicationRejectRequest, ShopApplicationSubmitRequest
from app.shop.service import (
    approve_shop_application,
    get_shop_status,
    list_shop_applications,
    reject_shop_application,
    submit_shop_application,
)

router = APIRouter(prefix="/shop", tags=["shop"])


@router.get("/application")
async def get_my_shop_application(
    current: Annotated[User, Depends(get_current_human)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await get_shop_status(db, current)
    return success(data.model_dump())


@router.post("/application")
async def submit_my_shop_application(
    payload: ShopApplicationSubmitRequest,
    current: Annotated[User, Depends(get_current_human)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    app = await submit_shop_application(db, user=current, payload=payload)
    return success(app.model_dump())


@router.post("/admin/applications/{user_id}/approve")
async def admin_approve_shop(
    user_id: UUID,
    _admin: Annotated[CurrentUser, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    app = await approve_shop_application(db, user_id=user_id)
    return success(app.model_dump())


@router.post("/admin/applications/{user_id}/reject")
async def admin_reject_shop(
    user_id: UUID,
    payload: ShopApplicationRejectRequest,
    _admin: Annotated[CurrentUser, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    app = await reject_shop_application(db, user_id=user_id, review_note=payload.review_note)
    return success(app.model_dump())


@router.get("/admin/applications")
async def admin_list_shop_applications(
    _admin: Annotated[CurrentUser, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
):
    data = await list_shop_applications(db, page=page, page_size=page_size, status=status or None)
    return success(data)
