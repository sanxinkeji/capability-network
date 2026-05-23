<template>
  <div>
    <AdminPageHeader title="订单详情" subtitle="仲裁操作与交付信息">
      <template #actions>
        <RouterLink to="/admin/deals" class="btn btn-secondary btn-sm">返回列表</RouterLink>
      </template>
    </AdminPageHeader>

    <div v-if="error" class="error-msg">{{ error }}</div>
    <LoadingSkeleton v-if="loading" :rows="3" />

    <template v-else-if="deal">
      <div v-if="deal.status === 'disputed'" class="admin-dispute-banner">
        争议订单 — {{ deal.dispute_reason || '无争议说明' }}
      </div>

      <StatusStepper :status="deal.status" />

      <p class="grouped-section-label">订单信息</p>
      <div class="admin-list">
        <GroupedList>
          <div class="admin-list-row admin-list-row--detail">
            <span class="detail-label">金额</span>
            <span class="detail-value">{{ formatCents(deal.amount_cents, deal.currency) }}</span>
          </div>
          <div class="admin-list-row admin-list-row--detail">
            <span class="detail-label">状态</span>
            <span :class="badgeClass(deal.status)">{{ statusLabel(deal.status) }}</span>
          </div>
          <div class="admin-list-row admin-list-row--detail">
            <span class="detail-label">创建时间</span>
            <span class="detail-value">{{ formatDate(deal.created_at) }}</span>
          </div>
          <div v-if="deal.completed_at" class="admin-list-row admin-list-row--detail">
            <span class="detail-label">完成时间</span>
            <span class="detail-value">{{ formatDate(deal.completed_at) }}</span>
          </div>
        </GroupedList>
      </div>

      <p class="grouped-section-label">关联 ID</p>
      <div class="admin-list">
        <GroupedList>
          <div class="admin-list-row admin-list-row--detail">
            <span class="detail-label">订单 ID</span>
            <code class="detail-code">{{ deal.id }}</code>
          </div>
          <div class="admin-list-row admin-list-row--detail">
            <span class="detail-label">买方</span>
            <code class="detail-code">{{ deal.buyer_id }}</code>
          </div>
          <div class="admin-list-row admin-list-row--detail">
            <span class="detail-label">卖方</span>
            <code class="detail-code">{{ deal.seller_id }}</code>
          </div>
        </GroupedList>
      </div>

      <template v-if="deal.delivery_text || deal.delivery_payload_url">
        <p class="grouped-section-label">交付内容</p>
        <div class="admin-form-card">
          <p v-if="deal.delivery_text" class="delivery-text">{{ deal.delivery_text }}</p>
          <a v-if="deal.delivery_payload_url" :href="deal.delivery_payload_url" target="_blank">
            查看交付物
          </a>
        </div>
      </template>

      <div v-if="canRefund" class="admin-action-card">
        <p class="grouped-section-label">仲裁操作</p>
        <button class="btn btn-danger" :disabled="refunding" @click="handleRefund">
          {{ refunding ? '处理中…' : '退款给买方' }}
        </button>
        <p class="form-hint">争议仲裁：全额退款并关闭订单</p>
      </div>

      <div v-if="canConfirm" class="admin-action-card">
        <button class="btn btn-lg" :disabled="confirming" @click="handleConfirm">
          {{ confirming ? '确认中…' : '代买方确认收货' }}
        </button>
        <p class="form-hint">已交付订单，确认后结算给卖方</p>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { getAdminDeal } from '@/api/admin'
import { confirmDeal, refundDeal } from '@/api/deals'
import type { Deal } from '@/types'
import { formatCents, formatDate, statusLabel } from '@/utils'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import GroupedList from '@/components/GroupedList.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'
import StatusStepper from '@/components/StatusStepper.vue'

const route = useRoute()
const dealId = route.params.dealId as string

const deal = ref<Deal | null>(null)
const loading = ref(true)
const error = ref('')
const refunding = ref(false)
const confirming = ref(false)

const canRefund = computed(() => deal.value?.status === 'disputed')
const canConfirm = computed(() => deal.value?.status === 'delivered')

function badgeClass(status: string) {
  const map: Record<string, string> = {
    pending: 'badge badge-delivered',
    in_progress: 'badge badge-open',
    delivered: 'badge badge-delivered',
    completed: 'badge badge-completed',
    disputed: 'badge badge-default',
  }
  return map[status] ?? 'badge badge-default'
}

async function loadDeal() {
  loading.value = true
  error.value = ''
  try {
    deal.value = await getAdminDeal(dealId)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function handleRefund() {
  if (!confirm('确认对该争议单执行全额退款？')) return
  refunding.value = true
  error.value = ''
  try {
    deal.value = await refundDeal(dealId)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '退款失败'
  } finally {
    refunding.value = false
  }
}

async function handleConfirm() {
  if (!confirm('确认代买方验收并完成结算？')) return
  confirming.value = true
  error.value = ''
  try {
    deal.value = await confirmDeal(dealId)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '确认失败'
  } finally {
    confirming.value = false
  }
}

onMounted(loadDeal)
</script>

<style scoped>
.detail-label {
  font-size: 14px;
  color: var(--color-label);
}

.detail-value {
  font-size: 14px;
  color: var(--color-label-secondary);
}

.detail-code {
  font-size: 12px;
  background: #f5f5f5;
  padding: 4px 8px;
  border-radius: 6px;
  word-break: break-all;
  max-width: 60%;
  text-align: right;
}

.delivery-text {
  margin: 0 0 8px;
  font-size: 14px;
  white-space: pre-wrap;
  line-height: 1.5;
}

.form-hint {
  margin-top: 8px;
  font-size: 13px;
  color: var(--color-label-tertiary);
}
</style>
