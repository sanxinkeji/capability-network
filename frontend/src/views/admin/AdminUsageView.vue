<template>
  <div>
    <AdminPageHeader title="使用记录" subtitle="平台流水、交易明细与消费分布">
      <template #actions>
        <div class="admin-range-tabs">
          <button
            v-for="d in dayOptions"
            :key="d"
            type="button"
            class="admin-range-tabs__btn"
            :class="{ 'admin-range-tabs__btn--active': days === d }"
            @click="setDays(d)"
          >
            近 {{ d }} 天
          </button>
        </div>
        <button class="btn btn-secondary btn-sm" :disabled="loading" @click="reload">刷新</button>
      </template>
    </AdminPageHeader>

    <AdminAlert v-if="error" :message="error" type="error" />

    <div v-if="summary" class="admin-stat-grid admin-stat-grid--4">
      <AdminStatCard icon="clipboard" label="流水笔数" :value="summary.entry_count" tone="primary" />
      <AdminStatCard icon="wallet" label="充值总额" :value="formatCents(summary.deposit_cents)" small-value tone="success" />
      <AdminStatCard icon="chart" label="结算总额" :value="formatCents(summary.payment_cents)" small-value tone="warning" />
      <AdminStatCard icon="target" label="佣金总额" :value="formatCents(summary.fee_cents)" small-value tone="danger" />
    </div>

    <div v-if="dashboard?.ledger_by_type.length" class="admin-split-grid admin-split-grid--wide">
      <div class="admin-panel">
        <div class="admin-panel__header"><h3>流水类型分布</h3></div>
        <table class="admin-mini-table admin-mini-table--full">
          <thead><tr><th>类型</th><th>笔数</th><th>金额</th><th>占比</th></tr></thead>
          <tbody>
            <tr v-for="item in dashboard.ledger_by_type" :key="item.entry_type">
              <td>{{ ledgerTypeLabel(item.entry_type) }}</td>
              <td>{{ item.entry_count }}</td>
              <td>{{ formatCents(item.amount_cents) }}</td>
              <td>{{ percent(item.amount_cents, totalLedgerAmount) }}%</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="admin-panel">
        <div class="admin-panel__header"><h3>支付渠道分布</h3></div>
        <ul v-if="dashboard.payment.channels.length" class="admin-channel-list">
          <li v-for="item in dashboard.payment.channels" :key="item.channel">
            <div class="admin-channel-list__head">
              <span>{{ channelLabel(item.channel) }}</span>
              <strong>{{ formatCents(item.amount_cents) }}</strong>
            </div>
            <div class="admin-channel-list__bar"><span :style="{ width: `${channelPct(item.amount_cents)}%` }" /></div>
          </li>
        </ul>
        <div v-else class="admin-panel__empty">暂无支付数据</div>
      </div>
    </div>

    <AdminDataTable :loading="loading" :error="listError" :empty="!loading && !listError && entries.length === 0">
      <template #toolbar>
        <div class="admin-toolbar admin-toolbar--wide" style="margin: 0; padding: 0; border: none; box-shadow: none">
          <select v-model="entryType" @change="reload">
            <option value="">全部类型</option>
            <option value="deposit">充值</option>
            <option value="withdraw">提现</option>
            <option value="payment">结算</option>
            <option value="fee">佣金</option>
          </select>
        </div>
      </template>

      <template #head>
        <tr>
          <th>类型</th>
          <th>说明</th>
          <th style="text-align: right">金额</th>
          <th>时间</th>
        </tr>
      </template>

      <tr v-for="entry in entries" :key="entry.id">
        <td><span class="admin-tag admin-tag--muted">{{ ledgerTypeLabel(entry.entry_type) }}</span></td>
        <td>{{ entry.description || '—' }}</td>
        <td style="text-align: right" :class="entry.amount_cents >= 0 ? 'amount-plus' : 'amount-minus'">
          {{ entry.amount_cents >= 0 ? '+' : '' }}{{ formatCents(Math.abs(entry.amount_cents)) }}
        </td>
        <td>{{ formatDate(entry.created_at) }}</td>
      </tr>

      <template #empty>
        <EmptyState icon="wallet">暂无使用记录</EmptyState>
      </template>

      <template #footer>
        <AdminPager v-model:page="page" :page-size="pageSize" :total="total" @update:page="loadEntries" />
      </template>
    </AdminDataTable>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getAdminDashboard, listAdminLedger } from '@/api/admin'
import type { DashboardAnalytics, WalletLedgerEntry } from '@/types'
import { formatCents, formatDate, ledgerTypeLabel } from '@/utils'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminStatCard from '@/components/admin/AdminStatCard.vue'
import AdminAlert from '@/components/admin/AdminAlert.vue'
import AdminDataTable from '@/components/admin/AdminDataTable.vue'
import EmptyState from '@/components/EmptyState.vue'
import AdminPager from '@/components/AdminPager.vue'

const dayOptions = [1, 7, 30]
const days = ref(7)
const dashboard = ref<DashboardAnalytics | null>(null)
const entries = ref<WalletLedgerEntry[]>([])
const loading = ref(true)
const listError = ref('')
const error = ref('')
const entryType = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)

const totalLedgerAmount = computed(() =>
  dashboard.value?.ledger_by_type.reduce((s, i) => s + i.amount_cents, 0) ?? 0,
)

const summary = computed(() => {
  if (!dashboard.value) return null
  const items = dashboard.value.ledger_by_type
  const deposit = items.find((i) => i.entry_type === 'deposit')
  const payment = items.find((i) => i.entry_type === 'payment')
  const fee = items.find((i) => i.entry_type === 'fee')
  return {
    entry_count: items.reduce((s, i) => s + i.entry_count, 0),
    deposit_cents: deposit?.amount_cents ?? 0,
    payment_cents: payment?.amount_cents ?? 0,
    fee_cents: fee?.amount_cents ?? 0,
  }
})

function percent(part: number, total: number) {
  if (!total) return '0'
  return ((part / total) * 100).toFixed(1)
}

function channelLabel(channel: string) {
  const map: Record<string, string> = { alipay: '支付宝', stripe: 'Stripe', easypay: 'EasyPay' }
  return map[channel] ?? channel
}

function channelPct(amount: number) {
  const total = dashboard.value?.payment.total_income_cents ?? 0
  return total ? (amount / total) * 100 : 0
}

async function loadDashboard() {
  try {
    dashboard.value = await getAdminDashboard(days.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载概览失败'
  }
}

async function loadEntries() {
  listError.value = ''
  try {
    const data = await listAdminLedger({
      page: page.value,
      page_size: pageSize,
      entry_type: entryType.value || undefined,
    })
    entries.value = data.items
    total.value = data.total
  } catch (e) {
    listError.value = e instanceof Error ? e.message : '加载失败'
  }
}

async function reload() {
  loading.value = true
  error.value = ''
  page.value = 1
  await Promise.all([loadDashboard(), loadEntries()])
  loading.value = false
}

function setDays(value: number) {
  days.value = value
  reload()
}

onMounted(reload)
</script>
