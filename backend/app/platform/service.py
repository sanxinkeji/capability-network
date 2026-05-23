from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import raise_auth_error
from app.core.maintenance import invalidate_maintenance_cache
from app.platform.settings_cache import invalidate_platform_settings_cache
from app.core.config import settings as app_settings
from app.platform.models import AdminAuditLog, PlatformSettings, RegistrationMode
from app.platform.registration import normalize_registration_mode, registration_invite_required
from app.platform.schemas import (
    PaymentConfigInfo,
    PlatformSettingsResponse,
    PlatformSettingsUpdate,
    PublicLegalAgreementSummary,
    PublicPlatformSettingsResponse,
)


def _parse_public_legal_agreements(json_str: str | None) -> list[PublicLegalAgreementSummary]:
    if not json_str or not json_str.strip():
        return []
    import json

    try:
        raw = json.loads(json_str)
    except json.JSONDecodeError:
        return []
    if not isinstance(raw, list):
        return []
    items: list[PublicLegalAgreementSummary] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        title = str(entry.get("title") or "").strip()
        slug = str(entry.get("slug") or "").strip()
        if not title or not slug:
            continue
        items.append(
            PublicLegalAgreementSummary(
                title=title,
                slug=slug,
                content=str(entry.get("content") or ""),
            )
        )
    return items


def _to_response(row: PlatformSettings) -> PlatformSettingsResponse:
    return PlatformSettingsResponse(
        site_name=row.site_name,
        site_tagline=row.site_tagline,
        site_announcement=row.site_announcement,
        support_email=row.support_email,
        support_url=row.support_url,
        docs_url=row.docs_url,
        api_public_url=row.api_public_url,
        footer_text=row.footer_text,
        custom_links_json=row.custom_links_json,
        default_page_size=row.default_page_size,
        page_size_options=row.page_size_options,
        legal_terms_enabled=row.legal_terms_enabled,
        legal_terms_mode=row.legal_terms_mode,
        legal_terms_updated_at=row.legal_terms_updated_at.isoformat() if row.legal_terms_updated_at else None,
        legal_agreements_json=row.legal_agreements_json,
        feature_marketplace_enabled=row.feature_marketplace_enabled,
        feature_matching_enabled=row.feature_matching_enabled,
        feature_wallet_enabled=row.feature_wallet_enabled,
        feature_referral_enabled=row.feature_referral_enabled,
        feature_agent_enabled=row.feature_agent_enabled,
        agent_max_keys_per_user=row.agent_max_keys_per_user,
        agent_platform_user_id_prefix=row.agent_platform_user_id_prefix,
        agent_mcp_docs_url=row.agent_mcp_docs_url,
        email_verification_required=row.email_verification_required,
        registration_email_domains=row.registration_email_domains,
        registration_invite_required=row.registration_invite_required,
        two_factor_allowed=row.two_factor_allowed,
        trust_proxy_ip=row.trust_proxy_ip,
        default_wallet_balance_cents=row.default_wallet_balance_cents,
        smtp_host=row.smtp_host,
        smtp_port=row.smtp_port,
        smtp_user=row.smtp_user,
        smtp_password=row.smtp_password,
        smtp_from=row.smtp_from,
        smtp_use_tls=row.smtp_use_tls,
        email_template_verify_subject=row.email_template_verify_subject,
        email_template_verify_html=row.email_template_verify_html,
        backup_s3_endpoint=row.backup_s3_endpoint,
        backup_s3_region=row.backup_s3_region,
        backup_s3_bucket=row.backup_s3_bucket,
        backup_s3_prefix=row.backup_s3_prefix,
        backup_s3_access_key=row.backup_s3_access_key,
        backup_s3_secret_key=row.backup_s3_secret_key,
        backup_auto_enabled=row.backup_auto_enabled,
        backup_cron=row.backup_cron,
        backup_retention_days=row.backup_retention_days,
        backup_max_count=row.backup_max_count,
        commission_rate_percent=row.commission_rate_percent,
        min_deposit_cents=row.min_deposit_cents,
        max_deposit_cents=row.max_deposit_cents,
        min_withdraw_cents=row.min_withdraw_cents,
        max_withdraw_cents=row.max_withdraw_cents,
        payment_wechat_enabled=row.payment_wechat_enabled,
        payment_alipay_enabled=row.payment_alipay_enabled,
        payment_enabled=row.payment_enabled,
        payment_product_name_prefix=row.payment_product_name_prefix,
        payment_product_name_suffix=row.payment_product_name_suffix,
        payment_product_description=row.payment_product_description,
        payment_order_timeout_minutes=row.payment_order_timeout_minutes,
        max_pending_payment_orders=row.max_pending_payment_orders,
        payment_daily_limit_cents=row.payment_daily_limit_cents,
        payment_fee_rate_percent=row.payment_fee_rate_percent,
        payment_recharge_rate_percent=row.payment_recharge_rate_percent,
        max_daily_payment_count=row.max_daily_payment_count,
        payment_broadcast_mode=row.payment_broadcast_mode,
        payment_help_text=row.payment_help_text,
        payment_help_image_url=row.payment_help_image_url,
        easypay_enabled=row.easypay_enabled,
        payment_airwallex_enabled=row.payment_airwallex_enabled,
        payment_alipay_source=row.payment_alipay_source,
        payment_wechat_source=row.payment_wechat_source,
        easypay_pid=row.easypay_pid,
        easypay_key=row.easypay_key,
        easypay_api_base=row.easypay_api_base,
        easypay_alipay_type=row.easypay_alipay_type,
        easypay_wechat_type=row.easypay_wechat_type,
        stripe_enabled=row.stripe_enabled,
        stripe_public_key=row.stripe_public_key,
        stripe_secret_key=row.stripe_secret_key,
        stripe_webhook_secret=row.stripe_webhook_secret,
        maintenance_mode=row.maintenance_mode,
        registration_mode=normalize_registration_mode(row.registration_mode),
        registration_invite_codes=row.registration_invite_codes,
        updated_at=row.updated_at.isoformat() if row.updated_at else None,
    )


