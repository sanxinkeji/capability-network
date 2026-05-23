"""deal_extensions table

Revision ID: 003
Revises: 002
Create Date: 2026-05-23

"""
from typing import Sequence, Union

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS deal_extensions (
            deal_id                  UUID PRIMARY KEY REFERENCES deals (id),
            match_log_id             UUID REFERENCES match_logs (id),
            auto_confirm             BOOLEAN      NOT NULL DEFAULT FALSE,
            auto_confirm_deadline    TIMESTAMPTZ,
            delivery_payload_url     VARCHAR(512),
            delivery_text            TEXT,
            created_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_deal_extensions_match_log_id "
        "ON deal_extensions (match_log_id);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_deal_extensions_match_log_id;")
    op.execute("DROP TABLE IF EXISTS deal_extensions CASCADE;")
