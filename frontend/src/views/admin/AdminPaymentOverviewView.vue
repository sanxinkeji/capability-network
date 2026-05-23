<template>
  <div>
    <AdminPageHeader title="支付概览" subtitle="充值收入、订单趋势与消费排行">
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
            {{ d }} 天
          </button>
        </div>
        <button class="btn btn-secondary btn-sm" :disabled="loading" @click="loadStats">刷新</button>
      </template>
    </AdminPageHeader>

    <AdminAlert v-if="error" :message="error" type="error" />

    <div v-if="stats" class="admin-stat-grid admin-stat-grid--4">
      <AdminStatCard
        icon="wallet"
        label="今日收入"
        :value="formatCents(stats.today_income_cents)"
        :sub="`${stats.today_orders} 笔订单`"
        tone="success"
      />
      <AdminStatCard
        icon="chart"
        label="总收入"
        :value="formatCents(stats.total_income_cents)"
        :sub="`${stats.total_orders} 笔订单`"
        tone="primary"
      />
      <AdminStatCard
        icon="clipboard"
        label="今日订单"
        :value="stats.today_orders"
        tone="warning"
      />
      <AdminStatCard
        icon="target"
        label="平均金额"
        :value="formatCents(stats.avg_amount_cents)"
        tone="danger"
      />
    </div>

    <div class="admin-panel admin-panel--chart">
      <div class="admin-panel__header">
        <h3>每日收入</h3>
        <div class="admin-chart-legend">
          <span class="admin-chart-legend__item admin-chart-legend__item--income">收入</span>
          <span class="admin-chart-legend__item admin-chart-legend__item--orders">订单数</span>
        </div>
      </div>
      <div v-if="stats" class="admin-dual-chart">
        <div class="admin-dual-chart__bars">
          <div
            v-for="point in stats.daily"
            :key="point.date"
            class="admin-dual-chart__col"
            :title="`${point.date} · ${formatCents(point.income_cents)} · ${point.order_count} 单`"
          >
            <div
              class="admin-dual-chart__bar admin-dual-chart__bar--income"
              :style="{ height: `${barHeight(point.income_cents, maxIncome)}%` }"
            />
            <div
              class="admin-dual-chart__bar admin-dual-chart__bar--orders"
              :style="{ height: `${barHeight(point.order_count, maxOrders)}%` }"
            />
          </div>
        </div>
        <div class="admin-dual-chart__labels">
          <span v-for="(point, idx) in stats.daily" :key="point.date">
            {{ idx % labelStep === 0 ? formatShortDate(point.date) : '' }}
          </span>
        </div>
      </div>
      <div v-else-if="loading" class="admin-panel__empty">加载中…</div>
    </div>

    <div class="admin-split-grid">
      <div class="admin-panel">
        <div class="admin-panel__header"><h3>支付方式分布</h3></div>
        <ul v-if="stats?.channels.length" class="admin-channel-list">
          <li v-for="item in stats.channels" :key="item.channel">
            <div class="admin-channel-list__head">
              <span>{{ channelLabel(item.channel) }}</span>
              <strong>{{ formatCents(item.amount_cents) }}</strong>
            </div>
            <div class="admin-channel-list__bar">
              <span :style="{ width: `${channelPercent(item.amount_cents)}%` }" />
            </div>
            <small>{{ item.order_count }} 笔 · {{ channelPercent(item.amount_cents).toFixed(0) }}%</small>
          </li>
        </ul>
        <div v-else class="admin-panel__empty">暂无支付数据</div>
      </div>

      <div class="admin-panel">
        <div class="admin-panel__header"><h3>消费排行</h3></div>
        <ol v-if="stats?.top_users.length" class="admin-rank-list">
          <li v-for="(user, idx) in stats.top_users" :key="user.email">
            <span class="admin-rank-list__idx">{{ idx + 1 }}</span>
            <div class="admin-rank-list__body">
              <strong>{{ user.email }}</strong>
              <span>{{ user.display_name }}</span>
            </div>
            <strong class="admin-rank-list__amount">{{ formatCents(user.amount_cents) }}</strong>
          </li>
        </ol>
        <div v-else class="admin-panel__empty">暂无消费记录</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getAdminDashboard, getAdminPaymentStats, listAdminPaymentOrders } from '@/api/admin'
import type { PaymentStats } from '@/types'
import { formatCents } from '@/utils'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminStatCard from '@/components/admin/AdminStatCard.vue'
import AdminAlert from '@/components/admin/AdminAlert.vue'

const dayOptions = [7, 30, 90]
const days = ref(7)
const stats = ref<PaymentStats | null>(null)
const loading = ref(true)
const error = ref('')

