import { request } from './request'
import type { Deal, PaginatedData } from '@/types'

export function listDeals(params?: {
  page?: number
  page_size?: number
}): Promise<PaginatedData<Deal>> {
  return request<PaginatedData<Deal>>({
    method: 'GET',
    url: '/deals',
    params: { page: params?.page ?? 1, page_size: params?.page_size ?? 20 },
  })
}

export function getDeal(dealId: string): Promise<Deal> {
  return request<Deal>({ method: 'GET', url: `/deals/${dealId}` })
}

export function createDeal(payload: {
  match_log_id?: string
  intent_id?: string
  offer_id?: string
}): Promise<Deal> {
  return request<Deal>({
    method: 'POST',
    url: '/deals',
    data: payload,
  })
}

export function confirmDeal(dealId: string): Promise<Deal> {
  return request<Deal>({ method: 'POST', url: `/deals/${dealId}/confirm`, data: {} })
}

export function payDeal(dealId: string): Promise<Deal> {
  return request<Deal>({ method: 'POST', url: `/deals/${dealId}/pay`, data: {} })
}

export function deliverDeal(dealId: string, payload: { text: string }): Promise<Deal> {
  return request<Deal>({
    method: 'POST',
    url: `/deals/${dealId}/deliver`,
    data: payload,
  })
}

export function refundDeal(dealId: string): Promise<Deal> {
  return request<Deal>({ method: 'POST', url: `/deals/${dealId}/refund`, data: {} })
}

export function disputeDeal(dealId: string, disputeReason: string): Promise<Deal> {
  return request<Deal>({
    method: 'POST',
    url: `/deals/${dealId}/dispute`,
    data: { dispute_reason: disputeReason },
  })
}
