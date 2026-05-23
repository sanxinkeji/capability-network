import { request } from './request'
import type { AuctionRoom } from '@/types'

export function getIntentAuction(intentId: string): Promise<AuctionRoom> {
  return request<AuctionRoom>({ method: 'GET', url: `/intents/${intentId}/auction` })
}

export function joinAuction(
  intentId: string,
  payload: { offer_id: string; match_log_id?: string },
): Promise<AuctionRoom> {
  return request<AuctionRoom>({
    method: 'POST',
    url: `/intents/${intentId}/auction/join`,
    data: payload,
  })
}

export function startAuction(intentId: string): Promise<AuctionRoom> {
  return request<AuctionRoom>({ method: 'POST', url: `/intents/${intentId}/auction/start` })
}

export function getAuction(auctionId: string): Promise<AuctionRoom> {
  return request<AuctionRoom>({ method: 'GET', url: `/auctions/${auctionId}` })
}

export function submitBid(auctionId: string, amountCents: number): Promise<AuctionRoom> {
  return request<AuctionRoom>({
    method: 'POST',
    url: `/auctions/${auctionId}/bid`,
    data: { amount_cents: amountCents },
  })
}

export function selectBid(auctionId: string, bidId: string): Promise<AuctionRoom> {
  return request<AuctionRoom>({
    method: 'POST',
    url: `/auctions/${auctionId}/select`,
    data: { bid_id: bidId },
  })
}
