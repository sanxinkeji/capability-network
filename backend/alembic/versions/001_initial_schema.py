"""initial schema from docs/database-schema.sql

Revision ID: 001
Revises:
Create Date: 2026-05-23

"""
from typing import Sequence, Union

from alembic import op

from migration_sql import execute_sql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    import os
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[3]
    use_local = os.getenv("LOCAL_SCHEMA", "").lower() in ("1", "true", "yes")
    sql_name = "database-schema-local.sql" if use_local else "database-schema.sql"
    sql_file = root / "docs" / sql_name
    sql = sql_file.read_text(encoding="utf-8")
    execute_sql(sql)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS match_logs CASCADE")
    op.execute("DROP TABLE IF EXISTS wallet_ledger CASCADE")
    op.execute("DROP TABLE IF EXISTS wallets CASCADE")
    op.execute("DROP TABLE IF EXISTS deals CASCADE")
    op.execute("DROP TABLE IF EXISTS intents CASCADE")
    op.execute("DROP TABLE IF EXISTS offers CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute('DROP EXTENSION IF EXISTS "vector"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
