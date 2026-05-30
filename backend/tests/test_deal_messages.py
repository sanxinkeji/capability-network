"""订单会话消息 API 测试。"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.constants import KycLevel
from app.auth.models import User
from app.auth.schemas import CurrentUser
from app.core.database import Base
from app.deals.constants import DealStatus
from app.deals.messages import list_deal_messages, post_deal_message
from app.deals.schemas import DealCreateRequest, DealMessageCreateRequest
from app.deals.service import create_deal, pay_deal
from app.deals.webhooks import clear_registry
from app.intents.constants import IntentChannel
from app.intents.models import Intent
from app.matching.models import MatchLog
from app.offers.constants import OfferStatus
from app.offers.models import Offer
from app.wallets.service import recharge

import app.auth.models  # noqa: F401
import app.deals.models  # noqa: F401
import app.intents.models  # noqa: F401
import app.matching.models  # noqa: F401
import app.offers.models  # noqa: F401
import app.wallets.models  # noqa: F401


def _user(user_id: uuid.UUID, *, role: str = "user") -> CurrentUser:
    return CurrentUser(id=user_id, role=role, caller_type="human", kyc_level=KycLevel.L0)


@pytest.fixture
async def db_session():
    clear_registry()
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


async def _seed_agent_match(db: AsyncSession, *, amount: int = 50000):
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
        title="论文写作 Agent · OpenClaw",
        description="智能体辅助论文撰写与润色",
        category="writing",
        price_cents=amount,
        tags={"channel": IntentChannel.AGENT, "billing_model": "per_use"},
        status=OfferStatus.PUBLISHED,
    )
    intent = Intent(
        user_id=buyer_id,
        title="毕业论文写作",
        description="计算机专业，8000字，查重低于15%",
        category="writing",
        budget_cents=amount,
        tags={"channel": IntentChannel.AGENT, "settlement": "points"},
    )
    db.add(offer)
    db.add(intent)
    await db.flush()

    db.add(
        MatchLog(
            intent_id=intent.id,
            offer_id=offer.id,
            score=0.92,
            rank=1,
            algorithm="keyword_v1",
            metadata_={"recommend_auto": True},
        )
    )
    await db.commit()
    return buyer_id, seller_id, intent.id, offer.id


@pytest.mark.asyncio
async def test_pay_bootstraps_chat_messages(db_session: AsyncSession):
    buyer_id, _, intent_id, offer_id = await _seed_agent_match(db_session)
    await recharge(db_session, user_id=buyer_id, amount_cents=100000)

    created = await create_deal(
        db_session,
        current=_user(buyer_id),
        payload=DealCreateRequest(intent_id=intent_id, offer_id=offer_id),
    )
    await pay_deal(db_session, deal_id=created.id, current=_user(buyer_id))

    listing = await list_deal_messages(
        db_session, deal_id=created.id, current=_user(buyer_id)
    )
    assert listing.total >= 2
    roles = [item.sender_role for item in listing.items]
    assert "system" in roles
    assert "agent" in roles
    assert any("智能助手" in item.body for item in listing.items)


@pytest.mark.asyncio
async def test_buyer_message_triggers_demo_delivery(db_session: AsyncSession):
    buyer_id, _, intent_id, offer_id = await _seed_agent_match(db_session)
    await recharge(db_session, user_id=buyer_id, amount_cents=100000)

    created = await create_deal(
        db_session,
        current=_user(buyer_id),
        payload=DealCreateRequest(intent_id=intent_id, offer_id=offer_id),
    )
    await pay_deal(db_session, deal_id=created.id, current=_user(buyer_id))

    await post_deal_message(
        db_session,
        deal_id=created.id,
        current=_user(buyer_id),
        payload=DealMessageCreateRequest(
            body="专业：计算机科学，字数8000，截止下周五，学校模板已上传邮箱。"
        ),
    )

    listing = await list_deal_messages(
        db_session, deal_id=created.id, current=_user(buyer_id)
    )
    assert any(item.kind == "delivery" for item in listing.items)

    from app.deals.service import get_deal

    deal = await get_deal(db_session, deal_id=created.id, current=_user(buyer_id))
    assert deal.status == DealStatus.DELIVERED
