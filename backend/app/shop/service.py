from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.constants import UserRole
from app.auth.models import User
from app.auth.schemas import raise_auth_error
from app.shop.models import ShopApplication
from app.shop.schemas import (
    AdminShopApplicationItem,
    ShopApplicationResponse,
    ShopApplicationStatusResponse,
    ShopApplicationSubmitRequest,
)

ERR_SHOP_ALREADY_APPLIED = 42001
ERR_SHOP_ALREADY_SELLER = 42002
ERR_SHOP_NOT_PENDING = 42003
ERR_SHOP_NOT_FOUND = 42004


def _to_response(row: ShopApplication) -> ShopApplicationResponse:
    return ShopApplicationResponse(
        id=row.id,
        shop_name=row.shop_name,
        agent_platform=row.agent_platform,
        description=row.description,
        status=row.status,
        review_note=row.review_note,
        created_at=row.created_at.isoformat(),
        reviewed_at=row.reviewed_at.isoformat() if row.reviewed_at else None,
    )


def user_is_seller(user: User) -> bool:
    return user.role in (UserRole.SELLER, UserRole.ADMIN)


async def get_shop_status(db: AsyncSession, user: User) -> ShopApplicationStatusResponse:
    result = await db.execute(select(ShopApplication).where(ShopApplication.user_id == user.id))
    app = result.scalar_one_or_none()
    return ShopApplicationStatusResponse(
        has_application=app is not None,
        is_seller=user_is_seller(user),
        application=_to_response(app) if app else None,
    )


async def submit_shop_application(
    db: AsyncSession,
    *,
    user: User,
    payload: ShopApplicationSubmitRequest,
) -> ShopApplicationResponse:
    if user_is_seller(user):
        raise_auth_error(
            code=ERR_SHOP_ALREADY_SELLER,
            message="already an approved seller",
            http_status=409,
        )

    existing = await db.execute(select(ShopApplication).where(ShopApplication.user_id == user.id))
    row = existing.scalar_one_or_none()
    if row is not None:
        if row.status == "pending":
            raise_auth_error(
                code=ERR_SHOP_ALREADY_APPLIED,
                message="application already pending review",
                http_status=409,
            )
        if row.status == "approved":
            raise_auth_error(code=ERR_SHOP_ALREADY_SELLER, message="already approved", http_status=409)
        row.shop_name = payload.shop_name.strip()
        row.agent_platform = payload.agent_platform
        row.description = payload.description.strip()
        row.status = "pending"
        row.review_note = None
        row.reviewed_at = None
        await db.flush()
        return _to_response(row)

    app = ShopApplication(
        user_id=user.id,
        shop_name=payload.shop_name.strip(),
        agent_platform=payload.agent_platform,
        description=payload.description.strip(),
        status="pending",
    )
    db.add(app)
    await db.flush()
    return _to_response(app)


async def approve_shop_application(
    db: AsyncSession,
    *,
    user_id: UUID,
    review_note: str | None = None,
) -> ShopApplicationResponse:
    result = await db.execute(select(ShopApplication).where(ShopApplication.user_id == user_id))
    app = result.scalar_one_or_none()
    if app is None:
        raise_auth_error(code=ERR_SHOP_NOT_FOUND, message="application not found", http_status=404)

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise_auth_error(code=ERR_SHOP_NOT_FOUND, message="user not found", http_status=404)

    if app.status == "approved":
        raise_auth_error(
            code=ERR_SHOP_NOT_PENDING,
            message="application already approved",
            http_status=409,
        )

    app.status = "approved"
    app.review_note = review_note
    app.reviewed_at = datetime.now(UTC)
    if user.role == UserRole.USER:
        user.role = UserRole.SELLER
    await db.flush()
    return _to_response(app)


async def reject_shop_application(
    db: AsyncSession,
    *,
    user_id: UUID,
    review_note: str,
) -> ShopApplicationResponse:
    result = await db.execute(select(ShopApplication).where(ShopApplication.user_id == user_id))
    app = result.scalar_one_or_none()
    if app is None:
        raise_auth_error(code=ERR_SHOP_NOT_FOUND, message="application not found", http_status=404)

    if app.status == "approved":
        raise_auth_error(
            code=ERR_SHOP_NOT_PENDING,
            message="cannot reject an approved application",
            http_status=409,
        )

    app.status = "rejected"
    app.review_note = review_note.strip()
    app.reviewed_at = datetime.now(UTC)
    await db.flush()
    return _to_response(app)


def require_seller(user: User) -> None:
    if not user_is_seller(user):
        raise_auth_error(
            code=ERR_SHOP_NOT_FOUND,
            message="seller approval required; submit shop application first",
            http_status=403,
        )


async def list_shop_applications(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    status: str | None = None,
) -> dict:
    query = select(ShopApplication, User).join(User, ShopApplication.user_id == User.id)
    count_query = select(func.count()).select_from(ShopApplication)

    if status:
        query = query.where(ShopApplication.status == status)
        count_query = count_query.where(ShopApplication.status == status)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(ShopApplication.created_at.desc()).offset(offset).limit(page_size)
    )
    rows = result.all()
    items = [
        AdminShopApplicationItem(
            user_id=app.user_id,
            email=user.email,
            display_name=user.display_name,
            shop_name=app.shop_name,
            agent_platform=app.agent_platform,
            description=app.description,
            status=app.status,
            review_note=app.review_note,
            created_at=app.created_at.isoformat(),
            reviewed_at=app.reviewed_at.isoformat() if app.reviewed_at else None,
        ).model_dump(mode="json")
        for app, user in rows
    ]
    return {"items": items, "total": int(total or 0), "page": page, "page_size": page_size}
