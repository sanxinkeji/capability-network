import asyncio
import logging

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis: redis.Redis | None = None
_redis_disabled = False

_REDIS_OPTS = {
    "decode_responses": True,
    "socket_connect_timeout": 1,
    "socket_timeout": 1,
}


async def get_redis() -> redis.Redis:
    global _redis, _redis_disabled
    if _redis_disabled:
        raise ConnectionError("redis unavailable")
    if _redis is None:
        client = redis.from_url(settings.REDIS_URL, **_REDIS_OPTS)
        try:
            await asyncio.wait_for(client.ping(), timeout=1.5)
            _redis = client
        except Exception as exc:
            _redis_disabled = True
            try:
                await client.aclose()
            except Exception:
                pass
            logger.warning("redis unavailable, rate limit and locks will be skipped: %s", exc)
            raise ConnectionError("redis unavailable") from exc
    return _redis


async def close_redis() -> None:
    global _redis, _redis_disabled
    if _redis is not None:
        try:
            await _redis.aclose()
        except Exception:
            logger.warning("failed to close redis client", exc_info=True)
        _redis = None
    _redis_disabled = False
