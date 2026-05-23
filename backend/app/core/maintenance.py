import logging
import time

import jwt
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.auth.constants import UserRole
from app.auth.security import decode_access_token, is_api_key_format
from app.core.database import async_session
from app.platform.models import PlatformSettings

logger = logging.getLogger(__name__)

MAINTENANCE_CODE = 50301
MAINTENANCE_MESSAGE = "系统维护中，请稍后再试"

_EXEMPT_EXACT_PATHS = frozenset(
    {
        "/health",
        "/health/ready",
        "/api/v1/platform/settings",
    }
)
_EXEMPT_AUTH_PATHS = frozenset(
    {
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/register",
        "/api/v1/auth/verify-email",
        "/api/v1/auth/resend-verification",
    }
)
_MAINTENANCE_CACHE_TTL_SECONDS = 5.0
_maintenance_cache: tuple[float, bool] | None = None


def _is_exempt_path(path: str) -> bool:
    if path in _EXEMPT_EXACT_PATHS or path in _EXEMPT_AUTH_PATHS:
        return True
    if "/payment-notify/" in path:
        return True
    return False


def _is_admin_request(request: Request) -> bool:
    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        return False

    token = auth_header[7:].strip()
    if not token or is_api_key_format(token):
        return False

    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        return False

    return payload.get("role") == UserRole.ADMIN


async def _maintenance_mode_enabled() -> bool:
    global _maintenance_cache
    now = time.monotonic()
    if _maintenance_cache is not None:
        cached_at, cached_value = _maintenance_cache
        if now - cached_at < _MAINTENANCE_CACHE_TTL_SECONDS:
            return cached_value

    enabled = False
    try:
        async with async_session() as db:
            result = await db.execute(select(PlatformSettings.maintenance_mode).where(PlatformSettings.id == 1))
            value = result.scalar_one_or_none()
            enabled = bool(value)
    except Exception:
        logger.warning("failed to read maintenance_mode", exc_info=True)

    _maintenance_cache = (now, enabled)
    return enabled


def invalidate_maintenance_cache() -> None:
    global _maintenance_cache
    _maintenance_cache = None


class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if not path.startswith("/api/v1") or _is_exempt_path(path):
            return await call_next(request)

        if not await _maintenance_mode_enabled():
            return await call_next(request)

        if _is_admin_request(request):
            return await call_next(request)

        return JSONResponse(
            status_code=503,
            content={
                "code": MAINTENANCE_CODE,
                "message": MAINTENANCE_MESSAGE,
                "data": None,
            },
        )
