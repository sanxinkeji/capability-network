<template>
  <div class="admin-settings-page">
    <AdminPageHeader title="系统设置" subtitle="管理站点、注册、支付、邮件与备份等全局配置">
      <template #actions>
        <button class="btn btn-primary-admin" :disabled="saving || loading || !form" @click="save">
          {{ saving ? '保存中…' : '保存设置' }}
        </button>
      </template>
    </AdminPageHeader>

    <AdminAlert v-if="error" :message="error" type="error" />
    <AdminAlert v-if="success" :message="success" type="success" />

    <div class="admin-settings-panel">
      <AdminSettingsTabs v-model="activeTab" :tabs="tabs" />

      <div class="admin-settings-body">
        <LoadingSkeleton v-if="loading" :rows="4" />
        <template v-else-if="form">
          <AdminSettingsGeneralTab v-if="activeTab === 'general'" v-model="form" />
          <AdminSettingsLegalTab v-else-if="activeTab === 'legal'" v-model="form" />
          <AdminSettingsFeaturesTab v-else-if="activeTab === 'features'" v-model="form" />
          <AdminSettingsAgentTab v-else-if="activeTab === 'agent'" v-model="form" />
          <AdminSettingsSecurityTab v-else-if="activeTab === 'security'" v-model="form" />
          <AdminSettingsDefaultsTab v-else-if="activeTab === 'defaults'" v-model="form" />
          <AdminSettingsTradeTab v-else-if="activeTab === 'trade'" v-model="form" />
          <AdminSettingsPaymentTab
            v-else-if="activeTab === 'payment'"
            v-model="form"
            :provider-rows="providerRows"
            :payment="payment"
            @refresh="load"
          />
          <AdminSettingsEmailTab v-else-if="activeTab === 'email'" v-model="form" :payment="payment" />
          <AdminSettingsBackupTab v-else-if="activeTab === 'backup'" v-model="form" />
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getAdminSettings, updateAdminSettings } from '@/api/admin'
import { usePlatformStore } from '@/stores/platform'
import type { PaymentConfigInfo, PlatformSettings } from '@/types'
import { buildSettingsPayload, normalizeSettingsForm } from '@/composables/adminSettingsForm'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminSettingsTabs from '@/components/admin/AdminSettingsTabs.vue'
import AdminAlert from '@/components/admin/AdminAlert.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'
import AdminSettingsGeneralTab from '@/views/admin/settings/AdminSettingsGeneralTab.vue'
import AdminSettingsLegalTab from '@/views/admin/settings/AdminSettingsLegalTab.vue'
import AdminSettingsFeaturesTab from '@/views/admin/settings/AdminSettingsFeaturesTab.vue'
import AdminSettingsAgentTab from '@/views/admin/settings/AdminSettingsAgentTab.vue'
import AdminSettingsSecurityTab from '@/views/admin/settings/AdminSettingsSecurityTab.vue'
import AdminSettingsDefaultsTab from '@/views/admin/settings/AdminSettingsDefaultsTab.vue'
import AdminSettingsTradeTab from '@/views/admin/settings/AdminSettingsTradeTab.vue'
import AdminSettingsPaymentTab from '@/views/admin/settings/AdminSettingsPaymentTab.vue'
import AdminSettingsEmailTab from '@/views/admin/settings/AdminSettingsEmailTab.vue'
import AdminSettingsBackupTab from '@/views/admin/settings/AdminSettingsBackupTab.vue'

const tabs = [
  { id: 'general', label: '通用设置' },
  { id: 'legal', label: '登录条款' },
  { id: 'features', label: '功能开关' },
  { id: 'agent', label: 'Agent / MCP' },
  { id: 'security', label: '安全与认证' },
  { id: 'defaults', label: '用户默认值' },
  { id: 'trade', label: '交易参数' },
  { id: 'payment', label: '支付设置' },
  { id: 'email', label: '邮件设置' },
  { id: 'backup', label: '数据备份' },
]

const activeTab = ref('general')
const route = useRoute()
const platform = usePlatformStore()
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')
const form = ref<PlatformSettings | null>(null)
const payment = ref<PaymentConfigInfo | null>(null)

const providerRows = computed(() => {
  const p = payment.value
  if (!p) return []
  return [
    { id: 'easypay', name: 'EasyPay', configured: p.easypay_configured, callback: p.notify_easypay_url },
    { id: 'wechat', name: '微信直连', configured: p.wechat_configured, callback: p.notify_wechat_url },
    { id: 'alipay', name: '支付宝直连', configured: p.alipay_configured, callback: p.notify_alipay_url },
    { id: 'stripe', name: 'Stripe', configured: p.stripe_configured, callback: p.notify_stripe_url },
  ]
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await getAdminSettings()
    form.value = normalizeSettingsForm(data.settings)
    payment.value = data.payment
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!form.value) return
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    const data = await updateAdminSettings(buildSettingsPayload(form.value))
    form.value = normalizeSettingsForm(data.settings)
    payment.value = data.payment
    await platform.fetchSettings(true)
    success.value = '设置已保存，前台页面已同步更新'
  } catch (e) {
    error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

function resetScroll() {
  window.scrollTo(0, 0)
  document.documentElement.scrollLeft = 0
  document.body.scrollLeft = 0
}

onMounted(() => {
  const tab = route.query.tab
  if (typeof tab === 'string' && tabs.some((t) => t.id === tab)) {
    activeTab.value = tab
  }
  resetScroll()
  load()
})

watch(
  () => route.query.tab,
  (tab) => {
    if (typeof tab === 'string' && tabs.some((t) => t.id === tab)) {
      activeTab.value = tab
    }
  },
)

onUnmounted(resetScroll)
</script>

<style scoped>
.admin-settings-body {
  min-height: 480px;
  padding: 20px 24px 24px;
}
</style>
