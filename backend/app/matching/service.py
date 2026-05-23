from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import CurrentUser, raise_auth_error
from app.intents.constants import IntentStatus
from app.intents.models import Intent
from app.intents.schemas import parse_tags_payload
from app.matching.constants import (
    DEFAULT_TOP_N,
    ERR_MATCH_FORBIDDEN,
    ERR_MATCH_INTENT_NOT_FOUND,
    ERR_MATCH_INTENT_NOT_OPEN,
    MatchAlgorithm,
)
from app.matching.models import MatchLog
from app.matching.scorer import compute_match_score, passes_keyword_filter
from app.matching.schemas import MatchCandidateResponse, MatchRunResponse
from app.offers.constants import OfferStatus
from app.offers.models import Offer
from app.offers.schemas import parse_tags_payload as parse_offer_tags


def _ensure_intent_owner(intent: Intent, current: CurrentUser) -> None:
    if intent.user_id != current.id:
        raise_auth_error(code=ERR_MATCH_FORBIDDEN, message="matching access denied", http_status=403)


async def run_matching(
    db: AsyncSession,
    *,
    intent_id: UUID,
    current: CurrentUser,
    top_n: int = DEFAULT_TOP_N,
) -> MatchRunResponse:
    intent = await _get_intent_or_404(db, intent_id)
    _ensure_intent_owner(intent, current)

    if intent.status != IntentStatus.OPEN:
        raise_auth_error(
            code=ERR_MATCH_INTENT_NOT_OPEN,
            message=f"intent status must be '{IntentStatus.OPEN}' to run matching",
            http_status=409,
        )

    intent_meta = parse_tags_payload(intent.tags)
    intent_channel = str(intent_meta.get("channel", "human"))

    query = (
        select(Offer)
        .where(Offer.status == OfferStatus.PUBLISHED)
        .where(Offer.user_id != intent.user_id)
        .where(Offer.category == intent.category)
        .where(Offer.price_cents <= intent.budget_cents)
        .where(Offer.currency == intent.currency)
        .where(Offer.tags["channel"].as_string() == intent_channel)
    )
    result = await db.execute(query)
    offers = result.scalars().all()

    scored: list[tuple[Offer, float, dict[str, float | bool]]] = []
    for offer in offers:
        if not passes_keyword_filter(intent, offer):
            continue
        match_score, breakdown = compute_match_score(intent, offer)
        scored.append((offer, match_score, breakdown))

    scored.sort(key=lambda item: item[1], reverse=True)
    top_candidates = scored[:top_n]

    candidates: list[MatchCandidateResponse] = []
    for rank, (offer, match_score, breakdown) in enumerate(top_candidates, start=1):
        offer_meta = parse_offer_tags(offer.tags)
        log = MatchLog(
            intent_id=intent.id,
            offer_id=offer.id,
            score=Decimal(str(match_score)),
            rank=rank,
            algorithm=MatchAlgorithm.KEYWORD_V1,
            metadata_={
                "score_breakdown": breakdown,
                "recommend_auto": breakdown["recommend_auto"],
                "intent_channel": intent_channel,
            },
        )
        db.add(log)
        await db.flush()

        candidates.append(
            MatchCandidateResponse(
                match_log_id=log.id,
                offer_id=offer.id,
                title=offer.title,
                description=offer.description,
                category=offer.category,
                channel=str(offer_meta.get("channel", intent_channel)),
                price_cents=offer.price_cents,
                currency=offer.currency,
                match_score=match_score,
                rank=rank,
                recommend_auto=bool(breakdown["recommend_auto"]),
                score_breakdown=breakdown,
            )
        )

    await db.commit()

    return MatchRunResponse(
        intent_id=intent.id,
        algorithm=MatchAlgorithm.KEYWORD_V1,
        total_candidates=len(candidates),
        candidates=candidates,
    )


async def _get_intent_or_404(db: AsyncSession, intent_id: UUID) -> Intent:
    result = await db.execute(select(Intent).where(Intent.id == intent_id))
    intent = result.scalar_one_or_none()
    if intent is None:
        raise_auth_error(code=ERR_MATCH_INTENT_NOT_FOUND, message="intent not found", http_status=404)
    return intent
