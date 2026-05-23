#!/usr/bin/env python3
"""删除 QA / 演示账号及其关联业务数据（上线前执行）。

匹配邮箱：
  - *_qa@test.com（buyer_qa、seller_qa、admin_qa、seller2_qa 等）
  - smoke@example.com（宝塔冒烟脚本）
  - agent@test.com（文档示例）

用法（项目根目录，需已配置 backend/.env 或根目录 .env）：
  python backend/scripts/purge_demo_data.py --dry-run
  python backend/scripts/purge_demo_data.py --confirm
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete, or_, select, update

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import app.auth.models  # noqa: F401,E402
import app.auctions.models  # noqa: F401,E402
import app.deals.models  # noqa: F401,E402
import app.intents.models  # noqa: F401,E402
import app.matching.models  # noqa: F401,E402
import app.offers.models  # noqa: F401,E402
import app.wallets.models  # noqa: F401,E402

from app.auth.models import ApiKey, RefreshToken, User  # noqa: E402
from app.auctions.models import Auction, AuctionBid, AuctionMessage, AuctionParticipant  # noqa: E402
from app.core.database import async_session  # noqa: E402
from app.deals.models import Deal, DealExtension, DealIdempotency  # noqa: E402
from app.intents.models import Intent  # noqa: E402
from app.matching.models import MatchLog  # noqa: E402
from app.offers.models import Offer  # noqa: E402
from app.platform.models import AdminAuditLog, DatabaseBackup, PlatformCode, PlatformSettings  # noqa: E402
from app.wallets.models import PaymentOrder, Wallet, WalletLedger, WithdrawRequest  # noqa: E402

DEMO_EMAILS = frozenset(
    {
        "buyer_qa@test.com",
        "seller_qa@test.com",
        "seller2_qa@test.com",
        "admin_qa@test.com",
        "smoke@example.com",
        "agent@test.com",
    }
)


def is_demo_email(email: str) -> bool:
    lower = email.lower()
    if lower in DEMO_EMAILS:
        return True
    if lower.endswith("_qa@test.com"):
        return True
    return False


async def purge_demo_users(*, dry_run: bool) -> None:
    async with async_session() as db:
        users = (await db.execute(select(User))).scalars().all()
        demo_users = [u for u in users if is_demo_email(u.email)]
        if not demo_users:
            print("未发现演示/QA 账号，无需清理。")
            return

        demo_ids: list[UUID] = [u.id for u in demo_users]
        print(f"将清理 {len(demo_users)} 个演示账号：")
        for u in demo_users:
            print(f"  - {u.email} ({u.display_name}, role={u.role})")

        offer_ids = set(
            (await db.execute(select(Offer.id).where(Offer.user_id.in_(demo_ids)))).scalars().all()
        )
        intent_ids = set(
            (await db.execute(select(Intent.id).where(Intent.user_id.in_(demo_ids)))).scalars().all()
        )
        deal_ids = set(
            (
                await db.execute(
                    select(Deal.id).where(
                        or_(Deal.buyer_id.in_(demo_ids), Deal.seller_id.in_(demo_ids))
                    )
                )
            )
            .scalars()
            .all()
        )
        wallet_ids = set(
            (await db.execute(select(Wallet.id).where(Wallet.user_id.in_(demo_ids)))).scalars().all()
        )
        auction_ids = set(
            (
                await db.execute(select(Auction.id).where(Auction.intent_id.in_(intent_ids)))
            )
            .scalars()
            .all()
        )

        print(
            f"关联数据：offers={len(offer_ids)} intents={len(intent_ids)} "
            f"deals={len(deal_ids)} auctions={len(auction_ids)} wallets={len(wallet_ids)}"
        )

        if dry_run:
            print("\n[dry-run] 未写入数据库。确认后请加 --confirm 执行。")
            return

        if auction_ids:
            await db.execute(
                update(Auction).where(Auction.id.in_(auction_ids)).values(deal_id=None)
            )
            await db.execute(delete(AuctionMessage).where(AuctionMessage.auction_id.in_(auction_ids)))
            await db.execute(delete(AuctionBid).where(AuctionBid.auction_id.in_(auction_ids)))
            await db.execute(
                delete(AuctionParticipant).where(AuctionParticipant.auction_id.in_(auction_ids))
            )
            await db.execute(delete(Auction).where(Auction.id.in_(auction_ids)))

        if deal_ids:
            await db.execute(delete(DealIdempotency).where(DealIdempotency.deal_id.in_(deal_ids)))
            await db.execute(delete(DealExtension).where(DealExtension.deal_id.in_(deal_ids)))
            if wallet_ids:
                await db.execute(
                    delete(WalletLedger).where(
                        or_(
                            WalletLedger.deal_id.in_(deal_ids),
                            WalletLedger.wallet_id.in_(wallet_ids),
                        )
                    )
                )
            await db.execute(delete(Deal).where(Deal.id.in_(deal_ids)))

        if offer_ids or intent_ids:
            await db.execute(
                delete(MatchLog).where(
                    or_(MatchLog.offer_id.in_(offer_ids), MatchLog.intent_id.in_(intent_ids))
                )
            )

        if offer_ids:
            await db.execute(delete(Offer).where(Offer.id.in_(offer_ids)))
        if intent_ids:
            await db.execute(delete(Intent).where(Intent.id.in_(intent_ids)))

        await db.execute(delete(PaymentOrder).where(PaymentOrder.user_id.in_(demo_ids)))
        await db.execute(delete(WithdrawRequest).where(WithdrawRequest.user_id.in_(demo_ids)))
        if wallet_ids:
            await db.execute(delete(WalletLedger).where(WalletLedger.wallet_id.in_(wallet_ids)))
            await db.execute(delete(Wallet).where(Wallet.id.in_(wallet_ids)))

        await db.execute(delete(ApiKey).where(ApiKey.user_id.in_(demo_ids)))
        await db.execute(delete(RefreshToken).where(RefreshToken.user_id.in_(demo_ids)))

        await db.execute(
            update(PlatformSettings)
            .where(PlatformSettings.updated_by_id.in_(demo_ids))
            .values(updated_by_id=None)
        )
        await db.execute(
            update(DatabaseBackup)
            .where(DatabaseBackup.created_by_admin_id.in_(demo_ids))
            .values(created_by_admin_id=None)
        )
        await db.execute(
            update(PlatformCode)
            .where(PlatformCode.used_by_id.in_(demo_ids))
            .values(used_by_id=None)
        )
        await db.execute(delete(PlatformCode).where(PlatformCode.created_by_id.in_(demo_ids)))
        await db.execute(delete(AdminAuditLog).where(AdminAuditLog.admin_id.in_(demo_ids)))

        await db.execute(delete(User).where(User.id.in_(demo_ids)))

        await db.commit()
        print("\n演示数据已清理完成。请通过运营后台创建真实管理员账号。")


def main() -> None:
    parser = argparse.ArgumentParser(description="删除 QA/演示账号及关联数据")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅预览将删除的账号，不写入数据库（默认行为）",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="确认执行删除",
    )
    args = parser.parse_args()
    dry_run = not args.confirm
    if dry_run:
        print("==> 预览模式（加 --confirm 才会真正删除）\n")
    asyncio.run(purge_demo_users(dry_run=dry_run))


if __name__ == "__main__":
    main()
