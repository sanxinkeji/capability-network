import { describe, expect, it } from 'vitest'
import {
  buildSettingsPayload,
  normalizeSettingsForm,
  parseCustomLinks,
  parseLegalAgreements,
  serializeCustomLinks,
  serializeLegalAgreements,
} from './adminSettingsForm'
import type { PlatformSettings } from '@/types'

function minimalSettings(overrides: Partial<PlatformSettings> = {}): PlatformSettings {
  return {
    site_name: 'Test Site',
    site_tagline: null,
    site_announcement: null,
    maintenance_mode: false,
    registration_mode: 'open',
    registration_invite_required: false,
    support_email: null,
    support_url: null,
    docs_url: null,
    api_public_url: null,
    footer_text: null,
    custom_links_json: null,
    default_page_size: 20,
    page_size_options: '10,20,50',
    legal_terms_enabled: false,
    legal_terms_mode: 'popup',
    legal_terms_updated_at: null,
    legal_agreements_json: null,
    feature_marketplace_enabled: true,
    feature_matching_enabled: true,
    feature_wallet_enabled: true,
    feature_referral_enabled: false,
    feature_agent_enabled: true,
    agent_max_keys_per_user: 5,
    agent_platform_user_id_prefix: null,
    agent_mcp_docs_url: null,
    email_verification_required: false,
    registration_email_domains: null,
    registration_invite_codes: null,
    two_factor_allowed: false,
    trust_proxy_ip: false,
    default_wallet_balance_cents: 0,
    smtp_host: null,
    smtp_port: 587,
    smtp_user: null,
    smtp_password: null,
    smtp_from: null,
    smtp_use_tls: true,
    email_template_verify_subject: null,
    email_template_verify_html: null,
    backup_s3_endpoint: null,
    backup_s3_region: null,
    backup_s3_bucket: null,
    backup_s3_prefix: null,
    backup_s3_access_key: null,
    backup_s3_secret_key: null,
    backup_auto_enabled: false,
    backup_cron: '0 3 * * *',
    backup_retention_days: 7,
    backup_max_count: 10,
    commission_rate_percent: 10,
    min_deposit_cents: 100,
    max_deposit_cents: null,
    min_withdraw_cents: 100,
    max_withdraw_cents: 100000,
    payment_wechat_enabled: false,
    payment_alipay_enabled: false,
    payment_enabled: false,
    payment_order_timeout_minutes: 30,
    max_pending_payment_orders: 3,
    payment_fee_rate_percent: 0,
    payment_recharge_rate_percent: 0,
    payment_broadcast_mode: false,
    easypay_enabled: false,
    payment_airwallex_enabled: false,
    payment_alipay_source: 'direct',
    payment_wechat_source: 'direct',
    stripe_enabled: false,
    updated_at: null,
    payment_product_name_prefix: null,
    payment_product_name_suffix: null,
    payment_product_description: null,
    payment_help_text: null,
    payment_help_image_url: null,
    payment_daily_limit_cents: null,
    max_daily_payment_count: null,
    easypay_pid: null,
    easypay_key: null,
    easypay_api_base: null,
    easypay_alipay_type: null,
    easypay_wechat_type: null,
    stripe_public_key: null,
    stripe_secret_key: null,
    stripe_webhook_secret: null,
    ...overrides,
  }
}

describe('adminSettingsForm', () => {
  describe('parseCustomLinks', () => {
    it('returns empty array for blank input', () => {
      expect(parseCustomLinks(null)).toEqual([])
      expect(parseCustomLinks('   ')).toEqual([])
    })

    it('parses valid JSON array', () => {
      const json = JSON.stringify([{ label: 'Docs', url: 'https://docs.example.com' }])
      expect(parseCustomLinks(json)).toEqual([{ label: 'Docs', url: 'https://docs.example.com' }])
    })

    it('returns empty array for invalid JSON', () => {
      expect(parseCustomLinks('{not json')).toEqual([])
    })
  })

  describe('serializeCustomLinks', () => {
    it('filters out incomplete links', () => {
      const result = serializeCustomLinks([
        { label: '  ', url: 'https://a.com' },
        { label: 'Help', url: 'https://help.example.com' },
      ])
      expect(result).toBe(JSON.stringify([{ label: 'Help', url: 'https://help.example.com' }]))
    })

    it('returns null when no valid links', () => {
      expect(serializeCustomLinks([{ label: '', url: '' }])).toBeNull()
    })
  })

  describe('parseLegalAgreements / serializeLegalAgreements', () => {
    it('round-trips legal agreements', () => {
      const items = [{ title: 'Terms', slug: 'terms', content: 'body' }]
      const json = serializeLegalAgreements(items)
      expect(parseLegalAgreements(json)).toEqual(items)
    })
  })

  describe('normalizeSettingsForm', () => {
    it('fills null optional strings with empty defaults', () => {
      const normalized = normalizeSettingsForm(minimalSettings({ docs_url: null, footer_text: null }))
      expect(normalized.docs_url).toBe('')
      expect(normalized.footer_text).toBe('')
    })

    it('truncates legal_terms_updated_at to date portion', () => {
      const normalized = normalizeSettingsForm(
        minimalSettings({ legal_terms_updated_at: '2026-05-23T12:00:00Z' }),
      )
      expect(normalized.legal_terms_updated_at).toBe('2026-05-23')
    })
  })

  describe('buildSettingsPayload', () => {
    it('converts empty strings to null for API payload', () => {
      const form = normalizeSettingsForm(minimalSettings({ docs_url: '', footer_text: 'Footer' }))
      const payload = buildSettingsPayload(form)
      expect(payload.docs_url).toBeNull()
      expect(payload.footer_text).toBe('Footer')
    })

    it('preserves numeric limits when set', () => {
      const form = normalizeSettingsForm(minimalSettings({ max_deposit_cents: 50000 }))
      const payload = buildSettingsPayload(form)
      expect(payload.max_deposit_cents).toBe(50000)
    })
  })
})
