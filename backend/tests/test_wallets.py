import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.models import User
from app.core.database import Base
from app.deals.models import Deal
from app.intents.models import Intent
from app.offers.models import Offer
from app.wallets.constants import LedgerEntryType
from app.wallets.models import Wallet, WalletLedger
from app.wallets.service import (
    freeze,
    get_my_wallet,
    recharge,
    settle,
    unfreeze,
)

# 确保所有 ORM 表注册到 Base.metadata（含 deal_extensions 等）
import app.auth.models  # noqa: F401
import app.deals.models  # noqa: F401
import app.matching.models  # noqa: F401
import app.wallets.models  # noqa: F401


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


async def _seed_deal(db: AsyncSession, *, amount: int = 10000) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
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
        title="offer",
        description="desc",
        category="test",
        price_cents=amount,
        tags={},
        status="published",
    )
    intent = Intent(
        user_id=buyer_id,
        title="intent",
        description="desc",
        category="test",
        budget_cents=amount,
        tags={},
    )
    db.add(offer)
    db.add(intent)
    await db.flush()

    deal = Deal(
        offer_id=offer.id,
        intent_id=intent.id,
        buyer_id=buyer_id,
        seller_id=seller_id,
        amount_cents=amount,
        status="paid",
    )
    db.add(deal)
    await db.commit()
    return buyer_id, seller_id, deal.id


@pytest.mark.asyncio
async def test_recharge_and_get_wallet(db_session: AsyncSession):
    user_id = uuid.uuid4()
    await recharge(db_session, user_id=user_id, amount_cents=5000, points_cents=2000)
    wallet = await get_my_wallet(db_session, user_id=user_id)
    assert wallet.balance_available == 5000
    assert wallet.points_non_withdrawable == 2000
    assert wallet.balance_frozen == 0


@pytest.mark.asyncio
async def test_freeze_deducts_points_before_available(db_session: AsyncSession):
    buyer_id, _, deal_id = await _seed_deal(db_session, amount=10000)
    await recharge(db_session, user_id=buyer_id, amount_cents=7000, points_cents=5000)

    result = await freeze(db_session, user_id=buyer_id, deal_id=deal_id, amount=10000)
    assert result.from_points_cents == 5000
    assert result.from_available_cents == 5000
    assert result.balance_frozen_after == 10000

    wallet = await get_my_wallet(db_session, user_id=buyer_id)
    assert wallet.points_non_withdrawable == 0
    assert wallet.balance_available == 2000
    assert wallet.balance_frozen == 10000


@pytest.mark.asyncio
async def test_freeze_settle_ledger_correct(db_session: AsyncSession):
    buyer_id, seller_id, deal_id = await _seed_deal(db_session, amount=10000)
    await recharge(db_session, user_id=buyer_id, amount_cents=10000)
    await freeze(db_session, user_id=buyer_id, deal_id=deal_id, amount=10000)

    settle_result = await settle(db_session, deal_id=deal_id)
    assert settle_result.commission_cents == 1000
    assert settle_result.seller_net_cents == 9000

    buyer = await get_my_wallet(db_session, user_id=buyer_id)
    seller = await get_my_wallet(db_session, user_id=seller_id)
    assert buyer.balance_available == 0
    assert buyer.balance_frozen == 0
    assert seller.balance_available == 9000

    buyer_wallet = (await db_session.execute(select(Wallet).where(Wallet.user_id == buyer_id))).scalar_one()
    seller_wallet = (await db_session.execute(select(Wallet).where(Wallet.user_id == seller_id))).scalar_one()

    buyer_ledger = (
        await db_session.execute(
            select(WalletLedger).where(WalletLedger.wallet_id == buyer_wallet.id, WalletLedger.deal_id == deal_id)
        )
    ).scalars().all()
    seller_ledger = (
        await db_session.execute(
            select(WalletLedger).where(WalletLedger.wallet_id == seller_wallet.id, WalletLedger.deal_id == deal_id)
        )
    ).scalars().all()

    buyer_types = {entry.entry_type for entry in buyer_ledger}
    seller_types = {entry.entry_type for entry in seller_ledger}
    assert LedgerEntryType.FREEZE in buyer_types
    assert LedgerEntryType.PAYMENT in buyer_types
    assert LedgerEntryType.FEE in buyer_types
    assert LedgerEntryType.PAYMENT in seller_types
    assert sum(entry.amount_cents for entry in seller_ledger if entry.entry_type == LedgerEntryType.PAYMENT) == 9000


@pytest.mark.asyncio
async def test_unfreeze_restores_points_and_available(db_session: AsyncSession):
    buyer_id, _, deal_id = await _seed_deal(db_session, amount=8000)
    await recharge(db_session, user_id=buyer_id, amount_cents=5000, points_cents=5000)
    await freeze(db_session, user_id=buyer_id, deal_id=deal_id, amount=8000)

    await unfreeze(db_session, user_id=buyer_id, deal_id=deal_id)

    wallet = await get_my_wallet(db_session, user_id=buyer_id)
    assert wallet.points_non_withdrawable == 5000
    assert wallet.balance_available == 5000
    assert wallet.balance_frozen == 0
