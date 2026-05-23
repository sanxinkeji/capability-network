import type { CustomLinkItem, LegalAgreementItem, PlatformSettings } from '@/types'

export function parseCustomLinks(json: string | null | undefined): CustomLinkItem[] {
  if (!json?.trim()) return []
  try {
    const parsed = JSON.parse(json) as CustomLinkItem[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function serializeCustomLinks(links: CustomLinkItem[]): string | null {
  const valid = links.filter((l) => l.label.trim() && l.url.trim())
  return valid.length ? JSON.stringify(valid) : null
}

export function parseLegalAgreements(json: string | null | undefined): LegalAgreementItem[] {
  if (!json?.trim()) return []
  try {
    const parsed = JSON.parse(json) as LegalAgreementItem[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function serializeLegalAgreements(items: LegalAgreementItem[]): string | null {
  const valid = items.filter((a) => a.title.trim() && a.slug.trim())
  return valid.length ? JSON.stringify(valid) : null
}

export function normalizeSettingsForm(settings: PlatformSettings): PlatformSettings {
  return {
    ...settings,
    registration_invite_codes: settings.registration_invite_codes ?? '',
    max_deposit_cents: settings.max_deposit_cents ?? null,
    docs_url: settings.docs_url ?? '',
    api_public_url: settings.api_public_url ?? '',
    footer_text: settings.footer_text ?? '',
    custom_links_json: settings.custom_links_json ?? '',
    legal_agreements_json: settings.legal_agreements_json ?? '',
    legal_terms_updated_at: settings.legal_terms_updated_at?.slice(0, 10) ?? '',
    registration_email_domains: settings.registration_email_domains ?? '',
    payment_product_name_prefix: settings.payment_product_name_prefix ?? '',
    payment_product_name_suffix: settings.payment_product_name_suffix ?? '',
    payment_product_description: settings.payment_product_description ?? '',
    payment_help_text: settings.payment_help_text ?? '',
    payment_help_image_url: settings.payment_help_image_url ?? '',
    payment_daily_limit_cents: settings.payment_daily_limit_cents ?? null,
    max_daily_payment_count: settings.max_daily_payment_count ?? null,
    easypay_pid: settings.easypay_pid ?? '',
    easypay_key: settings.easypay_key ?? '',
    easypay_api_base: settings.easypay_api_base ?? '',
    easypay_alipay_type: settings.easypay_alipay_type ?? '',
    easypay_wechat_type: settings.easypay_wechat_type ?? '',
    stripe_public_key: settings.stripe_public_key ?? '',
    stripe_secret_key: settings.stripe_secret_key ?? '',
    stripe_webhook_secret: settings.stripe_webhook_secret ?? '',
    smtp_host: settings.smtp_host ?? '',
    smtp_user: settings.smtp_user ?? '',
    smtp_password: settings.smtp_password ?? '',
    smtp_from: settings.smtp_from ?? '',
    email_template_verify_subject: settings.email_template_verify_subject ?? '',
    email_template_verify_html: settings.email_template_verify_html ?? '',
    backup_s3_endpoint: settings.backup_s3_endpoint ?? '',
    backup_s3_region: settings.backup_s3_region ?? '',
    backup_s3_bucket: settings.backup_s3_bucket ?? '',
    backup_s3_prefix: settings.backup_s3_prefix ?? '',
    backup_s3_access_key: settings.backup_s3_access_key ?? '',
    backup_s3_secret_key: settings.backup_s3_secret_key ?? '',
    agent_platform_user_id_prefix: settings.agent_platform_user_id_prefix ?? '',
    agent_mcp_docs_url: settings.agent_mcp_docs_url ?? '',
  }
}

export function buildSettingsPayload(form: PlatformSettings): PlatformSettings {
  return {
    ...form,
    max_deposit_cents: form.max_deposit_cents || null,
    docs_url: form.docs_url || null,
    api_public_url: form.api_public_url || null,
    footer_text: form.footer_text || null,
    custom_links_json: form.custom_links_json || null,
    legal_agreements_json: form.legal_agreements_json || null,
    legal_terms_updated_at: form.legal_terms_updated_at || null,
    registration_email_domains: form.registration_email_domains || null,
    payment_product_name_prefix: form.payment_product_name_prefix || null,
    payment_product_name_suffix: form.payment_product_name_suffix || null,
    payment_product_description: form.payment_product_description || null,
    payment_help_text: form.payment_help_text || null,
    payment_help_image_url: form.payment_help_image_url || null,
    payment_daily_limit_cents: form.payment_daily_limit_cents || null,
    max_daily_payment_count: form.max_daily_payment_count || null,
    smtp_host: form.smtp_host || null,
    smtp_user: form.smtp_user || null,
    smtp_password: form.smtp_password || null,
    smtp_from: form.smtp_from || null,
    email_template_verify_subject: form.email_template_verify_subject || null,
    email_template_verify_html: form.email_template_verify_html || null,
    backup_s3_endpoint: form.backup_s3_endpoint || null,
    backup_s3_region: form.backup_s3_region || null,
    backup_s3_bucket: form.backup_s3_bucket || null,
    backup_s3_prefix: form.backup_s3_prefix || null,
    backup_s3_access_key: form.backup_s3_access_key || null,
    backup_s3_secret_key: form.backup_s3_secret_key || null,
    agent_platform_user_id_prefix: form.agent_platform_user_id_prefix || null,
    agent_mcp_docs_url: form.agent_mcp_docs_url || null,
  }
}

export const DEFAULT_VERIFY_TEMPLATE = `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
body{font-family:sans-serif;background:#f5f5f5;margin:0;padding:24px}
.box{max-width:480px;margin:0 auto;background:#fff;border-radius:12px;padding:32px}
.code{font-size:32px;font-weight:700;letter-spacing:4px;color:#14b8a6;text-align:center;margin:24px 0}
</style></head>
<body><div class="box">
<h2>邮箱验证码</h2>
<p>{{name}}，您好：</p>
<div class="code">{{code}}</div>
<p style="color:#888;font-size:13px">验证码 15 分钟内有效，请勿泄露。</p>
</div></body></html>`
