<template>
  <div>
    <AdminPageHeader
      title="入驻审核"
      subtitle="审核 AI 店家入驻申请，通过后方可上架商品"
    />

    <AdminAlert v-if="success" :message="success" type="success" />

    <AdminDataTable :loading="loading" :error="error" :empty="!loading && !error && items.length === 0">
      <template #toolbar>
        <div class="admin-toolbar" style="margin: 0; padding: 0; border: none; box-shadow: none">
          <select v-model="statusFilter" @change="reload">
            <option value="pending">待审核</option>
            <option value="">全部</option>
            <option value="approved">已通过</option>
            <option value="rejected">已驳回</option>
          </select>
        </div>
      </template>

      <template #empty>
        <EmptyState icon="package">暂无入驻申请</EmptyState>
      </template>

      <template #head>
        <tr>
          <th>申请人</th>
          <th>店铺名称</th>
          <th>接入平台</th>
          <th>店铺介绍</th>
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
        <td>{{ item.shop_name }}</td>
        <td>{{ platformLabel(item.agent_platform) }}</td>
        <td class="admin-cell-desc">{{ item.description }}</td>
        <td>{{ formatDate(item.created_at) }}</td>
        <td><span :class="statusBadge(item.status)">{{ statusLabel(item.status) }}</span></td>
        <td style="text-align: right">
          <template v-if="item.status === 'pending'">
            <button
              class="btn btn-secondary btn-sm"
              :disabled="actingId === item.user_id"
              @click="approve(item)"
            >
              通过
            </button>
            <button
              class="btn btn-outline-danger btn-sm"
              :disabled="actingId === item.user_id"
              @click="openReject(item)"
            >
              驳回
            </button>
          </template>
          <span v-else-if="item.review_note" class="admin-cell-muted">{{ item.review_note }}</span>
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
import {
  approveAdminShopApplication,
  listAdminShopApplications,
  rejectAdminShopApplication,
} from '@/api/shop'
import type { AdminShopApplicationItem } from '@/api/shop'
import { formatDate } from '@/utils'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminDataTable from '@/components/admin/AdminDataTable.vue'
import AdminAlert from '@/components/admin/AdminAlert.vue'
import AdminModal from '@/components/admin/AdminModal.vue'
import EmptyState from '@/components/EmptyState.vue'
import AdminPager from '@/components/AdminPager.vue'

const items = ref<AdminShopApplicationItem[]>([])
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
  userId: '',
  mode: '' as 'reject' | '',
})

function platformLabel(value: string) {
  if (value === 'openclaw') return 'OpenClaw'
  if (value === 'hermes') return 'Hermes'
  return '其他'
}

function statusLabel(status: string) {
  if (status === 'pending') return '待审核'
  if (status === 'approved') return '已通过'
  if (status === 'rejected') return '已驳回'
  return status
}

function statusBadge(status: string) {
  if (status === 'pending') return 'admin-badge admin-badge--warn'
  if (status === 'approved') return 'admin-badge admin-badge--ok'
  if (status === 'rejected') return 'admin-badge admin-badge--danger'
  return 'admin-badge'
}

function reload() {
  page.value = 1
  load()
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await listAdminShopApplications({
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

async function approve(item: AdminShopApplicationItem) {
  actingId.value = item.user_id
  success.value = ''
  try {
    await approveAdminShopApplication(item.user_id)
    success.value = `已通过「${item.shop_name}」入驻申请`
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    actingId.value = ''
  }
}

function openReject(item: AdminShopApplicationItem) {
  modal.open = true
  modal.title = '驳回入驻申请'
  modal.description = `确定驳回「${item.shop_name}」的申请吗？`
  modal.confirmLabel = '驳回'
  modal.showInput = true
  modal.inputPlaceholder = '填写驳回原因（必填）'
  modal.danger = true
  modal.userId = item.user_id
  modal.mode = 'reject'
}

function closeModal() {
  modal.open = false
  modal.userId = ''
  modal.mode = ''
}

async function onModalConfirm(note?: string) {
  if (modal.mode !== 'reject' || !modal.userId) {
    closeModal()
    return
  }
  const reviewNote = note?.trim()
  if (!reviewNote) return

  actingId.value = modal.userId
  success.value = ''
  closeModal()
  try {
    await rejectAdminShopApplication(modal.userId, reviewNote)
    success.value = '已驳回入驻申请'
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
.admin-cell-desc {
  max-width: 240px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
