"""HTTP 层：/health/ready 与 maintenance_mode 中间件。"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.models import User
from app.core.database import Base, get_db
from app.core.maintenance import invalidate_maintenance_cache
from app.deals.tasks import clear_scheduled_tasks
from app.deals.webhooks import clear_registry
from app.main import app as fastapi_app
from app.platform.models import PlatformSettings

import app.auth.models  # noqa: F401
import app.deals.models  # noqa: F401
import app.intents.models  # noqa: F401
import app.matching.models  # noqa: F401
import app.offers.models  # noqa: F401
import app.platform.models  # noqa: F401
import app.wallets.models  # noqa: F401

from tests.fake_redis import FakeRedis

API = "/api/v1"


@pytest.fixture
async def client(monkeypatch):
    clear_registry()
    clear_scheduled_tasks()
    invalidate_maintenance_cache()

    fake_redis = FakeRedis()

    async def _get_redis():
        return fake_redis

    monkeypatch.setattr("app.core.health.get_redis", _get_redis)
    monkeypatch.setattr("app.core.redis_client.get_redis", _get_redis)

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr("app.core.maintenance.async_session", session_factory)
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, session_factory
    fastapi_app.dependency_overrides.clear()
    clear_scheduled_tasks()
    invalidate_maintenance_cache()
    await engine.dispose()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _register(client: AsyncClient, *, suffix: str) -> tuple[str, str]:
    email = f"maint-test-{suffix}@example.com"
    resp = await client.post(
        f"{API}/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": f"User {suffix}",
        },
    )
    assert resp.status_code == 200, resp.text
    return email, resp.json()["data"]["access_token"]


async def _promote_to_admin(session_factory, email: str) -> None:
    async with session_factory() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        user.role = "admin"
        await db.commit()


async def _set_maintenance_mode(session_factory, enabled: bool) -> None:
    async with session_factory() as db:
        result = await db.execute(select(PlatformSettings).where(PlatformSettings.id == 1))
        row = result.scalar_one_or_none()
        if row is None:
            row = PlatformSettings(id=1, site_name="Capability", maintenance_mode=enabled)
            db.add(row)
        else:
            row.maintenance_mode = enabled
        await db.commit()
    invalidate_maintenance_cache()


@pytest.mark.asyncio
async def test_health_ready_ok(client):
    ac, _ = client
    resp = await ac.get("/health/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"]["ok"] is True
    assert body["checks"]["redis"]["ok"] is True


@pytest.mark.asyncio
async def test_health_stays_lightweight(client):
    ac, _ = client
    resp = await ac.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert "checks" not in resp.json()


@pytest.mark.asyncio
async def test_maintenance_mode_blocks_regular_user_api(client):
    ac, session_factory = client
    _, user_token = await _register(ac, suffix="user")

    await _set_maintenance_mode(session_factory, True)

    resp = await ac.get(f"{API}/users/me", headers=_auth(user_token))
    assert resp.status_code == 503
    assert resp.json()["code"] == 50301
    assert "维护" in resp.json()["message"]


@pytest.mark.asyncio
async def test_maintenance_mode_allows_admin_api(client):
    ac, session_factory = client
    admin_email, _ = await _register(ac, suffix="admin")
    await _promote_to_admin(session_factory, admin_email)
    admin_token = (
        await ac.post(
            f"{API}/auth/login",
            json={"account": admin_email, "password": "password123"},
        )
    ).json()["data"]["access_token"]

    await _set_maintenance_mode(session_factory, True)

    resp = await ac.get(f"{API}/admin/stats", headers=_auth(admin_token))
    assert resp.status_code == 200
    assert resp.json()["code"] == 0


@pytest.mark.asyncio
async def test_maintenance_mode_exempts_public_settings_and_health(client):
    ac, session_factory = client
    await _set_maintenance_mode(session_factory, True)

    health = await ac.get("/health")
    ready = await ac.get("/health/ready")
    settings = await ac.get(f"{API}/platform/settings")

    assert health.status_code == 200
    assert ready.status_code == 200
    assert settings.status_code == 200
    assert settings.json()["data"]["maintenance_mode"] is True


@pytest.mark.asyncio
async def test_maintenance_mode_allows_login(client):
    ac, session_factory = client
    email, _ = await _register(ac, suffix="login")
    await _set_maintenance_mode(session_factory, True)

    resp = await ac.post(
        f"{API}/auth/login",
        json={"account": email, "password": "password123"},
    )
    assert resp.status_code == 200
    assert resp.json()["code"] == 0
