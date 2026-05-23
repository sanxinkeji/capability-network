import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { usePlatformStore } from './platform'
import * as platformApi from '@/api/platform'
import type { PublicPlatformSettings } from '@/types'

vi.mock('@/api/platform', () => ({
  getPublicPlatformSettings: vi.fn(),
}))

const mockSettings: PublicPlatformSettings = {
  site_name: 'QA Platform',
  site_tagline: '  Tagline  ',
  site_announcement: '  Announcement  ',
  maintenance_mode: true,
  registration_mode: 'open',
  registration_invite_required: false,
  footer_text: '  Footer  ',
  custom_links_json: JSON.stringify([{ label: 'Docs', url: 'https://docs.test' }]),
  docs_url: 'https://docs.test',
  feature_marketplace_enabled: false,
  feature_matching_enabled: true,
  feature_wallet_enabled: true,
  feature_referral_enabled: true,
  feature_agent_enabled: false,
  agent_mcp_docs_url: 'https://mcp.test',
  legal_terms_enabled: true,
  legal_terms_updated_at: '2026-05-23T08:00:00Z',
  legal_agreements: [{ title: 'Terms', slug: 'terms', content: 'body' }],
}

describe('usePlatformStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.mocked(platformApi.getPublicPlatformSettings).mockReset()
  })

  it('uses fallback getters before settings load', () => {
    const store = usePlatformStore()
    expect(store.siteName).toBe('Capability Network')
    expect(store.maintenanceMode).toBe(false)
    expect(store.docsUrl).toBe('/docs')
    expect(store.featureReferralEnabled).toBe(false)
  })

  it('fetchSettings loads public settings from API', async () => {
    vi.mocked(platformApi.getPublicPlatformSettings).mockResolvedValue(mockSettings)
    const store = usePlatformStore()

    await store.fetchSettings()

    expect(store.loaded).toBe(true)
    expect(store.siteName).toBe('QA Platform')
    expect(store.siteTagline).toBe('Tagline')
    expect(store.announcement).toBe('Announcement')
    expect(store.maintenanceMode).toBe(true)
    expect(store.customLinks).toEqual([{ label: 'Docs', url: 'https://docs.test' }])
    expect(store.featureMarketplaceEnabled).toBe(false)
    expect(store.agentMcpDocsUrl).toBe('https://mcp.test')
    expect(store.legalTermsUpdatedAt).toBe('2026-05-23')
    expect(store.legalAgreements).toHaveLength(1)
  })

  it('skips duplicate fetch when already loaded', async () => {
    vi.mocked(platformApi.getPublicPlatformSettings).mockResolvedValue(mockSettings)
    const store = usePlatformStore()
    await store.fetchSettings()
    await store.fetchSettings()

    expect(platformApi.getPublicPlatformSettings).toHaveBeenCalledTimes(1)
  })

  it('force refresh re-fetches settings', async () => {
    vi.mocked(platformApi.getPublicPlatformSettings).mockResolvedValue(mockSettings)
    const store = usePlatformStore()
    await store.fetchSettings()
    await store.fetchSettings(true)

    expect(platformApi.getPublicPlatformSettings).toHaveBeenCalledTimes(2)
  })

  it('falls back when API fails and no cached settings', async () => {
    vi.mocked(platformApi.getPublicPlatformSettings).mockRejectedValue(new Error('network'))
    const store = usePlatformStore()

    await store.fetchSettings()

    expect(store.loaded).toBe(false)
    expect(store.siteName).toBe('Capability Network')
    expect(store.settings?.maintenance_mode).toBe(false)
  })
})
