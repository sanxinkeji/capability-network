"""kyc id number encryption storage

Revision ID: 016
Revises: 015
Create Date: 2026-05-23

"""
from typing import Sequence, Union

from alembic import op

revision: str = "016_kyc"
down_revision: Union[str, None] = "016_database_backups"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ALTER COLUMN kyc_id_number TYPE VARCHAR(512);")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS kyc_id_number_hash VARCHAR(64);")
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_kyc_id_number_hash
            ON users (kyc_id_number_hash)
            WHERE kyc_id_number_hash IS NOT NULL;
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_users_kyc_id_number_hash;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS kyc_id_number_hash;")
    op.execute("ALTER TABLE users ALTER COLUMN kyc_id_number TYPE VARCHAR(64);")
