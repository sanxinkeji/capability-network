from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import get_redis


async def probe_database(db: AsyncSession) -> tuple[bool, str]:
    try:
        await db.execute(text("SELECT 1"))
        return True, "连接正常"
    except Exception as exc:
        return False, str(exc)


async def probe_redis() -> tuple[bool, str]:
    try:
        client = await get_redis()
        pong = await client.ping()
        if pong:
            return True, "PONG"
        return False, "PING 无响应"
    except Exception as exc:
        return False, str(exc)


async def run_readiness_checks(db: AsyncSession) -> dict:
    db_ok, db_detail = await probe_database(db)
    redis_ok, redis_detail = await probe_redis()
    all_ok = db_ok and redis_ok
    return {
        "status": "ok" if all_ok else "unavailable",
        "checks": {
            "database": {"ok": db_ok, "detail": db_detail},
            "redis": {"ok": redis_ok, "detail": redis_detail},
        },
    }
