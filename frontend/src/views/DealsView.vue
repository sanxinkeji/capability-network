<template>
  <div class="app-page deals-page">
    <ShopPageHeader
      title="我的订单"
      subtitle="待付款 · 待发货 · 待收货 · 平台担保交易"
    />

    <CommerceTabs v-model="activeTab" :tabs="tabs" />

    <div v-if="error" class="error-msg">{{ error }}</div>
    <LoadingSkeleton v-if="loading" />

    <EmptyState v-else-if="filteredDeals.length === 0" icon="clipboard">
      <template v-if="activeTab === 'all'">
        暂无订单，去
        <RouterLink to="/app/market">首页逛逛</RouterLink>
        选个 AI 服务吧。
      </template>
      <template v-else-if="activeTab === 'pending'">
        没有待付款订单。
        <RouterLink to="/app/wallet">去充值</RouterLink>
        后可继续付款。
      </template>
      <template v-else>该状态下暂无订单</template>
    </EmptyState>

    <div v-else class="order-list">
      <CommerceDealCard
        v-for="deal in filteredDeals"
        :key="deal.id"
        :deal="deal"
        :to="dealLink(deal)"
        :viewer-role="viewerRole(deal)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { listDeals } from '@/api/deals'
import { useAuthStore } from '@/stores/auth'
import type { Deal } from '@/types'
import { dealTabKey, type DealViewerRole } from '@/utils'
import CommerceTabs from '@/components/CommerceTabs.vue'
import CommerceDealCard from '@/components/CommerceDealCard.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'
import EmptyState from '@/components/EmptyState.vue'
import ShopPageHeader from '@/components/ShopPageHeader.vue'

const auth = useAuthStore()
const route = useRoute()
const deals = ref<Deal[]>([])
const loading = ref(true)
const error = ref('')
const activeTab = ref('all')

const tabDefs = [
  { key: 'all', label: '全部' },
  { key: 'pending', label: '待付款' },
  { key: 'active', label: '待发货' },
  { key: 'delivered', label: '待收货' },
  { key: 'done', label: '已完成' },
  { key: 'dispute', label: '退款/售后' },
]

const tabs = computed(() =>
  tabDefs.map((tab) => ({
    ...tab,
    count:
      tab.key === 'all'
        ? undefined
        : deals.value.filter((d) => dealTabKey(d.status) === tab.key).length,
  })),
)

const filteredDeals = computed(() => {
  if (activeTab.value === 'all') return deals.value
  return deals.value.filter((d) => dealTabKey(d.status) === activeTab.value)
})

function dealLink(deal: Deal) {
  if (['in_progress', 'delivered', 'disputed', 'paid'].includes(deal.status)) {
    return `/app/deals/${deal.id}/chat`
  }
  return `/app/deals/${deal.id}`
}

function viewerRole(deal: Deal): DealViewerRole {
  const uid = auth.user?.id
  if (!uid) return 'other'
  if (deal.buyer_id === uid) return 'buyer'
  if (deal.seller_id === uid) return 'seller'
  return 'other'
}

async function loadDeals() {
  loading.value = true
  error.value = ''
  try {
    if (!auth.user) await auth.fetchProfile()
    const data = await listDeals({ page: 1, page_size: 50 })
    deals.value = data.items
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

watch(
  () => route.query.tab,
  (tab) => {
    if (typeof tab === 'string' && tabDefs.some((t) => t.key === tab)) {
      activeTab.value = tab
    }
  },
  { immediate: true },
)

onMounted(loadDeals)
</script>
