"""deal_messages table for order chat

Revision ID: 019_deal_messages
Revises: 018_auctions
Create Date: 2026-05-30
"""

from alembic import op

revision = "019_deal_messages"
down_revision = "018_auctions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS deal_messages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            deal_id UUID NOT NULL REFERENCES deals(id),
            sender_role VARCHAR(16) NOT NULL,
            sender_id UUID REFERENCES users(id),
            body TEXT NOT NULL,
            kind VARCHAR(32) NOT NULL DEFAULT 'text',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_deal_messages_deal_created
        ON deal_messages (deal_id, created_at);
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_deal_messages_deal_created;")
    op.execute("DROP TABLE IF EXISTS deal_messages CASCADE;")
