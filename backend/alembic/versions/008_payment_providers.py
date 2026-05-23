"""payment provider settings on platform_settings

Revision ID: 008
Revises: 007
Create Date: 2026-05-23

"""
from typing import Sequence, Union

from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS payment_enabled BOOLEAN NOT NULL DEFAULT TRUE;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS payment_alipay_source VARCHAR(32) NOT NULL DEFAULT 'direct';
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS payment_wechat_source VARCHAR(32) NOT NULL DEFAULT 'direct';
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS easypay_pid VARCHAR(64);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS easypay_key VARCHAR(256);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS easypay_api_base VARCHAR(512);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS easypay_alipay_type VARCHAR(32);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS easypay_wechat_type VARCHAR(32);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS stripe_enabled BOOLEAN NOT NULL DEFAULT FALSE;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS stripe_public_key VARCHAR(256);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS stripe_secret_key VARCHAR(256);
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS stripe_secret_key;")
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS stripe_public_key;")
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS stripe_enabled;")
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS easypay_wechat_type;")
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS easypay_alipay_type;")
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS easypay_api_base;")
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS easypay_key;")
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS easypay_pid;")
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS payment_wechat_source;")
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS payment_alipay_source;")
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS payment_enabled;")
