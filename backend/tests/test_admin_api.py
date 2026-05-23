"""HTTP 层：/api/v1/admin 运营后台。"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.models import User
from app.core.database import Base, get_db
from app.deals.tasks import clear_scheduled_tasks
from app.deals.webhooks import clear_registry
from app.main import app as fastapi_app

import app.auth.models  # noqa: F401
import app.deals.models  # noqa: F401
import app.intents.models  # noqa: F401
import app.matching.models  # noqa: F401
import app.offers.models  # noqa: F401
import app.platform.models  # noqa: F401
import app.wallets.models  # noqa: F401

API = "/api/v1"


@pytest.fixture
async def client():
    clear_registry()
    clear_scheduled_tasks()
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
    clear_scheduled_tasks()
    await engine.dispose()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _register(client: AsyncClient, *, suffix: str) -> tuple[str, str]:
    email = f"admin-test-{suffix}@example.com"
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


async def _login(client: AsyncClient, email: str) -> str:
    resp = await client.post(
        f"{API}/auth/login",
        json={"account": email, "password": "password123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_admin_endpoints_forbid_non_admin(client):
    ac, _ = client
    _, user_token = await _register(ac, suffix="regular")
    endpoints = [
        ("GET", f"{API}/admin/stats"),
        ("GET", f"{API}/admin/users"),
        ("GET", f"{API}/admin/deals"),
    ]
    for method, url in endpoints:
        resp = await ac.request(method, url, headers=_auth(user_token))
        assert resp.status_code == 403, f"{method} {url}: {resp.text}"
        assert resp.json()["code"] == 47001


@pytest.mark.asyncio
async def test_admin_can_list_users_and_deals(client):
    ac, session_factory = client
    admin_email, _ = await _register(ac, suffix="admin-user")
    await _promote_to_admin(session_factory, admin_email)
    admin_token = await _login(ac, admin_email)

    stats_resp = await ac.get(f"{API}/admin/stats", headers=_auth(admin_token))
    assert stats_resp.status_code == 200
    stats = stats_resp.json()["data"]
    assert stats["users_total"] >= 1
    assert "deals_total" in stats

    users_resp = await ac.get(f"{API}/admin/users", headers=_auth(admin_token))
    assert users_resp.status_code == 200
    users_data = users_resp.json()["data"]
    assert users_data["total"] >= 1
    assert len(users_data["items"]) >= 1

    deals_resp = await ac.get(f"{API}/admin/deals", headers=_auth(admin_token))
    assert deals_resp.status_code == 200
    deals_data = deals_resp.json()["data"]
    assert "items" in deals_data


@pytest.mark.asyncio
async def test_admin_can_suspend_user(client):
    ac, session_factory = client
    target_email, target_token = await _register(ac, suffix="suspend-target")
    me_resp = await ac.get(f"{API}/users/me", headers=_auth(target_token))
    target_id = me_resp.json()["data"]["id"]

    admin_email, _ = await _register(ac, suffix="suspend-admin")
    await _promote_to_admin(session_factory, admin_email)
    admin_token = await _login(ac, admin_email)

    patch_resp = await ac.patch(
        f"{API}/admin/users/{target_id}",
        headers=_auth(admin_token),
        json={"status": "suspended"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["data"]["status"] == "suspended"

    restore_resp = await ac.patch(
        f"{API}/admin/users/{target_id}",
        headers=_auth(admin_token),
        json={"status": "active"},
    )
    assert restore_resp.status_code == 200
    assert restore_resp.json()["data"]["status"] == "active"
    assert target_email  # used


@pytest.mark.asyncio
async def test_admin_cannot_suspend_self(client):
    ac, session_factory = client
    admin_email, _ = await _register(ac, suffix="self-admin")
    await _promote_to_admin(session_factory, admin_email)
    admin_token = await _login(ac, admin_email)

    me_resp = await ac.get(f"{API}/users/me", headers=_auth(admin_token))
    admin_id = me_resp.json()["data"]["id"]

    resp = await ac.patch(
        f"{API}/admin/users/{admin_id}",
        headers=_auth(admin_token),
        json={"status": "suspended"},
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == 47002


@pytest.mark.asyncio
async def test_admin_backup_trigger_forbidden(client):
    ac, _ = client
    _, user_token = await _register(ac, suffix="backup-regular")
    resp = await ac.post(
        f"{API}/admin/backups/trigger",
        headers=_auth(user_token),
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == 47001


@pytest.mark.asyncio
async def test_admin_backup_trigger_dry_run(client):
    ac, session_factory = client
    admin_email, _ = await _register(ac, suffix="backup-admin")
    await _promote_to_admin(session_factory, admin_email)
    admin_token = await _login(ac, admin_email)

    trigger_resp = await ac.post(
        f"{API}/admin/backups/trigger",
        headers=_auth(admin_token),
        params={"dry_run": "true"},
    )
    assert trigger_resp.status_code == 200, trigger_resp.text
    item = trigger_resp.json()["data"]
    assert item["status"] == "dry_run"
    assert item["trigger_type"] == "manual"
    assert item["filename"]
    assert item["created_by_admin_id"]

    list_resp = await ac.get(
        f"{API}/admin/backups",
        headers=_auth(admin_token),
    )
    assert list_resp.status_code == 200
    data = list_resp.json()["data"]
    assert data["total"] >= 1
    assert any(row["id"] == item["id"] for row in data["items"])

