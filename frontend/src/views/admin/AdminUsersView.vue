<template>
  <div>
    <AdminPageHeader title="用户管理" subtitle="管理您的用户和权限" />

    <AdminAlert v-if="error" :message="error" type="error" />
    <AdminAlert v-if="success" :message="success" type="success" />

    <AdminDataTable :loading="loading" :error="listError" :empty="!loading && !listError && users.length === 0">
      <template #toolbar>
        <div class="admin-toolbar admin-toolbar--wide" style="margin: 0; padding: 0; border: none; box-shadow: none">
          <input
            v-model="search"
            type="search"
            placeholder="邮箱 / 用户名 模糊搜索"
            @keyup.enter="reload"
          />
          <select v-model="statusFilter" @change="reload">
            <option value="">全部状态</option>
            <option value="active">启用</option>
            <option value="suspended">已封禁</option>
          </select>
          <button class="btn btn-secondary btn-sm" @click="reload">刷新</button>
        </div>
      </template>

      <template #empty>
        <EmptyState icon="users">暂无匹配用户</EmptyState>
      </template>

      <template #head>
        <tr>
          <th>用户</th>
          <th>ID</th>
          <th>角色</th>
          <th>余额</th>
          <th>状态</th>
          <th>创建时间</th>
          <th style="text-align: right">操作</th>
        </tr>
      </template>

      <tr v-for="user in users" :key="user.id">
        <td>
          <div class="admin-user-cell">
            <span class="admin-user-cell__avatar">{{ userInitial(user) }}</span>
            <div>
              <strong>{{ user.email }}</strong>
              <div class="admin-subline">{{ user.display_name }}</div>
            </div>
          </div>
        </td>
        <td class="mono-cell">{{ shortId(user.id) }}</td>
        <td>
          <span v-if="user.role === 'admin'" class="admin-tag admin-tag--open">管理员</span>
          <span v-else class="admin-tag admin-tag--muted">用户</span>
        </td>
        <td>
          <div class="admin-balance-cell">
            <strong>{{ formatCents(user.wallet_balance_cents ?? 0) }}</strong>
            <button type="button" class="admin-link-btn" @click="openCredit(user)">充值</button>
          </div>
        </td>
        <td>
          <span class="admin-status-dot" :class="user.status === 'active' ? 'admin-status-dot--on' : 'admin-status-dot--off'">
            {{ userStatusLabel(user.status) }}
          </span>
        </td>
        <td>{{ formatDate(user.created_at) }}</td>
        <td style="text-align: right">
          <div class="admin-row-actions">
            <button
              v-if="user.status === 'active' && user.role !== 'admin'"
              type="button"
              class="admin-icon-btn admin-icon-btn--danger"
              title="封禁"
              :disabled="actingId === user.id"
              @click="toggleStatus(user, 'suspended')"
            >
              <AppIcon name="lock" size="sm" />
            </button>
            <button
              v-else-if="user.status === 'suspended'"
              type="button"
              class="admin-icon-btn"
              title="解封"
              :disabled="actingId === user.id"
              @click="toggleStatus(user, 'active')"
            >
              <AppIcon name="refresh" size="sm" />
            </button>
          </div>
        </td>
      </tr>

      <template #footer>
        <AdminPager v-model:page="page" :page-size="pageSize" :total="total" @update:page="loadUsers" />
      </template>
    </AdminDataTable>

    <Teleport to="body">
      <div v-if="creditUser" class="admin-modal-overlay" @click.self="creditUser = null">
        <div class="admin-modal" role="dialog">
          <div class="admin-modal__header">
            <h3 class="admin-modal__title">手动充值 · {{ creditUser.email }}</h3>
          </div>
          <div class="admin-modal__body">
            <div class="admin-form-field">
              <label>充值金额（元）</label>
              <input v-model.number="creditAmountYuan" type="number" min="0.01" step="0.01" />
            </div>
            <div class="admin-form-field">
              <label>备注（可选）</label>
              <input v-model="creditNote" type="text" maxlength="120" />
            </div>
          </div>
          <div class="admin-modal__footer">
            <button class="btn btn-secondary btn-sm" @click="creditUser = null">取消</button>
            <button
              class="btn btn-primary-admin btn-sm"
              :disabled="crediting || !creditAmountYuan || creditAmountYuan <= 0"
              @click="submitCredit"
            >
              {{ crediting ? '处理中…' : '确认充值' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { creditAdminUser, listAdminUsers, updateAdminUserStatus } from '@/api/admin'
import type { UserProfile } from '@/types'
import { formatCents, formatDate } from '@/utils'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminDataTable from '@/components/admin/AdminDataTable.vue'
import AdminAlert from '@/components/admin/AdminAlert.vue'
import EmptyState from '@/components/EmptyState.vue'
import AdminPager from '@/components/AdminPager.vue'
import AppIcon from '@/components/AppIcon.vue'

const users = ref<UserProfile[]>([])
const loading = ref(true)
const listError = ref('')
const error = ref('')
const success = ref('')
const search = ref('')
const statusFilter = ref('')
const page = ref(1)
const pageSize = 10
const total = ref(0)
const actingId = ref('')

const creditUser = ref<UserProfile | null>(null)
const creditAmountYuan = ref<number | null>(null)
const creditNote = ref('')
const crediting = ref(false)

function userInitial(user: UserProfile) {
  return (user.display_name?.[0] || user.email[0] || '?').toUpperCase()
}

function shortId(id: string) {
  return id.slice(0, 8)
}

function userStatusLabel(status: string) {
  const map: Record<string, string> = { active: '启用', suspended: '已封禁', deleted: '已删除' }
  return map[status] ?? status
}

async function loadUsers() {
  loading.value = true
  listError.value = ''
  try {
    const data = await listAdminUsers({
      page: page.value,
      page_size: pageSize,
      status: statusFilter.value || undefined,
      search: search.value.trim() || undefined,
    })
    users.value = data.items
    total.value = data.total
  } catch (e) {
    listError.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function reload() {
  page.value = 1
  loadUsers()
}

function openCredit(user: UserProfile) {
  creditUser.value = user
  creditAmountYuan.value = null
  creditNote.value = ''
}

async function submitCredit() {
  if (!creditUser.value || !creditAmountYuan.value) return
  crediting.value = true
  error.value = ''
  success.value = ''
  try {
    const amount_cents = Math.round(creditAmountYuan.value * 100)
    await creditAdminUser(creditUser.value.id, {
      amount_cents,
      note: creditNote.value.trim() || undefined,
    })
    success.value = `已为 ${creditUser.value.email} 充值 ${formatCents(amount_cents)}`
    creditUser.value = null
    await loadUsers()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '充值失败'
  } finally {
    crediting.value = false
  }
}

async function toggleStatus(user: UserProfile, status: 'active' | 'suspended') {
  actingId.value = user.id
  error.value = ''
  try {
    const updated = await updateAdminUserStatus(user.id, status)
    const idx = users.value.findIndex((u) => u.id === user.id)
    if (idx >= 0) users.value[idx] = { ...users.value[idx], ...updated }
    success.value = status === 'suspended' ? '用户已封禁' : '用户已解封'
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    actingId.value = ''
  }
}

onMounted(loadUsers)
</script>

<style scoped>
.mono-cell {
  font-size: 12px;
  color: #6b7280;
  font-family: ui-monospace, monospace;
}

.admin-subline {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 2px;
}
</style>
