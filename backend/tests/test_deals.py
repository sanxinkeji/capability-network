import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.constants import KycLevel
from app.auth.models import User
from app.auth.schemas import CurrentUser
from app.core.database import Base
from app.deals.constants import DealStatus
from app.deals.schemas import DealConfirmRequest, DealCreateRequest, DealDeliverRequest, DealDisputeRequest
from app.deals.service import confirm_deal, create_deal, deliver_deal, dispute_deal, pay_deal, refund_deal
from app.deals.tasks import clear_scheduled_tasks, get_scheduled_deadline
from app.deals.webhooks import clear_registry
from app.intents.constants import IntentChannel
from app.intents.models import Intent
from app.matching.models import MatchLog
from app.offers.constants import OfferStatus
from app.offers.models import Offer
from app.wallets.service import get_my_wallet, recharge

# 确保所有 ORM 表注册到 Base.metadata
import app.auth.models  # noqa: F401
import app.deals.models  # noqa: F401
import app.wallets.models  # noqa: F401


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


async def _seed_match(
    db: AsyncSession,
    *,
    amount: int = 10000,
    channel: str = IntentChannel.HUMAN,
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID]:
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
            display_name="seller",
        )
    )
    offer = Offer(
        user_id=seller_id,
        title="test offer",
        description="offer description for matching",
        category="test",
        price_cents=amount,
        tags={"channel": channel},
        status=OfferStatus.PUBLISHED,
    )
    intent = Intent(
        user_id=buyer_id,
        title="test intent",
        description="intent description for matching",
        category="test",
        budget_cents=amount,
        tags={"channel": channel, "settlement": "fiat"},
    )
    db.add(offer)
    db.add(intent)
    await db.flush()

    match_log = MatchLog(
        intent_id=intent.id,
        offer_id=offer.id,
        score=0.85,
        rank=1,
        algorithm="keyword_v1",
        metadata_={"recommend_auto": True},
    )
    db.add(match_log)
    await db.commit()
    return buyer_id, seller_id, intent.id, offer.id, match_log.id


@pytest.mark.asyncio
async def test_deal_flow_create_deliver_confirm_settle(db_session: AsyncSession):
    buyer_id, seller_id, intent_id, offer_id, _ = await _seed_match(db_session, amount=10000)
    await recharge(db_session, user_id=buyer_id, amount_cents=10000)

    created = await create_deal(
        db_session,
        current=_user(buyer_id),
        payload=DealCreateRequest(intent_id=intent_id, offer_id=offer_id),
    )
    assert created.status == DealStatus.PENDING
    assert created.auto_confirm is False

    paid = await pay_deal(db_session, deal_id=created.id, current=_user(buyer_id))
    assert paid.status == DealStatus.IN_PROGRESS

    buyer_wallet = await get_my_wallet(db_session, user_id=buyer_id)
    assert buyer_wallet.balance_frozen == 10000

    delivered = await deliver_deal(
        db_session,
        deal_id=created.id,
        current=_user(seller_id),
        payload=DealDeliverRequest(text="delivery payload content"),
    )
    assert delivered.status == DealStatus.DELIVERED
    assert delivered.delivery_text == "delivery payload content"
    assert get_scheduled_deadline(created.id) is not None

    confirmed = await confirm_deal(
        db_session,
        deal_id=created.id,
        current=_user(buyer_id),
        payload=DealConfirmRequest(),
    )
    assert confirmed.status == DealStatus.COMPLETED
    assert confirmed.completed_at is not None

    buyer = await get_my_wallet(db_session, user_id=buyer_id)
    seller = await get_my_wallet(db_session, user_id=seller_id)
    assert buyer.balance_frozen == 0
    assert seller.balance_available == 9000


@pytest.mark.asyncio
async def test_deal_create_from_match_log_id(db_session: AsyncSession):
    buyer_id, _, _, _, match_log_id = await _seed_match(db_session, amount=8000)
    await recharge(db_session, user_id=buyer_id, amount_cents=8000)

    created = await create_deal(
        db_session,
        current=_user(buyer_id),
        payload=DealCreateRequest(match_log_id=match_log_id),
    )
    assert created.status == DealStatus.PENDING
    assert created.match_log_id == match_log_id
    assert created.amount_cents == 8000

    paid = await pay_deal(db_session, deal_id=created.id, current=_user(buyer_id))
    assert paid.status == DealStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_deal_dispute_keeps_funds_frozen(db_session: AsyncSession):
    buyer_id, seller_id, intent_id, offer_id, _ = await _seed_match(db_session, amount=5000)
    await recharge(db_session, user_id=buyer_id, amount_cents=5000)

    created = await create_deal(
        db_session,
        current=_user(buyer_id),
        payload=DealCreateRequest(intent_id=intent_id, offer_id=offer_id),
    )
    await pay_deal(db_session, deal_id=created.id, current=_user(buyer_id))
    await deliver_deal(
        db_session,
        deal_id=created.id,
        current=_user(seller_id),
        payload=DealDeliverRequest(payload_url="https://example.com/result"),
    )

    disputed = await dispute_deal(
        db_session,
        deal_id=created.id,
        current=_user(buyer_id),
        payload=DealDisputeRequest(dispute_reason="quality not acceptable"),
    )
    assert disputed.status == DealStatus.DISPUTED

    buyer = await get_my_wallet(db_session, user_id=buyer_id)
    seller = await get_my_wallet(db_session, user_id=seller_id)
    assert buyer.balance_frozen == 5000
    assert seller.balance_available == 0

    refunded = await refund_deal(
        db_session,
        deal_id=created.id,
        current=_user(buyer_id, role="admin"),
    )
    assert refunded.status == DealStatus.REFUNDED
    assert refunded.refund_amount_cents == 5000

    buyer_after = await get_my_wallet(db_session, user_id=buyer_id)
    assert buyer_after.balance_frozen == 0
    assert buyer_after.balance_available == 5000


@pytest.mark.asyncio
async def test_per_query_auto_confirm_on_deliver(db_session: AsyncSession):
    buyer_id, seller_id, intent_id, offer_id, _ = await _seed_match(
        db_session, amount=3000, channel="per_query"
    )
    await recharge(db_session, user_id=buyer_id, amount_cents=3000)

    created = await create_deal(
        db_session,
        current=_user(buyer_id),
        payload=DealCreateRequest(intent_id=intent_id, offer_id=offer_id),
    )
    assert created.auto_confirm is True

    await pay_deal(db_session, deal_id=created.id, current=_user(buyer_id))

    completed = await deliver_deal(
        db_session,
        deal_id=created.id,
        current=_user(seller_id),
        payload=DealDeliverRequest(text="instant answer"),
    )
    assert completed.status == DealStatus.COMPLETED

    seller = await get_my_wallet(db_session, user_id=seller_id)
    assert seller.balance_available == 2700
