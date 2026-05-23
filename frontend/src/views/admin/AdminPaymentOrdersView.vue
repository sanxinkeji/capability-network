<template>
  <div>
    <AdminPageHeader title="订单记录" subtitle="充值支付订单，支持筛选与详情查看" />

    <AdminAlert v-if="error" :message="error" type="error" />
    <AdminAlert v-if="success" :message="success" type="success" />

    <AdminDataTable :loading="loading" :error="listError" :empty="!loading && !listError && orders.length === 0">
      <template #toolbar>
        <div class="admin-toolbar admin-toolbar--wide" style="margin: 0; padding: 0; border: none; box-shadow: none">
          <input v-model="search" type="search" placeholder="搜索订单号 / 用户邮箱" @keyup.enter="reload" />
          <select v-model="statusFilter" @change="reload">
            <option value="">全部状态</option>
            <option value="pending">待支付</option>
            <option value="paid">已到账</option>
            <option value="refunded">已退款</option>
            <option value="failed">失败</option>
            <option value="expired">已过期</option>
          </select>
          <select v-model="channelFilter" @change="reload">
            <option value="">全部支付方式</option>
            <option value="alipay">支付宝</option>
            <option value="wechat">微信支付</option>
            <option value="stripe">Stripe</option>
            <option value="easypay">EasyPay</option>
          </select>
          <button class="btn btn-secondary btn-sm" @click="reload">刷新</button>
        </div>
      </template>

      <template #empty>
        <EmptyState icon="wallet">暂无订单记录</EmptyState>
      </template>

      <template #head>
        <tr>
          <th>订单 ID</th>
          <th>订单编号</th>
          <th>用户</th>
          <th>实付</th>
          <th>支付方式</th>
          <th>状态</th>
          <th>创建时间</th>
          <th style="text-align: right">操作</th>
        </tr>
      </template>

      <tr v-for="(order, idx) in orders" :key="order.id">
        <td><span class="admin-order-id">#{{ rowNumber(idx) }}</span></td>
        <td class="mono-cell">{{ order.provider_ref }}</td>
        <td>
          <div class="admin-user-cell">
            <span class="admin-user-cell__avatar">{{ userInitial(order.user_email) }}</span>
            <span>{{ order.user_email || '—' }}</span>
          </div>
        </td>
        <td><strong>{{ formatCents(order.amount_cents, order.currency) }}</strong></td>
        <td>{{ channelLabel(order.channel) }}</td>
        <td><span class="admin-tag" :class="statusClass(order.status)">{{ statusLabel(order.status) }}</span></td>
        <td>{{ formatDate(order.created_at) }}</td>
        <td style="text-align: right">
          <div class="admin-row-actions">
            <button type="button" class="admin-icon-btn" title="查看" @click="viewOrder(order)">
              <AppIcon name="eye" size="sm" />
            </button>
            <button
              v-if="order.status === 'paid'"
              type="button"
              class="admin-icon-btn admin-icon-btn--danger"
              title="退款"
              :disabled="actingId === order.id"
              @click="openRefund(order)"
            >
              <AppIcon name="refresh" size="sm" />
            </button>
          </div>
        </td>
      </tr>

      <template #footer>
        <AdminPager v-model:page="page" :page-size="pageSize" :total="total" @update:page="loadOrders" />
      </template>
    </AdminDataTable>

    <Teleport to="body">
      <div v-if="detail" class="admin-modal-overlay" @click.self="detail = null">
        <div class="admin-modal" role="dialog">
          <div class="admin-modal__header">
            <h3 class="admin-modal__title">订单详情</h3>
          </div>
          <div class="admin-modal__body admin-detail-grid">
            <div><span>订单编号</span><strong>{{ detail.provider_ref }}</strong></div>
            <div><span>用户</span><strong>{{ detail.user_email }}</strong></div>
            <div><span>金额</span><strong>{{ formatCents(detail.amount_cents, detail.currency) }}</strong></div>
            <div><span>渠道</span><strong>{{ channelLabel(detail.channel) }}</strong></div>
            <div><span>状态</span><strong>{{ statusLabel(detail.status) }}</strong></div>
            <div><span>创建时间</span><strong>{{ formatDate(detail.created_at) }}</strong></div>
            <div v-if="detail.paid_at"><span>到账时间</span><strong>{{ formatDate(detail.paid_at) }}</strong></div>
            <div v-if="detail.pay_url" class="admin-detail-grid__full">
              <span>支付链接</span>
              <a :href="detail.pay_url" target="_blank" rel="noopener">{{ detail.pay_url }}</a>
            </div>
          </div>
          <div class="admin-modal__footer">
            <button class="btn btn-secondary btn-sm" @click="detail = null">关闭</button>
          </div>
        </div>
      </div>
    </Teleport>

    <AdminModal
      :open="refundModal.open"
      title="确认退款"
      :description="refundModal.description"
      confirm-label="确认退款"
      :show-input="true"
      input-placeholder="退款备注（可选）"
      :danger="true"
      @confirm="onRefundConfirm"
      @cancel="closeRefundModal"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { listAdminPaymentOrders, refundAdminPaymentOrder } from '@/api/admin'
