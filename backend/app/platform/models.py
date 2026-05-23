import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RegistrationMode:
    OPEN = "open"
    INVITE_ONLY = "invite_only"
    CLOSED = "closed"


class PaymentSource:
    DIRECT = "direct"
    EASYPAY = "easypay"


class PlatformSettings(Base):
    __tablename__ = "platform_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    site_name: Mapped[str] = mapped_column(String(128), nullable=False, default="Capability")
    site_tagline: Mapped[str | None] = mapped_column(String(256))
    site_announcement: Mapped[str | None] = mapped_column(Text)
    support_email: Mapped[str | None] = mapped_column(String(255))
    support_url: Mapped[str | None] = mapped_column(String(512))
    docs_url: Mapped[str | None] = mapped_column(String(512))
    api_public_url: Mapped[str | None] = mapped_column(String(512))
    footer_text: Mapped[str | None] = mapped_column(Text)
    custom_links_json: Mapped[str | None] = mapped_column(Text)
    default_page_size: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    page_size_options: Mapped[str] = mapped_column(String(64), nullable=False, default="10,20,50")
    legal_terms_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    legal_terms_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="popup")
    legal_terms_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    legal_agreements_json: Mapped[str | None] = mapped_column(Text)
    feature_marketplace_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    feature_matching_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    feature_wallet_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    feature_referral_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    feature_agent_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    agent_max_keys_per_user: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    agent_platform_user_id_prefix: Mapped[str | None] = mapped_column(String(64))
    agent_mcp_docs_url: Mapped[str | None] = mapped_column(String(512))
    email_verification_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    registration_email_domains: Mapped[str | None] = mapped_column(Text)
    registration_invite_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    two_factor_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    trust_proxy_ip: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    default_wallet_balance_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    smtp_host: Mapped[str | None] = mapped_column(String(255))
    smtp_port: Mapped[int] = mapped_column(Integer, nullable=False, default=587)
    smtp_user: Mapped[str | None] = mapped_column(String(255))
    smtp_password: Mapped[str | None] = mapped_column(String(256))
    smtp_from: Mapped[str | None] = mapped_column(String(255))
    smtp_use_tls: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email_template_verify_subject: Mapped[str | None] = mapped_column(String(256))
    email_template_verify_html: Mapped[str | None] = mapped_column(Text)
    backup_s3_endpoint: Mapped[str | None] = mapped_column(String(512))
    backup_s3_region: Mapped[str | None] = mapped_column(String(64))
    backup_s3_bucket: Mapped[str | None] = mapped_column(String(128))
    backup_s3_prefix: Mapped[str | None] = mapped_column(String(128))
    backup_s3_access_key: Mapped[str | None] = mapped_column(String(128))
    backup_s3_secret_key: Mapped[str | None] = mapped_column(String(256))
    backup_auto_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    backup_cron: Mapped[str] = mapped_column(String(64), nullable=False, default="0 2 * * *")
    backup_retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    backup_max_count: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    commission_rate_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    min_deposit_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=100)
    max_deposit_cents: Mapped[int | None] = mapped_column(BigInteger)
    min_withdraw_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=10000)
    max_withdraw_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=50_000_000)
    payment_wechat_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    payment_alipay_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    payment_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    payment_product_name_prefix: Mapped[str | None] = mapped_column(String(128))
    payment_product_name_suffix: Mapped[str | None] = mapped_column(String(128))
    payment_product_description: Mapped[str | None] = mapped_column(String(256))
    payment_order_timeout_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    max_pending_payment_orders: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    payment_daily_limit_cents: Mapped[int | None] = mapped_column(BigInteger)
    payment_fee_rate_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payment_recharge_rate_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    max_daily_payment_count: Mapped[int | None] = mapped_column(Integer)
    payment_broadcast_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payment_help_text: Mapped[str | None] = mapped_column(Text)
    payment_help_image_url: Mapped[str | None] = mapped_column(String(512))
    easypay_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    payment_airwallex_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payment_alipay_source: Mapped[str] = mapped_column(String(32), nullable=False, default="direct")
    payment_wechat_source: Mapped[str] = mapped_column(String(32), nullable=False, default="direct")
    easypay_pid: Mapped[str | None] = mapped_column(String(64))
    easypay_key: Mapped[str | None] = mapped_column(String(256))
    easypay_api_base: Mapped[str | None] = mapped_column(String(512))
    easypay_alipay_type: Mapped[str | None] = mapped_column(String(32))
    easypay_wechat_type: Mapped[str | None] = mapped_column(String(32))
    stripe_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stripe_public_key: Mapped[str | None] = mapped_column(String(256))
    stripe_secret_key: Mapped[str | None] = mapped_column(String(256))
    stripe_webhook_secret: Mapped[str | None] = mapped_column(String(256))
    maintenance_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    registration_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    registration_invite_codes: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))


class BackupStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DRY_RUN = "dry_run"


class BackupTrigger:
    MANUAL = "manual"
    SCHEDULED = "scheduled"


class DatabaseBackup(Base):
    __tablename__ = "database_backups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    filename: Mapped[str | None] = mapped_column(String(256))
    file_path: Mapped[str | None] = mapped_column(Text)
    object_key: Mapped[str | None] = mapped_column(Text)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    trigger_type: Mapped[str] = mapped_column(String(16), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(32))
    target_id: Mapped[str | None] = mapped_column(String(64))
    detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CodeType:
    INVITE = "invite"
    RECHARGE = "recharge"


class PlatformCode(Base):
    __tablename__ = "platform_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    code_type: Mapped[str] = mapped_column(String(16), nullable=False)
    value_cents: Mapped[int | None] = mapped_column(BigInteger)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    used_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
