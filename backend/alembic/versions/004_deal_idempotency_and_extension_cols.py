"""deal_idempotency table and deal_extensions columns

Revision ID: 004
Revises: 003
Create Date: 2026-05-23

"""
from typing import Sequence, Union

from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS deal_idempotency (
            id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            idempotency_key VARCHAR(128) NOT NULL,
            operation       VARCHAR(32)  NOT NULL,
            deal_id         UUID REFERENCES deals (id),
            actor_id        UUID         NOT NULL REFERENCES users (id),
            response_json   TEXT         NOT NULL,
            expires_at      TIMESTAMPTZ  NOT NULL,
            created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_deal_idempotency UNIQUE (idempotency_key, operation, deal_id)
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_deal_idempotency_expires_at "
        "ON deal_idempotency (expires_at);"
    )
    op.execute(
        "ALTER TABLE deal_extensions "
        "ADD COLUMN IF NOT EXISTS disputed_by_id UUID REFERENCES users (id);"
    )
    op.execute(
        "ALTER TABLE deal_extensions "
        "ADD COLUMN IF NOT EXISTS negotiated_refund BOOLEAN NOT NULL DEFAULT FALSE;"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE deal_extensions DROP COLUMN IF EXISTS negotiated_refund;"
    )
    op.execute(
        "ALTER TABLE deal_extensions DROP COLUMN IF EXISTS disputed_by_id;"
    )
    op.execute("DROP INDEX IF EXISTS idx_deal_idempotency_expires_at;")
    op.execute("DROP TABLE IF EXISTS deal_idempotency CASCADE;")
