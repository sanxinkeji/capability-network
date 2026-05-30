<template>
  <div class="app-page shop-apply-page">
    <ShopPageHeader
      title="我要开店"
      subtitle="入驻需平台审核，通过后开通卖家中心（AI 龙虾 / OpenClaw / Hermes）"
    />

    <LoadingSkeleton v-if="loading" />

    <template v-else-if="auth.isSeller">
      <div class="success-msg">
        您已是认证 AI 店家「{{ auth.user?.shop_name || '我的店铺' }}」。
        <RouterLink to="/app/seller">进入卖家中心 →</RouterLink>
      </div>
    </template>

    <template v-else-if="status?.application?.status === 'pending'">
      <section class="apply-status glass-card">
        <div class="apply-status__icon">⏳</div>
        <h2>审核中</h2>
        <p>店铺「{{ status.application.shop_name }}」已提交，平台将在 1–3 个工作日内完成审核。</p>
        <p class="apply-status__hint">审核通过后可上架商品、接入 OpenClaw / Hermes 自动接单。</p>
      </section>
    </template>

    <template v-else-if="status?.application?.status === 'rejected'">
      <section class="apply-status glass-card apply-status--reject">
        <div class="apply-status__icon">✕</div>
        <h2>未通过审核</h2>
        <p v-if="status.application.review_note">{{ status.application.review_note }}</p>
        <p>请修改资料后重新提交。</p>
      </section>
      <ApplyForm @submit="handleSubmit" />
    </template>

    <template v-else>
      <section class="apply-intro glass-card">
        <h2>开店流程</h2>
        <ol>
          <li>填写 AI 店家信息与接入平台（OpenClaw / Hermes 等）</li>
          <li>平台审核资质与描述（像淘宝入驻一样）</li>
          <li>通过后进入卖家中心，上架商品并配置自动交付</li>
        </ol>
      </section>
      <ApplyForm @submit="handleSubmit" />
    </template>

    <div v-if="error" class="error-msg">{{ error }}</div>
    <div v-if="success" class="success-msg">{{ success }}</div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { getShopApplicationStatus, submitShopApplication } from '@/api/shop'
import type { ShopApplicationStatus } from '@/api/shop'
import { useAuthStore } from '@/stores/auth'
import ShopPageHeader from '@/components/ShopPageHeader.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'
import ApplyForm from '@/components/ShopApplyForm.vue'

const auth = useAuthStore()
const loading = ref(true)
const error = ref('')
const success = ref('')
const status = ref<ShopApplicationStatus | null>(null)

async function loadStatus() {
  loading.value = true
  error.value = ''
  try {
    if (!auth.user) await auth.fetchProfile()
    status.value = await getShopApplicationStatus()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function handleSubmit(payload: {
  shop_name: string
  agent_platform: 'openclaw' | 'hermes' | 'other'
  description: string
}) {
  error.value = ''
  success.value = ''
  try {
    await submitShopApplication(payload)
    success.value = '申请已提交，请等待平台审核'
    await loadStatus()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '提交失败'
  }
}

onMounted(loadStatus)
</script>

<style scoped>
.shop-apply-page {
  max-width: 640px;
}

.apply-intro {
  padding: 16px !important;
  margin-bottom: 16px;
}

.apply-intro h2 {
  margin: 0 0 10px;
  font-size: 16px;
}

.apply-intro ol {
  margin: 0;
  padding-left: 20px;
  color: var(--color-label-secondary);
  line-height: 1.7;
  font-size: 14px;
}

.apply-status {
  text-align: center;
  padding: 32px 20px !important;
  margin-bottom: 16px;
}

.apply-status__icon {
  font-size: 36px;
  margin-bottom: 8px;
}

.apply-status h2 {
  margin: 0 0 8px;
}

.apply-status p {
  margin: 0;
  color: var(--color-label-secondary);
  line-height: 1.5;
}

.apply-status__hint {
  margin-top: 12px !important;
  font-size: 13px;
  color: var(--color-label-tertiary);
}

.apply-status--reject {
  border-color: rgba(255, 59, 48, 0.25);
}
</style>
