from pydantic import BaseModel, Field, field_validator


class LegalAgreementItem(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    slug: str = Field(min_length=1, max_length=128)
    content: str = ""


class CustomLinkItem(BaseModel):
    label: str = Field(min_length=1, max_length=64)
    url: str = Field(min_length=1, max_length=512)


class PlatformSettingsResponse(BaseModel):
    site_name: str
    site_tagline: str | None = None
    site_announcement: str | None = None
    support_email: str | None = None
    support_url: str | None = None
    docs_url: str | None = None
    api_public_url: str | None = None
    footer_text: str | None = None
    custom_links_json: str | None = None
    default_page_size: int
    page_size_options: str
    legal_terms_enabled: bool
    legal_terms_mode: str
    legal_terms_updated_at: str | None = None
    legal_agreements_json: str | None = None
    feature_marketplace_enabled: bool
    feature_matching_enabled: bool
    feature_wallet_enabled: bool
    feature_referral_enabled: bool
    feature_agent_enabled: bool
    agent_max_keys_per_user: int
    agent_platform_user_id_prefix: str | None = None
    agent_mcp_docs_url: str | None = None
    email_verification_required: bool
    registration_email_domains: str | None = None
    registration_invite_required: bool
    two_factor_allowed: bool
    trust_proxy_ip: bool
    default_wallet_balance_cents: int
    smtp_host: str | None = None
    smtp_port: int
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_use_tls: bool
    email_template_verify_subject: str | None = None
    email_template_verify_html: str | None = None
    backup_s3_endpoint: str | None = None
    backup_s3_region: str | None = None
    backup_s3_bucket: str | None = None
    backup_s3_prefix: str | None = None
    backup_s3_access_key: str | None = None
    backup_s3_secret_key: str | None = None
    backup_auto_enabled: bool
    backup_cron: str
    backup_retention_days: int
    backup_max_count: int
    commission_rate_percent: int
    min_deposit_cents: int
    max_deposit_cents: int | None = None
    min_withdraw_cents: int
    max_withdraw_cents: int
    payment_wechat_enabled: bool
    payment_alipay_enabled: bool
    payment_enabled: bool
    payment_product_name_prefix: str | None = None
    payment_product_name_suffix: str | None = None
    payment_product_description: str | None = None
    payment_order_timeout_minutes: int
    max_pending_payment_orders: int
    payment_daily_limit_cents: int | None = None
    payment_fee_rate_percent: int
    payment_recharge_rate_percent: int
    max_daily_payment_count: int | None = None
    payment_broadcast_mode: bool
    payment_help_text: str | None = None
    payment_help_image_url: str | None = None
    easypay_enabled: bool
    payment_airwallex_enabled: bool
    payment_alipay_source: str
    payment_wechat_source: str
    easypay_pid: str | None = None
    easypay_key: str | None = None
    easypay_api_base: str | None = None
    easypay_alipay_type: str | None = None
    easypay_wechat_type: str | None = None
    stripe_enabled: bool
    stripe_public_key: str | None = None
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    maintenance_mode: bool
    registration_mode: str
    registration_invite_codes: str | None = None
    updated_at: str | None = None


class PublicLegalAgreementSummary(BaseModel):
    title: str
    slug: str
    content: str = ""


class PublicPlatformSettingsResponse(BaseModel):
    site_name: str
    site_tagline: str | None = None
    site_announcement: str | None = None
    maintenance_mode: bool
    registration_mode: str
    registration_invite_required: bool
    footer_text: str | None = None
    custom_links_json: str | None = None
    docs_url: str | None = None
    support_email: str | None = None
    support_url: str | None = None
    feature_marketplace_enabled: bool = True
    feature_matching_enabled: bool = True
    feature_wallet_enabled: bool = True
    feature_referral_enabled: bool = False
    feature_agent_enabled: bool = True
    agent_mcp_docs_url: str | None = None
    email_verification_required: bool = False
    legal_terms_enabled: bool = False
    legal_terms_updated_at: str | None = None
    legal_agreements: list[PublicLegalAgreementSummary] = Field(default_factory=list)


class PlatformSettingsUpdate(BaseModel):
    site_name: str | None = Field(default=None, min_length=1, max_length=128)
    site_tagline: str | None = Field(default=None, max_length=256)
    site_announcement: str | None = None
    support_email: str | None = Field(default=None, max_length=255)
    support_url: str | None = Field(default=None, max_length=512)
    docs_url: str | None = Field(default=None, max_length=512)
    api_public_url: str | None = Field(default=None, max_length=512)
    footer_text: str | None = None
    custom_links_json: str | None = None
    default_page_size: int | None = Field(default=None, ge=5, le=200)
    page_size_options: str | None = Field(default=None, max_length=64)
    legal_terms_enabled: bool | None = None
    legal_terms_mode: str | None = Field(default=None, pattern="^(popup|redirect)$")
    legal_terms_updated_at: str | None = None
    legal_agreements_json: str | None = None
    feature_marketplace_enabled: bool | None = None
    feature_matching_enabled: bool | None = None
    feature_wallet_enabled: bool | None = None
    feature_referral_enabled: bool | None = None
    feature_agent_enabled: bool | None = None
    agent_max_keys_per_user: int | None = Field(default=None, ge=1, le=100)
    agent_platform_user_id_prefix: str | None = Field(default=None, max_length=64)
    agent_mcp_docs_url: str | None = Field(default=None, max_length=512)
    email_verification_required: bool | None = None
    registration_email_domains: str | None = None
    registration_invite_required: bool | None = None
    two_factor_allowed: bool | None = None
    trust_proxy_ip: bool | None = None
    default_wallet_balance_cents: int | None = Field(default=None, ge=0)
    smtp_host: str | None = Field(default=None, max_length=255)
    smtp_port: int | None = Field(default=None, ge=1, le=65535)
    smtp_user: str | None = Field(default=None, max_length=255)
    smtp_password: str | None = Field(default=None, max_length=256)
    smtp_from: str | None = Field(default=None, max_length=255)
    smtp_use_tls: bool | None = None
    email_template_verify_subject: str | None = Field(default=None, max_length=256)
    email_template_verify_html: str | None = None
    backup_s3_endpoint: str | None = Field(default=None, max_length=512)
    backup_s3_region: str | None = Field(default=None, max_length=64)
    backup_s3_bucket: str | None = Field(default=None, max_length=128)
    backup_s3_prefix: str | None = Field(default=None, max_length=128)
    backup_s3_access_key: str | None = Field(default=None, max_length=128)
    backup_s3_secret_key: str | None = Field(default=None, max_length=256)
    backup_auto_enabled: bool | None = None
    backup_cron: str | None = Field(default=None, max_length=64)
    backup_retention_days: int | None = Field(default=None, ge=1, le=365)
    backup_max_count: int | None = Field(default=None, ge=1, le=100)
    commission_rate_percent: int | None = Field(default=None, ge=0, le=50)
    min_deposit_cents: int | None = Field(default=None, ge=1)
    max_deposit_cents: int | None = Field(default=None, ge=1)
    min_withdraw_cents: int | None = Field(default=None, ge=1)
    max_withdraw_cents: int | None = Field(default=None, ge=1)
    payment_wechat_enabled: bool | None = None
    payment_alipay_enabled: bool | None = None
    payment_enabled: bool | None = None
    payment_product_name_prefix: str | None = Field(default=None, max_length=128)
    payment_product_name_suffix: str | None = Field(default=None, max_length=128)
    payment_product_description: str | None = Field(default=None, max_length=256)
    payment_order_timeout_minutes: int | None = Field(default=None, ge=1, le=1440)
    max_pending_payment_orders: int | None = Field(default=None, ge=1, le=20)
    payment_daily_limit_cents: int | None = Field(default=None, ge=1)
    payment_fee_rate_percent: int | None = Field(default=None, ge=0, le=50)
    payment_recharge_rate_percent: int | None = Field(default=None, ge=1, le=1000)
    max_daily_payment_count: int | None = Field(default=None, ge=1, le=1000)
    payment_broadcast_mode: bool | None = None
    payment_help_text: str | None = None
    payment_help_image_url: str | None = Field(default=None, max_length=512)
    easypay_enabled: bool | None = None
    payment_airwallex_enabled: bool | None = None
    payment_alipay_source: str | None = Field(default=None, pattern="^(direct|easypay)$")
    payment_wechat_source: str | None = Field(default=None, pattern="^(direct|easypay)$")
    easypay_pid: str | None = Field(default=None, max_length=64)
    easypay_key: str | None = Field(default=None, max_length=256)
    easypay_api_base: str | None = Field(default=None, max_length=512)
    easypay_alipay_type: str | None = Field(default=None, max_length=32)
    easypay_wechat_type: str | None = Field(default=None, max_length=32)
    stripe_enabled: bool | None = None
    stripe_public_key: str | None = Field(default=None, max_length=256)
    stripe_secret_key: str | None = Field(default=None, max_length=256)
    stripe_webhook_secret: str | None = Field(default=None, max_length=256)
    maintenance_mode: bool | None = None
    registration_mode: str | None = Field(default=None, pattern="^(open|invite_only|closed)$")
    registration_invite_codes: str | None = None

    @field_validator("registration_invite_codes")
    @classmethod
    def normalize_invite_codes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        from app.platform.registration import serialize_invite_codes

        return serialize_invite_codes(value)


class PaymentConfigInfo(BaseModel):
    public_base_url: str
    payment_provider: str
    payment_enabled: bool
    payment_alipay_source: str
    payment_wechat_source: str
    wechat_configured: bool
    alipay_configured: bool
    easypay_configured: bool
    stripe_configured: bool
    wechat_enabled: bool
    alipay_enabled: bool
    stripe_enabled: bool
    notify_wechat_url: str
    notify_alipay_url: str
    notify_easypay_url: str
    notify_stripe_url: str
    smtp_configured: bool


class AdminAuditLogResponse(BaseModel):
    id: str
    admin_id: str
    action: str
    target_type: str | None
    target_id: str | None
    detail: str | None
    created_at: str
