<template>
  <div>
    <AdminPageHeader title="实名审核" subtitle="审核用户提交的姓名与身份证号" />

    <AdminAlert v-if="success" :message="success" type="success" />

    <AdminDataTable :loading="loading" :error="error" :empty="!loading && !error && items.length === 0">
      <template #toolbar>
        <div class="admin-toolbar" style="margin: 0; padding: 0; border: none; box-shadow: none">
          <select v-model="statusFilter" @change="reload">
            <option value="pending">待审核</option>
            <option value="">全部</option>
            <option value="verified">已通过</option>
          </select>
        </div>
      </template>

      <template #empty>
        <EmptyState icon="lock">暂无实名认证记录</EmptyState>
      </template>

      <template #head>
        <tr>
          <th>用户</th>
          <th>真实姓名</th>
          <th>身份证号</th>
          <th>提交时间</th>
          <th>状态</th>
          <th style="text-align: right">操作</th>
        </tr>
      </template>

      <tr v-for="item in items" :key="item.user_id">
        <td>
          <div>{{ item.display_name }}</div>
          <div class="admin-cell-muted">{{ item.email }}</div>
        </td>
        <td>{{ item.real_name || '—' }}</td>
        <td>{{ item.id_number || item.id_number_masked || '—' }}</td>
        <td>{{ formatDate(item.submitted_at) }}</td>
        <td><span :class="statusBadge(item.kyc_status)">{{ kycStatusLabel(item.kyc_status) }}</span></td>
        <td style="text-align: right">
          <template v-if="item.kyc_status === 'pending'">
            <button class="btn btn-secondary btn-sm" :disabled="actingId === item.user_id" @click="openApprove(item)">
              通过
            </button>
            <button class="btn btn-outline-danger btn-sm" :disabled="actingId === item.user_id" @click="openReject(item)">
              驳回
            </button>
          </template>
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
      :danger="modal.danger"
      @confirm="onModalConfirm"
      @cancel="closeModal"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { listAdminKyc, reviewAdminKyc } from '@/api/admin'
import type { AdminKycItem } from '@/types'
import { formatDate } from '@/utils'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminDataTable from '@/components/admin/AdminDataTable.vue'
import AdminAlert from '@/components/admin/AdminAlert.vue'
import AdminModal from '@/components/admin/AdminModal.vue'
import EmptyState from '@/components/EmptyState.vue'
import AdminPager from '@/components/AdminPager.vue'

const items = ref<AdminKycItem[]>([])
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
  danger: false,
  action: '' as 'approve' | 'reject',
  item: null as AdminKycItem | null,
})

function kycStatusLabel(status: string) {
  const map: Record<string, string> = {
    none: '未提交',
    pending: '待审核',
    verified: '已通过',
  }
  return map[status] ?? status
}

function statusBadge(status: string) {
  if (status === 'pending') return 'admin-badge admin-badge--warning'
  if (status === 'verified') return 'admin-badge admin-badge--success'
  return 'admin-badge'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await listAdminKyc({
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

function openApprove(item: AdminKycItem) {
  modal.open = true
  modal.title = '通过实名认证'
  modal.description = `确认通过 ${item.real_name}（${item.id_number_masked || item.id_number}）的实名认证？`
  modal.confirmLabel = '通过'
  modal.showInput = false
  modal.danger = false
  modal.action = 'approve'
  modal.item = item
}

function openReject(item: AdminKycItem) {
  modal.open = true
  modal.title = '驳回实名认证'
  modal.description = `驳回后用户需重新提交。${item.real_name} · ${item.id_number_masked || item.id_number}`
  modal.confirmLabel = '驳回'
  modal.showInput = true
  modal.inputPlaceholder = '驳回原因（可选）'
  modal.danger = true
  modal.action = 'reject'
  modal.item = item
}

function closeModal() {
  modal.open = false
  modal.item = null
}

async function onModalConfirm(note?: string) {
  if (!modal.item) return
  actingId.value = modal.item.user_id
  success.value = ''
  try {
    await reviewAdminKyc(modal.item.user_id, {
      action: modal.action,
      admin_note: note || undefined,
    })
    success.value = modal.action === 'approve' ? '已通过实名认证' : '已驳回'
    closeModal()
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    actingId.value = ''
  }
}

onMounted(load)
</script>

<style scoped>
.admin-cell-muted {
  font-size: 12px;
  color: var(--admin-muted, #888);
  margin-top: 2px;
}
</style>
