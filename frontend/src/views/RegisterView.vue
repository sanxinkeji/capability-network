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
      <h1>注册</h1>
      <p class="subtitle">使用邮箱创建账号，开始发布需求或供给</p>

      <LoadingSkeleton v-if="policyLoading" :rows="2" />

      <template v-else>
        <HelpTip v-if="registrationClosed" variant="warn" title="注册已关闭">
          平台当前未开放新用户注册，如需账号请联系管理员。
        </HelpTip>
        <HelpTip v-else-if="inviteRequired" title="邀请码注册">
          当前注册需要有效邀请码，请向管理员索取。
        </HelpTip>
        <HelpTip v-else>
          只需邮箱和密码即可注册。注册后建议先到
          <RouterLink to="/app/wallet?welcome=1">钱包充值</RouterLink>
          便于下单支付。
        </HelpTip>

        <div v-if="error" class="error-msg">{{ error }}</div>

        <form v-if="!registrationClosed" @submit.prevent="handleSubmit">
          <div class="form-group">
            <label>邮箱</label>
            <input v-model="email" type="email" required autocomplete="email" placeholder="user@example.com" />
          </div>
          <div class="form-group">
            <label>密码</label>
            <input v-model="password" type="password" required minlength="8" autocomplete="new-password" placeholder="至少 8 位" />
          </div>
          <div v-if="inviteRequired" class="form-group">
            <label>邀请码</label>
            <input v-model="inviteCode" type="text" required autocomplete="off" placeholder="请输入邀请码" />
          </div>
          <LegalAgreementNotice
            v-if="legalTermsEnabled"
            v-model="termsAccepted"
            mode="checkbox"
          />
          <button
            class="btn btn-commerce"
            type="submit"
            :disabled="auth.loading || (legalTermsEnabled && !termsAccepted)"
            style="width: 100%"
          >
            {{ auth.loading ? '注册中…' : '创建账号' }}
          </button>
        </form>
      </template>

      <p class="footer-link">已有账号？<RouterLink to="/login">登录</RouterLink></p>
      <p class="footer-link"><RouterLink to="/">← 返回官网</RouterLink></p>
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
import HelpTip from '@/components/HelpTip.vue'
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
</style>
