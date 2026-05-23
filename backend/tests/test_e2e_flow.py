"""HTTP 层端到端流程：注册 → 充值 → 发布供给 → 创建需求 → 匹配 → 成交 → 支付 → 交付 → 确认。"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.deals.tasks import clear_scheduled_tasks
from app.deals.webhooks import clear_registry
from app.main import app as fastapi_app

# 确保所有 ORM 表注册到 Base.metadata
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
    email = f"user-{suffix}@example.com"
    resp = await client.post(
        f"{API}/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": f"User {suffix}",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["code"] == 0
    return body["data"]["access_token"]


@pytest.mark.asyncio
async def test_full_flow_register_match_deal_complete(client: AsyncClient):
    seller_token = await _register(client, suffix="seller")
    buyer_token = await _register(client, suffix="buyer")

    # 卖方创建并发布供给
    offer_resp = await client.post(
        f"{API}/offers",
        headers=_auth(seller_token),
        json={
            "title": "Professional Logo Design",
            "description": "Brand logo and VI design service for startups",
            "category": "design",
            "channel": "human",
            "billing_model": "per_use",
            "price_cents": 10000,
            "currency": "CNY",
            "delivery_description": "Deliver logo files in SVG and PNG",
        },
    )
    assert offer_resp.status_code == 200
    offer_id = offer_resp.json()["data"]["id"]

    publish_resp = await client.post(
        f"{API}/offers/{offer_id}/publish",
        headers=_auth(seller_token),
    )
    assert publish_resp.status_code == 200
    assert publish_resp.json()["data"]["status"] == "published"

    # 买方充值（测试支付渠道即时到账）
    recharge_resp = await client.post(
        f"{API}/wallets/deposit-orders",
        headers=_auth(buyer_token),
        json={"amount_cents": 20000, "channel": "wechat"},
    )
    assert recharge_resp.status_code == 200, recharge_resp.text
    recharge_body = recharge_resp.json()["data"]
    assert recharge_body["status"] == "paid"
    assert recharge_body["wallet"]["balance_available"] == 20000

    # 买方创建需求（中文「设计」与卖方 logo/design 同义词匹配）
    intent_resp = await client.post(
        f"{API}/intents",
        headers=_auth(buyer_token),
        json={
            "title": "需要品牌设计",
            "description": "寻找 logo 与视觉设计服务",
            "category": "design",
            "channel": "human",
            "budget_max": 15000,
            "currency": "CNY",
        },
    )
    assert intent_resp.status_code == 200
    intent_id = intent_resp.json()["data"]["id"]

    # 运行匹配
    match_resp = await client.post(
        f"{API}/matching/run",
        headers=_auth(buyer_token),
        json={"intent_id": intent_id, "top_n": 5},
    )
    assert match_resp.status_code == 200, match_resp.text
    match_body = match_resp.json()
    assert match_body["code"] == 0
    candidates = match_body["data"]["candidates"]
    assert len(candidates) >= 1
    top = candidates[0]
    assert top["offer_id"] == offer_id
    assert "match_log_id" in top
    match_log_id = top["match_log_id"]
    uuid.UUID(match_log_id)
    assert top["recommend_auto"] is True or top["match_score"] >= 0
    assert "score_breakdown" in top
    assert "alignment" in top["score_breakdown"]

    # 用 match_log_id 创建成交
    deal_resp = await client.post(
        f"{API}/deals",
        headers=_auth(buyer_token),
        json={"match_log_id": match_log_id},
    )
    assert deal_resp.status_code == 200
    deal = deal_resp.json()["data"]
    deal_id = deal["id"]
    assert deal["match_log_id"] == match_log_id
    assert deal["status"] == "pending"

    # 支付
    pay_resp = await client.post(
        f"{API}/deals/{deal_id}/pay",
        headers=_auth(buyer_token),
    )
    assert pay_resp.status_code == 200
    assert pay_resp.json()["data"]["status"] == "in_progress"

    # 卖方交付
    deliver_resp = await client.post(
        f"{API}/deals/{deal_id}/deliver",
        headers=_auth(seller_token),
        json={"text": "Logo package delivered"},
    )
    assert deliver_resp.status_code == 200
    assert deliver_resp.json()["data"]["status"] == "delivered"

    # 买方确认
    confirm_resp = await client.post(
        f"{API}/deals/{deal_id}/confirm",
        headers=_auth(buyer_token),
        json={},
    )
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["data"]["status"] == "completed"

    # 卖方收到结算（扣 10% 佣金）
    seller_wallet = await client.get(f"{API}/wallets/me", headers=_auth(seller_token))
    assert seller_wallet.status_code == 200
    assert seller_wallet.json()["data"]["balance_available"] == 9000
