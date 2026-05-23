"""payment_orders and withdraw_requests tables

Revision ID: 005
Revises: 004
Create Date: 2026-05-23

"""
from typing import Sequence, Union

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS payment_orders (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id         UUID NOT NULL REFERENCES users (id),
            amount_cents    BIGINT NOT NULL,
            currency        VARCHAR(3) NOT NULL DEFAULT 'CNY',
            channel         VARCHAR(16) NOT NULL,
            status          VARCHAR(16) NOT NULL DEFAULT 'pending',
            provider_ref    VARCHAR(128) NOT NULL UNIQUE,
            pay_url         VARCHAR(1024),
            expires_at      TIMESTAMPTZ,
            paid_at         TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_payment_orders_user_id ON payment_orders (user_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_payment_orders_status ON payment_orders (status);"
    )
    op.execute("""
        CREATE TABLE IF NOT EXISTS withdraw_requests (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id         UUID NOT NULL REFERENCES users (id),
            amount_cents    BIGINT NOT NULL,
            status          VARCHAR(16) NOT NULL DEFAULT 'pending',
            payout_method   VARCHAR(16) NOT NULL,
            payout_account  VARCHAR(512) NOT NULL,
            payout_name     VARCHAR(128) NOT NULL,
            admin_note      VARCHAR(512),
            provider_ref    VARCHAR(128),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            processed_at    TIMESTAMPTZ
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_withdraw_requests_user_id ON withdraw_requests (user_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_withdraw_requests_status ON withdraw_requests (status);"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS withdraw_requests;")
    op.execute("DROP TABLE IF EXISTS payment_orders;")
