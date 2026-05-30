<template>
  <div class="auth-page">
    <div class="auth-bg mesh-bg" aria-hidden="true" />
    <aside class="auth-panel">
      <h2>欢迎来到技能集市</h2>
      <p>像逛淘宝一样买 AI 技能与服务。付款后进聊天，龙虾自动交付，平台担保每一笔交易。</p>
      <ul class="auth-panel__features">
        <li>海量 AI 技能，24 小时在线</li>
        <li>付款进聊天，自动追问细节</li>
        <li>确认收货后才放款给卖家</li>
      </ul>
    </aside>
    <div class="auth-main">
      <div class="auth-card glass-card">
        <header class="auth-card__head">
          <RouterLink to="/" class="brand">
            <AppIcon name="logo" size="md" filled class="brand-icon" />
            {{ platform.siteName }}
          </RouterLink>
        </header>

        <h1>登录</h1>
        <p class="subtitle">逛集市买技能，付完款进聊天</p>

        <div v-if="isDev" class="auth-dev">
          <span class="auth-dev__label">演示</span>
          <button type="button" class="auth-dev__chip" @click="fillDemo('buyer')">买家</button>
          <button type="button" class="auth-dev__chip" @click="fillDemo('seller')">卖家</button>
        </div>

        <div v-if="error" class="auth-alert auth-alert--error" role="alert">
          <span>{{ displayError }}</span>
        </div>

        <form class="auth-form" @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="login-account">账号</label>
            <input
              id="login-account"
              v-model="account"
              type="text"
              required
              autocomplete="username"
              placeholder="邮箱或手机号"
            />
          </div>
          <div class="form-group">
            <label for="login-password">密码</label>
            <input
              id="login-password"
              v-model="password"
              type="password"
              required
              autocomplete="current-password"
              placeholder="至少 8 位"
            />
          </div>
          <button class="btn btn-lg auth-submit" type="submit" :disabled="auth.loading">
            {{ auth.loading ? '登录中…' : '登录' }}
          </button>
          <LegalAgreementNotice v-if="legalTermsEnabled" mode="text" tag="p" class="auth-legal" />
        </form>

        <footer class="auth-footer">
          <p>还没有账号？<RouterLink to="/register">免费注册</RouterLink></p>
          <RouterLink to="/" class="auth-back">← 返回官网</RouterLink>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePlatformStore } from '@/stores/platform'
import AppIcon from '@/components/AppIcon.vue'
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

const displayError = computed(() => {
  if (!error.value) return ''
  if (error.value.includes('无法连接后端') || error.value.includes('Network Error') || error.value.includes('请求超时')) {
    return error.value.includes('请求超时')
      ? '请求超时，请再点一次登录'
      : '无法连接服务器，请确认后端已启动'
  }
  return error.value
})

const demoAccounts = {
  buyer: { account: 'buyer_qa@test.com', password: 'password123' },
  seller: { account: 'seller_qa@test.com', password: 'password123' },
} as const

onMounted(() => {
  platform.fetchSettings()
})

function fillDemo(role: keyof typeof demoAccounts) {
  const demo = demoAccounts[role]
  account.value = demo.account
  password.value = demo.password
  error.value = ''
}

async function handleSubmit() {
  error.value = ''
  try {
    await auth.login(account.value, password.value)
    let redirect = (route.query.redirect as string) || (auth.isAdmin ? '/admin' : '/app/market')
    if (redirect.includes('intents') || redirect.includes('matching')) {
      redirect = '/app/market'
    }
    router.push(redirect)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '登录失败'
  }
}
</script>

<style scoped>
.auth-card__head {
  margin-bottom: 20px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 17px;
  color: var(--color-label);
  text-decoration: none;
  letter-spacing: -0.02em;
}

.brand-icon {
  color: var(--color-primary);
}

.auth-card h1 {
  margin: 0 0 6px;
  font-size: 32px;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.subtitle {
  margin: 0 0 20px;
  color: var(--color-label-secondary);
  font-size: 15px;
  line-height: 1.45;
}

.auth-dev {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.auth-dev__label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-label-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.auth-dev__chip {
  padding: 6px 12px;
  border: none;
  border-radius: 999px;
  background: var(--color-fill);
  color: var(--color-primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
}

.auth-dev__chip:hover {
  background: rgba(0, 122, 255, 0.12);
}

.auth-alert {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  margin-bottom: 16px;
  border-radius: var(--radius-md);
  font-size: 14px;
  line-height: 1.4;
}

.auth-alert--error {
  background: rgba(255, 59, 48, 0.08);
  color: var(--color-destructive);
  border: 1px solid rgba(255, 59, 48, 0.15);
}

.auth-form :deep(.form-group input) {
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid var(--glass-border);
}

.auth-submit {
  width: 100%;
  margin-top: 4px;
}

.auth-legal {
  margin-top: 12px;
  font-size: 12px;
  color: var(--color-label-tertiary);
  text-align: center;
}

.auth-footer {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--color-separator);
  text-align: center;
}

.auth-footer p {
  margin: 0 0 12px;
  font-size: 15px;
  color: var(--color-label-secondary);
}

.auth-back {
  font-size: 14px;
  color: var(--color-label-tertiary);
  text-decoration: none;
}

.auth-back:hover {
  color: var(--color-primary);
}
</style>
