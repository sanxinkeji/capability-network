<template>
  <div class="auth-page">
    <div class="auth-bg mesh-bg" aria-hidden="true" />
    <aside class="auth-panel">
      <h2>加入技能集市</h2>
      <p>注册即可逛 AI 集市，或开店接入 OpenClaw 让龙虾自动接单。</p>
      <ul class="auth-panel__features">
        <li>免费注册，即刻下单</li>
        <li>钱包充值，一键购买</li>
        <li>卖家可上架服务、接入 OpenClaw</li>
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

        <h1>注册</h1>
        <p class="subtitle">创建账号，开始逛集市或申请开店</p>

        <LoadingSkeleton v-if="policyLoading" :rows="2" />

        <template v-else>
          <div v-if="registrationClosed" class="auth-alert auth-alert--warn" role="status">
            <span>平台当前未开放新用户注册，如需账号请联系管理员。</span>
          </div>
          <p v-else-if="inviteRequired" class="auth-hint">
            当前注册需要有效邀请码，请向管理员索取。
          </p>
          <p v-else class="auth-hint">
            注册后建议先到
            <RouterLink to="/app/wallet?welcome=1">钱包充值</RouterLink>
            便于下单支付。
          </p>

          <div v-if="error" class="auth-alert auth-alert--error" role="alert">
            <span>{{ error }}</span>
          </div>

          <form v-if="!registrationClosed" class="auth-form" @submit.prevent="handleSubmit">
            <div class="form-group">
              <label for="reg-email">邮箱</label>
              <input
                id="reg-email"
                v-model="email"
                type="email"
                required
                autocomplete="email"
                placeholder="user@example.com"
              />
            </div>
            <div class="form-group">
              <label for="reg-password">密码</label>
              <input
                id="reg-password"
                v-model="password"
                type="password"
                required
                minlength="8"
                autocomplete="new-password"
                placeholder="至少 8 位"
              />
            </div>
            <div v-if="inviteRequired" class="form-group">
              <label for="reg-invite">邀请码</label>
              <input
                id="reg-invite"
                v-model="inviteCode"
                type="text"
                required
                autocomplete="off"
                placeholder="请输入邀请码"
              />
            </div>
            <LegalAgreementNotice
              v-if="legalTermsEnabled"
              v-model="termsAccepted"
              mode="checkbox"
            />
            <button
              class="btn btn-lg auth-submit"
              type="submit"
              :disabled="auth.loading || (legalTermsEnabled && !termsAccepted)"
            >
              {{ auth.loading ? '注册中…' : '创建账号' }}
            </button>
          </form>
        </template>

        <footer class="auth-footer">
          <p>已有账号？<RouterLink to="/login">登录</RouterLink></p>
          <RouterLink to="/" class="auth-back">← 返回官网</RouterLink>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePlatformStore } from '@/stores/platform'
import type { RegistrationMode } from '@/types'
import AppIcon from '@/components/AppIcon.vue'
import LegalAgreementNotice from '@/components/LegalAgreementNotice.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'

const auth = useAuthStore()
const platform = usePlatformStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const inviteCode = ref('')
const termsAccepted = ref(false)
const error = ref('')
const policyLoading = ref(true)
const registrationMode = ref<RegistrationMode>('open')
const registrationInviteRequired = ref(false)

const registrationClosed = computed(() => registrationMode.value === 'closed')
const inviteRequired = computed(
  () => registrationMode.value === 'invite_only' || registrationInviteRequired.value,
)
const legalTermsEnabled = computed(() => platform.legalTermsEnabled)

onMounted(async () => {
  try {
    await platform.fetchSettings()
    registrationMode.value = platform.settings?.registration_mode ?? 'open'
    registrationInviteRequired.value = platform.settings?.registration_invite_required ?? false
  } catch {
    registrationMode.value = 'open'
    registrationInviteRequired.value = false
  } finally {
    policyLoading.value = false
  }
})

async function handleSubmit() {
  error.value = ''
  if (!email.value.trim()) {
    error.value = '请填写邮箱'
    return
  }
  if (inviteRequired.value && !inviteCode.value.trim()) {
    error.value = '请填写邀请码'
    return
  }
  if (legalTermsEnabled.value && !termsAccepted.value) {
    error.value = '请先阅读并同意相关协议'
    return
  }
  try {
    const result = await auth.register({
      email: email.value.trim(),
      password: password.value,
      invite_code: inviteCode.value.trim() || undefined,
    })
    if (result.verificationRequired) {
      router.push({ name: 'login', query: { verify: result.email } })
      return
    }
    router.push('/app/wallet?welcome=1')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '注册失败'
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
.auth-hint {
  margin: 0 0 16px;
  font-size: 14px;
  color: var(--color-label-secondary);
  line-height: 1.45;
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
.auth-alert--warn {
  background: rgba(255, 149, 0, 0.08);
  color: #c93400;
  border: 1px solid rgba(255, 149, 0, 0.18);
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