def _to_public_response(row: PlatformSettings) -> PublicPlatformSettingsResponse:
    return PublicPlatformSettingsResponse(
        site_name=row.site_name,
        site_tagline=row.site_tagline,
        site_announcement=row.site_announcement,
        maintenance_mode=row.maintenance_mode,
        registration_mode=normalize_registration_mode(row.registration_mode),
        registration_invite_required=registration_invite_required(row),
        footer_text=row.footer_text,
        custom_links_json=row.custom_links_json,
        docs_url=row.docs_url,
        support_email=row.support_email,
        support_url=row.support_url,
        feature_marketplace_enabled=row.feature_marketplace_enabled,
        feature_matching_enabled=row.feature_matching_enabled,
        feature_wallet_enabled=row.feature_wallet_enabled,
        feature_referral_enabled=row.feature_referral_enabled,
        feature_agent_enabled=row.feature_agent_enabled,
        agent_mcp_docs_url=row.agent_mcp_docs_url,
        email_verification_required=row.email_verification_required,
        legal_terms_enabled=row.legal_terms_enabled,
        legal_terms_updated_at=row.legal_terms_updated_at.isoformat() if row.legal_terms_updated_at else None,
        legal_agreements=_parse_public_legal_agreements(row.legal_agreements_json),
    )


async def get_or_create_settings(db: AsyncSession) -> PlatformSettings:
    result = await db.execute(select(PlatformSettings).where(PlatformSettings.id == 1))
    row = result.scalar_one_or_none()
    if row is not None:
        return row

    row = PlatformSettings(
        id=1,
        site_name="Capability",
        commission_rate_percent=10,
        min_deposit_cents=app_settings.MIN_DEPOSIT_CENTS,
        min_withdraw_cents=app_settings.MIN_WITHDRAW_CENTS,
        max_withdraw_cents=app_settings.MAX_WITHDRAW_CENTS,
        registration_mode=RegistrationMode.OPEN,
    )
    db.add(row)
    await db.flush()
    return row


async def get_platform_settings(db: AsyncSession) -> PlatformSettingsResponse:
    row = await get_or_create_settings(db)
    return _to_response(row)


async def get_public_platform_settings(db: AsyncSession) -> PublicPlatformSettingsResponse:
    row = await get_or_create_settings(db)
    return _to_public_response(row)


