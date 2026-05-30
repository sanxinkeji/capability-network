import { request } from './request'
import type {
  Intent,
  IntentCreatePayload,
  IntentParseResult,
  MarketplaceOffer,
  MatchRunResult,
  Offer,
  OfferChannel,
  OfferCreatePayload,
  PaginatedData,
  RegisterResponse,
  TokenResponse,
  UserProfile,
} from '@/types'

export function register(payload: {
  email: string
  password: string
  display_name?: string
  invite_code?: string
}): Promise<RegisterResponse> {
  return request<RegisterResponse>({ method: 'POST', url: '/auth/register', data: payload })
}

export function login(payload: { account: string; password: string }): Promise<TokenResponse> {
  return request<TokenResponse>({ method: 'POST', url: '/auth/login', data: payload })
}

export function getMe(): Promise<UserProfile> {
  return request<UserProfile>({ method: 'GET', url: '/users/me' })
}

export function listOffers(params?: {
  status?: string
  page?: number
  page_size?: number
}): Promise<PaginatedData<Offer>> {
  return request<PaginatedData<Offer>>({ method: 'GET', url: '/offers', params })
}

export function createOffer(payload: OfferCreatePayload): Promise<Offer> {
  return request<Offer>({ method: 'POST', url: '/offers', data: payload })
}

export function publishOffer(offerId: string): Promise<Offer> {
  return request<Offer>({ method: 'POST', url: `/offers/${offerId}/publish` })
}

export function listIntents(): Promise<Intent[]> {
  return request<Intent[]>({ method: 'GET', url: '/intents' })
}

export function createIntent(payload: IntentCreatePayload): Promise<Intent> {
  return request<Intent>({ method: 'POST', url: '/intents', data: payload })
}

export function parseIntent(text: string): Promise<IntentParseResult> {
  return request<IntentParseResult>({ method: 'POST', url: '/intents/parse', data: { text } })
}

export function listMarketplaceOffers(params?: {
  category?: string
  channel?: OfferChannel
  page?: number
  page_size?: number
}): Promise<PaginatedData<Offer>> {
  return request<PaginatedData<Offer>>({ method: 'GET', url: '/offers/marketplace', params })
}

export function getMarketplaceOffer(offerId: string): Promise<MarketplaceOffer> {
  return request<MarketplaceOffer>({ method: 'GET', url: `/offers/marketplace/${offerId}` })
}

export function getIntent(intentId: string): Promise<Intent> {
  return request<Intent>({ method: 'GET', url: `/intents/${intentId}` })
}

export function runMatching(intentId: string, topN = 5): Promise<MatchRunResult> {
  return request<MatchRunResult>({
    method: 'POST',
    url: '/matching/run',
    data: { intent_id: intentId, top_n: topN },
  })
}
