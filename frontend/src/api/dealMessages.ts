import { request } from './request'
import type { DealMessage, DealMessageList } from '@/types'

export function listDealMessages(dealId: string): Promise<DealMessageList> {
  return request<DealMessageList>({
    method: 'GET',
    url: `/deals/${dealId}/messages`,
  })
}

export function postDealMessage(dealId: string, body: string): Promise<DealMessage> {
  return request<DealMessage>({
    method: 'POST',
    url: `/deals/${dealId}/messages`,
    data: { body },
  })
}
