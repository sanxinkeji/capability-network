"""platform invite & recharge codes

Revision ID: 011
Revises: 010
Create Date: 2026-05-23

"""
from typing import Sequence, Union

from alembic import op

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS platform_codes (
            id UUID PRIMARY KEY,
            code VARCHAR(32) NOT NULL UNIQUE,
            code_type VARCHAR(16) NOT NULL,
            value_cents BIGINT,
            expires_at TIMESTAMPTZ,
            used_at TIMESTAMPTZ,
            used_by_id UUID REFERENCES users(id),
            batch_id UUID NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by_id UUID NOT NULL REFERENCES users(id)
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_platform_codes_type ON platform_codes (code_type);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_platform_codes_batch ON platform_codes (batch_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_platform_codes_used ON platform_codes (used_at);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS platform_codes;")
