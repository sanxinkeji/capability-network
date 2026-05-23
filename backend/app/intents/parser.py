import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.intents.constants import IntentChannel, IntentSettlement
from app.intents.schemas import IntentParseResponse, default_settlement_for_channel

LLM_API_KEY_ENV = "INTENT_PARSE_API_KEY"
LLM_API_BASE_ENV = "INTENT_PARSE_API_BASE"
LLM_MODEL_ENV = "INTENT_PARSE_MODEL"

DEFAULT_LLM_BASE = "https://api.openai.com/v1"
DEFAULT_LLM_MODEL = "gpt-4o-mini"

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "development": ("开发", "编程", "代码", "api", "后端", "前端", "网站", "app"),
    "design": ("设计", "ui", "ux", "界面", "视觉", "logo"),
    "data": ("数据", "分析", "报表", "清洗", "爬虫"),
    "content": ("文案", "写作", "翻译", "内容", "文章"),
    "consulting": ("咨询", "顾问", "方案", "策略"),
}


def _detect_channel(text: str) -> IntentChannel:
    lowered = text.lower()
    if any(token in lowered for token in ("agent", "智能体", "自动", "机器人", "ai代理")):
        return IntentChannel.AGENT
    return IntentChannel.HUMAN


def _detect_category(text: str) -> str:
    lowered = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return "design"


def _extract_budget_cents(text: str) -> int:
    patterns = [
        r"(\d+(?:\.\d+)?)\s*万",
        r"预算\s*[：:]?\s*(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*元",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        amount = float(match.group(1))
        if "万" in pattern:
            amount *= 10000
        return int(amount * 100)
    return 0


def _extract_deadline(text: str) -> datetime | None:
    match = re.search(r"(\d+)\s*天", text)
    if match:
        days = int(match.group(1))
        return datetime.now(timezone.utc) + timedelta(days=days)
    date_match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", text)
    if date_match:
        year, month, day = map(int, date_match.groups())
        return datetime(year, month, day, tzinfo=timezone.utc)
    return None


def _build_title(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text.strip())
    return cleaned[:50] + ("..." if len(cleaned) > 50 else "")


def _build_acceptance_criteria(text: str, category: str) -> dict[str, Any]:
    criteria: dict[str, Any] = {
        "summary": text.strip(),
        "category": category,
        "deliverables": [],
        "quality_bar": "符合需求描述并完成约定交付物",
    }
    if "验收" in text:
        criteria["notes"] = "包含用户描述的验收要求"
    return criteria


def parse_intent_by_rules(text: str) -> IntentParseResponse:
    channel = _detect_channel(text)
    settlement = default_settlement_for_channel(channel)
    category = _detect_category(text)
    return IntentParseResponse(
        title=_build_title(text),
        description=text.strip(),
        category=category,
        channel=channel,
        settlement=settlement,
        budget_max=_extract_budget_cents(text),
        currency="CNY",
        deadline=_extract_deadline(text),
        acceptance_criteria=_build_acceptance_criteria(text, category),
        parsed_by="rules",
    )


async def _parse_intent_by_llm(text: str, *, api_key: str) -> IntentParseResponse:
    api_base = os.getenv(LLM_API_BASE_ENV, DEFAULT_LLM_BASE).rstrip("/")
    model = os.getenv(LLM_MODEL_ENV, DEFAULT_LLM_MODEL)
    prompt = (
        "将以下能力需求自然语言解析为 JSON，字段："
        "title, description, category, channel(human|agent), "
        "settlement(human 用 fiat，agent 用 points), budget_max(分), "
        "currency, deadline(ISO8601 或 null), acceptance_criteria(对象)。"
        "只返回 JSON。"
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{api_base}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

    data = json.loads(content)
    channel = IntentChannel(data.get("channel", IntentChannel.HUMAN))
    settlement_raw = data.get("settlement")
    settlement = (
        IntentSettlement(settlement_raw)
        if settlement_raw
        else default_settlement_for_channel(channel)
    )
    deadline_raw = data.get("deadline")
    deadline = datetime.fromisoformat(deadline_raw.replace("Z", "+00:00")) if deadline_raw else None

    return IntentParseResponse(
        title=str(data.get("title") or _build_title(text)),
        description=str(data.get("description") or text.strip()),
        category=str(data.get("category") or _detect_category(text)),
        channel=channel,
        settlement=settlement,
        budget_max=int(data.get("budget_max") or 0),
        currency=str(data.get("currency") or "CNY"),
        deadline=deadline,
        acceptance_criteria=dict(data.get("acceptance_criteria") or {}),
        parsed_by="llm",
    )


async def parse_intent_text(text: str) -> IntentParseResponse:
    api_key = os.getenv(LLM_API_KEY_ENV) or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return parse_intent_by_rules(text)

    try:
        return await _parse_intent_by_llm(text, api_key=api_key)
    except Exception:
        return parse_intent_by_rules(text)
