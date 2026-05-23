<template>
  <div>
    <AdminPageHeader title="提现审核" subtitle="批准、驳回或确认打款" />

    <AdminAlert v-if="success" :message="success" type="success" />

    <AdminDataTable :loading="loading" :error="error" :empty="!loading && !error && items.length === 0">
      <template #toolbar>
        <div class="admin-toolbar" style="margin: 0; padding: 0; border: none; box-shadow: none">
          <select v-model="statusFilter" @change="reload">
            <option value="pending">待审核</option>
            <option value="">全部状态</option>
            <option value="approved">待打款</option>
            <option value="completed">已完成</option>
            <option value="rejected">已驳回</option>
          </select>
        </div>
      </template>

      <template #empty>
        <EmptyState icon="wallet">暂无提现记录</EmptyState>
      </template>

      <template #head>
        <tr>
          <th>金额</th>
          <th>收款人</th>
          <th>收款方式</th>
          <th>申请时间</th>
          <th>状态</th>
          <th style="text-align: right">操作</th>
        </tr>
      </template>

      <tr v-for="item in items" :key="item.id">
        <td><strong>{{ formatCents(item.amount_cents) }}</strong></td>
        <td>{{ item.payout_name }}</td>
        <td>{{ payoutLabel(item.payout_method) }} · {{ item.payout_account }}</td>
        <td>{{ formatDate(item.created_at) }}</td>
        <td><span :class="statusBadge(item.status)">{{ withdrawStatusLabel(item.status) }}</span></td>
        <td style="text-align: right">
          <template v-if="item.status === 'pending'">
            <button class="btn btn-secondary btn-sm" :disabled="actingId === item.id" @click="openApprove(item)">
              批准
            </button>
            <button class="btn btn-outline-danger btn-sm" :disabled="actingId === item.id" @click="openReject(item)">
              驳回
            </button>
          </template>
          <button
            v-else-if="item.status === 'approved'"
            class="btn btn-primary-admin btn-sm"
            :disabled="actingId === item.id"
            @click="openComplete(item)"
          >
            确认打款
          </button>
        </td>
      </tr>

      <template #footer>
        <AdminPager v-model:page="page" :page-size="pageSize" :total="total" @update:page="load" />
      </template>
    </AdminDataTable>

    <AdminModal
      :open="modal.open"
      :title="modal.title"
      :description="modal.description"
      :confirm-label="modal.confirmLabel"
      :show-input="modal.showInput"
      :input-placeholder="modal.inputPlaceholder"
      :input-required="modal.inputRequired"
      :danger="modal.danger"
      @confirm="onModalConfirm"
      @cancel="closeModal"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { listAdminWithdrawals, processAdminWithdraw } from '@/api/admin'
import type { AdminWithdrawItem } from '@/types'
import { formatCents, formatDate } from '@/utils'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminDataTable from '@/components/admin/AdminDataTable.vue'
import AdminAlert from '@/components/admin/AdminAlert.vue'
import AdminModal from '@/components/admin/AdminModal.vue'
import EmptyState from '@/components/EmptyState.vue'
import AdminPager from '@/components/AdminPager.vue'

const items = ref<AdminWithdrawItem[]>([])
const loading = ref(true)
const error = ref('')
const success = ref('')
const statusFilter = ref('pending')
const page = ref(1)
const pageSize = 20
const total = ref(0)
const actingId = ref('')

const modal = reactive({
  open: false,
  title: '',
  description: '',
  confirmLabel: '确认',
  showInput: false,
  inputPlaceholder: '',
  inputRequired: false,
  danger: false,
  action: '' as 'approve' | 'reject' | 'complete',
  item: null as AdminWithdrawItem | null,
})

function payoutLabel(method: string) {
  const map: Record<string, string> = { alipay: '支付宝', wechat: '微信', bank: '银行卡' }
  return map[method] ?? method
}

function withdrawStatusLabel(status: string) {
  const map: Record<string, string> = {
    pending: '待审核',
    approved: '待打款',
    processing: '处理中',
    completed: '已完成',
    rejected: '已驳回',
  }
  return map[status] ?? status
}

function statusBadge(status: string) {
  const map: Record<string, string> = {
    pending: 'admin-tag admin-tag--open',
    approved: 'admin-tag admin-tag--warn',
    completed: 'admin-tag admin-tag--success',
    rejected: 'admin-tag admin-tag--muted',
  }
  return map[status] ?? 'admin-tag admin-tag--muted'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await listAdminWithdrawals({
      page: page.value,
      page_size: pageSize,
      status: statusFilter.value || undefined,
    })
    items.value = data.items
    total.value = data.total
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function reload() {
  page.value = 1
  load()
}

function closeModal() {
  modal.open = false
  modal.item = null
}

function openApprove(item: AdminWithdrawItem) {
  modal.open = true
  modal.title = '批准提现'
  modal.description = `确认批准 ${item.payout_name} 的 ${formatCents(item.amount_cents)} 提现申请？`
  modal.confirmLabel = '批准'
  modal.showInput = false
  modal.inputRequired = false
  modal.danger = false
  modal.action = 'approve'
  modal.item = item
}

function openReject(item: AdminWithdrawItem) {
  modal.open = true
  modal.title = '驳回提现'
  modal.description = '驳回后将退回用户余额，可填写原因（可选）。'
  modal.confirmLabel = '驳回'
  modal.showInput = true
  modal.inputPlaceholder = '驳回原因'
  modal.inputRequired = false
  modal.danger = true
  modal.action = 'reject'
  modal.item = item
}

function openComplete(item: AdminWithdrawItem) {
  modal.open = true
  modal.title = '确认打款'
  modal.description = '请输入银行/支付平台流水号，标记为已打款。'
  modal.confirmLabel = '确认打款'
  modal.showInput = true
  modal.inputPlaceholder = '打款流水号'
  modal.inputRequired = true
  modal.danger = false
  modal.action = 'complete'
  modal.item = item
}

async function onModalConfirm(value: string) {
  const item = modal.item
  const action = modal.action
  if (!item) return
  closeModal()
  actingId.value = item.id
  success.value = ''
  error.value = ''
  try {
    if (action === 'approve') {
      await processAdminWithdraw(item.id, { action: 'approve' })
      success.value = '已批准，等待打款'
    } else if (action === 'reject') {
      await processAdminWithdraw(item.id, { action: 'reject', admin_note: value || undefined })
      success.value = '已驳回并退款'
    } else {
      await processAdminWithdraw(item.id, {
        action: 'complete',
        provider_ref: value,
        admin_note: '打款完成',
      })
      success.value = '已标记为打款完成'
    }
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    actingId.value = ''
  }
}

onMounted(load)
</script>
