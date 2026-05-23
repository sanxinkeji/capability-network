"""Agent 需求竞价室 Phase A 测试。"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.deals.tasks import clear_scheduled_tasks
from app.deals.webhooks import clear_registry
from app.main import app as fastapi_app

import app.auctions.models  # noqa: F401
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
        yield ac
    fastapi_app.dependency_overrides.clear()
    clear_scheduled_tasks()
    await engine.dispose()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _register(client: AsyncClient, *, suffix: str) -> str:
    email = f"auction-{suffix}@example.com"
    resp = await client.post(
        f"{API}/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": f"Auction {suffix}",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"]


async def _create_agent_offer(client: AsyncClient, token: str, *, title: str, price: int) -> str:
    resp = await client.post(
        f"{API}/offers",
        headers=_auth(token),
        json={
            "title": title,
            "description": "Agent automation service for testing auction flow",
            "category": "development",
            "channel": "agent",
            "billing_model": "per_query",
            "price_cents": price,
            "currency": "CNY",
            "delivery_description": "Automated delivery",
        },
    )
    assert resp.status_code == 200, resp.text
    offer_id = resp.json()["data"]["id"]
    publish = await client.post(f"{API}/offers/{offer_id}/publish", headers=_auth(token))
    assert publish.status_code == 200
    return offer_id


async def _create_agent_intent(client: AsyncClient, buyer_token: str) -> str:
    resp = await client.post(
        f"{API}/intents",
        headers=_auth(buyer_token),
        json={
            "title": "Agent 自动化任务",
            "description": "需要 agent 通道自动化处理",
            "category": "development",
            "channel": "agent",
            "budget_max": 10000,
            "currency": "CNY",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["id"]


@pytest.mark.asyncio
async def test_auction_flow_join_start_bid_select(client: AsyncClient):
    buyer_token = await _register(client, suffix="buyer")
    agent1_token = await _register(client, suffix="agent1")
    agent2_token = await _register(client, suffix="agent2")

    offer1 = await _create_agent_offer(client, agent1_token, title="Agent A", price=8000)
    offer2 = await _create_agent_offer(client, agent2_token, title="Agent B", price=7500)
    intent_id = await _create_agent_intent(client, buyer_token)

    join1 = await client.post(
        f"{API}/intents/{intent_id}/auction/join",
        headers=_auth(agent1_token),
        json={"offer_id": offer1},
    )
    assert join1.status_code == 200, join1.text
    assert join1.json()["data"]["status"] == "open"
    assert join1.json()["data"]["participant_count"] == 1

    join2 = await client.post(
        f"{API}/intents/{intent_id}/auction/join",
        headers=_auth(agent2_token),
        json={"offer_id": offer2},
    )
    assert join2.status_code == 200, join2.text
    assert join2.json()["data"]["status"] == "matched"
    auction_id = join2.json()["data"]["id"]

    start = await client.post(
        f"{API}/intents/{intent_id}/auction/start",
        headers=_auth(buyer_token),
    )
    assert start.status_code == 200, start.text
    assert start.json()["data"]["status"] == "auctioning"

    bid1 = await client.post(
        f"{API}/auctions/{auction_id}/bid",
        headers=_auth(agent1_token),
        json={"amount_cents": 6000},
    )
    assert bid1.status_code == 200, bid1.text

    bid2 = await client.post(
        f"{API}/auctions/{auction_id}/bid",
        headers=_auth(agent2_token),
        json={"amount_cents": 5500},
    )
    assert bid2.status_code == 200, bid2.text
    assert len(bid2.json()["data"]["bids"]) == 2

    winning_bid_id = bid2.json()["data"]["bids"][0]["id"]
    select = await client.post(
        f"{API}/auctions/{auction_id}/select",
        headers=_auth(buyer_token),
        json={"bid_id": winning_bid_id},
    )
    assert select.status_code == 200, select.text
    selected = select.json()["data"]
    assert selected["status"] == "deal"
    assert selected["deal_id"] is not None
    uuid.UUID(selected["deal_id"])

    intent_resp = await client.get(f"{API}/intents/{intent_id}", headers=_auth(buyer_token))
    assert intent_resp.json()["data"]["status"] == "deal"

    deal_resp = await client.get(
        f"{API}/deals/{selected['deal_id']}",
        headers=_auth(buyer_token),
    )
    assert deal_resp.status_code == 200
    assert deal_resp.json()["data"]["amount_cents"] == 5500


@pytest.mark.asyncio
async def test_auction_bid_over_budget_rejected(client: AsyncClient):
    buyer_token = await _register(client, suffix="buyer-budget")
    agent1_token = await _register(client, suffix="agent-b1")
    agent2_token = await _register(client, suffix="agent-b2")

    offer1 = await _create_agent_offer(client, agent1_token, title="Budget Agent A", price=5000)
    offer2 = await _create_agent_offer(client, agent2_token, title="Budget Agent B", price=4000)
    intent_id = await _create_agent_intent(client, buyer_token)

    await client.post(
        f"{API}/intents/{intent_id}/auction/join",
        headers=_auth(agent1_token),
        json={"offer_id": offer1},
    )
    join2 = await client.post(
        f"{API}/intents/{intent_id}/auction/join",
        headers=_auth(agent2_token),
        json={"offer_id": offer2},
    )
    auction_id = join2.json()["data"]["id"]

    await client.post(
        f"{API}/intents/{intent_id}/auction/start",
        headers=_auth(buyer_token),
    )

    over = await client.post(
        f"{API}/auctions/{auction_id}/bid",
        headers=_auth(agent1_token),
        json={"amount_cents": 15000},
    )
    assert over.status_code == 422
    assert over.json()["code"] == 48008


@pytest.mark.asyncio
async def test_auction_participant_limit(client: AsyncClient):
    buyer_token = await _register(client, suffix="buyer-limit")
    intent_id = await _create_agent_intent(client, buyer_token)

    tokens_and_offers: list[tuple[str, str]] = []
    for i in range(8):
        token = await _register(client, suffix=f"limit-agent-{i}")
        offer_id = await _create_agent_offer(
            client, token, title=f"Limit Agent {i}", price=1000 + i * 100
        )
        tokens_and_offers.append((token, offer_id))

    for token, offer_id in tokens_and_offers:
        resp = await client.post(
            f"{API}/intents/{intent_id}/auction/join",
            headers=_auth(token),
            json={"offer_id": offer_id},
        )
        assert resp.status_code == 200, resp.text

    extra_token = await _register(client, suffix="limit-agent-extra")
    extra_offer = await _create_agent_offer(client, extra_token, title="Extra Agent", price=900)
    overflow = await client.post(
        f"{API}/intents/{intent_id}/auction/join",
        headers=_auth(extra_token),
        json={"offer_id": extra_offer},
    )
    assert overflow.status_code == 422
    assert overflow.json()["code"] == 48005


@pytest.mark.asyncio
async def test_one_deal_per_intent(client: AsyncClient):
    buyer_token = await _register(client, suffix="buyer-one-deal")
    agent1_token = await _register(client, suffix="one-agent1")
    agent2_token = await _register(client, suffix="one-agent2")

    offer1 = await _create_agent_offer(client, agent1_token, title="One Deal A", price=5000)
    offer2 = await _create_agent_offer(client, agent2_token, title="One Deal B", price=4500)
    intent_id = await _create_agent_intent(client, buyer_token)

    await client.post(
        f"{API}/intents/{intent_id}/auction/join",
        headers=_auth(agent1_token),
        json={"offer_id": offer1},
    )
    join2 = await client.post(
        f"{API}/intents/{intent_id}/auction/join",
        headers=_auth(agent2_token),
        json={"offer_id": offer2},
    )
    auction_id = join2.json()["data"]["id"]
    await client.post(f"{API}/intents/{intent_id}/auction/start", headers=_auth(buyer_token))

    bid = await client.post(
        f"{API}/auctions/{auction_id}/bid",
        headers=_auth(agent1_token),
        json={"amount_cents": 4000},
    )
    bid_id = bid.json()["data"]["bids"][0]["id"]
    select = await client.post(
        f"{API}/auctions/{auction_id}/select",
        headers=_auth(buyer_token),
        json={"bid_id": bid_id},
    )
    assert select.status_code == 200

    duplicate = await client.post(
        f"{API}/deals",
        headers=_auth(buyer_token),
        json={"intent_id": intent_id, "offer_id": offer2},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == 45009
