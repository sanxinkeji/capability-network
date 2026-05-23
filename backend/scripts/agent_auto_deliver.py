#!/usr/bin/env python3
"""轮询 in_progress 的 agent 订单并触发自动交付（演示备用脚本）。

正常流程已在 pay_deal 内联 auto_deliver；本脚本用于补救已支付但未自动交付的历史订单。

用法（项目根目录，后端已启动且 DB 可连）：
  python backend/scripts/agent_auto_deliver.py
  python backend/scripts/agent_auto_deliver.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import app.auth.models  # noqa: F401,E402
import app.deals.models  # noqa: F401,E402
import app.intents.models  # noqa: F401,E402
import app.offers.models  # noqa: F401,E402

from app.core.database import async_session  # noqa: E402
from app.deals.constants import DealStatus  # noqa: E402
from app.deals.models import Deal  # noqa: E402
from app.deals.service import auto_deliver_deal  # noqa: E402


async def run(*, dry_run: bool) -> int:
    delivered = 0
    async with async_session() as db:
        result = await db.execute(
            select(Deal).where(Deal.status == DealStatus.IN_PROGRESS)
        )
        deals = result.scalars().all()
        for deal in deals:
            if dry_run:
                print(f"[dry-run] would try auto_deliver deal_id={deal.id}")
                continue
            response = await auto_deliver_deal(db, deal_id=deal.id)
            if response is None:
                continue
            await db.commit()
            delivered += 1
            print(
                f"[delivered] deal_id={deal.id} status={response.status} "
                f"agent_auto={response.agent_auto_delivered}"
            )
    print(f"==> done: {delivered} agent deal(s) auto-delivered")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-deliver in_progress agent channel deals")
    parser.add_argument("--dry-run", action="store_true", help="List candidates without delivering")
    args = parser.parse_args()
    return asyncio.run(run(dry_run=args.dry_run))


if __name__ == "__main__":
    raise SystemExit(main())
