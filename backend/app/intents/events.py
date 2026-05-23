import json
import logging
from uuid import UUID

import redis.asyncio as redis

from app.core.config import settings
from app.intents.constants import INTENT_CREATED_QUEUE

logger = logging.getLogger(__name__)


async def publish_intent_created(*, intent_id: UUID, user_id: UUID, status: str) -> None:
    payload = {
        "event": "intent.created",
        "intent_id": str(intent_id),
        "user_id": str(user_id),
        "status": status,
    }
    message = json.dumps(payload, ensure_ascii=False)

    logger.info(
        "intent.created event queued: queue=%s payload=%s",
        INTENT_CREATED_QUEUE,
        message,
    )

    try:
        client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        try:
            await client.lpush(INTENT_CREATED_QUEUE, message)
        finally:
            await client.aclose()
    except Exception:
        logger.warning(
            "failed to push intent.created to redis queue=%s; logged only",
            INTENT_CREATED_QUEUE,
            exc_info=True,
        )
