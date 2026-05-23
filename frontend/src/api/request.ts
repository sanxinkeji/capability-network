import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'
import { TOKEN_KEY } from '@/utils'
import type { ApiResponse } from '@/types'

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const http: AxiosInstance = axios.create({
  baseURL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => {
    const body = response.data as ApiResponse
    if (body && typeof body.code === 'number' && body.code !== 0) {
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    return response
  },
  (error) => {
    const status = error.response?.status as number | undefined
    const body = error.response?.data as { message?: string } | undefined
    let message = body?.message || error.message || '网络错误'
    const isDev = import.meta.env.DEV
    if (status === 500 && message === 'Request failed with status code 500') {
      message = isDev
        ? '服务器内部错误：请确认后端已启动（http://127.0.0.1:8000/health）后重试'
        : '服务器内部错误，请稍后重试或联系管理员'
    } else if (status === 404) {
      message = isDev
        ? '接口不存在（404）：请重启后端以加载最新代码：cd backend && python -m uvicorn app.main:app --reload --port 8000'
        : '请求的服务暂不可用，请稍后重试'
    } else if (status === 502 || status === 503) {
      message = isDev
        ? '无法连接后端服务，请先启动：cd backend && python -m uvicorn app.main:app --reload --port 8000'
        : '服务暂时不可用，请稍后重试'
    } else if (status === 405) {
      message = isDev
        ? '接口方法不允许（405）：请重启后端服务以加载最新 Agent Key 接口，或确认已部署最新 backend 代码'
        : '请求方法不允许，请联系管理员'
    } else if (status === 409 || status === 403) {
      message = body?.message || message
    }
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem('cn_refresh_token')
      if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/register')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(new Error(message))
  },
)

export async function request<T>(config: AxiosRequestConfig): Promise<T> {
  const response = await http.request<ApiResponse<T>>(config)
  return response.data.data
}

export default http
