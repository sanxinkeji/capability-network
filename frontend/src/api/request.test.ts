import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import MockAdapter from 'axios-mock-adapter'
import http, { request } from './request'
import { TOKEN_KEY } from '@/utils'

describe('request interceptors', () => {
  let mock: MockAdapter
  let locationHref = ''

  beforeEach(() => {
    mock = new MockAdapter(http)
    localStorage.clear()
    locationHref = ''
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: {
        pathname: '/market',
        get href() {
          return locationHref
        },
        set href(value: string) {
          locationHref = value
        },
      },
    })
  })

  afterEach(() => {
    mock.restore()
  })

  it('attaches Bearer token from localStorage on outgoing requests', async () => {
    localStorage.setItem(TOKEN_KEY, 'test-token')
    mock.onGet('/ping').reply((config) => {
      expect(config.headers?.Authorization).toBe('Bearer test-token')
      return [200, { code: 0, message: 'ok', data: { ok: true } }]
    })

    await request<{ ok: boolean }>({ method: 'GET', url: '/ping' })
  })

  it('rejects when API body code is non-zero', async () => {
    mock.onGet('/fail').reply(200, { code: 40001, message: '业务失败', data: null })

    await expect(request({ method: 'GET', url: '/fail' })).rejects.toThrow('业务失败')
  })

  it('returns data field on successful responses', async () => {
    mock.onGet('/ok').reply(200, { code: 0, message: 'ok', data: { value: 42 } })

    const data = await request<{ value: number }>({ method: 'GET', url: '/ok' })
    expect(data).toEqual({ value: 42 })
  })

  it('clears tokens and redirects to login on 401', async () => {
    localStorage.setItem(TOKEN_KEY, 'expired')
    localStorage.setItem('cn_refresh_token', 'refresh')
    mock.onGet('/protected').reply(401, { message: '未授权' })

    await expect(request({ method: 'GET', url: '/protected' })).rejects.toThrow('未授权')
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull()
    expect(localStorage.getItem('cn_refresh_token')).toBeNull()
    expect(locationHref).toBe('/login')
  })

  it('does not redirect on 401 when already on login page', async () => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { pathname: '/login', href: '' },
    })
    mock.onGet('/protected').reply(401, { message: '未授权' })

    await expect(request({ method: 'GET', url: '/protected' })).rejects.toThrow('未授权')
    expect(locationHref).toBe('')
  })

  it('maps 503 to friendly backend-unavailable message', async () => {
    mock.onGet('/down').reply(503, { message: 'Service Unavailable' })

    await expect(request({ method: 'GET', url: '/down' })).rejects.toThrow('无法连接后端服务')
  })
})
