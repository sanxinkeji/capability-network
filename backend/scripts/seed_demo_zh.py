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

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

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
AGENT_OFFER_THESIS_TITLE = "毕业论文写作 Agent · OpenClaw"
AGENT_OFFER_THESIS_DESCRIPTION = (
    "接入 OpenClaw 的智能体专店：付款后主动沟通论文细节，自动撰写、润色并交付。"
)
ZH_AGENT_INTENT_TITLE = "需要 AI 文档摘要"
ZH_AGENT_INTENT_DESCRIPTION = (
    "对 20 页产品白皮书生成中文摘要，重点提取功能亮点，预算 1 元按次调用。"
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

        from app.shop.models import ShopApplication

        for user, shop_name, platform in (
            (seller, "龙虾设计工作室", "openclaw"),
            (
                (await db.execute(select(User).where(User.email == SELLER2_EMAIL))).scalar_one_or_none(),
                "Hermes 写作助手",
                "hermes",
            ),
        ):
            if user is None:
                continue
            if user.role not in ("seller", "admin"):
                user.role = "seller"
                print(f"  [seller] {user.email} role -> seller")
            existing_app = (
                await db.execute(select(ShopApplication).where(ShopApplication.user_id == user.id))
            ).scalar_one_or_none()
            if existing_app is None:
                db.add(
                    ShopApplication(
                        user_id=user.id,
                        shop_name=shop_name,
                        agent_platform=platform,
                        description="演示已通过审核的 AI 店家",
                        status="approved",
                    )
                )
                print(f"  [shop] approved application for {user.email}")
            elif existing_app.status != "approved":
                existing_app.status = "approved"
                existing_app.shop_name = shop_name
                print(f"  [shop] updated application for {user.email}")

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
        {
            "title": AGENT_OFFER_THESIS_TITLE,
            "description": AGENT_OFFER_THESIS_DESCRIPTION,
            "category": "writing",
            "channel": "agent",
            "billing_model": "per_use",
            "price_cents": 9900,
            "delivery_description": "论文初稿 + 查重说明 + 修改建议",
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


DEMO_BUYER_NOTE = "计算机科学专业，8000 字，下周五截止，学校模板已上传邮箱。"


def list_buyer_deals(api: ApiClient, buyer_token: str) -> list[dict]:
    items: list[dict] = []
    page = 1
    while True:
        body = api.request("GET", f"/deals?page={page}&page_size=100", token=buyer_token)
        data = body["data"]
        items.extend(data["items"])
        if len(items) >= data["total"] or not data["items"]:
            break
        page += 1
    return items


def run_buyer_purchase_demo(api: ApiClient, buyer_token: str, offer_id: str) -> None:
    """演示「逛淘宝式」买 AI 服务全链路：充值 → 一键购买 → 付款 → 进聊天 → 触发自动交付。"""
    for deal in list_buyer_deals(api, buyer_token):
        if deal["offer_id"] == offer_id and deal["status"] in (
            "in_progress",
            "delivered",
            "completed",
        ):
            print(f"  [skip] buyer already has active deal for offer: {deal['id']} ({deal['status']})")
            return

    try:
        api.request(
            "POST",
            "/wallets/deposit-orders",
            token=buyer_token,
            json={"amount_cents": 20000, "channel": "wechat"},
        )
        print("  [recharge] buyer wallet +¥200")
    except DemoSeedError as exc:
        print(f"  [recharge] skipped ({exc})")

    bought = api.request(
        "POST",
        "/deals/buy-from-offer",
        token=buyer_token,
        json={"offer_id": offer_id, "buyer_note": DEMO_BUYER_NOTE},
    )
    deal_id = bought["data"]["deal"]["id"]
    print(f"  [buy] deal created: {deal_id}")

    paid = api.request("POST", f"/deals/{deal_id}/pay", token=buyer_token)
    print(f"  [pay] deal status={paid['data']['status']}")

    api.request(
        "POST",
        f"/deals/{deal_id}/messages",
        token=buyer_token,
        json={"body": DEMO_BUYER_NOTE},
    )
    print(f"  [chat] buyer message sent → 触发智能体自动交付演示")
    print(f"  [demo] 订单聊天页：http://127.0.0.1:5173/app/deals/{deal_id}/chat")


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
        "--run-purchase",
        action="store_true",
        help="演示买家全链路：充值 → 一键购买智能体服务 → 付款 → 进订单聊天 → 触发自动交付",
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

        print("\n5. 卖方二：发布另一家 AI 店铺供给")
        ensure_seller2_agent_offer(api, seller2_token)

        print("\n6. 买方：创建中文需求")
        intent_id = ensure_zh_intent(api, buyer_token)

        print("\n7. 买方：创建智能体需求")
        agent_intent_id = ensure_zh_agent_intent(api, buyer_token)

        thesis_offer_id = agent_offer_ids[2] if len(agent_offer_ids) > 2 else logo_offer_a
        if args.run_purchase:
            print("\n8. 买方：一键购买 AI 服务 → 付款 → 进订单聊天")
            run_buyer_purchase_demo(api, buyer_token, thesis_offer_id)

        if args.run_match:
            step = 9 if args.run_purchase else 8
            print(f"\n{step}. 匹配验证（不创建订单）")
            run_match_check(api, buyer_token, intent_id)
            run_match_check(api, buyer_token, agent_intent_id)

        print("\n==> 中文演示数据 seed 完成")
        print(f"  卖方 {SELLER_EMAIL} / {PASSWORD} — 人工「{ZH_OFFER_TITLE}」+ 智能体供给（含 OpenClaw 论文店）")
        print(f"  卖方二 {SELLER2_EMAIL} / {PASSWORD} — 「{AGENT_OFFER_LOGO_B_TITLE}」")
        print(f"  买方 {BUYER_EMAIL} / {PASSWORD} — 逛集市买 AI 服务、查看订单聊天")
        if args.run_purchase:
            print("  已生成一笔完整订单（付款 → 聊天 → 自动交付），登录买家在「我的订单」查看")
        print(f"  管理员 {ADMIN_EMAIL} / {PASSWORD} — 运营后台 /admin（含入驻审核）")
        return 0
    except DemoSeedError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        api.close()


if __name__ == "__main__":
    raise SystemExit(main())
