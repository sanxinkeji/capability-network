<template>
  <div>
    <AdminPageHeader title="管理控制台" subtitle="平台运营数据总览与趋势分析">
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
        <button class="btn btn-secondary btn-sm" :disabled="loading" @click="loadData">刷新</button>
      </template>
    </AdminPageHeader>

    <AdminAlert v-if="error" :message="error" type="error" />
    <LoadingSkeleton v-if="loading" :rows="3" />

    <template v-else-if="data">
      <div class="admin-stat-grid admin-stat-grid--4 admin-stat-grid--dense">
        <AdminStatCard icon="users" label="用户" :value="data.stats.users_total" :sub="`今日 +${data.stats.users_today}`" tone="primary" link-to="/admin/users" />
        <AdminStatCard icon="clipboard" label="订单" :value="data.stats.deals_total" :sub="`今日 +${data.stats.deals_today}`" tone="primary" link-to="/admin/deals" />
        <AdminStatCard icon="package" label="供给" :value="data.stats.offers_published ?? 0" sub="已发布" tone="success" link-to="/admin/offers" />
        <AdminStatCard icon="target" label="需求" :value="data.stats.intents_open ?? 0" sub="开放中" tone="success" link-to="/admin/intents" />
        <AdminStatCard icon="wallet" label="今日充值" :value="formatCents(data.payment.today_income_cents)" :sub="`${data.payment.today_orders} 笔`" tone="warning" link-to="/admin/payments" />
        <AdminStatCard icon="chart" label="累计充值" :value="formatCents(data.stats.wallet_deposits_cents ?? 0)" small-value tone="primary" link-to="/admin/finance" />
        <AdminStatCard icon="wallet" label="待审提现" :value="data.stats.withdrawals_pending ?? 0" warn tone="danger" link-to="/admin/withdrawals" />
        <AdminStatCard icon="clipboard" label="争议订单" :value="data.stats.deals_disputed" warn tone="danger" link-to="/admin/deals?status=disputed" />
        <AdminStatCard icon="agent" label="活跃 Agent Key" :value="data.stats.agent_keys_active ?? 0" :sub="`${data.stats.agent_users_total ?? 0} 用户`" tone="primary" link-to="/admin/agent-keys" />
      </div>

      <div class="admin-split-grid admin-split-grid--wide">
        <div class="admin-panel">
          <div class="admin-panel__header"><h3>订单状态分布</h3></div>
          <div v-if="data.deals_by_status.length" class="admin-distribution">
            <div class="admin-distribution__chart">
              <div
                v-for="(item, idx) in data.deals_by_status"
                :key="item.status"
                class="admin-distribution__slice"
                :style="donutSliceStyle(item.count, idx)"
                :title="`${dealStatusLabel(item.status)}: ${item.count}`"
              />
            </div>
            <table class="admin-mini-table">
              <thead><tr><th>状态</th><th>数量</th><th>占比</th></tr></thead>
              <tbody>
                <tr v-for="item in data.deals_by_status" :key="item.status">
                  <td>{{ dealStatusLabel(item.status) }}</td>
                  <td>{{ item.count }}</td>
                  <td>{{ percent(item.count, totalDeals) }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="admin-panel__empty">暂无订单数据</div>
        </div>

        <div class="admin-panel">
          <div class="admin-panel__header"><h3>流水类型分布</h3></div>
          <table v-if="data.ledger_by_type.length" class="admin-mini-table admin-mini-table--full">
            <thead><tr><th>类型</th><th>笔数</th><th>金额</th></tr></thead>
            <tbody>
              <tr v-for="item in data.ledger_by_type" :key="item.entry_type">
                <td>{{ ledgerTypeLabel(item.entry_type) }}</td>
                <td>{{ item.entry_count }}</td>
                <td>{{ formatCents(item.amount_cents) }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="admin-panel__empty">暂无流水数据</div>
        </div>
      </div>

      <div class="admin-panel admin-panel--chart">
        <div class="admin-panel__header">
          <h3>增长趋势</h3>
          <div class="admin-chart-legend">
            <span class="admin-chart-legend__item admin-chart-legend__item--income">新增用户</span>
            <span class="admin-chart-legend__item admin-chart-legend__item--orders">新增订单</span>
          </div>
        </div>
        <div class="admin-dual-chart">
          <div class="admin-dual-chart__bars">
            <div v-for="(point, idx) in data.daily_users" :key="point.date" class="admin-dual-chart__col">
              <div class="admin-dual-chart__bar admin-dual-chart__bar--income" :style="{ height: `${barHeight(point.count, maxUsers)}%` }" />
              <div class="admin-dual-chart__bar admin-dual-chart__bar--orders" :style="{ height: `${barHeight(data.daily_deals[idx]?.count ?? 0, maxDeals)}%` }" />
            </div>
          </div>
          <div class="admin-dual-chart__labels">
            <span v-for="(point, idx) in data.daily_users" :key="point.date">
              {{ idx % labelStep === 0 ? formatShortDate(point.date) : '' }}
            </span>
          </div>
        </div>
      </div>

      <div class="admin-panel">
        <div class="admin-panel__header"><h3>最活跃用户 Top 12</h3></div>
        <div v-if="data.top_active_users.length" class="admin-active-users">
          <div v-for="(user, idx) in data.top_active_users" :key="user.email" class="admin-active-users__row">
            <span class="admin-rank-list__idx">{{ idx + 1 }}</span>
            <span class="admin-active-users__email">{{ user.email }}</span>
            <span class="admin-active-users__bar-wrap">
              <span class="admin-active-users__bar" :style="{ width: `${barWidth(user.deal_count)}%` }" />
            </span>
            <strong>{{ user.deal_count }} 单</strong>
          </div>
        </div>
        <div v-else class="admin-panel__empty">暂无活跃数据</div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getAdminDashboard } from '@/api/admin'
import type { DashboardAnalytics } from '@/types'
import { formatCents, ledgerTypeLabel } from '@/utils'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminStatCard from '@/components/admin/AdminStatCard.vue'
import AdminAlert from '@/components/admin/AdminAlert.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'

const dayOptions = [7, 30]
const days = ref(7)
const data = ref<DashboardAnalytics | null>(null)
const loading = ref(true)
const error = ref('')

const totalDeals = computed(() => data.value?.stats.deals_total ?? 0)
const maxUsers = computed(() => Math.max(...(data.value?.daily_users.map((d) => d.count) ?? [0]), 1))
const maxDeals = computed(() => Math.max(...(data.value?.daily_deals.map((d) => d.count) ?? [0]), 1))
const maxActiveDeals = computed(() =>
  Math.max(...(data.value?.top_active_users.map((u) => u.deal_count) ?? [0]), 1),
)
const labelStep = computed(() => (days.value <= 7 ? 1 : 5))

const donutColors = ['#3b82f6', '#14b8a6', '#f59e0b', '#ef4444', '#8b5cf6', '#6b7280']

function barHeight(value: number, max: number) {
  return Math.max(4, Math.round((value / max) * 100))
}

function barWidth(count: number) {
  return Math.max(8, Math.round((count / maxActiveDeals.value) * 100))
}

function formatShortDate(iso: string) {
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function percent(part: number, total: number) {
  if (!total) return '0'
  return ((part / total) * 100).toFixed(1)
}

function dealStatusLabel(status: string) {
  const map: Record<string, string> = {
    pending: '待支付', paid: '已支付', in_progress: '进行中', delivered: '已交付',
    completed: '已完成', disputed: '争议中', refunded: '已退款', cancelled: '已取消',
  }
  return map[status] ?? status
}

function donutSliceStyle(count: number, idx: number) {
  const total = data.value?.deals_by_status.reduce((s, i) => s + i.count, 0) ?? 1
  const pct = (count / total) * 100
  return {
    flex: `${pct} 1 0`,
    background: donutColors[idx % donutColors.length],
  }
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    data.value = await getAdminDashboard(days.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function setDays(value: number) {
  days.value = value
  loadData()
}

onMounted(loadData)
</script>
