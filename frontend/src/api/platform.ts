import { request } from './request'
import type { PublicPlatformSettings } from '@/types'

export function getPublicPlatformSettings(): Promise<PublicPlatformSettings> {
  return request<PublicPlatformSettings>({ method: 'GET', url: '/platform/settings' })
}
