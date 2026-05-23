"""platform_settings and admin_audit_logs

Revision ID: 006
Revises: 005
Create Date: 2026-05-23

"""
from typing import Sequence, Union

from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS platform_settings (
            id                      INTEGER PRIMARY KEY DEFAULT 1,
            site_name               VARCHAR(128) NOT NULL DEFAULT 'Capability',
            site_tagline            VARCHAR(256),
            site_announcement       TEXT,
            support_email           VARCHAR(255),
            support_url             VARCHAR(512),
            commission_rate_percent INTEGER NOT NULL DEFAULT 10,
            min_deposit_cents       BIGINT NOT NULL DEFAULT 100,
            min_withdraw_cents      BIGINT NOT NULL DEFAULT 10000,
            max_withdraw_cents      BIGINT NOT NULL DEFAULT 50000000,
            payment_wechat_enabled  BOOLEAN NOT NULL DEFAULT TRUE,
            payment_alipay_enabled  BOOLEAN NOT NULL DEFAULT TRUE,
            maintenance_mode        BOOLEAN NOT NULL DEFAULT FALSE,
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_by_id           UUID REFERENCES users (id)
        );
    """)
    op.execute("""
        INSERT INTO platform_settings (id)
        VALUES (1)
        ON CONFLICT (id) DO NOTHING;
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS admin_audit_logs (
            id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            admin_id     UUID NOT NULL REFERENCES users (id),
            action       VARCHAR(64) NOT NULL,
            target_type  VARCHAR(32),
            target_id    VARCHAR(64),
            detail       TEXT,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_created_at ON admin_audit_logs (created_at DESC);"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS admin_audit_logs;")
    op.execute("DROP TABLE IF EXISTS platform_settings;")
