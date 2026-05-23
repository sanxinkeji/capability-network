import { request } from './request'

export interface ApiKeyInfo {
  id: string
  platform_user_id: string
  name: string | null
  key_prefix: string
  status: string
  created_at: string
}

export interface ApiKeyCreated extends ApiKeyInfo {
  api_key: string
}

export function listApiKeys(): Promise<{ items: ApiKeyInfo[] }> {
  return request<{ items: ApiKeyInfo[] }>({ method: 'GET', url: '/agent/api-keys' })
}

export function createApiKey(payload: {
  platform_user_id: string
  name?: string
  rotate_key_id?: string
}): Promise<ApiKeyCreated> {
  return request<ApiKeyCreated>({
    method: 'POST',
    url: '/agent/api-keys',
    data: payload,
  })
}

export function revokeApiKey(keyId: string): Promise<ApiKeyInfo> {
  return request<ApiKeyInfo>({ method: 'DELETE', url: `/agent/api-keys/${keyId}` })
}
