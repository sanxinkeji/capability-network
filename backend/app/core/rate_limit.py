import hashlib
import logging

from fastapi import Request

from app.auth.constants import ERR_LOGIN_LOCKED, ERR_RATE_LIMIT
from app.auth.schemas import AuthError, raise_auth_error
from app.core.config import settings
from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)


async def resolve_client_ip(request: Request) -> str:
    from app.platform.settings_cache import trust_proxy_ip_enabled

    if await trust_proxy_ip_enabled():
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _account_key(account: str) -> str:
    normalized = account.strip().lower()
    digest = hashlib.sha256(normalized.encode()).hexdigest()
    return digest


async def _incr_window(key: str, window_seconds: int) -> int:
    client = await get_redis()
    count = await client.incr(key)
    if count == 1:
        await client.expire(key, window_seconds)
    return count


async def check_rate_limit(*, key: str, max_requests: int, window_seconds: int) -> None:
    if not settings.RATE_LIMIT_ENABLED:
        return
    try:
        client = await get_redis()
        count = await _incr_window(key, window_seconds)
        if count > max_requests:
            ttl = await client.ttl(key)
            retry_after = max(ttl, 1)
            raise_auth_error(
                code=ERR_RATE_LIMIT,
                message=f"rate limit exceeded, retry after {retry_after}s",
                http_status=429,
            )
    except AuthError:
        raise
    except Exception:
        logger.warning("rate limit check skipped: key=%s", key, exc_info=True)


async def enforce_login_rate_limit(request: Request) -> None:
    ip = await resolve_client_ip(request)
    await check_rate_limit(
        key=f"rl:login:ip:{ip}",
        max_requests=settings.RATE_LIMIT_LOGIN_MAX,
        window_seconds=settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS,
    )


async def enforce_register_rate_limit(request: Request) -> None:
    ip = await resolve_client_ip(request)
    await check_rate_limit(
        key=f"rl:register:ip:{ip}",
        max_requests=settings.RATE_LIMIT_REGISTER_MAX,
        window_seconds=settings.RATE_LIMIT_REGISTER_WINDOW_SECONDS,
    )


async def enforce_payment_notify_rate_limit(request: Request) -> None:
    ip = await resolve_client_ip(request)
    await check_rate_limit(
        key=f"rl:paynotify:ip:{ip}",
        max_requests=settings.RATE_LIMIT_PAYMENT_NOTIFY_MAX,
        window_seconds=settings.RATE_LIMIT_PAYMENT_NOTIFY_WINDOW_SECONDS,
    )


def _lock_keys(account: str, client_ip: str | None) -> list[str]:
    scope = settings.LOGIN_LOCKOUT_SCOPE.lower()
    keys: list[str] = []
    if scope in {"account", "both"}:
        keys.append(f"auth:lock:acct:{_account_key(account)}")
    if scope in {"ip", "both"} and client_ip:
        keys.append(f"auth:lock:ip:{client_ip}")
    return keys


def _fail_keys(account: str, client_ip: str | None) -> list[str]:
    scope = settings.LOGIN_LOCKOUT_SCOPE.lower()
    keys: list[str] = []
    if scope in {"account", "both"}:
        keys.append(f"auth:fail:acct:{_account_key(account)}")
    if scope in {"ip", "both"} and client_ip:
        keys.append(f"auth:fail:ip:{client_ip}")
    return keys


async def check_login_not_locked(account: str, client_ip: str | None) -> None:
    if settings.LOGIN_MAX_ATTEMPTS <= 0:
        return
    try:
        client = await get_redis()
        for key in _lock_keys(account, client_ip):
            if await client.get(key):
                ttl = await client.ttl(key)
                retry_after = max(ttl, 1)
                raise_auth_error(
                    code=ERR_LOGIN_LOCKED,
                    message=f"account temporarily locked, retry after {retry_after}s",
                    http_status=429,
                )
    except AuthError:
        raise
    except Exception:
        logger.warning("login lockout check skipped", exc_info=True)


async def record_login_failure(account: str, client_ip: str | None) -> None:
    if settings.LOGIN_MAX_ATTEMPTS <= 0:
        return
    try:
        client = await get_redis()
        for fail_key in _fail_keys(account, client_ip):
            count = await _incr_window(fail_key, settings.LOGIN_LOCKOUT_SECONDS)
            if count >= settings.LOGIN_MAX_ATTEMPTS:
                lock_key = fail_key.replace("auth:fail:", "auth:lock:")
                await client.set(lock_key, "1", ex=settings.LOGIN_LOCKOUT_SECONDS)
    except Exception:
        logger.warning("login failure recording skipped", exc_info=True)


async def clear_login_attempts(account: str, client_ip: str | None) -> None:
    if settings.LOGIN_MAX_ATTEMPTS <= 0:
        return
    try:
        client = await get_redis()
        keys = _fail_keys(account, client_ip) + _lock_keys(account, client_ip)
        if keys:
            await client.delete(*keys)
    except Exception:
        logger.warning("login attempt cleanup skipped", exc_info=True)
