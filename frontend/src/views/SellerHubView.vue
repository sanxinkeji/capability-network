<template>
  <div class="app-page seller-hub">
    <ShopPageHeader
      :title="auth.user?.shop_name || '卖家中心'"
      subtitle="管理商品、接入 AI 工具、处理订单"
    />

    <section class="seller-stats" aria-label="经营概览">
      <div class="seller-stat glass-card">
        <span class="seller-stat__value">{{ loading ? '—' : stats.published }}</span>
        <span class="seller-stat__label">在售商品</span>
      </div>
      <RouterLink
        to="/app/deals"
        class="seller-stat glass-card"
        :class="{ 'seller-stat--alert': stats.todo > 0 }"
      >
        <span class="seller-stat__value">{{ loading ? '—' : stats.todo }}</span>
        <span class="seller-stat__label">待办订单</span>
      </RouterLink>
      <div class="seller-stat glass-card">
        <span class="seller-stat__value">{{ loading ? '—' : stats.completed }}</span>
        <span class="seller-stat__label">已完成</span>
      </div>
      <div class="seller-stat glass-card">
        <span class="seller-stat__value seller-stat__value--money">¥{{ loading ? '—' : revenueYuan }}</span>
        <span class="seller-stat__label">累计营收</span>
      </div>
    </section>

    <p v-if="error" class="seller-error">{{ error }}</p>

    <section v-if="!loading && stats.todo > 0" class="seller-todo glass-card">
      <div class="seller-todo__head">
        <strong>有 {{ stats.todo }} 笔订单等待你处理</strong>
        <RouterLink to="/app/deals" class="seller-todo__link">去处理 →</RouterLink>
      </div>
      <p class="seller-todo__hint">
        买家已付款，进入订单聊天补充交付物或与买家沟通；确认收货后平台放款。
      </p>
    </section>

    <h2 class="seller-section-title">店铺管理</h2>
    <section class="seller-grid">
      <RouterLink to="/app/offers" class="seller-card glass-card">
        <span class="seller-card__icon">🛍</span>
        <strong>商品管理</strong>
        <span>上架 / 发布 AI 技能商品</span>
      </RouterLink>
      <RouterLink v-if="platform.featureAgentEnabled" to="/app/agent" class="seller-card glass-card">
        <span class="seller-card__icon">🔑</span>
        <strong>开店助手</strong>
        <span>API Key 与 MCP 配置</span>
      </RouterLink>
      <RouterLink to="/connect" class="seller-card glass-card">
        <span class="seller-card__icon">📖</span>
        <strong>接入指南</strong>
        <span>OpenClaw / Hermes 文档</span>
      </RouterLink>
      <RouterLink to="/app/offers/new" class="seller-card glass-card seller-card--primary">
        <span class="seller-card__icon">＋</span>
        <strong>发布新商品</strong>
        <span>添加到首页集市</span>
      </RouterLink>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { listOffers } from '@/api'
import { listDeals } from '@/api/deals'
import { useAuthStore } from '@/stores/auth'
import { usePlatformStore } from '@/stores/platform'
import ShopPageHeader from '@/components/ShopPageHeader.vue'

const auth = useAuthStore()
const platform = usePlatformStore()

const loading = ref(true)
const error = ref('')
const stats = ref({ published: 0, todo: 0, completed: 0, revenueCents: 0 })

const revenueYuan = computed(() => (stats.value.revenueCents / 100).toFixed(2))

async function loadStats() {
  loading.value = true
  error.value = ''
  try {
    const myId = auth.user?.id
    const [offersData, dealsData] = await Promise.all([
      listOffers({ page: 1, page_size: 100 }),
      listDeals({ page: 1, page_size: 100 }),
    ])

    const published = offersData.items.filter((o) => o.status === 'published').length
    const sellerDeals = dealsData.items.filter((d) => d.seller_id === myId)
    const todo = sellerDeals.filter((d) => d.status === 'paid' || d.status === 'in_progress').length
    const completedDeals = sellerDeals.filter((d) => d.status === 'completed')
    const revenueCents = completedDeals.reduce((sum, d) => sum + (d.amount_cents || 0), 0)

    stats.value = { published, todo, completed: completedDeals.length, revenueCents }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '经营数据加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadStats)
</script>

<style scoped>
.seller-hub {
  max-width: 960px;
}

.seller-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

@media (min-width: 769px) {
  .seller-stats {
    grid-template-columns: repeat(4, 1fr);
  }
}

.seller-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 18px 12px !important;
  text-decoration: none;
  color: inherit;
}

.seller-stat--alert {
  border-color: rgba(238, 10, 36, 0.3);
  background: #fff8f6;
}

.seller-stat__value {
  font-size: 26px;
  font-weight: 700;
  color: var(--color-label);
  line-height: 1.1;
}

.seller-stat__value--money {
  color: var(--color-commerce);
  font-size: 22px;
}

.seller-stat__label {
  font-size: 12px;
  color: var(--color-label-tertiary);
}

.seller-error {
  margin: 0 0 12px;
  color: #cf1322;
  font-size: 14px;
}

.seller-todo {
  padding: 16px !important;
  margin-bottom: 20px;
  border-color: rgba(238, 10, 36, 0.2);
}

.seller-todo__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}

.seller-todo__head strong {
  font-size: 15px;
  color: var(--color-label);
}

.seller-todo__link {
  flex-shrink: 0;
  color: var(--color-commerce);
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
}

.seller-todo__hint {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-label-secondary);
}

.seller-section-title {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 700;
  color: var(--color-label);
}

.seller-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

@media (min-width: 769px) {
  .seller-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

.seller-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 6px;
  padding: 20px 12px !important;
  text-decoration: none;
  color: inherit;
  transition: box-shadow 0.15s, transform 0.15s;
}

.seller-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
}

.seller-card__icon {
  font-size: 28px;
}

.seller-card strong {
  font-size: 14px;
}

.seller-card span:last-child {
  font-size: 11px;
  color: var(--color-label-tertiary);
}

.seller-card--primary {
  border-color: rgba(238, 10, 36, 0.25);
  background: #fff8f6;
}
</style>
