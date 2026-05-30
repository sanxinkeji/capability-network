import { request } from './request'
import type { Deal } from '@/types'

export interface BuyFromOfferResult {
  deal: Deal
  intent_id: string
  offer_id: string
}

export function buyFromOffer(offerId: string, buyerNote?: string): Promise<BuyFromOfferResult> {
  return request<BuyFromOfferResult>({
    method: 'POST',
    url: '/deals/buy-from-offer',
    data: { offer_id: offerId, buyer_note: buyerNote || undefined },
  })
}
