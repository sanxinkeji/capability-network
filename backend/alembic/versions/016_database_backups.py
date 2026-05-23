"""database backup history

Revision ID: 016
Revises: 015
Create Date: 2026-05-23

"""
from typing import Sequence, Union

from alembic import op

revision: str = "016_database_backups"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS database_backups (
            id UUID PRIMARY KEY,
            status VARCHAR(16) NOT NULL,
            filename VARCHAR(256),
            file_path TEXT,
            object_key TEXT,
            size_bytes BIGINT,
            trigger_type VARCHAR(16) NOT NULL,
            error_message TEXT,
            started_at TIMESTAMPTZ NOT NULL,
            finished_at TIMESTAMPTZ,
            created_by_admin_id UUID REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_database_backups_created_at "
        "ON database_backups (created_at DESC);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_database_backups_status "
        "ON database_backups (status);"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS database_backups;")
