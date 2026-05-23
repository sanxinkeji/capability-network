"""User email verification columns."""

from alembic import op

revision = "017_email_verification"
down_revision = "016_kyc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMPTZ;
        """
    )
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS email_verification_code VARCHAR(8);
        """
    )
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS email_verification_expires_at TIMESTAMPTZ;
        """
    )
    op.execute(
        """
        UPDATE users
        SET email_verified_at = COALESCE(email_verified_at, created_at)
        WHERE email_verified_at IS NULL;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS email_verification_expires_at;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS email_verification_code;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS email_verified_at;")
