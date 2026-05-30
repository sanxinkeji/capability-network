import os
import sys
from pathlib import Path

os.environ.setdefault("PAYMENT_PROVIDER", "test")
os.environ.setdefault("JWT_SECRET_KEY", "pytest-secret-key-not-for-production")
os.environ.setdefault("DEBUG", "true")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.platform.models  # noqa: F401
# SQLite 测试库不支持 JSONB，编译为 JSON
import pytest
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

import app.core.redis_client as _redis_client

from tests.fake_redis import FakeRedis


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):
    return compiler.visit_JSON(JSON(), **kw)


@pytest.fixture(autouse=True)
async def _isolate_global_async_resources(monkeypatch):
    """pytest-asyncio 每个用例独立事件循环，但维护中间件/平台设置缓存默认走全局
    Postgres engine、限流走全局 redis 单例；跨用例复用会触发 'Event loop is closed'。

    这里给每个用例提供一份当前事件循环内的内存库与 FakeRedis，作为这些只读探测的默认
    后端。需要真正读写平台设置的用例（如 test_maintenance_mode）会在自己的 fixture 中
    再次 monkeypatch 覆盖，互不影响。"""
    from app.core.database import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    monkeypatch.setattr("app.core.maintenance.async_session", session_factory, raising=False)
    monkeypatch.setattr("app.platform.settings_cache.async_session", session_factory, raising=False)

    fake_redis = FakeRedis()

    async def _get_redis():
        return fake_redis

    for target in (
        "app.core.redis_client.get_redis",
        "app.core.rate_limit.get_redis",
        "app.core.health.get_redis",
    ):
        monkeypatch.setattr(target, _get_redis, raising=False)

    _redis_client._redis = None
    _redis_client._redis_disabled = False

    yield

    _redis_client._redis = None
    _redis_client._redis_disabled = False
    await engine.dispose()
