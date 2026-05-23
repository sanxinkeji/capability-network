<template>
  <div>
    <AdminPageHeader title="财务中心" subtitle="平台流水与操作审计" />

    <AdminSectionTabs v-model="activeTab" :tabs="tabsList" />

    <AdminDataTable
      :loading="loading"
      :error="error"
      :empty="!loading && !error && currentEmpty"
    >
      <template #toolbar>
        <div v-if="activeTab === 'ledger'" class="admin-toolbar" style="margin: 0; padding: 0; border: none; box-shadow: none">
          <select v-model="ledgerType" @change="reloadLedger">
            <option value="">全部类型</option>
            <option value="deposit">充值</option>
            <option value="withdraw">提现</option>
            <option value="payment">结算</option>
            <option value="fee">佣金</option>
          </select>
        </div>
      </template>

      <template v-if="activeTab === 'ledger'" #head>
        <tr>
          <th>类型</th>
          <th>说明</th>
          <th style="text-align: right">金额</th>
          <th>时间</th>
        </tr>
      </template>
      <template v-else #head>
        <tr>
          <th>操作</th>
          <th>目标</th>
          <th>时间</th>
        </tr>
      </template>

      <template v-if="activeTab === 'ledger'">
        <tr v-for="entry in ledger" :key="entry.id">
          <td>{{ ledgerTypeLabel(entry.entry_type) }}</td>
          <td>{{ entry.description || '—' }}</td>
          <td style="text-align: right" :class="entry.amount_cents >= 0 ? 'amount-plus' : 'amount-minus'">
            {{ entry.amount_cents >= 0 ? '+' : '' }}{{ formatCents(Math.abs(entry.amount_cents)) }}
          </td>
          <td>{{ formatDate(entry.created_at) }}</td>
        </tr>
      </template>

      <template v-else>
        <tr v-for="log in auditLogs" :key="log.id">
          <td><strong>{{ log.action }}</strong></td>
          <td>{{ log.target_type }} {{ log.target_id || '' }}</td>
          <td>{{ formatDate(log.created_at) }}</td>
        </tr>
      </template>

      <template #empty>
        <EmptyState :icon="activeTab === 'audit' ? 'clipboard' : 'wallet'">
          {{ activeTab === 'ledger' ? '暂无流水' : '暂无审计记录' }}
        </EmptyState>
      </template>

      <template #footer>
        <AdminPager v-model:page="page" :page-size="pageSize" :total="total" @update:page="loadCurrent" />
      </template>
    </AdminDataTable>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { listAdminAuditLogs, listAdminLedger } from '@/api/admin'
import type { AdminAuditLog, WalletLedgerEntry } from '@/types'
import { formatCents, formatDate, ledgerTypeLabel } from '@/utils'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminSectionTabs from '@/components/admin/AdminSectionTabs.vue'
import AdminDataTable from '@/components/admin/AdminDataTable.vue'
import EmptyState from '@/components/EmptyState.vue'
import AdminPager from '@/components/AdminPager.vue'

const tabsList = [
  { id: 'ledger', label: '充值记录' },
  { id: 'audit', label: '审计日志' },
]

type TabId = 'ledger' | 'audit'

const activeTab = ref<TabId>('ledger')
const loading = ref(true)
const error = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)

const ledger = ref<WalletLedgerEntry[]>([])
const auditLogs = ref<AdminAuditLog[]>([])
const ledgerType = ref('')

const currentEmpty = computed(() => {
  if (activeTab.value === 'ledger') return ledger.value.length === 0
  return auditLogs.value.length === 0
})

async function loadCurrent() {
  loading.value = true
  error.value = ''
  try {
    if (activeTab.value === 'ledger') {
      const data = await listAdminLedger({
        page: page.value,
        page_size: pageSize,
        entry_type: ledgerType.value || undefined,
      })
      ledger.value = data.items
      total.value = data.total
    } else {
      const data = await listAdminAuditLogs({ page: page.value, page_size: pageSize })
      auditLogs.value = data.items
      total.value = data.total
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

watch(activeTab, () => {
  page.value = 1
  loadCurrent()
})

function reloadLedger() {
  page.value = 1
  loadCurrent()
}

watch(page, loadCurrent)
onMounted(loadCurrent)
</script>
