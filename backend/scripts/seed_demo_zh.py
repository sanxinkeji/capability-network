#!/usr/bin/env python3
"""导入中文演示数据（供给 / 需求 / 可选匹配验证）。

前置：后端已启动（默认 http://127.0.0.1:8000），数据库已迁移。

用法（项目根目录）：
  python backend/scripts/seed_demo_zh.py
  python backend/scripts/seed_demo_zh.py --reset
  python backend/scripts/seed_demo_zh.py --purge-demo
  python backend/scripts/seed_demo_zh.py --base-url http://127.0.0.1:8000/api/v1 --run-match
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import re
import sys
from pathlib import Path

import httpx
from sqlalchemy import select

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

import app.auth.models  # noqa: F401,E402
import app.deals.models  # noqa: F401,E402
import app.intents.models  # noqa: F401,E402
import app.matching.models  # noqa: F401,E402
import app.offers.models  # noqa: F401,E402

from app.auth.models import User  # noqa: E402
from app.core.database import async_session  # noqa: E402
from app.deals.models import Deal  # noqa: E402
from app.intents.constants import IntentStatus  # noqa: E402
from app.intents.models import Intent  # noqa: E402
from app.matching.models import MatchLog  # noqa: E402
from app.offers.constants import OfferStatus  # noqa: E402
from app.offers.models import Offer  # noqa: E402

API_V1 = "/api/v1"

SELLER_EMAIL = "seller_qa@test.com"
BUYER_EMAIL = "buyer_qa@test.com"
ADMIN_EMAIL = "admin_qa@test.com"
SELLER2_EMAIL = "seller2_qa@test.com"
SELLER2_DISPLAY_NAME = "演示卖家二"
PASSWORD = "password123"
SELLER_DISPLAY_NAME = "演示卖家"
BUYER_DISPLAY_NAME = "演示买家"
ADMIN_DISPLAY_NAME = "演示管理员"

ZH_OFFER_TITLE = "品牌 Logo 设计服务"
ZH_OFFER_DESCRIPTION = (
    "提供专业品牌 Logo 与 VI 视觉设计，含 PNG/SVG 源文件交付，适合初创品牌。"
)
ZH_INTENT_TITLE = "需要品牌 Logo 设计"
ZH_INTENT_DESCRIPTION = (
    "寻找设计师为初创品牌做 Logo 与视觉识别设计，预算约 100 元，需源文件。"
)

AGENT_OFFER_SUMMARY_TITLE = "文档摘要 API · 按次 ¥1"
AGENT_OFFER_SUMMARY_DESCRIPTION = (
    "智能体自动摘要长文档，支持 PDF/Word，按次计费，秒级返回结构化摘要。"
)
AGENT_OFFER_LOGO_TITLE = "品牌 Logo 生成 Agent"
AGENT_OFFER_LOGO_DESCRIPTION = (
    "AI 智能体根据品牌描述自动生成 Logo 方案，含 PNG 预览与配色建议。"
)
ZH_AGENT_INTENT_TITLE = "需要 AI 文档摘要"
ZH_AGENT_INTENT_DESCRIPTION = (
    "对 20 页产品白皮书生成中文摘要，重点提取功能亮点，预算 1 元按次调用。"
)
ZH_AUCTION_INTENT_TITLE = "Logo 竞价演示需求"
ZH_AUCTION_INTENT_DESCRIPTION = (
    "需要智能体为品牌生成 Logo 方案，欢迎多个 Agent 竞价，预算 5 元。"
)
AGENT_OFFER_LOGO_B_TITLE = "Logo 竞标 Agent B"
AGENT_OFFER_LOGO_B_DESCRIPTION = (
    "第二路 Logo 智能体，侧重极简几何风格，支持快速迭代与低价竞标。"
)

CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def has_cjk(text: str) -> bool:
    return bool(CJK_RE.search(text))


class DemoSeedError(RuntimeError):
    pass


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=30.0)

    def close(self) -> None:
        self.client.close()

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.base_url}{path}"

    def request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        json: dict | None = None,
    ) -> dict:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = self.client.request(method, self._url(path), headers=headers, json=json)
        if response.status_code >= 400:
            raise DemoSeedError(
                f"{method} {path} failed ({response.status_code}): {response.text}"
            )
        body = response.json()
        if body.get("code") != 0:
            raise DemoSeedError(f"{method} {path} business error: {body}")
        return body

    def health_ok(self) -> bool:
        root = self.base_url.removesuffix(API_V1)
        try:
            response = self.client.get(f"{root}/health")
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    def login_or_register(
        self,
        *,
        email: str,
        password: str,
        display_name: str,
    ) -> str:
        try:
            body = self.request(
                "POST",
                "/auth/login",
                json={"account": email, "password": password},
            )
            print(f"  [login] {email}")
        except DemoSeedError:
            body = self.request(
                "POST",
                "/auth/register",
                json={"email": email, "password": password, "display_name": display_name},
            )
            print(f"  [register] {email} ({display_name})")
        return body["data"]["access_token"]


async def _ensure_admin_role() -> None:
    async with async_session() as db:
        admin = (
            await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        ).scalar_one_or_none()
        if admin is None:
            return
        if admin.role != "admin":
            admin.role = "admin"
            print(f"  [admin] {ADMIN_EMAIL} role -> admin")
        if admin.display_name != ADMIN_DISPLAY_NAME:
            admin.display_name = ADMIN_DISPLAY_NAME
        await db.commit()


async def run_db_maintenance(
    *,
    reset: bool,
    purge_demo: bool,
    update_names: bool,
) -> None:
    async with async_session() as db:
        seller = (
            await db.execute(select(User).where(User.email == SELLER_EMAIL))
        ).scalar_one_or_none()
        buyer = (
            await db.execute(select(User).where(User.email == BUYER_EMAIL))
        ).scalar_one_or_none()

        if reset:
            if seller:
                offers = (
                    await db.execute(
                        select(Offer).where(
                            Offer.user_id == seller.id,
                            Offer.status == OfferStatus.PUBLISHED,
                        )
                    )
                ).scalars().all()
                for offer in offers:
                    if not has_cjk(offer.title):
                        offer.status = OfferStatus.PAUSED
                        print(f"  [reset] paused offer: {offer.title}")

            if buyer:
                intents = (
                    await db.execute(
                        select(Intent).where(
                            Intent.user_id == buyer.id,
                            Intent.status == IntentStatus.OPEN,
                        )
                    )
                ).scalars().all()
                for intent in intents:
                    if not has_cjk(intent.title):
                        intent.status = IntentStatus.CLOSED
                        print(f"  [reset] closed intent: {intent.title}")

        if purge_demo:
            deal_offer_ids = set(
                (await db.execute(select(Deal.offer_id))).scalars().all()
            )
            deal_intent_ids = set(
                (await db.execute(select(Deal.intent_id))).scalars().all()
            )

            if seller:
                paused_offers = (
                    await db.execute(
                        select(Offer).where(
                            Offer.user_id == seller.id,
                            Offer.status == OfferStatus.PAUSED,
                        )
                    )
                ).scalars().all()
                for offer in paused_offers:
                    if offer.id in deal_offer_ids:
                        print(f"  [purge-demo] skip offer (linked deal): {offer.title}")
                        continue
                    await db.execute(
                        MatchLog.__table__.delete().where(MatchLog.offer_id == offer.id)
                    )
                    await db.delete(offer)
                    print(f"  [purge-demo] deleted paused offer: {offer.title}")

            if buyer:
                history_intents = (
                    await db.execute(
                        select(Intent).where(
                            Intent.user_id == buyer.id,
                            Intent.status.in_(
                                [IntentStatus.CLOSED, IntentStatus.MATCHED]
                            ),
                        )
                    )
                ).scalars().all()
                for intent in history_intents:
                    if has_cjk(intent.title):
                        continue
                    if intent.id in deal_intent_ids:
                        print(f"  [purge-demo] skip intent (linked deal): {intent.title}")
                        continue
                    await db.execute(
                        MatchLog.__table__.delete().where(MatchLog.intent_id == intent.id)
                    )
                    await db.delete(intent)
                    print(f"  [purge-demo] deleted history intent: {intent.title}")

        if update_names:
            for user, name in (
                (seller, SELLER_DISPLAY_NAME),
                (buyer, BUYER_DISPLAY_NAME),
            ):
                if user is None:
                    continue
                if user.display_name != name:
                    user.display_name = name
                    print(f"  [nickname] {user.email} -> {name}")

        admin = (
            await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        ).scalar_one_or_none()
        if admin is not None:
            changed = False
            if admin.role != "admin":
                admin.role = "admin"
                changed = True
                print(f"  [admin] {ADMIN_EMAIL} role -> admin")
            if update_names and admin.display_name != ADMIN_DISPLAY_NAME:
                admin.display_name = ADMIN_DISPLAY_NAME
                changed = True
                print(f"  [nickname] {ADMIN_EMAIL} -> {ADMIN_DISPLAY_NAME}")
            if not changed and admin.role == "admin":
                pass

        await db.commit()


def list_all_offers(api: ApiClient, token: str) -> list[dict]:
    items: list[dict] = []
    page = 1
    while True:
        body = api.request("GET", f"/offers?page={page}&page_size=100", token=token)
        data = body["data"]
        items.extend(data["items"])
        if len(items) >= data["total"]:
            break
        page += 1
    return items


def ensure_zh_offer(api: ApiClient, seller_token: str) -> str:
    for offer in list_all_offers(api, seller_token):
        if offer["title"] == ZH_OFFER_TITLE and offer["status"] == "published":
            print(f"  [skip] offer already exists: {offer['id']}")
            return offer["id"]

    body = api.request(
        "POST",
        "/offers",
        token=seller_token,
        json={
            "title": ZH_OFFER_TITLE,
            "description": ZH_OFFER_DESCRIPTION,
            "category": "design",
            "channel": "human",
            "billing_model": "per_use",
            "price_cents": 10000,
            "currency": "CNY",
            "delivery_description": "交付 PNG 与 SVG 源文件，含 2 轮修改",
        },
    )
    offer_id = body["data"]["id"]
    api.request("POST", f"/offers/{offer_id}/publish", token=seller_token)
    print(f"  [offer] created + published: {offer_id}")
    return offer_id


def ensure_zh_intent(api: ApiClient, buyer_token: str) -> str:
    profile = api.request("GET", "/users/me", token=buyer_token)
    buyer_id = profile["data"]["id"]
    body = api.request("GET", "/intents?status=open", token=buyer_token)
    for intent in body["data"]:
        if (
            intent["user_id"] == buyer_id
            and intent["title"] == ZH_INTENT_TITLE
            and intent["status"] == "open"
        ):
            print(f"  [skip] intent already exists: {intent['id']}")
            return intent["id"]

    body = api.request(
        "POST",
        "/intents",
        token=buyer_token,
        json={
            "title": ZH_INTENT_TITLE,
            "description": ZH_INTENT_DESCRIPTION,
            "category": "design",
            "channel": "human",
            "budget_max": 10000,
            "currency": "CNY",
        },
    )
    intent_id = body["data"]["id"]
    print(f"  [intent] created: {intent_id}")
    return intent_id


def ensure_agent_offers(api: ApiClient, seller_token: str) -> list[str]:
    """发布智能体通道供给（channel=agent）。"""
    existing = {o["title"]: o for o in list_all_offers(api, seller_token)}
    created_ids: list[str] = []

    specs = [
        {
            "title": AGENT_OFFER_SUMMARY_TITLE,
            "description": AGENT_OFFER_SUMMARY_DESCRIPTION,
            "category": "ai",
            "channel": "agent",
            "billing_model": "per_use",
            "price_cents": 100,
            "delivery_description": "JSON 结构化摘要 + 关键句列表",
        },
        {
            "title": AGENT_OFFER_LOGO_TITLE,
            "description": AGENT_OFFER_LOGO_DESCRIPTION,
            "category": "design",
            "channel": "agent",
            "billing_model": "per_use",
            "price_cents": 500,
            "delivery_description": "自动生成 Logo PNG 预览与配色方案",
        },
    ]

    for spec in specs:
        title = spec["title"]
        if title in existing and existing[title]["status"] == "published":
            print(f"  [skip] agent offer already exists: {existing[title]['id']}")
            created_ids.append(existing[title]["id"])
            continue

        body = api.request(
            "POST",
            "/offers",
            token=seller_token,
            json={
                **spec,
                "currency": "CNY",
            },
        )
        offer_id = body["data"]["id"]
        api.request("POST", f"/offers/{offer_id}/publish", token=seller_token)
        print(f"  [agent-offer] created + published: {offer_id} — {title}")
        created_ids.append(offer_id)

    return created_ids


def ensure_zh_agent_intent(api: ApiClient, buyer_token: str) -> str:
    profile = api.request("GET", "/users/me", token=buyer_token)
    buyer_id = profile["data"]["id"]
    body = api.request("GET", "/intents?status=open", token=buyer_token)
    for intent in body["data"]:
        if (
            intent["user_id"] == buyer_id
            and intent["title"] == ZH_AGENT_INTENT_TITLE
            and intent["status"] == "open"
        ):
            print(f"  [skip] agent intent already exists: {intent['id']}")
            return intent["id"]

    body = api.request(
        "POST",
        "/intents",
        token=buyer_token,
        json={
            "title": ZH_AGENT_INTENT_TITLE,
            "description": ZH_AGENT_INTENT_DESCRIPTION,
            "category": "ai",
            "channel": "agent",
            "budget_max": 100,
            "currency": "CNY",
        },
    )
    intent_id = body["data"]["id"]
    print(f"  [agent-intent] created: {intent_id}")
    return intent_id


def ensure_seller2_agent_offer(api: ApiClient, seller2_token: str) -> str:
    existing = {o["title"]: o for o in list_all_offers(api, seller2_token)}
    title = AGENT_OFFER_LOGO_B_TITLE
    if title in existing and existing[title]["status"] == "published":
        print(f"  [skip] seller2 agent offer exists: {existing[title]['id']}")
        return existing[title]["id"]

    body = api.request(
        "POST",
        "/offers",
        token=seller2_token,
        json={
            "title": title,
            "description": AGENT_OFFER_LOGO_B_DESCRIPTION,
            "category": "design",
            "channel": "agent",
            "billing_model": "per_use",
            "price_cents": 480,
            "currency": "CNY",
            "delivery_description": "极简 Logo PNG + 配色 JSON",
        },
    )
    offer_id = body["data"]["id"]
    api.request("POST", f"/offers/{offer_id}/publish", token=seller2_token)
    print(f"  [seller2-offer] created + published: {offer_id}")
    return offer_id


def ensure_auction_intent(api: ApiClient, buyer_token: str) -> str:
    profile = api.request("GET", "/users/me", token=buyer_token)
    buyer_id = profile["data"]["id"]
    body = api.request("GET", "/intents?status=open", token=buyer_token)
    for intent in body["data"]:
        if (
            intent["user_id"] == buyer_id
            and intent["title"] == ZH_AUCTION_INTENT_TITLE
            and intent["status"] in ("open", "matched", "auctioning")
        ):
            print(f"  [skip] auction intent exists: {intent['id']} ({intent['status']})")
            return intent["id"]

    body = api.request(
        "POST",
        "/intents",
        token=buyer_token,
        json={
            "title": ZH_AUCTION_INTENT_TITLE,
            "description": ZH_AUCTION_INTENT_DESCRIPTION,
            "category": "design",
            "channel": "agent",
            "budget_max": 500,
            "currency": "CNY",
        },
    )
    intent_id = body["data"]["id"]
    print(f"  [auction-intent] created: {intent_id}")
    return intent_id


def run_auction_demo(
    api: ApiClient,
    *,
    buyer_token: str,
    seller_token: str,
    seller2_token: str,
    intent_id: str,
    offer_a_id: str,
    offer_b_id: str,
    complete: bool,
) -> None:
    """Agent 报名至 matched；可选完成出价 + 选定 + 支付。"""
    join_a = api.request(
        "POST",
        f"/intents/{intent_id}/auction/join",
        token=seller_token,
        json={"offer_id": offer_a_id},
    )
    auction = join_a["data"]
    print(
        f"  [auction-join] seller1 -> participants={auction['participant_count']} "
        f"status={auction['status']}"
    )

    join_b = api.request(
        "POST",
        f"/intents/{intent_id}/auction/join",
        token=seller2_token,
        json={"offer_id": offer_b_id},
    )
    auction = join_b["data"]
    print(
        f"  [auction-join] seller2 -> participants={auction['participant_count']} "
        f"status={auction['status']}"
    )
    if auction["status"] != "matched":
        raise DemoSeedError(f"expected auction status matched, got {auction['status']}")

    auction_id = auction["id"]
    if not complete:
        print(f"  [auction] ready — open http://127.0.0.1:5173/app/auctions/{intent_id}")
        return

    api.request("POST", f"/intents/{intent_id}/auction/start", token=buyer_token)
    print("  [auction] started (auctioning)")

    bid_b = api.request(
        "POST",
        f"/auctions/{auction_id}/bid",
        token=seller2_token,
        json={"amount_cents": 450},
    )
    bids = bid_b["data"]["bids"]
    if not bids:
        raise DemoSeedError("no bids after seller2 bid")
    win_bid = min(bids, key=lambda item: item["amount_cents"])
    print(f"  [auction-bid] lowest={win_bid['amount_cents']} cents")

    selected = api.request(
        "POST",
        f"/auctions/{auction_id}/select",
        token=buyer_token,
        json={"bid_id": win_bid["id"]},
    )
    deal_id = selected["data"].get("deal_id")
    if not deal_id:
        raise DemoSeedError("deal_id missing after select")
    print(f"  [auction-select] deal_id={deal_id}")

    try:
        api.request("POST", "/wallets/recharge", token=buyer_token, json={"amount_cents": 10000})
    except DemoSeedError:
        pass
    paid = api.request("POST", f"/deals/{deal_id}/pay", token=buyer_token)
    print(f"  [auction-pay] deal status={paid['data']['status']}")


def run_match_check(api: ApiClient, buyer_token: str, intent_id: str) -> None:
    body = api.request(
        "POST",
        "/matching/run",
        token=buyer_token,
        json={"intent_id": intent_id, "top_n": 5},
    )
    candidates = body["data"]["candidates"]
    if not candidates:
        raise DemoSeedError("matching returned no candidates for Chinese demo intent")
    top = candidates[0]
    print(
        "  [match] "
        f"candidates={len(candidates)}, "
        f"top={top['title']} score={top['match_score']}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed Chinese demo data for capability-network")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000/api/v1",
        help="API base URL (default: http://127.0.0.1:8000/api/v1)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Pause English published offers and close English open intents for demo accounts",
    )
    parser.add_argument(
        "--purge-demo",
        action="store_true",
        help=(
            "Delete paused offers and English closed/matched intents for QA accounts "
            "(skips rows linked to deals; keeps Chinese samples)"
        ),
    )
    parser.add_argument(
        "--run-match",
        action="store_true",
        help="Run matching for the Chinese intent (does not create deals)",
    )
    parser.add_argument(
        "--skip-names",
        action="store_true",
        help="Do not update demo account display names to Chinese",
    )
    parser.add_argument(
        "--run-auction",
        action="store_true",
        help="Prepare agent auction demo (2 sellers join, status matched)",
    )
    parser.add_argument(
        "--run-auction-complete",
        action="store_true",
        help="Full auction flow: join → start → bid → select → pay (implies --run-auction)",
    )
    return parser.parse_args()


async def _finalize_db(
    *,
    reset: bool,
    purge_demo: bool,
    update_names: bool,
) -> None:
    """注册完成后的 DB 维护 + 管理员 role（单次 asyncio 调用）。"""
    if reset or purge_demo or update_names:
        await run_db_maintenance(
            reset=reset,
            purge_demo=purge_demo,
            update_names=update_names,
        )
    await _ensure_admin_role()


def main() -> int:
    args = parse_args()
    api = ApiClient(args.base_url)

    print("==> 中文演示数据 seed")
    if not api.health_ok():
        print("后端未响应。请先启动：cd backend && python -m uvicorn app.main:app --reload --port 8000")
        api.close()
        return 1

    try:
        db_steps: list[str] = []
        run_maintenance = args.reset or args.purge_demo or not args.skip_names

        if run_maintenance:
            if args.reset:
                db_steps.append("清理旧英文演示记录")
            if args.purge_demo:
                db_steps.append("删除历史演示垃圾数据")
            if not args.skip_names:
                db_steps.append("更新演示账号昵称")
            print(f"\n1. {' + '.join(db_steps) if db_steps else '维护演示账号'}")
        else:
            print("\n1. 维护演示账号")

        print("\n2. 登录 / 注册演示账号")
        seller_token = api.login_or_register(
            email=SELLER_EMAIL,
            password=PASSWORD,
            display_name=SELLER_DISPLAY_NAME,
        )
        buyer_token = api.login_or_register(
            email=BUYER_EMAIL,
            password=PASSWORD,
            display_name=BUYER_DISPLAY_NAME,
        )
        api.login_or_register(
            email=ADMIN_EMAIL,
            password=PASSWORD,
            display_name=ADMIN_DISPLAY_NAME,
        )
        seller2_token = api.login_or_register(
            email=SELLER2_EMAIL,
            password=PASSWORD,
            display_name=SELLER2_DISPLAY_NAME,
        )

        # 单次 asyncio.run，避免 Windows 上二次 run 导致 asyncpg 连接池异常
        asyncio.run(
            _finalize_db(
                reset=args.reset,
                purge_demo=args.purge_demo,
                update_names=not args.skip_names,
            )
        )

        print("\n3. 卖方：发布中文供给")
        ensure_zh_offer(api, seller_token)

        print("\n4. 卖方：发布智能体供给（channel=agent）")
        agent_offer_ids = ensure_agent_offers(api, seller_token)
        logo_offer_a = agent_offer_ids[1] if len(agent_offer_ids) > 1 else agent_offer_ids[0]

        print("\n5. 卖方二：发布竞价用 Agent 供给")
        logo_offer_b = ensure_seller2_agent_offer(api, seller2_token)

        print("\n6. 买方：创建中文需求")
        intent_id = ensure_zh_intent(api, buyer_token)

        print("\n7. 买方：创建智能体需求")
        agent_intent_id = ensure_zh_agent_intent(api, buyer_token)

        run_auction = args.run_auction or args.run_auction_complete
        auction_intent_id: str | None = None
        if run_auction:
            print("\n8. 买方：创建 Logo 竞价演示需求")
            auction_intent_id = ensure_auction_intent(api, buyer_token)
            print("\n9. Agent 竞价室演示")
            run_auction_demo(
                api,
                buyer_token=buyer_token,
                seller_token=seller_token,
                seller2_token=seller2_token,
                intent_id=auction_intent_id,
                offer_a_id=logo_offer_a,
                offer_b_id=logo_offer_b,
                complete=args.run_auction_complete,
            )

        if args.run_match:
            step = 10 if run_auction else 8
            print(f"\n{step}. 匹配验证（不创建订单）")
            run_match_check(api, buyer_token, intent_id)
            run_match_check(api, buyer_token, agent_intent_id)
            if auction_intent_id:
                run_match_check(api, buyer_token, auction_intent_id)

        print("\n==> 中文演示数据 seed 完成")
        print(f"  卖方 {SELLER_EMAIL} / {PASSWORD} — 人工「{ZH_OFFER_TITLE}」+ 智能体供给")
        print(f"  卖方二 {SELLER2_EMAIL} / {PASSWORD} — 「{AGENT_OFFER_LOGO_B_TITLE}」")
        print(f"  买方 {BUYER_EMAIL} / {PASSWORD} — 人工「{ZH_INTENT_TITLE}」+ 智能体「{ZH_AGENT_INTENT_TITLE}」")
        if auction_intent_id:
            print(f"  竞价演示 {ZH_AUCTION_INTENT_TITLE} → /app/auctions/{auction_intent_id}")
        print(f"  管理员 {ADMIN_EMAIL} / {PASSWORD} — 运营后台 /admin")
        return 0
    except DemoSeedError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        api.close()


if __name__ == "__main__":
    raise SystemExit(main())
