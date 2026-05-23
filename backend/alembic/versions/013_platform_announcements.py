"""platform announcements

Revision ID: 013
Revises: 012
Create Date: 2026-05-23

"""
from typing import Sequence, Union

from alembic import op

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS platform_announcements (
            id SERIAL PRIMARY KEY,
            title VARCHAR(256) NOT NULL,
            content TEXT NOT NULL DEFAULT '',
            status VARCHAR(16) NOT NULL DEFAULT 'draft',
            notify_mode VARCHAR(16) NOT NULL DEFAULT 'popup',
            audience VARCHAR(32) NOT NULL DEFAULT 'all',
            starts_at TIMESTAMPTZ,
            ends_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS platform_announcements;")
