import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getMe, login as apiLogin, register as apiRegister } from '@/api'
import { REFRESH_TOKEN_KEY, TOKEN_KEY } from '@/utils'
import type { UserProfile } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const user = ref<UserProfile | null>(null)
  const loading = ref(false)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  function setTokens(access: string, refresh: string) {
    token.value = access
    localStorage.setItem(TOKEN_KEY, access)
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }

  async function login(account: string, password: string) {
    loading.value = true
    try {
      const tokens = await apiLogin({ account, password })
      setTokens(tokens.access_token, tokens.refresh_token)
      user.value = await getMe()
    } finally {
      loading.value = false
    }
  }

  async function register(payload: {
    email: string
    password: string
    display_name?: string
    invite_code?: string
  }) {
    loading.value = true
    try {
      const result = await apiRegister(payload)
      if (result.verification_required) {
        return { verificationRequired: true as const, email: result.email ?? payload.email }
      }
      if (!result.access_token || !result.refresh_token) {
        throw new Error('注册响应无效')
      }
      setTokens(result.access_token, result.refresh_token)
      user.value = await getMe()
      return { verificationRequired: false as const }
    } finally {
      loading.value = false
    }
  }

  async function fetchProfile() {
    if (!token.value) return
    user.value = await getMe()
  }

  return {
    token,
    user,
    loading,
    isLoggedIn,
    isAdmin,
    login,
    register,
    logout,
    fetchProfile,
  }
})
