import os
import sys
from pathlib import Path

os.environ.setdefault("PAYMENT_PROVIDER", "test")
os.environ.setdefault("JWT_SECRET_KEY", "pytest-secret-key-not-for-production")
os.environ.setdefault("DEBUG", "true")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.platform.models  # noqa: F401
# SQLite 测试库不支持 JSONB，编译为 JSON
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):
    return compiler.visit_JSON(JSON(), **kw)
