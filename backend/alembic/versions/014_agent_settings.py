"""agent / openclaw platform settings

Revision ID: 014
Revises: 013
Create Date: 2026-05-23

"""
from typing import Sequence, Union

from alembic import op

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS feature_agent_enabled BOOLEAN NOT NULL DEFAULT TRUE;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS agent_max_keys_per_user INTEGER NOT NULL DEFAULT 10;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS agent_platform_user_id_prefix VARCHAR(64);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS agent_mcp_docs_url VARCHAR(512);
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS agent_mcp_docs_url;")
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS agent_platform_user_id_prefix;")
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS agent_max_keys_per_user;")
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS feature_agent_enabled;")
