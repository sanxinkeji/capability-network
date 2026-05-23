import logging
import time

from sqlalchemy import select

from app.core.database import async_session
from app.platform.models import PlatformSettings

logger = logging.getLogger(__name__)

_CACHE_TTL_SECONDS = 5.0
_trust_proxy_cache: tuple[float, bool] | None = None


async def trust_proxy_ip_enabled() -> bool:
    global _trust_proxy_cache
    now = time.monotonic()
    if _trust_proxy_cache is not None:
        cached_at, cached_value = _trust_proxy_cache
        if now - cached_at < _CACHE_TTL_SECONDS:
            return cached_value

    enabled = False
    try:
        async with async_session() as db:
            result = await db.execute(
                select(PlatformSettings.trust_proxy_ip).where(PlatformSettings.id == 1)
            )
            value = result.scalar_one_or_none()
            enabled = bool(value)
    except Exception:
        logger.warning("failed to read trust_proxy_ip", exc_info=True)

    _trust_proxy_cache = (now, enabled)
    return enabled


def invalidate_platform_settings_cache() -> None:
    global _trust_proxy_cache
    _trust_proxy_cache = None
