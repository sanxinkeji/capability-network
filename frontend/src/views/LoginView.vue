<template>
  <div class="auth-page">
    <div class="mesh-bg" aria-hidden="true" />
    <header class="auth-nav">
      <RouterLink to="/" class="brand">
        <AppIcon name="logo" size="md" filled class="brand-icon" />
        {{ platform.siteName }}
      </RouterLink>
    </header>
    <div class="auth-card glass-card">
      <h1>登录</h1>
      <p class="subtitle">买方发需求、卖方发供给，订单资金由平台托管</p>

      <HelpTip v-if="isDev" title="演示账号（仅本地开发）">
        买方 <code>buyer_qa@test.com</code> · 卖方 <code>seller_qa@test.com</code> · 密码均为 <code>password123</code>
      </HelpTip>

      <div v-if="error" class="error-msg">{{ error }}</div>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>账号（邮箱或手机）</label>
          <input v-model="account" type="text" required placeholder="请输入邮箱或手机号" />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="password" type="password" required placeholder="至少 8 位" />
        </div>
        <button class="btn btn-commerce" type="submit" :disabled="auth.loading" style="width: 100%">
          {{ auth.loading ? '登录中…' : '登录' }}
        </button>
        <LegalAgreementNotice v-if="legalTermsEnabled" mode="text" tag="p" />
      </form>

      <p class="footer-link">
        还没有账号？<RouterLink to="/register">免费注册</RouterLink>
      </p>
      <p class="footer-link">
        <RouterLink to="/">← 返回官网</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePlatformStore } from '@/stores/platform'
import AppIcon from '@/components/AppIcon.vue'
import HelpTip from '@/components/HelpTip.vue'
import LegalAgreementNotice from '@/components/LegalAgreementNotice.vue'

const auth = useAuthStore()
const platform = usePlatformStore()
const router = useRouter()
const route = useRoute()

const account = ref('')
const password = ref('')
const error = ref('')

const legalTermsEnabled = computed(() => platform.legalTermsEnabled)
const isDev = import.meta.env.DEV

onMounted(() => {
  platform.fetchSettings()
})

async function handleSubmit() {
  error.value = ''
  try {
    await auth.login(account.value, password.value)
    let redirect = (route.query.redirect as string) || (auth.isAdmin ? '/admin' : '/app/market')
    if (redirect.includes('mode=ai') || redirect.includes('mode%3Dai')) {
      redirect = '/app/intents/new?mode=ai'
    }
    router.push(redirect)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '登录失败'
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
}

.auth-nav {
  position: absolute;
  top: 20px;
  left: 24px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 17px;
  color: var(--color-label);
  text-decoration: none;
}

.brand-icon {
  color: var(--color-primary);
}

.auth-card {
  width: 100%;
  max-width: 420px;
  margin-top: 40px;
}

.auth-card h1 {
  margin: 0 0 4px;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.subtitle {
  margin: 0 0 24px;
  color: var(--color-label-secondary);
  font-size: 15px;
}

.footer-link {
  margin-top: 16px;
  text-align: center;
  color: var(--color-label-tertiary);
  font-size: 15px;
}

.footer-hint {
  margin-top: 8px;
  text-align: center;
  color: var(--color-label-tertiary);
  font-size: 12px;
}
</style>
