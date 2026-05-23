"""payment UX settings on platform_settings

Revision ID: 009
Revises: 008
Create Date: 2026-05-23

"""
from typing import Sequence, Union

from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS max_deposit_cents BIGINT;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS payment_product_name_prefix VARCHAR(128);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS payment_product_name_suffix VARCHAR(128);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS payment_order_timeout_minutes INTEGER NOT NULL DEFAULT 30;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS max_pending_payment_orders INTEGER NOT NULL DEFAULT 3;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS payment_help_text TEXT;
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS payment_help_text;")
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS max_pending_payment_orders;")
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS payment_order_timeout_minutes;")
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS payment_product_name_suffix;")
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS payment_product_name_prefix;")
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS max_deposit_cents;")