async def update_platform_settings(
    db: AsyncSession,
    *,
    payload: PlatformSettingsUpdate,
    admin_id: UUID,
) -> PlatformSettingsResponse:
    row = await get_or_create_settings(db)
    updates = payload.model_dump(exclude_unset=True)

    if "min_withdraw_cents" in updates and "max_withdraw_cents" in updates:
        if updates["min_withdraw_cents"] > updates["max_withdraw_cents"]:
            raise_auth_error(code=48001, message="min withdraw cannot exceed max withdraw", http_status=422)
    elif "min_withdraw_cents" in updates and updates["min_withdraw_cents"] > row.max_withdraw_cents:
        raise_auth_error(code=48001, message="min withdraw cannot exceed max withdraw", http_status=422)
    elif "max_withdraw_cents" in updates and updates["max_withdraw_cents"] < row.min_withdraw_cents:
        raise_auth_error(code=48001, message="max withdraw cannot be less than min withdraw", http_status=422)

    if updates.get("registration_mode") == RegistrationMode.INVITE_ONLY:
        pass

    alipay_source = updates.get("payment_alipay_source", row.payment_alipay_source)
    wechat_source = updates.get("payment_wechat_source", row.payment_wechat_source)
    easypay_pid = updates.get("easypay_pid", row.easypay_pid)
    easypay_key = updates.get("easypay_key", row.easypay_key)
    easypay_api_base = updates.get("easypay_api_base", row.easypay_api_base)
    if alipay_source == "easypay" or wechat_source == "easypay":
        if not (easypay_pid and easypay_key and easypay_api_base):
            raise_auth_error(
                code=48003,
                message="easypay source requires pid, key and api base",
                http_status=422,
            )

    if "legal_terms_updated_at" in updates:
        raw = updates["legal_terms_updated_at"]
        if raw in (None, ""):
            updates["legal_terms_updated_at"] = None
        elif isinstance(raw, str):
            from datetime import datetime

            updates["legal_terms_updated_at"] = datetime.fromisoformat(raw.replace("Z", "+00:00"))

    for key, value in updates.items():
        setattr(row, key, value)
    row.updated_by_id = admin_id

    await log_admin_action(
        db,
        admin_id=admin_id,
        action="update_platform_settings",
        target_type="platform_settings",
        target_id="1",
        detail=str(list(updates.keys())),
    )
    await db.commit()
    await db.refresh(row)
    if "maintenance_mode" in updates:
        invalidate_maintenance_cache()
    if "trust_proxy_ip" in updates:
        invalidate_platform_settings_cache()
    return _to_response(row)


async def get_commission_rate(db: AsyncSession) -> float:
    row = await get_or_create_settings(db)
    return row.commission_rate_percent / 100.0


async def get_payment_config_info(db: AsyncSession) -> PaymentConfigInfo:
    row = await get_or_create_settings(db)
    base = app_settings.PUBLIC_BASE_URL.rstrip("/")
    easypay_configured = bool(row.easypay_pid and row.easypay_key and row.easypay_api_base)
    stripe_configured = bool(
        row.stripe_public_key and row.stripe_secret_key and row.stripe_webhook_secret
    )
    smtp_configured = bool(row.smtp_host and row.smtp_from)
    return PaymentConfigInfo(
        public_base_url=base,
        payment_provider=app_settings.PAYMENT_PROVIDER,
        payment_enabled=row.payment_enabled,
        payment_alipay_source=row.payment_alipay_source,
        payment_wechat_source=row.payment_wechat_source,
        wechat_configured=app_settings.wechat_pay_configured or easypay_configured,
        alipay_configured=app_settings.alipay_configured or easypay_configured,
        easypay_configured=easypay_configured,
        stripe_configured=stripe_configured,
        wechat_enabled=row.payment_wechat_enabled,
        alipay_enabled=row.payment_alipay_enabled,
        stripe_enabled=row.stripe_enabled,
        notify_wechat_url=f"{base}/api/v1/wallets/payment-notify/wechat",
        notify_alipay_url=f"{base}/api/v1/wallets/payment-notify/alipay",
        notify_easypay_url=f"{base}/api/v1/wallets/payment-notify/easypay",
        notify_stripe_url=f"{base}/api/v1/wallets/payment-notify/stripe",
        smtp_configured=smtp_configured,
    )


async def log_admin_action(
    db: AsyncSession,
    *,
    admin_id: UUID,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    detail: str | None = None,
) -> None:
    db.add(
        AdminAuditLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
        )
    )


async def list_audit_logs(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    from sqlalchemy import func

    query = select(AdminAuditLog)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    result = await db.execute(
        query.order_by(AdminAuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    logs = result.scalars().all()
    return {
        "items": [
            {
                "id": str(log.id),
                "admin_id": str(log.admin_id),
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "detail": log.detail,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
