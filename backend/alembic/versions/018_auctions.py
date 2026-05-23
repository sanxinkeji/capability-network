"""Agent 需求竞价室表结构

Revision ID: 018_auctions
Revises: 017_email_verification
Create Date: 2026-05-23
"""

from alembic import op

revision = "018_auctions"
down_revision = "017_email_verification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS auctions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            intent_id UUID NOT NULL UNIQUE REFERENCES intents(id),
            status VARCHAR(32) NOT NULL DEFAULT 'open',
            selected_bid_id UUID,
            deal_id UUID REFERENCES deals(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS auction_participants (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            auction_id UUID NOT NULL REFERENCES auctions(id),
            offer_id UUID NOT NULL REFERENCES offers(id),
            user_id UUID NOT NULL REFERENCES users(id),
            match_log_id UUID REFERENCES match_logs(id),
            joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_auction_participant_offer UNIQUE (auction_id, offer_id)
        );
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS auction_bids (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            auction_id UUID NOT NULL REFERENCES auctions(id),
            participant_id UUID NOT NULL REFERENCES auction_participants(id),
            offer_id UUID NOT NULL REFERENCES offers(id),
            user_id UUID NOT NULL REFERENCES users(id),
            amount_cents BIGINT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS auction_messages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            auction_id UUID NOT NULL REFERENCES auctions(id),
            user_id UUID NOT NULL REFERENCES users(id),
            message TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_auction_bids_auction_id
        ON auction_bids (auction_id, created_at DESC);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_auction_participants_auction_id
        ON auction_participants (auction_id);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS auction_messages;")
    op.execute("DROP TABLE IF EXISTS auction_bids;")
    op.execute("DROP TABLE IF EXISTS auction_participants;")
    op.execute("DROP TABLE IF EXISTS auctions;")
