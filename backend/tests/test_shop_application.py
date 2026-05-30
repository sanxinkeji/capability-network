"""开店入驻申请与审核服务层测试。"""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.constants import UserRole
from app.auth.models import User
from app.auth.schemas import AuthError
from app.core.database import Base
from app.shop.schemas import ShopApplicationSubmitRequest
from app.shop.service import (
    ERR_SHOP_ALREADY_APPLIED,
    ERR_SHOP_ALREADY_SELLER,
    ERR_SHOP_NOT_PENDING,
    approve_shop_application,
    get_shop_status,
    list_shop_applications,
    reject_shop_application,
    require_seller,
    submit_shop_application,
)

import app.auth.models  # noqa: F401
import app.shop.models  # noqa: F401


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


async def _new_user(db: AsyncSession, *, role: str = UserRole.USER) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@test.com",
        password_hash="hash",
        display_name="申请人",
        role=role,
    )
    db.add(user)
    await db.flush()
    return user


def _payload(**overrides) -> ShopApplicationSubmitRequest:
    data = {
        "shop_name": "龙虾论文工坊",
        "agent_platform": "openclaw",
        "description": "由我训练的小龙虾智能体，自动完成论文写作与润色。",
    }
    data.update(overrides)
    return ShopApplicationSubmitRequest(**data)


@pytest.mark.asyncio
async def test_submit_creates_pending_application(db_session: AsyncSession):
    user = await _new_user(db_session)
    resp = await submit_shop_application(db_session, user=user, payload=_payload())
    assert resp.status == "pending"
    assert resp.shop_name == "龙虾论文工坊"

    status = await get_shop_status(db_session, user)
    assert status.has_application is True
    assert status.is_seller is False


@pytest.mark.asyncio
async def test_duplicate_pending_application_rejected(db_session: AsyncSession):
    user = await _new_user(db_session)
    await submit_shop_application(db_session, user=user, payload=_payload())
    with pytest.raises(AuthError) as exc:
        await submit_shop_application(db_session, user=user, payload=_payload())
    assert exc.value.code == ERR_SHOP_ALREADY_APPLIED


@pytest.mark.asyncio
async def test_approve_promotes_user_to_seller(db_session: AsyncSession):
    user = await _new_user(db_session)
    await submit_shop_application(db_session, user=user, payload=_payload())

    resp = await approve_shop_application(db_session, user_id=user.id, review_note="通过")
    assert resp.status == "approved"

    refreshed = (await db_session.execute(select(User).where(User.id == user.id))).scalar_one()
    assert refreshed.role == UserRole.SELLER


@pytest.mark.asyncio
async def test_double_approve_rejected(db_session: AsyncSession):
    user = await _new_user(db_session)
    await submit_shop_application(db_session, user=user, payload=_payload())
    await approve_shop_application(db_session, user_id=user.id)
    with pytest.raises(AuthError) as exc:
        await approve_shop_application(db_session, user_id=user.id)
    assert exc.value.code == ERR_SHOP_NOT_PENDING


@pytest.mark.asyncio
async def test_reject_then_resubmit_resets_to_pending(db_session: AsyncSession):
    user = await _new_user(db_session)
    await submit_shop_application(db_session, user=user, payload=_payload())
    rejected = await reject_shop_application(db_session, user_id=user.id, review_note="资料不全")
    assert rejected.status == "rejected"
    assert rejected.review_note == "资料不全"

    resubmitted = await submit_shop_application(
        db_session, user=user, payload=_payload(shop_name="龙虾设计铺")
    )
    assert resubmitted.status == "pending"
    assert resubmitted.shop_name == "龙虾设计铺"
    assert resubmitted.review_note is None


@pytest.mark.asyncio
async def test_reject_approved_application_rejected(db_session: AsyncSession):
    user = await _new_user(db_session)
    await submit_shop_application(db_session, user=user, payload=_payload())
    await approve_shop_application(db_session, user_id=user.id)
    with pytest.raises(AuthError) as exc:
        await reject_shop_application(db_session, user_id=user.id, review_note="改主意了")
    assert exc.value.code == ERR_SHOP_NOT_PENDING


@pytest.mark.asyncio
async def test_existing_seller_cannot_apply(db_session: AsyncSession):
    seller = await _new_user(db_session, role=UserRole.SELLER)
    with pytest.raises(AuthError) as exc:
        await submit_shop_application(db_session, user=seller, payload=_payload())
    assert exc.value.code == ERR_SHOP_ALREADY_SELLER


@pytest.mark.asyncio
async def test_require_seller_gate(db_session: AsyncSession):
    user = await _new_user(db_session)
    with pytest.raises(AuthError):
        require_seller(user)
    seller = await _new_user(db_session, role=UserRole.SELLER)
    require_seller(seller)


@pytest.mark.asyncio
async def test_admin_list_applications_with_filter(db_session: AsyncSession):
    user_a = await _new_user(db_session)
    user_b = await _new_user(db_session)
    await submit_shop_application(db_session, user=user_a, payload=_payload(shop_name="店铺A"))
    await submit_shop_application(db_session, user=user_b, payload=_payload(shop_name="店铺B"))
    await approve_shop_application(db_session, user_id=user_a.id)

    all_items = await list_shop_applications(db_session, page=1, page_size=20)
    assert all_items["total"] == 2

    pending = await list_shop_applications(db_session, page=1, page_size=20, status="pending")
    assert pending["total"] == 1
    assert pending["items"][0]["shop_name"] == "店铺B"