import type { DepositOrder } from '@/types'
import { formatCents, formatDate } from '@/utils'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminDataTable from '@/components/admin/AdminDataTable.vue'
import AdminAlert from '@/components/admin/AdminAlert.vue'
import AdminModal from '@/components/admin/AdminModal.vue'
import EmptyState from '@/components/EmptyState.vue'
import AdminPager from '@/components/AdminPager.vue'
import AppIcon from '@/components/AppIcon.vue'

const orders = ref<DepositOrder[]>([])
const loading = ref(true)
const listError = ref('')
const error = ref('')
const success = ref('')
const search = ref('')
const statusFilter = ref('')
const channelFilter = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)
const detail = ref<DepositOrder | null>(null)
const actingId = ref('')

const refundModal = reactive({
  open: false,
  description: '',
  order: null as DepositOrder | null,
})

function rowNumber(idx: number) {
  return total.value - (page.value - 1) * pageSize - idx
}

function userInitial(email?: string) {
  return (email?.[0] ?? '?').toUpperCase()
}

function channelLabel(channel: string) {
  const map: Record<string, string> = {
    alipay: '支付宝',
    wechat: '微信支付',
    stripe: 'Stripe',
    easypay: 'EasyPay',
  }
  return map[channel] ?? channel
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    pending: '待支付',
    paid: '已到账',
    refunded: '已退款',
    failed: '失败',
    expired: '已过期',
  }
  return map[status] ?? status
}

function statusClass(status: string) {
  if (status === 'paid') return 'admin-tag--success'
  if (status === 'refunded') return 'admin-tag--muted'
  if (status === 'pending') return 'admin-tag--warning'
  if (status === 'failed') return 'admin-tag--danger'
  return 'admin-tag--muted'
}

async function loadOrders() {
  loading.value = true
  listError.value = ''
  try {
    const data = await listAdminPaymentOrders({
      page: page.value,
      page_size: pageSize,
      status: statusFilter.value || undefined,
      channel: channelFilter.value || undefined,
      search: search.value.trim() || undefined,
    })
    orders.value = data.items
    total.value = data.total
  } catch (e) {
    listError.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function reload() {
  page.value = 1
  loadOrders()
}

function viewOrder(order: DepositOrder) {
  detail.value = order
}

function openRefund(order: DepositOrder) {
  refundModal.order = order
  refundModal.description = `将从用户余额扣回 ${formatCents(order.amount_cents, order.currency)}，订单 ${order.provider_ref}`
  refundModal.open = true
}

function closeRefundModal() {
  refundModal.open = false
  refundModal.order = null
}

async function onRefundConfirm(note?: string) {
  const order = refundModal.order
  if (!order) return
  actingId.value = order.id
  error.value = ''
  success.value = ''
  closeRefundModal()
  try {
    await refundAdminPaymentOrder(order.id, { admin_note: note || undefined })
    success.value = `订单 ${order.provider_ref} 已退款`
    await loadOrders()
    if (detail.value?.id === order.id) {
      detail.value = { ...detail.value, status: 'refunded' }
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '退款失败'
  } finally {
    actingId.value = ''
  }
}

onMounted(loadOrders)
</script>

<style scoped>
.mono-cell {
  font-size: 12px;
  color: #6b7280;
  word-break: break-all;
  max-width: 220px;
}
</style>
