"""Platform settings enforcement: email verification, domains, feature flags, trust_proxy."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app as fastapi_app
from app.platform.service import get_or_create_settings
from app.platform.settings_cache import invalidate_platform_settings_cache

import app.platform.models  # noqa: F401
import app.auth.models  # noqa: F401

API = "/api/v1"


@pytest.fixture(autouse=True)
def _isolate_global_platform_db_reads(monkeypatch):
    async def _trust_proxy_false():
        return False

    async def _maintenance_false():
        return False

    monkeypatch.setattr("app.platform.settings_cache.trust_proxy_ip_enabled", _trust_proxy_false)
    monkeypatch.setattr("app.core.maintenance._maintenance_mode_enabled", _maintenance_false)


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
    invalidate_platform_settings_cache()
    await engine.dispose()


async def _patch_settings(session_factory, **kwargs) -> None:
    async with session_factory() as db:
        row = await get_or_create_settings(db)
        for key, value in kwargs.items():
            setattr(row, key, value)
        await db.commit()
    invalidate_platform_settings_cache()


async def _register(ac, email: str, invite_code: str | None = None):
    body = {"email": email, "password": "password123"}
    if invite_code:
        body["invite_code"] = invite_code
    return await ac.post(f"{API}/auth/register", json=body)


async def _login(ac, account: str, password: str = "password123"):
    return await ac.post(f"{API}/auth/login", json={"account": account, "password": password})


async def _auth_headers(ac, email: str):
    resp = await _register(ac, email)
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    token = data["access_token"]
    assert token
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_registration_email_domain_whitelist(client):
    ac, session_factory = client
    await _patch_settings(session_factory, registration_email_domains="@example.com, gmail.com")

    blocked = await _register(ac, "user@qq.com")
    assert blocked.status_code == 403
    assert blocked.json()["code"] == 40310

    ok = await _register(ac, "allowed@gmail.com")
    assert ok.status_code == 200, ok.text


@pytest.mark.asyncio
async def test_email_verification_required_on_register(client):
    ac, session_factory = client
    await _patch_settings(session_factory, email_verification_required=True)

    resp = await _register(ac, "verify-me@example.com")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["verification_required"] is True
    assert data.get("access_token") in (None, "")

    login_resp = await _login(ac, "verify-me@example.com")
    assert login_resp.status_code == 403
    assert login_resp.json()["code"] == 41016


@pytest.mark.asyncio
async def test_email_verification_verify_then_login(client, monkeypatch):
    monkeypatch.setattr(
        "app.auth.email_verification.generate_verification_code",
        lambda: "123456",
    )
    ac, session_factory = client
    await _patch_settings(session_factory, email_verification_required=True)

    await _register(ac, "verify-ok@example.com")

    verify = await ac.post(
        f"{API}/auth/verify-email",
        json={"email": "verify-ok@example.com", "code": "123456"},
    )
    assert verify.status_code == 200, verify.text
    assert verify.json()["data"]["access_token"]

    login_resp = await _login(ac, "verify-ok@example.com")
    assert login_resp.status_code == 200, login_resp.text


@pytest.mark.asyncio
async def test_feature_marketplace_disabled_blocks_marketplace_api(client):
    ac, session_factory = client
    headers = await _auth_headers(ac, "market-user@example.com")
    await _patch_settings(session_factory, feature_marketplace_enabled=False)

    resp = await ac.get(f"{API}/offers/marketplace", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["code"] == 41020


@pytest.mark.asyncio
async def test_feature_matching_disabled_blocks_matching_run(client):
    ac, session_factory = client
    headers = await _auth_headers(ac, "match-user@example.com")
    await _patch_settings(session_factory, feature_matching_enabled=False)

    resp = await ac.post(
        f"{API}/matching/run",
        headers=headers,
        json={"intent_id": "00000000-0000-0000-0000-000000000001", "top_n": 5},
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == 41021


@pytest.mark.asyncio
async def test_feature_wallet_disabled_blocks_deposit(client):
    ac, session_factory = client
    headers = await _auth_headers(ac, "wallet-user@example.com")
    await _patch_settings(session_factory, feature_wallet_enabled=False)

    resp = await ac.post(
        f"{API}/wallets/deposit-orders",
        headers=headers,
        json={"amount_cents": 1000, "channel": "wechat"},
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == 41022


@pytest.mark.asyncio
async def test_feature_agent_disabled_blocks_api_key_issue(client):
    ac, session_factory = client
    headers = await _auth_headers(ac, "agent-user@example.com")
    await _patch_settings(session_factory, feature_agent_enabled=False)

    resp = await ac.post(
        f"{API}/agent/api-keys",
        headers=headers,
        json={"platform_user_id": "test-agent"},
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == 41007


@pytest.mark.asyncio
async def test_trust_proxy_ip_uses_x_forwarded_for(client, monkeypatch):
    ac, session_factory = client

    async def _trust_proxy_true():
        return True

    monkeypatch.setattr("app.platform.settings_cache.trust_proxy_ip_enabled", _trust_proxy_true)
    await _patch_settings(session_factory, trust_proxy_ip=True)

    resp = await ac.post(
        f"{API}/auth/login",
        json={"account": "nobody@example.com", "password": "wrong"},
        headers={"X-Forwarded-For": "203.0.113.50, 10.0.0.1"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_public_settings_exposes_email_verification_flag(client):
    ac, session_factory = client
    await _patch_settings(session_factory, email_verification_required=True)

    resp = await ac.get(f"{API}/platform/settings")
    assert resp.status_code == 200
    assert resp.json()["data"]["email_verification_required"] is True
