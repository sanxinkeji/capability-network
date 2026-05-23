"""extended system settings (Sub2API-style tabs)

Revision ID: 010
Revises: 009
Create Date: 2026-05-23

"""
from typing import Sequence, Union

from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS docs_url VARCHAR(512);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS api_public_url VARCHAR(512);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS footer_text TEXT;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS custom_links_json TEXT;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS default_page_size INTEGER NOT NULL DEFAULT 20;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS page_size_options VARCHAR(64) NOT NULL DEFAULT '10,20,50';
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS legal_terms_enabled BOOLEAN NOT NULL DEFAULT FALSE;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS legal_terms_mode VARCHAR(16) NOT NULL DEFAULT 'popup';
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS legal_terms_updated_at TIMESTAMPTZ;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS legal_agreements_json TEXT;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS feature_marketplace_enabled BOOLEAN NOT NULL DEFAULT TRUE;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS feature_matching_enabled BOOLEAN NOT NULL DEFAULT TRUE;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS feature_wallet_enabled BOOLEAN NOT NULL DEFAULT TRUE;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS feature_referral_enabled BOOLEAN NOT NULL DEFAULT FALSE;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS email_verification_required BOOLEAN NOT NULL DEFAULT FALSE;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS registration_email_domains TEXT;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS registration_invite_required BOOLEAN NOT NULL DEFAULT FALSE;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS two_factor_allowed BOOLEAN NOT NULL DEFAULT FALSE;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS trust_proxy_ip BOOLEAN NOT NULL DEFAULT FALSE;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS default_wallet_balance_cents BIGINT NOT NULL DEFAULT 0;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS smtp_host VARCHAR(255);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS smtp_port INTEGER NOT NULL DEFAULT 587;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS smtp_user VARCHAR(255);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS smtp_password VARCHAR(256);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS smtp_from VARCHAR(255);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS smtp_use_tls BOOLEAN NOT NULL DEFAULT TRUE;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS email_template_verify_subject VARCHAR(256);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS email_template_verify_html TEXT;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS backup_s3_endpoint VARCHAR(512);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS backup_s3_region VARCHAR(64);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS backup_s3_bucket VARCHAR(128);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS backup_s3_prefix VARCHAR(128);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS backup_s3_access_key VARCHAR(128);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS backup_s3_secret_key VARCHAR(256);
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS backup_auto_enabled BOOLEAN NOT NULL DEFAULT FALSE;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS backup_cron VARCHAR(64) NOT NULL DEFAULT '0 2 * * *';
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS backup_retention_days INTEGER NOT NULL DEFAULT 7;
    """)
    op.execute("""
        ALTER TABLE platform_settings
        ADD COLUMN IF NOT EXISTS backup_max_count INTEGER NOT NULL DEFAULT 10;
    """)


def downgrade() -> None:
    cols = [
        "backup_max_count",
        "backup_retention_days",
        "backup_cron",
        "backup_auto_enabled",
        "backup_s3_secret_key",
        "backup_s3_access_key",
        "backup_s3_prefix",
        "backup_s3_bucket",
        "backup_s3_region",
        "backup_s3_endpoint",
        "email_template_verify_html",
        "email_template_verify_subject",
        "smtp_use_tls",
        "smtp_from",
        "smtp_password",
        "smtp_user",
        "smtp_port",
        "smtp_host",
        "default_wallet_balance_cents",
        "trust_proxy_ip",
        "two_factor_allowed",
        "registration_invite_required",
        "registration_email_domains",
        "email_verification_required",
        "feature_referral_enabled",
        "feature_wallet_enabled",
        "feature_matching_enabled",
        "feature_marketplace_enabled",
        "legal_agreements_json",
        "legal_terms_updated_at",
        "legal_terms_mode",
        "legal_terms_enabled",
        "page_size_options",
        "default_page_size",
        "custom_links_json",
        "footer_text",
        "api_public_url",
        "docs_url",
    ]
    for col in cols:
        op.execute(f"ALTER TABLE platform_settings DROP COLUMN IF EXISTS {col};")
