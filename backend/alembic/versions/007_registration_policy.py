"""registration policy on platform_settings

Revision ID: 007
Revises: 006
Create Date: 2026-05-23

"""
from typing import Sequence, Union

from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS registration_mode VARCHAR(32) NOT NULL DEFAULT 'open';
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS registration_invite_codes TEXT;
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS registration_invite_codes;")
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS registration_mode;")
