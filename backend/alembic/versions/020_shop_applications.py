"""shop_applications for seller onboarding

Revision ID: 020_shop_applications
Revises: 019_deal_messages
Create Date: 2026-05-30
"""

from alembic import op

revision = "020_shop_applications"
down_revision = "019_deal_messages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS shop_applications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            shop_name VARCHAR(100) NOT NULL,
            agent_platform VARCHAR(32) NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status VARCHAR(16) NOT NULL DEFAULT 'pending',
            review_note TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            reviewed_at TIMESTAMPTZ
        );
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_shop_applications_status
        ON shop_applications (status);
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_shop_applications_status;")
    op.execute("DROP TABLE IF EXISTS shop_applications CASCADE;")
