import { defineStore } from 'pinia'
import { getPublicPlatformSettings } from '@/api/platform'
import { parseCustomLinks } from '@/composables/adminSettingsForm'
import type { CustomLinkItem, LegalAgreementItem, PublicPlatformSettings } from '@/types'

import { BRAND_NAME, BRAND_SLOGAN } from '@/utils/brand'

const FALLBACK: PublicPlatformSettings = {
  site_name: BRAND_NAME,
  site_tagline: BRAND_SLOGAN,
  site_announcement: null,
  maintenance_mode: false,
  registration_mode: 'open',
  registration_invite_required: false,
  footer_text: null,
  custom_links_json: null,
  docs_url: null,
  support_email: null,
  support_url: null,
  feature_marketplace_enabled: true,
  feature_matching_enabled: true,
  feature_wallet_enabled: true,
  feature_referral_enabled: false,
  feature_agent_enabled: true,
  agent_mcp_docs_url: null,
  legal_terms_enabled: false,
  legal_terms_updated_at: null,
  legal_agreements: [],
}

export const usePlatformStore = defineStore('platform', {
  state: () => ({
    settings: null as PublicPlatformSettings | null,
    loaded: false,
    loading: false,
  }),

  getters: {
    siteName(state): string {
      return state.settings?.site_name || FALLBACK.site_name
    },
    siteTagline(state): string {
      return state.settings?.site_tagline?.trim() || ''
    },
    announcement(state): string {
      return state.settings?.site_announcement?.trim() || ''
    },
    maintenanceMode(state): boolean {
      return state.settings?.maintenance_mode ?? false
    },
    footerText(state): string {
      return state.settings?.footer_text?.trim() || ''
    },
    docsUrl(state): string {
      return state.settings?.docs_url?.trim() || '/docs'
    },
    customLinks(state): CustomLinkItem[] {
      return parseCustomLinks(state.settings?.custom_links_json)
    },
    featureMarketplaceEnabled(state): boolean {
      return state.settings?.feature_marketplace_enabled ?? true
    },
    featureMatchingEnabled(state): boolean {
      return state.settings?.feature_matching_enabled ?? true
    },
    featureWalletEnabled(state): boolean {
      return state.settings?.feature_wallet_enabled ?? true
    },
    featureReferralEnabled(state): boolean {
      return state.settings?.feature_referral_enabled ?? false
    },
    featureAgentEnabled(state): boolean {
      return state.settings?.feature_agent_enabled ?? true
    },
    agentMcpDocsUrl(state): string {
      return state.settings?.agent_mcp_docs_url?.trim() || '/connect'
    },
    legalTermsEnabled(state): boolean {
      return state.settings?.legal_terms_enabled ?? false
    },
    legalTermsUpdatedAt(state): string {
      const raw = state.settings?.legal_terms_updated_at
      if (!raw) return ''
      return raw.slice(0, 10)
    },
    legalAgreements(state): LegalAgreementItem[] {
      const fromApi = state.settings?.legal_agreements
      if (fromApi?.length) return fromApi
      return []
    },
  },

  actions: {
    async fetchSettings(force = false) {
      if (this.loaded && !force) return
      if (this.loading) {
        await new Promise<void>((resolve) => {
          const timer = setInterval(() => {
            if (!this.loading) {
              clearInterval(timer)
              resolve()
            }
          }, 50)
        })
        return
      }
      this.loading = true
      try {
        this.settings = await getPublicPlatformSettings()
        this.loaded = true
      } catch {
        if (!this.settings) this.settings = { ...FALLBACK }
        this.loaded = true
      } finally {
        this.loading = false
      }
    },
  },
})
