<template>
  <div>
    <AdminPageHeader title="需求管理" subtitle="查看并管理用户发布的需求" />

    <AdminDataTable :loading="loading" :error="error" :empty="!loading && !error && intents.length === 0">
      <template #toolbar>
        <div class="admin-toolbar" style="margin: 0; padding: 0; border: none; box-shadow: none">
          <select v-model="statusFilter" @change="reload">
            <option value="">全部状态</option>
            <option value="open">开放</option>
            <option value="matched">已匹配</option>
            <option value="closed">已关闭</option>
          </select>
        </div>
      </template>

      <template #empty>
        <EmptyState icon="target">暂无需求</EmptyState>
      </template>

      <template #head>
        <tr>
          <th>标题</th>
          <th>分类</th>
          <th>预算</th>
          <th>状态</th>
          <th style="text-align: right">操作</th>
        </tr>
      </template>

      <tr v-for="intent in intents" :key="intent.id">
        <td><strong>{{ intent.title }}</strong></td>
        <td>{{ categoryLabel(intent.category) }}</td>
        <td>{{ formatCents(intent.budget_max, intent.currency) }}</td>
        <td><span :class="badgeClass(intent.status)">{{ statusLabel(intent.status) }}</span></td>
        <td style="text-align: right">
          <button
            v-if="intent.status !== 'closed'"
            class="btn btn-outline-danger btn-sm"
            :disabled="actingId === intent.id"
            @click="closeIntent(intent.id)"
          >
            {{ actingId === intent.id ? '处理中…' : '强制关闭' }}
          </button>
        </td>
      </tr>

      <template #footer>
        <AdminPager v-model:page="page" :page-size="pageSize" :total="total" @update:page="loadIntents" />
      </template>
    </AdminDataTable>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listAdminIntents, updateAdminIntentStatus } from '@/api/admin'
import type { Intent } from '@/types'
import { categoryLabel, formatCents, statusLabel } from '@/utils'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminDataTable from '@/components/admin/AdminDataTable.vue'
import EmptyState from '@/components/EmptyState.vue'
import AdminPager from '@/components/AdminPager.vue'

const intents = ref<Intent[]>([])
const loading = ref(true)
const error = ref('')
const statusFilter = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)
const actingId = ref('')

function badgeClass(status: string) {
  const map: Record<string, string> = {
    open: 'admin-tag admin-tag--open',
    matched: 'admin-tag admin-tag--success',
    closed: 'admin-tag admin-tag--muted',
  }
  return map[status] ?? 'admin-tag admin-tag--muted'
}

async function loadIntents() {
  loading.value = true
  error.value = ''
  try {
    const data = await listAdminIntents({
      page: page.value,
      page_size: pageSize,
      status: statusFilter.value || undefined,
    })
    intents.value = data.items
    total.value = data.total
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function reload() {
  page.value = 1
  loadIntents()
}

async function closeIntent(intentId: string) {
  if (!confirm('确认强制关闭此需求？')) return
  actingId.value = intentId
  try {
    await updateAdminIntentStatus(intentId, 'closed')
    await loadIntents()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    actingId.value = ''
  }
}

onMounted(loadIntents)
</script>
