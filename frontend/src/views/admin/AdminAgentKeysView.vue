<template>
  <div>
    <AdminPageHeader title="Agent / 龙虾接入" subtitle="查看全平台 OpenClaw / MCP Agent Key，支持搜索与撤销">
      <template #actions>
        <RouterLink to="/connect" class="btn btn-secondary btn-sm" target="_blank">接入文档</RouterLink>
        <RouterLink to="/admin/settings?tab=agent" class="btn btn-secondary btn-sm">MCP 设置</RouterLink>
        <button class="btn btn-secondary btn-sm" :disabled="loading" @click="reload">刷新</button>
      </template>
    </AdminPageHeader>

    <AdminAlert v-if="error" :message="error" type="error" />
    <AdminAlert v-if="success" :message="success" type="success" />

    <div v-if="stats" class="admin-stat-grid admin-stat-grid--4 admin-stat-grid--compact" style="margin-bottom: 16px">
      <div class="admin-metric-card">
        <span class="admin-metric-card__label">活跃 Key</span>
        <strong class="admin-metric-card__value">{{ stats.keys_active }}</strong>
      </div>
      <div class="admin-metric-card">
        <span class="admin-metric-card__label">接入用户</span>
        <strong class="admin-metric-card__value">{{ stats.users_with_keys }}</strong>
      </div>
      <div class="admin-metric-card">
        <span class="admin-metric-card__label">累计签发</span>
        <strong class="admin-metric-card__value">{{ stats.keys_total }}</strong>
      </div>
      <div class="admin-metric-card">
        <span class="admin-metric-card__label">已撤销</span>
        <strong class="admin-metric-card__value">{{ stats.keys_revoked }}</strong>
      </div>
      <div class="admin-metric-card">
        <span class="admin-metric-card__label">已轮换</span>
        <strong class="admin-metric-card__value">{{ stats.keys_rotated }}</strong>
      </div>
    </div>

    <AdminDataTable :loading="loading" :error="listError" :empty="!loading && !listError && keys.length === 0">
      <template #toolbar>
        <div class="admin-toolbar admin-toolbar--wide" style="margin: 0; padding: 0; border: none; box-shadow: none">
          <input
            v-model="search"
            type="search"
            placeholder="邮箱 / Agent ID / 备注 / Key 前缀"
            @keyup.enter="reload"
          />
          <select v-model="statusFilter" @change="reload">
            <option value="">全部状态</option>
            <option value="active">活跃</option>
            <option value="revoked">已撤销</option>
            <option value="rotated">已轮换</option>
          </select>
          <button class="btn btn-secondary btn-sm" @click="reload">搜索</button>
        </div>
      </template>

      <template #empty>
        <EmptyState icon="agent">暂无 Agent Key，用户可在用户端「Agent 接入」页签发</EmptyState>
      </template>

      <template #head>
        <tr>
          <th>用户</th>
          <th>Agent 身份 ID</th>
          <th>备注</th>
          <th>Key 前缀</th>
          <th>状态</th>
          <th>签发时间</th>
          <th style="text-align: right">操作</th>
        </tr>
      </template>

      <tr v-for="item in keys" :key="item.id">
        <td>
          <div class="admin-user-cell">
            <span class="admin-user-cell__avatar">{{ userInitial(item) }}</span>
            <div>
              <strong>{{ item.user_email }}</strong>
              <div class="admin-subline">{{ item.user_display_name }}</div>
            </div>
          </div>
        </td>
        <td><code class="admin-code">{{ item.platform_user_id }}</code></td>
        <td>{{ item.name || '—' }}</td>
        <td class="mono-cell">{{ item.key_prefix }}…</td>
        <td><span class="admin-tag" :class="statusClass(item.status)">{{ statusLabel(item.status) }}</span></td>
        <td>{{ formatDate(item.created_at) }}</td>
        <td style="text-align: right">
          <button
            v-if="item.status === 'active'"
            type="button"
            class="admin-link-btn admin-link-btn--danger"
            :disabled="actingId === item.id"
            @click="handleRevoke(item)"
          >
            {{ actingId === item.id ? '撤销中…' : '撤销' }}
          </button>
          <span v-else class="admin-subline">—</span>
        </td>
      </tr>

      <template #footer>
        <AdminPager v-model:page="page" :page-size="pageSize" :total="total" @update:page="loadKeys" />
      </template>
    </AdminDataTable>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { getAdminAgentStats, listAdminAgentKeys, revokeAdminAgentKey } from '@/api/admin'
import type { AdminApiKeyItem, AgentStats } from '@/types'
import { formatDate } from '@/utils'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminAlert from '@/components/admin/AdminAlert.vue'
import AdminDataTable from '@/components/admin/AdminDataTable.vue'
import AdminPager from '@/components/AdminPager.vue'
import EmptyState from '@/components/EmptyState.vue'

const loading = ref(true)
const listError = ref('')
const error = ref('')
const success = ref('')
const stats = ref<AgentStats | null>(null)
const keys = ref<AdminApiKeyItem[]>([])
const page = ref(1)
const pageSize = 20
const total = ref(0)
const search = ref('')
const statusFilter = ref('')
const actingId = ref('')

function userInitial(item: AdminApiKeyItem) {
  return (item.user_display_name || item.user_email || '?').slice(0, 1).toUpperCase()
}

function statusLabel(status: string) {
  if (status === 'active') return '活跃'
  if (status === 'revoked') return '已撤销'
  if (status === 'rotated') return '已轮换'
  return status
}

function statusClass(status: string) {
  if (status === 'active') return 'admin-tag--open'
  if (status === 'revoked') return 'admin-tag--danger'
  return 'admin-tag--muted'
}

async function loadStats() {
  try {
    stats.value = await getAdminAgentStats()
  } catch {
    /* ignore */
  }
}

async function loadKeys() {
  loading.value = true
  listError.value = ''
  try {
    const data = await listAdminAgentKeys({
      page: page.value,
      page_size: pageSize,
      status: statusFilter.value || undefined,
      search: search.value.trim() || undefined,
    })
    keys.value = data.items
    total.value = data.total
  } catch (e) {
    listError.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function reload() {
  page.value = 1
  loadStats()
  loadKeys()
}

async function handleRevoke(item: AdminApiKeyItem) {
  if (!confirm(`确定撤销 ${item.user_email} 的 Agent Key「${item.platform_user_id}」？`)) return
  actingId.value = item.id
  error.value = ''
  success.value = ''
  try {
    await revokeAdminAgentKey(item.id)
    success.value = 'Key 已撤销'
    await Promise.all([loadStats(), loadKeys()])
  } catch (e) {
    error.value = e instanceof Error ? e.message : '撤销失败'
  } finally {
    actingId.value = ''
  }
}

onMounted(() => {
  reload()
})
</script>
