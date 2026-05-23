"""stripe webhook secret

Revision ID: 015
Revises: 014
Create Date: 2026-05-23

"""
from typing import Sequence, Union

from alembic import op

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS stripe_webhook_secret VARCHAR(256);
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE platform_settings DROP COLUMN IF EXISTS stripe_webhook_secret;")
