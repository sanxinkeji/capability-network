<template>

  <div class="app-page">

    <div class="commerce-page-head">

      <div>

        <h1>我的订单</h1>

        <p class="commerce-page-head__sub">托管支付 · 交付验收 · 资金由平台担保</p>

      </div>

    </div>

    <HelpTip v-if="!loading && !error">
      {{ BUYER_FLOW_HINT }}
    </HelpTip>

    <CommerceTabs v-model="activeTab" :tabs="tabs" />



    <div v-if="error" class="error-msg">{{ error }}</div>

    <LoadingSkeleton v-if="loading" />



    <EmptyState v-else-if="filteredDeals.length === 0" icon="clipboard">

      <template v-if="activeTab === 'all'">

        暂无订单。你可以
        <RouterLink to="/app/intents/new?mode=ai">AI 发需求</RouterLink>
        匹配下单，或在
        <RouterLink to="/app/market">能力市场</RouterLink>
        选用能力。

      </template>

      <template v-else-if="activeTab === 'pending'">

        没有待付款订单。
        <RouterLink to="/app/wallet">去钱包充值</RouterLink>
        后可继续支付。

      </template>

      <template v-else>该状态下暂无订单，试试其他筛选</template>

    </EmptyState>



    <div v-else class="order-list">

      <CommerceDealCard

        v-for="deal in filteredDeals"

        :key="deal.id"

        :deal="deal"

        :to="`/app/deals/${deal.id}`"

        :viewer-role="viewerRole(deal)"

      />

    </div>

  </div>

</template>



<script setup lang="ts">

import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { listDeals } from '@/api/deals'

import { useAuthStore } from '@/stores/auth'

import type { Deal } from '@/types'

import { dealTabKey, type DealViewerRole } from '@/utils'
import { BUYER_FLOW_HINT } from '@/utils/platformGuide'
import HelpTip from '@/components/HelpTip.vue'

import CommerceTabs from '@/components/CommerceTabs.vue'

import CommerceDealCard from '@/components/CommerceDealCard.vue'

import LoadingSkeleton from '@/components/LoadingSkeleton.vue'

import EmptyState from '@/components/EmptyState.vue'



const auth = useAuthStore()

const deals = ref<Deal[]>([])

const loading = ref(true)

const error = ref('')

const activeTab = ref('all')



const tabDefs = [

  { key: 'all', label: '全部' },

  { key: 'pending', label: '待付款' },

  { key: 'active', label: '进行中' },

  { key: 'delivered', label: '待收货' },

  { key: 'done', label: '已完成' },

  { key: 'dispute', label: '售后' },

]



const tabs = computed(() =>

  tabDefs.map((tab) => ({

    ...tab,

    count: tab.key === 'all' ? undefined : deals.value.filter((d) => dealTabKey(d.status) === tab.key).length,

  })),

)



const filteredDeals = computed(() => {

  if (activeTab.value === 'all') return deals.value

  return deals.value.filter((d) => dealTabKey(d.status) === activeTab.value)

})



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



onMounted(loadDeals)

</script>

