"""users auth extensions: phone, kyc, refresh_tokens, api_keys

Revision ID: 002
Revises: 001
Create Date: 2026-05-23

"""
from typing import Sequence, Union

from alembic import op

from migration_sql import execute_sql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    execute_sql("""
        ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20) UNIQUE;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS kyc_level VARCHAR(8) NOT NULL DEFAULT 'L0';
        ALTER TABLE users ADD COLUMN IF NOT EXISTS kyc_real_name VARCHAR(100);
        ALTER TABLE users ADD COLUMN IF NOT EXISTS kyc_id_number VARCHAR(64);
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_phone ON users (phone);")

    op.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id         UUID         NOT NULL REFERENCES users (id) ON DELETE CASCADE,
            token_hash      VARCHAR(255) NOT NULL UNIQUE,
            expires_at      TIMESTAMPTZ  NOT NULL,
            revoked_at      TIMESTAMPTZ,
            created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens (user_id);")

    op.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id           UUID         NOT NULL REFERENCES users (id) ON DELETE CASCADE,
            platform_user_id  VARCHAR(128) NOT NULL,
            key_hash          VARCHAR(255) NOT NULL,
            key_prefix        VARCHAR(16)  NOT NULL,
            name              VARCHAR(100),
            status            VARCHAR(32)  NOT NULL DEFAULT 'active',
            created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            rotated_at        TIMESTAMPTZ,
            expires_at        TIMESTAMPTZ
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys (user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys (key_hash);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_platform_user_id ON api_keys (platform_user_id);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS api_keys CASCADE;")
    op.execute("DROP TABLE IF EXISTS refresh_tokens CASCADE;")
    op.execute("DROP INDEX IF EXISTS idx_users_phone;")
    execute_sql("""
        ALTER TABLE users DROP COLUMN IF EXISTS kyc_id_number;
        ALTER TABLE users DROP COLUMN IF EXISTS kyc_real_name;
        ALTER TABLE users DROP COLUMN IF EXISTS kyc_level;
        ALTER TABLE users DROP COLUMN IF EXISTS phone;
    """)