const maxIncome = computed(() =>
  Math.max(...(stats.value?.daily.map((d) => d.income_cents) ?? [0]), 1),
)
const maxOrders = computed(() =>
  Math.max(...(stats.value?.daily.map((d) => d.order_count) ?? [0]), 1),
)
const labelStep = computed(() => (days.value <= 7 ? 1 : days.value <= 30 ? 5 : 10))

function barHeight(value: number, max: number) {
  return Math.max(4, Math.round((value / max) * 100))
}

function formatShortDate(iso: string) {
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function channelLabel(channel: string) {
  const map: Record<string, string> = {
    alipay: '支付宝',
    stripe: 'Stripe',
    easypay: 'EasyPay',
    wechat: '微信支付',
  }
  return map[channel] ?? channel
}

function channelPercent(amount: number) {
  const total = stats.value?.total_income_cents ?? 0
  if (!total) return 0
  return (amount / total) * 100
}

async function loadStats() {
  loading.value = true
  error.value = ''
  try {
    stats.value = await getAdminPaymentStats(days.value)
  } catch (e) {
    const msg = e instanceof Error ? e.message : ''
    if (msg.includes('404')) {
      try {
        const dashboard = await getAdminDashboard(days.value)
        stats.value = dashboard.payment
        error.value = ''
        return
      } catch {
        /* fall through */
      }
    }
    try {
      stats.value = await buildStatsFromOrders()
      if (stats.value) {
        error.value = ''
        return
      }
    } catch {
      /* ignore */
    }
    error.value = msg || '加载失败'
  } finally {
    loading.value = false
  }
}

async function buildStatsFromOrders(): Promise<PaymentStats | null> {
  const data = await listAdminPaymentOrders({ page: 1, page_size: 200, status: 'paid' })
  if (!data.items.length) {
    return {
      today_income_cents: 0,
      today_orders: 0,
      total_income_cents: 0,
      total_orders: 0,
      avg_amount_cents: 0,
      daily: [],
      channels: [],
      top_users: [],
    }
  }
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const rangeStart = new Date(today)
  rangeStart.setDate(rangeStart.getDate() - (days.value - 1))

  let todayIncome = 0
  let todayOrders = 0
  let totalIncome = 0
  const channelMap: Record<string, { amount_cents: number; order_count: number }> = {}
  const userMap: Record<string, { email: string; display_name: string; amount_cents: number }> = {}
  const dailyMap: Record<string, { income_cents: number; order_count: number }> = {}

  for (const order of data.items) {
    totalIncome += order.amount_cents
    const paidAt = order.paid_at ? new Date(order.paid_at) : new Date(order.created_at)
    if (paidAt >= today) {
      todayIncome += order.amount_cents
      todayOrders += 1
    }
    if (paidAt >= rangeStart) {
      const key = paidAt.toISOString().slice(0, 10)
      if (!dailyMap[key]) dailyMap[key] = { income_cents: 0, order_count: 0 }
      dailyMap[key].income_cents += order.amount_cents
      dailyMap[key].order_count += 1
    }
    if (!channelMap[order.channel]) channelMap[order.channel] = { amount_cents: 0, order_count: 0 }
    channelMap[order.channel].amount_cents += order.amount_cents
    channelMap[order.channel].order_count += 1
    const email = order.user_email || order.user_id || 'unknown'
    if (!userMap[email]) userMap[email] = { email, display_name: order.user_display_name || email, amount_cents: 0 }
    userMap[email].amount_cents += order.amount_cents
  }

  const daily: PaymentStats['daily'] = []
  for (let i = 0; i < days.value; i++) {
    const d = new Date(rangeStart)
    d.setDate(d.getDate() + i)
    const key = d.toISOString().slice(0, 10)
    daily.push({ date: key, income_cents: dailyMap[key]?.income_cents ?? 0, order_count: dailyMap[key]?.order_count ?? 0 })
  }

  const totalOrders = data.items.length
  return {
    today_income_cents: todayIncome,
    today_orders: todayOrders,
    total_income_cents: totalIncome,
    total_orders: totalOrders,
    avg_amount_cents: totalOrders ? Math.round(totalIncome / totalOrders) : 0,
    daily,
    channels: Object.entries(channelMap).map(([channel, v]) => ({ channel, ...v })),
    top_users: Object.values(userMap).sort((a, b) => b.amount_cents - a.amount_cents).slice(0, 10),
  }
}

function setDays(value: number) {
  days.value = value
  loadStats()
}

onMounted(loadStats)
</script>
