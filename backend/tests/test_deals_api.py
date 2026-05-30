"""HTTP 层：GET /api/v1/deals 列表。"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from sqlalchemy import select

from app.auth.constants import UserRole
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
        ac.session_factory = session_factory
        yield ac
    fastapi_app.dependency_overrides.clear()
    clear_scheduled_tasks()
    await engine.dispose()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _promote_seller(session_factory, *, suffix: str) -> None:
    email = f"deals-{suffix}@example.com"
    async with session_factory() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one()
        user.role = UserRole.SELLER
        await db.commit()


async def _register(client: AsyncClient, *, suffix: str) -> str:
    resp = await client.post(
        f"{API}/auth/register",
        json={
            "email": f"deals-{suffix}@example.com",
            "password": "password123",
            "display_name": f"Deals {suffix}",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"]


async def _create_deal_via_match(client: AsyncClient, buyer_token: str, seller_token: str) -> str:
    offer_resp = await client.post(
        f"{API}/offers",
        headers=_auth(seller_token),
        json={
            "title": "API test offer",
            "description": "Logo design service for list deals test",
            "category": "design",
            "channel": "human",
            "billing_model": "per_use",
            "price_cents": 5000,
            "currency": "CNY",
            "delivery_description": "Deliver source files",
        },
    )
    assert offer_resp.status_code == 200
    offer_id = offer_resp.json()["data"]["id"]
    await client.post(f"{API}/offers/{offer_id}/publish", headers=_auth(seller_token))

    intent_resp = await client.post(
        f"{API}/intents",
        headers=_auth(buyer_token),
        json={
            "title": "Need design",
            "description": "Looking for logo design",
            "category": "design",
            "channel": "human",
            "budget_max": 8000,
            "currency": "CNY",
        },
    )
    assert intent_resp.status_code == 200
    intent_id = intent_resp.json()["data"]["id"]

    match_resp = await client.post(
        f"{API}/matching/run",
        headers=_auth(buyer_token),
        json={"intent_id": intent_id, "top_n": 5},
    )
    assert match_resp.status_code == 200
    match_log_id = match_resp.json()["data"]["candidates"][0]["match_log_id"]

    deal_resp = await client.post(
        f"{API}/deals",
        headers=_auth(buyer_token),
        json={"match_log_id": match_log_id},
    )
    assert deal_resp.status_code == 200
    return deal_resp.json()["data"]["id"]


@pytest.mark.asyncio
async def test_list_deals_requires_auth(client: AsyncClient):
    resp = await client.get(f"{API}/deals")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_deals_empty_for_new_user(client: AsyncClient):
    token = await _register(client, suffix="empty")
    resp = await client.get(f"{API}/deals", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] >= 1


@pytest.mark.asyncio
async def test_list_deals_includes_deal_for_buyer_and_seller(client: AsyncClient):
    buyer_token = await _register(client, suffix="buyer-list")
    seller_token = await _register(client, suffix="seller-list")
    await _promote_seller(client.session_factory, suffix="seller-list")
    deal_id = await _create_deal_via_match(client, buyer_token, seller_token)

    buyer_resp = await client.get(f"{API}/deals?page=1&page_size=10", headers=_auth(buyer_token))
    assert buyer_resp.status_code == 200
    buyer_data = buyer_resp.json()["data"]
    assert buyer_data["total"] == 1
    assert len(buyer_data["items"]) == 1
    assert buyer_data["items"][0]["id"] == deal_id
    assert buyer_data["items"][0]["status"] == "pending"

    seller_resp = await client.get(f"{API}/deals", headers=_auth(seller_token))
    assert seller_resp.status_code == 200
    seller_data = seller_resp.json()["data"]
    assert seller_data["total"] == 1
    assert seller_data["items"][0]["id"] == deal_id


@pytest.mark.asyncio
async def test_list_deals_not_visible_to_unrelated_user(client: AsyncClient):
    buyer_token = await _register(client, suffix="buyer-only")
    seller_token = await _register(client, suffix="seller-only")
    other_token = await _register(client, suffix="other")
    await _promote_seller(client.session_factory, suffix="seller-only")
    await _create_deal_via_match(client, buyer_token, seller_token)

    other_resp = await client.get(f"{API}/deals", headers=_auth(other_token))
    assert other_resp.status_code == 200
    assert other_resp.json()["data"]["total"] == 0
    assert other_resp.json()["data"]["items"] == []
