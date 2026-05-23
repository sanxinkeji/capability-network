<template>
  <div>
    <AdminPageHeader title="订单管理" subtitle="全平台交易订单，争议单高亮显示">
      <template #actions>
        <button class="btn btn-secondary btn-sm" :disabled="loading" @click="loadDeals">刷新</button>
      </template>
    </AdminPageHeader>

    <AdminDataTable :loading="loading" :error="error" :empty="!loading && !error && deals.length === 0">
      <template #toolbar>
        <div class="admin-toolbar" style="margin: 0; padding: 0; border: none; box-shadow: none">
          <select v-model="statusFilter" @change="reload">
            <option value="">全部状态</option>
            <option v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
        </div>
      </template>

      <template #empty>
        <EmptyState icon="clipboard">暂无订单</EmptyState>
      </template>

      <template #head>
        <tr>
          <th>订单 ID</th>
          <th>金额</th>
          <th>状态</th>
          <th>创建时间</th>
          <th style="text-align: right">操作</th>
        </tr>
      </template>

      <tr
        v-for="deal in deals"
        :key="deal.id"
        :class="{ 'admin-table-row--warn': deal.status === 'disputed' }"
      >
        <td><code class="mono-id">{{ deal.id.slice(0, 8) }}…</code></td>
        <td><strong>{{ formatCents(deal.amount_cents, deal.currency) }}</strong></td>
        <td><span :class="dealTagClass(deal.status)">{{ statusLabel(deal.status) }}</span></td>
        <td>{{ formatDate(deal.created_at) }}</td>
        <td style="text-align: right">
          <RouterLink :to="`/admin/deals/${deal.id}`" class="admin-link">查看详情</RouterLink>
        </td>
      </tr>

      <template #footer>
        <AdminPager v-model:page="page" :page-size="pageSize" :total="total" @update:page="loadDeals" />
      </template>
    </AdminDataTable>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { listAdminDeals } from '@/api/admin'
import type { Deal } from '@/types'
import { formatCents, formatDate, statusLabel } from '@/utils'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminDataTable from '@/components/admin/AdminDataTable.vue'
import EmptyState from '@/components/EmptyState.vue'
import AdminPager from '@/components/AdminPager.vue'

const route = useRoute()
const deals = ref<Deal[]>([])
const loading = ref(true)
const error = ref('')
const statusFilter = ref((route.query.status as string) || '')
const page = ref(1)
const pageSize = 20
const total = ref(0)

const statusOptions = [
  { value: 'pending', label: '待支付' },
  { value: 'in_progress', label: '进行中' },
  { value: 'delivered', label: '已交付' },
  { value: 'disputed', label: '争议中' },
  { value: 'completed', label: '已完成' },
  { value: 'refunded', label: '已退款' },
  { value: 'cancelled', label: '已取消' },
]

function dealTagClass(status: string) {
  const map: Record<string, string> = {
    pending: 'admin-tag admin-tag--muted',
    in_progress: 'admin-tag admin-tag--open',
    delivered: 'admin-tag admin-tag--warn',
    disputed: 'admin-tag admin-tag--danger',
    completed: 'admin-tag admin-tag--success',
    refunded: 'admin-tag admin-tag--muted',
    cancelled: 'admin-tag admin-tag--muted',
  }
  return map[status] ?? 'admin-tag admin-tag--muted'
}

async function loadDeals() {
  loading.value = true
  error.value = ''
  try {
    const data = await listAdminDeals({
      page: page.value,
      page_size: pageSize,
      status: statusFilter.value || undefined,
    })
    deals.value = data.items
    total.value = data.total
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function reload() {
  page.value = 1
  loadDeals()
}

watch(
  () => route.query.status,
  (val) => {
    statusFilter.value = (val as string) || ''
    reload()
  },
)

onMounted(loadDeals)
</script>

<style scoped>
.mono-id {
  font-size: 12px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
}
</style>
