"""Agent 通道：支付后由 Agent 调用 deliver 接口提交交付。"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.constants import KycLevel
from app.auth.models import User
from app.auth.schemas import CurrentUser
from app.core.database import Base, get_db
from app.deals.constants import DealStatus
from app.deals.models import Deal
from app.deals.schemas import DealCreateRequest, DealDeliverRequest
from app.deals.service import auto_deliver_deal, create_deal, deliver_deal, pay_deal
from app.deals.tasks import clear_scheduled_tasks, get_scheduled_deadline
from app.deals.webhooks import clear_registry
from app.intents.constants import IntentChannel
from app.intents.models import Intent
from app.main import app as fastapi_app
from app.matching.models import MatchLog
from app.offers.constants import OfferStatus
from app.offers.models import Offer
from app.wallets.service import get_my_wallet, recharge

import app.auth.models  # noqa: F401
import app.deals.models  # noqa: F401
import app.intents.models  # noqa: F401
import app.matching.models  # noqa: F401
import app.offers.models  # noqa: F401
import app.wallets.models  # noqa: F401

API = "/api/v1"


def _user(user_id: uuid.UUID, *, role: str = "user") -> CurrentUser:
    return CurrentUser(id=user_id, role=role, caller_type="human", kyc_level=KycLevel.L0)


@pytest.fixture
async def db_session():
    clear_registry()
    clear_scheduled_tasks()
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    clear_scheduled_tasks()
    await engine.dispose()


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


async def _promote_seller(session_factory, *, email: str) -> None:
    from app.auth.constants import UserRole

    async with session_factory() as session:
        user = (
            await session.execute(select(User).where(User.email == email))
        ).scalar_one()
        user.role = UserRole.SELLER
        await session.commit()


async def _seed_agent_match(
    db: AsyncSession,
    *,
    amount: int = 100,
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID]:
    buyer_id = uuid.uuid4()
    seller_id = uuid.uuid4()
    db.add(
        User(
            id=buyer_id,
            email=f"{buyer_id}@test.com",
            password_hash="hash",
            display_name="buyer",
        )
    )
    db.add(
        User(
            id=seller_id,
            email=f"{seller_id}@test.com",
            password_hash="hash",
            display_name="agent-seller",
        )
    )
    offer = Offer(
        user_id=seller_id,
        title="文档摘要 API · 按次 ¥1",
        description="自动摘要长文档，按次计费",
        category="ai",
        price_cents=amount,
        tags={"channel": IntentChannel.AGENT, "billing_model": "per_use"},
        status=OfferStatus.PUBLISHED,
    )
    intent = Intent(
        user_id=buyer_id,
        title="需要文档摘要",
        description="请对 10 页 PDF 生成中文摘要",
        category="ai",
        budget_cents=amount,
        tags={"channel": IntentChannel.AGENT, "settlement": "points"},
    )
    db.add(offer)
    db.add(intent)
    await db.flush()

    match_log = MatchLog(
        intent_id=intent.id,
        offer_id=offer.id,
        score=0.92,
        rank=1,
        algorithm="keyword_v1",
        metadata_={"recommend_auto": True},
    )
    db.add(match_log)
    await db.commit()
    return buyer_id, seller_id, intent.id, offer.id


@pytest.mark.asyncio
async def test_agent_pay_waits_for_delivery(db_session: AsyncSession):
    buyer_id, seller_id, intent_id, offer_id = await _seed_agent_match(db_session)
    await recharge(db_session, user_id=buyer_id, amount_cents=100)

    created = await create_deal(
        db_session,
        current=_user(buyer_id),
        payload=DealCreateRequest(intent_id=intent_id, offer_id=offer_id),
    )
    assert created.status == DealStatus.PENDING

    paid = await pay_deal(db_session, deal_id=created.id, current=_user(buyer_id))
    assert paid.status == DealStatus.IN_PROGRESS
    assert paid.agent_auto_delivered is False
    assert paid.delivery_text is None

    delivered = await deliver_deal(
        db_session,
        deal_id=created.id,
        current=_user(seller_id),
        payload=DealDeliverRequest(text="已完成 PDF 摘要交付"),
    )
    assert delivered.status == DealStatus.DELIVERED
    assert delivered.delivery_text == "已完成 PDF 摘要交付"
    assert get_scheduled_deadline(created.id) is not None

    buyer_wallet = await get_my_wallet(db_session, user_id=buyer_id)
    assert buyer_wallet.balance_frozen == 100


@pytest.mark.asyncio
async def test_auto_deliver_deal_with_payload(db_session: AsyncSession):
    buyer_id, _, intent_id, offer_id = await _seed_agent_match(db_session)
    await recharge(db_session, user_id=buyer_id, amount_cents=100)

    created = await create_deal(
        db_session,
        current=_user(buyer_id),
        payload=DealCreateRequest(intent_id=intent_id, offer_id=offer_id),
    )

    deal = (await db_session.execute(select(Deal).where(Deal.id == created.id))).scalar_one()
    deal.status = DealStatus.IN_PROGRESS
    await db_session.commit()

    result = await auto_deliver_deal(
        db_session,
        deal_id=created.id,
        delivery_text="Agent 交付结果：摘要已完成",
    )
    assert result is not None
    assert result.status == DealStatus.DELIVERED
    assert "摘要已完成" in (result.delivery_text or "")


@pytest.mark.asyncio
async def test_human_offer_pay_stays_in_progress(db_session: AsyncSession):
    buyer_id = uuid.uuid4()
    seller_id = uuid.uuid4()
    db_session.add_all(
        [
            User(id=buyer_id, email="b@test.com", password_hash="h", display_name="b"),
            User(id=seller_id, email="s@test.com", password_hash="h", display_name="s"),
        ]
    )
    offer = Offer(
        user_id=seller_id,
        title="human offer",
        description="manual delivery",
        category="design",
        price_cents=5000,
        tags={"channel": IntentChannel.HUMAN},
        status=OfferStatus.PUBLISHED,
    )
    intent = Intent(
        user_id=buyer_id,
        title="human intent",
        description="need design",
        category="design",
        budget_cents=5000,
        tags={"channel": IntentChannel.HUMAN, "settlement": "fiat"},
    )
    db_session.add(offer)
    db_session.add(intent)
    await db_session.flush()
    await db_session.commit()

    await recharge(db_session, user_id=buyer_id, amount_cents=5000)
    created = await create_deal(
        db_session,
        current=_user(buyer_id),
        payload=DealCreateRequest(intent_id=intent.id, offer_id=offer.id),
    )
    paid = await pay_deal(db_session, deal_id=created.id, current=_user(buyer_id))
    assert paid.status == DealStatus.IN_PROGRESS
    assert paid.agent_auto_delivered is False
    assert paid.delivery_text is None


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _register(client: AsyncClient, *, suffix: str) -> str:
    resp = await client.post(
        f"{API}/auth/register",
        json={
            "email": f"agent-{suffix}@example.com",
            "password": "password123",
            "display_name": f"Agent {suffix}",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_agent_deliver_via_api(client: AsyncClient):
    buyer_token = await _register(client, suffix="buyer-api")
    seller_token = await _register(client, suffix="seller-api")
    await _promote_seller(client.session_factory, email="agent-seller-api@example.com")

    offer_resp = await client.post(
        f"{API}/offers",
        headers=_auth(seller_token),
        json={
            "title": "品牌 Logo 生成 Agent",
            "description": "AI 自动生成品牌 Logo 方案",
            "category": "design",
            "channel": "agent",
            "billing_model": "per_use",
            "price_cents": 100,
            "currency": "CNY",
            "delivery_description": "自动生成交付 PNG 预览",
        },
    )
    assert offer_resp.status_code == 200
    offer_id = offer_resp.json()["data"]["id"]
    await client.post(f"{API}/offers/{offer_id}/publish", headers=_auth(seller_token))

    intent_resp = await client.post(
        f"{API}/intents",
        headers=_auth(buyer_token),
        json={
            "title": "AI Logo 需求",
            "description": "科技风 Logo，蓝色主色",
            "category": "design",
            "channel": "agent",
            "budget_max": 500,
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
    deal_id = deal_resp.json()["data"]["id"]

    await client.post(
        f"{API}/wallets/deposit-orders",
        headers=_auth(buyer_token),
        json={"amount_cents": 1000, "channel": "wechat"},
    )

    pay_resp = await client.post(
        f"{API}/deals/{deal_id}/pay",
        headers=_auth(buyer_token),
    )
    assert pay_resp.status_code == 200
    assert pay_resp.json()["data"]["status"] == "in_progress"

    deliver_resp = await client.post(
        f"{API}/deals/{deal_id}/deliver",
        headers=_auth(seller_token),
        json={"text": "Logo 方案已生成并交付"},
    )
    assert deliver_resp.status_code == 200
    data = deliver_resp.json()["data"]
    assert data["status"] == "delivered"
    assert "Logo 方案" in data["delivery_text"]

