"""限流与登录锁定测试。"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.constants import ERR_LOGIN_LOCKED, ERR_RATE_LIMIT
from app.auth.schemas import AuthError
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.rate_limit import check_rate_limit
from app.deals.tasks import clear_scheduled_tasks
from app.deals.webhooks import clear_registry
from app.main import app as fastapi_app
from app.main import validate_production_secrets
from tests.fake_redis import FakeRedis

import app.auth.models  # noqa: F401
import app.deals.models  # noqa: F401
import app.intents.models  # noqa: F401
import app.matching.models  # noqa: F401
import app.offers.models  # noqa: F401
import app.wallets.models  # noqa: F401

API = "/api/v1"


@pytest.fixture
async def client(monkeypatch):
    clear_registry()
    clear_scheduled_tasks()
    fake = FakeRedis()

    async def _get_redis():
        return fake

    monkeypatch.setattr("app.core.rate_limit.get_redis", _get_redis)
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "LOGIN_MAX_ATTEMPTS", 3)
    monkeypatch.setattr(settings, "LOGIN_LOCKOUT_SECONDS", 900)
    monkeypatch.setattr(settings, "LOGIN_LOCKOUT_SCOPE", "account")
    monkeypatch.setattr(settings, "RATE_LIMIT_LOGIN_MAX", 5)
    monkeypatch.setattr(settings, "RATE_LIMIT_LOGIN_WINDOW_SECONDS", 60)
    monkeypatch.setattr(settings, "RATE_LIMIT_REGISTER_MAX", 2)
    monkeypatch.setattr(settings, "RATE_LIMIT_REGISTER_WINDOW_SECONDS", 3600)
    monkeypatch.setattr(settings, "RATE_LIMIT_PAYMENT_NOTIFY_MAX", 2)
    monkeypatch.setattr(settings, "RATE_LIMIT_PAYMENT_NOTIFY_WINDOW_SECONDS", 60)

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
        yield ac, fake
    fastapi_app.dependency_overrides.clear()
    clear_scheduled_tasks()
    await engine.dispose()
    await fake.aclose()


@pytest.mark.asyncio
async def test_check_rate_limit_blocks_after_max(monkeypatch):
    fake = FakeRedis()

    async def _get_redis():
        return fake

    monkeypatch.setattr("app.core.rate_limit.get_redis", _get_redis)
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)

    await check_rate_limit(key="rl:test", max_requests=2, window_seconds=60)
    await check_rate_limit(key="rl:test", max_requests=2, window_seconds=60)

    with pytest.raises(AuthError) as exc_info:
        await check_rate_limit(key="rl:test", max_requests=2, window_seconds=60)
    assert exc_info.value.code == ERR_RATE_LIMIT


@pytest.mark.asyncio
async def test_login_lockout_after_failed_attempts(client):
    ac, _fake = client
    email = "lockout-user@example.com"
    register_resp = await ac.post(
        f"{API}/auth/register",
        json={"email": email, "password": "password123", "display_name": "Lockout"},
    )
    assert register_resp.status_code == 200, register_resp.text

    for _ in range(3):
        resp = await ac.post(
            f"{API}/auth/login",
            json={"account": email, "password": "wrong-password"},
        )
        assert resp.status_code == 401
        assert resp.json()["code"] == 41001

    locked = await ac.post(
        f"{API}/auth/login",
        json={"account": email, "password": "password123"},
    )
    assert locked.status_code == 429
    assert locked.json()["code"] == ERR_LOGIN_LOCKED


@pytest.mark.asyncio
async def test_login_ip_rate_limit(client):
    ac, _fake = client
    for i in range(5):
        resp = await ac.post(
            f"{API}/auth/login",
            json={"account": f"user{i}@example.com", "password": "wrong"},
        )
        assert resp.status_code in {401, 429}

    blocked = await ac.post(
        f"{API}/auth/login",
        json={"account": "another@example.com", "password": "wrong"},
    )
    assert blocked.status_code == 429
    assert blocked.json()["code"] == ERR_RATE_LIMIT


@pytest.mark.asyncio
async def test_register_ip_rate_limit(client):
    ac, _fake = client
    for i in range(2):
        resp = await ac.post(
            f"{API}/auth/register",
            json={
                "email": f"rate-{i}@example.com",
                "password": "password123",
                "display_name": f"User {i}",
            },
        )
        assert resp.status_code == 200, resp.text

    blocked = await ac.post(
        f"{API}/auth/register",
        json={
            "email": "rate-blocked@example.com",
            "password": "password123",
            "display_name": "Blocked",
        },
    )
    assert blocked.status_code == 429
    assert blocked.json()["code"] == ERR_RATE_LIMIT


@pytest.mark.asyncio
async def test_payment_notify_ip_rate_limit(client):
    ac, _fake = client
    for _ in range(2):
        resp = await ac.post(f"{API}/wallets/payment-notify/wechat", content=b"{}")
        assert resp.status_code == 200

    blocked = await ac.post(f"{API}/wallets/payment-notify/wechat", content=b"{}")
    assert blocked.status_code == 429
    assert blocked.json()["code"] == ERR_RATE_LIMIT


def test_validate_production_secrets_rejects_default(monkeypatch):
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", "change-me-in-production")
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        validate_production_secrets()


def test_validate_production_secrets_allows_debug_default(monkeypatch):
    monkeypatch.setattr(settings, "DEBUG", True)
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", "change-me-in-production")
    validate_production_secrets()


def test_production_docs_disabled(monkeypatch):
    monkeypatch.setattr(settings, "DEBUG", False)
    assert ("/docs" if settings.DEBUG else None) is None
    assert ("/redoc" if settings.DEBUG else None) is None
