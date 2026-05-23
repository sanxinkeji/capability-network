import re
from datetime import datetime, timezone

from app.intents.models import Intent
from app.matching.constants import (
    RECOMMEND_AUTO_THRESHOLD,
    TRUST_DEFAULT,
    WEIGHT_ALIGNMENT,
    WEIGHT_FRESHNESS,
    WEIGHT_PRICE,
    WEIGHT_QUALITY,
    WEIGHT_SEMANTIC,
    WEIGHT_TRUST,
)
from app.offers.models import Offer
from app.offers.schemas import parse_tags_payload

# ---------------------------------------------------------------------------
# 综合匹配分公式（match_score ∈ [0, 1]）：
#
#   match_score = semantic   × 0.25
#               + alignment  × 0.25
#               + quality    × 0.20
#               + price      × 0.15
#               + trust      × 0.10
#               + freshness  × 0.05
#
# 各维度说明：
#   semantic  — 语义相似度（pgvector 余弦），第一阶段权重生效但分值固定 0
#   alignment — 关键词/标签重叠（Jaccard）
#   quality   — offer 信息完整度
#   price     — 价格相对预算的友好度（price <= budget 已在过滤层保证）
#   trust     — 供给方信誉，无数据时默认 0.5
#   freshness — 发布时间新鲜度（90 天线性衰减）
#
# recommend_auto = (match_score >= 0.7)，仅标记，不自动创建 deal
# ---------------------------------------------------------------------------

_STOPWORDS = frozenset(
    {
        "的",
        "了",
        "和",
        "与",
        "或",
        "及",
        "等",
        "一个",
        "需要",
        "提供",
        "服务",
        "能力",
        "the",
        "and",
        "for",
        "with",
        "from",
        "this",
        "that",
        "are",
        "was",
        "have",
        "has",
    }
)

_TOKEN_PATTERN = re.compile(r"[\w\u4e00-\u9fff]+")

# 预过滤同义词/类目组：组内任意词命中即视为同一语义簇，用于提升跨语言与近域召回。
# 例：intent 含「设计」、offer 含「logo」可通过扩展后交集通过，无需 pgvector。
_SYNONYM_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"design", "logo", "设计", "品牌", "branding", "vi", "视觉", "graphic"}),
    frozenset({"develop", "development", "开发", "编程", "code", "software", "程序", "web"}),
    frozenset({"write", "writing", "文案", "content", "copywriting", "撰写", "article"}),
    frozenset({"翻译", "translate", "translation", "localization", "本地化", "interpret"}),
    frozenset({"数据", "data", "analysis", "analytics", "分析", "报表", "report"}),
)

# 同义词扩展仍无交集时，用原始 token 的 Jaccard 作软通过阈值（低于 alignment 打分用的完整 Jaccard）
KEYWORD_FILTER_JACCARD_MIN = 0.08


def _expand_with_synonyms(keywords: set[str]) -> set[str]:
    expanded = set(keywords)
    for group in _SYNONYM_GROUPS:
        if keywords & group:
            expanded |= group
    return expanded


def extract_keywords(*texts: str) -> set[str]:
    tokens: set[str] = set()
    for text in texts:
        if not text:
            continue
        for token in _TOKEN_PATTERN.findall(text.lower()):
            if len(token) >= 2 and token not in _STOPWORDS:
                tokens.add(token)
    return tokens


def passes_keyword_filter(intent: Intent, offer: Offer) -> bool:
    """关键词预过滤：同义词扩展优先，Jaccard 软阈值兜底。

    策略（keyword_v1，无 pgvector）：
    1. intent 无有效关键词 → 放行（由 category/channel/价格等硬条件约束）
    2. offer 无关键词 → 拒绝
    3. 双方 token 经 _SYNONYM_GROUPS 扩展后若有交集 → 通过
    4. 否则计算原始 token Jaccard，>= KEYWORD_FILTER_JACCARD_MIN 则通过
    """
    intent_keywords = extract_keywords(intent.title, intent.description, intent.category)
    if not intent_keywords:
        return True

    offer_keywords = extract_keywords(offer.title, offer.description, offer.category)
    if not offer_keywords:
        return False

    if _expand_with_synonyms(intent_keywords) & _expand_with_synonyms(offer_keywords):
        return True

    union = intent_keywords | offer_keywords
    jaccard = len(intent_keywords & offer_keywords) / len(union)
    return jaccard >= KEYWORD_FILTER_JACCARD_MIN


def compute_semantic_score(_intent: Intent, _offer: Offer) -> float:
    # TODO(phase-2): 使用 pgvector 余弦相似度计算 semantic 分值
    #   示例 SQL:
    #     SELECT 1 - (i.embedding <=> o.embedding) AS cosine_sim
    #     FROM intents i, offers o
    #     WHERE i.id = :intent_id AND o.id = :offer_id
    #         AND i.embedding IS NOT NULL AND o.embedding IS NOT NULL
    #   将 cosine_sim 映射到 [0, 1] 后直接作为 semantic 维度分值。
    return 0.0


def compute_alignment_score(intent: Intent, offer: Offer) -> float:
    intent_keywords = extract_keywords(intent.title, intent.description, intent.category)
    offer_keywords = extract_keywords(offer.title, offer.description, offer.category)
    if not intent_keywords or not offer_keywords:
        return 0.5

    intersection = intent_keywords & offer_keywords
    union = intent_keywords | offer_keywords
    return len(intersection) / len(union)


def compute_quality_score(offer: Offer) -> float:
    meta = parse_tags_payload(offer.tags)
    score = 0.0
    if meta.get("delivery_description"):
        score += 0.35
    if meta.get("acceptance_sample_url"):
        score += 0.35
    if len(offer.description) >= 100:
        score += 0.30
    return min(score, 1.0)


def compute_price_score(price_cents: int, budget_cents: int) -> float:
    if budget_cents <= 0:
        return 1.0 if price_cents == 0 else 0.5
    ratio = price_cents / budget_cents
    return max(0.0, 1.0 - ratio)


def compute_trust_score(_offer: Offer) -> float:
    # 暂无用户信誉数据，使用默认值
    return TRUST_DEFAULT


def compute_freshness_score(created_at: datetime) -> float:
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_days = max(0, (now - created_at).days)
    return max(0.0, 1.0 - age_days / 90.0)


def compute_match_score(intent: Intent, offer: Offer) -> tuple[float, dict[str, float | bool]]:
    semantic = compute_semantic_score(intent, offer)
    alignment = compute_alignment_score(intent, offer)
    quality = compute_quality_score(offer)
    price = compute_price_score(offer.price_cents, intent.budget_cents)
    trust = compute_trust_score(offer)
    freshness = compute_freshness_score(offer.created_at)

    match_score = (
        semantic * WEIGHT_SEMANTIC
        + alignment * WEIGHT_ALIGNMENT
        + quality * WEIGHT_QUALITY
        + price * WEIGHT_PRICE
        + trust * WEIGHT_TRUST
        + freshness * WEIGHT_FRESHNESS
    )
    match_score = round(min(max(match_score, 0.0), 1.0), 4)

    breakdown: dict[str, float | bool] = {
        "semantic": round(semantic, 4),
        "alignment": round(alignment, 4),
        "quality": round(quality, 4),
        "price": round(price, 4),
        "trust": round(trust, 4),
        "freshness": round(freshness, 4),
        "recommend_auto": match_score >= RECOMMEND_AUTO_THRESHOLD,
    }
    return match_score, breakdown
