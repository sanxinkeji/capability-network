"""payment settings extended (Sub2API-style)

Revision ID: 012
Revises: 011
Create Date: 2026-05-23

"""
from typing import Sequence, Union

from alembic import op

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS payment_product_description VARCHAR(256);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS payment_daily_limit_cents BIGINT;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS payment_fee_rate_percent INTEGER NOT NULL DEFAULT 0;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS payment_recharge_rate_percent INTEGER NOT NULL DEFAULT 100;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS max_daily_payment_count INTEGER;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS payment_broadcast_mode BOOLEAN NOT NULL DEFAULT FALSE;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS easypay_enabled BOOLEAN NOT NULL DEFAULT TRUE;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS payment_airwallex_enabled BOOLEAN NOT NULL DEFAULT FALSE;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS payment_help_image_url VARCHAR(512);
    """)


def downgrade() -> None:
    cols = [
        "payment_help_image_url",
        "payment_airwallex_enabled",
        "easypay_enabled",
        "payment_broadcast_mode",
        "max_daily_payment_count",
        "payment_recharge_rate_percent",
        "payment_fee_rate_percent",
        "payment_daily_limit_cents",
        "payment_product_description",
    ]
    for col in cols:
        op.execute(f"ALTER TABLE platform_settings DROP COLUMN IF EXISTS {col};")
