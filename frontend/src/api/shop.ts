import { request } from './request'
import type { PaginatedData } from '@/types'

export interface ShopApplication {
  id: string
  shop_name: string
  agent_platform: string
  description: string
  status: 'pending' | 'approved' | 'rejected'
  review_note: string | null
  created_at: string
  reviewed_at: string | null
}

export interface ShopApplicationStatus {
  has_application: boolean
  is_seller: boolean
  application: ShopApplication | null
}

export function getShopApplicationStatus(): Promise<ShopApplicationStatus> {
  return request({ method: 'GET', url: '/shop/application' })
}

export function submitShopApplication(payload: {
  shop_name: string
  agent_platform: 'openclaw' | 'hermes' | 'other'
  description: string
}): Promise<ShopApplication> {
  return request({ method: 'POST', url: '/shop/application', data: payload })
}

export interface AdminShopApplicationItem {
  user_id: string
  email: string
  display_name: string
  shop_name: string
  agent_platform: string
  description: string
  status: 'pending' | 'approved' | 'rejected'
  review_note: string | null
  created_at: string
  reviewed_at: string | null
}

export function listAdminShopApplications(params?: {
  page?: number
  page_size?: number
  status?: string
}): Promise<PaginatedData<AdminShopApplicationItem>> {
  return request({
    method: 'GET',
    url: '/shop/admin/applications',
    params: {
      page: params?.page ?? 1,
      page_size: params?.page_size ?? 20,
      status: params?.status || undefined,
    },
  })
}

export function approveAdminShopApplication(userId: string): Promise<ShopApplication> {
  return request({ method: 'POST', url: `/shop/admin/applications/${userId}/approve` })
}

export function rejectAdminShopApplication(
  userId: string,
  reviewNote: string,
): Promise<ShopApplication> {
  return request({
    method: 'POST',
    url: `/shop/admin/applications/${userId}/reject`,
    data: { review_note: reviewNote },
  })
}
