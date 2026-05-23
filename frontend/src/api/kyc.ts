import { request } from './request'
import type { KycStatusInfo } from '@/types'

export function submitKyc(payload: {
  real_name: string
  id_number: string
}): Promise<KycStatusInfo> {
  return request<KycStatusInfo>({
    method: 'POST',
    url: '/users/kyc/submit',
    data: payload,
  })
}
