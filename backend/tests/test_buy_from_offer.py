"""一键购买 API 测试。"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.constants import KycLevel
from app.auth.models import User
from app.auth.schemas import CurrentUser
from app.core.database import Base
from app.deals.constants import DealStatus
from app.deals.service import buy_from_offer, pay_deal
from app.deals.webhooks import clear_registry
from app.intents.constants import IntentChannel
from app.offers.constants import OfferStatus
from app.offers.models import Offer
from app.wallets.service import recharge

import app.auth.models  # noqa: F401
import app.deals.models  # noqa: F401
import app.intents.models  # noqa: F401
import app.offers.models  # noqa: F401
import app.wallets.models  # noqa: F401


def _user(user_id: uuid.UUID) -> CurrentUser:
    return CurrentUser(id=user_id, role="user", caller_type="human", kyc_level=KycLevel.L0)


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


async def _seed_offer(db: AsyncSession):
    buyer_id = uuid.uuid4()
    seller_id = uuid.uuid4()
    db.add(
        User(
            id=buyer_id,
            email=f"{buyer_id}@test.com",
            password_hash="hash",
            display_name="买家",
        )
    )
    db.add(
        User(
            id=seller_id,
            email=f"{seller_id}@test.com",
            password_hash="hash",
            display_name="龙虾论文店",
        )
    )
    offer = Offer(
        user_id=seller_id,
        title="毕业论文写作 Agent",
        description="OpenClaw 专店",
        category="writing",
        price_cents=9900,
        tags={"channel": IntentChannel.AGENT, "billing_model": "per_use"},
        status=OfferStatus.PUBLISHED,
    )
    db.add(offer)
    await db.commit()
    await db.refresh(offer)
    return buyer_id, seller_id, offer.id


@pytest.mark.asyncio
async def test_buy_from_offer_creates_deal(db_session: AsyncSession):
    buyer_id, _, offer_id = await _seed_offer(db_session)
    result = await buy_from_offer(
        db_session,
        current=_user(buyer_id),
        offer_id=offer_id,
        buyer_note="计算机专业8000字",
    )
    assert result.deal.status == DealStatus.PENDING
    assert result.deal.offer_id == offer_id
    assert result.intent_id is not None


@pytest.mark.asyncio
async def test_buy_from_offer_then_pay(db_session: AsyncSession):
    buyer_id, _, offer_id = await _seed_offer(db_session)
    await recharge(db_session, user_id=buyer_id, amount_cents=20000)
    result = await buy_from_offer(
        db_session,
        current=_user(buyer_id),
        offer_id=offer_id,
    )
    paid = await pay_deal(db_session, deal_id=result.deal.id, current=_user(buyer_id))
    assert paid.status == DealStatus.IN_PROGRESS
