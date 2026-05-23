"""Registration policy and platform codes."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app as fastapi_app
from app.platform.codes import generate_platform_codes
from app.platform.models import CodeType
from app.platform.service import get_or_create_settings

import app.platform.models  # noqa: F401
import app.auth.models  # noqa: F401

API = "/api/v1"


@pytest.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, session_factory
    fastapi_app.dependency_overrides.clear()
    await engine.dispose()


async def _register(ac, email: str, invite_code: str | None = None):
    body = {
        "email": email,
        "password": "password123",
    }
    if invite_code:
        body["invite_code"] = invite_code
    return await ac.post(f"{API}/auth/register", json=body)


@pytest.mark.asyncio
async def test_public_settings_includes_registration_flags(client):
    ac, _ = client
    resp = await ac.get(f"{API}/platform/settings")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["registration_mode"] == "open"
    assert data["registration_invite_required"] is False


@pytest.mark.asyncio
async def test_register_open_email_password_only(client):
    ac, _ = client
    resp = await _register(ac, "open-user@example.com")
    assert resp.status_code == 200, resp.text


@pytest.mark.asyncio
async def test_register_closed(client):
    ac, session_factory = client
    async with session_factory() as db:
        row = await get_or_create_settings(db)
        row.registration_mode = "closed"
        await db.commit()

    resp = await _register(ac, "closed-user@example.com")
    assert resp.status_code == 403
    assert resp.json()["code"] == 40303


@pytest.mark.asyncio
async def test_register_with_invite_code(client):
    ac, session_factory = client
    async with session_factory() as db:
        from app.auth.models import User
        from app.auth.security import hash_password

        admin = User(
            email="admin@test.com",
            password_hash=hash_password("password123"),
            display_name="Admin",
            role="admin",
        )
        db.add(admin)
        await db.flush()

        row = await get_or_create_settings(db)
        row.registration_mode = "invite_only"
        await db.commit()

        generated = await generate_platform_codes(
            db,
            admin_id=admin.id,
            code_type=CodeType.INVITE,
            count=1,
            expires_at=None,
        )
        invite_code = generated["codes"][0]

    bad = await _register(ac, "bad-invite@example.com", invite_code="WRONG")
    assert bad.status_code == 403
    assert bad.json()["code"] == 40304

    ok = await _register(ac, "good-invite@example.com", invite_code=invite_code)
    assert ok.status_code == 200, ok.text

    reused = await _register(ac, "reuse-invite@example.com", invite_code=invite_code)
    assert reused.status_code == 403
    assert reused.json()["code"] == 40306
