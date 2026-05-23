<template>

  <div class="app-page app-page--wide">

    <div class="commerce-page-head">

      <div>

        <h1>匹配结果</h1>

        <p class="commerce-page-head__sub">为你精选 TOP 候选供给</p>

      </div>

      <RouterLink to="/app/intents" class="btn btn-secondary btn-sm">返回需求</RouterLink>

    </div>



    <HelpTip variant="warn" title="下单说明">
      {{ MATCH_PAY_HINT }}
    </HelpTip>

    <section
      v-if="showAuctionPrompt"
      class="glass-card auction-prompt"
    >
      <h2 class="auction-prompt__title">检测到多个 Agent 命中</h2>
      <p class="auction-prompt__text">
        不能自动成交，请启动拍价由 Agent 出价后选定，或手动选择一家直接下单。
      </p>
      <div class="auction-prompt__actions">
        <RouterLink :to="`/app/auctions/${intentId}`" class="btn btn-primary btn-sm">
          启动拍价
        </RouterLink>
        <span class="auction-prompt__hint">也可在下方卡片中手动选择</span>
      </div>
    </section>

    <section v-if="intent" class="deal-goods-card glass-card intent-banner">

      <div class="deal-goods-card__thumb intent-banner__icon" aria-hidden="true">需</div>

      <div class="deal-goods-card__main">

        <h2 class="deal-goods-card__title">{{ intent.title }}</h2>

        <p class="intent-banner__meta">

          预算

          <span class="price-commerce price-inline">

            <span class="price-symbol">¥</span>

            <span class="price-int">{{ budgetParts.int }}</span>

            <span class="price-dec">{{ budgetParts.dec }}</span>

          </span>

          · {{ categoryLabel(intent.category) }}

        </p>

      </div>

    </section>



    <div v-if="error" class="error-msg">{{ error }}</div>

    <LoadingSkeleton v-if="loading" />



    <EmptyState v-else-if="!error && candidates.length === 0" icon="search">

      暂无匹配供给。请确认已有<strong>同类目</strong>且<strong>同通道</strong>的已发布供给，预算 ≥ 供给价格。

      可先访问 <RouterLink to="/app/market">能力市场</RouterLink> 查看。

    </EmptyState>



    <template v-else>

      <p class="match-result-hint">

        TOP-{{ topN }} 匹配 · 共 {{ totalCandidates }} 个候选

      </p>



      <div class="product-grid product-grid--match">

        <MatchCandidateCard

          v-for="item in candidates"

          :key="item.match_log_id"

          :candidate="item"

          :intent="intent"

          :creating="creatingId === item.match_log_id"

          @create-deal="handleCreateDeal"

        />

      </div>

    </template>

  </div>

</template>



<script setup lang="ts">

import { computed, onMounted, ref } from 'vue'

import { RouterLink, useRoute, useRouter } from 'vue-router'

import { getIntent, runMatching } from '@/api'

import { createDeal, payDeal } from '@/api/deals'

import type { Intent, MatchCandidate } from '@/types'

import { categoryLabel } from '@/utils'
import { MATCH_PAY_HINT } from '@/utils/platformGuide'
import HelpTip from '@/components/HelpTip.vue'

import MatchCandidateCard from '@/components/MatchCandidateCard.vue'

import LoadingSkeleton from '@/components/LoadingSkeleton.vue'

import EmptyState from '@/components/EmptyState.vue'



const route = useRoute()

const router = useRouter()

const intentId = route.params.intentId as string



const intent = ref<Intent | null>(null)

const candidates = ref<MatchCandidate[]>([])

const totalCandidates = ref(0)

const topN = ref(5)

const loading = ref(true)

const error = ref('')

const creatingId = ref<string | null>(null)



const budgetParts = computed(() => {

  const cents = intent.value?.budget_max ?? 0

  const [int, dec] = (cents / 100).toFixed(2).split('.')

  return { int, dec: `.${dec}` }

})



const showAuctionPrompt = computed(() => {

  if (!intent.value) return false

  const agentCandidates = candidates.value.filter((item) => item.channel === 'agent')

  return intent.value.channel === 'agent' && agentCandidates.length >= 2

})



async function loadMatching() {

  loading.value = true

  error.value = ''

  try {

    intent.value = await getIntent(intentId)

    const result = await runMatching(intentId, topN.value)

    candidates.value = result.candidates

    totalCandidates.value = result.total_candidates

  } catch (e) {

    error.value = e instanceof Error ? e.message : '匹配失败'

  } finally {

    loading.value = false

  }

}



async function handleCreateDeal(item: MatchCandidate) {

  const price = (item.price_cents / 100).toFixed(2)

  const ok = confirm(

    `确认选择「${item.title}」？\n\n将创建订单并尝试从钱包支付 ¥${price}。\n余额不足会进入待支付，请先到钱包充值。`,

  )

  if (!ok) return

  creatingId.value = item.match_log_id

  error.value = ''

  try {

    const payload = item.match_log_id

      ? { match_log_id: item.match_log_id }

      : { intent_id: intentId, offer_id: item.offer_id }

    const deal = await createDeal(payload)

    try {

      await payDeal(deal.id)

      router.push(`/app/deals/${deal.id}`)

    } catch {

      router.push({ path: `/app/deals/${deal.id}`, query: { pay_pending: '1' } })

    }

  } catch (e) {

    error.value = e instanceof Error ? e.message : '创建成交失败'

  } finally {

    creatingId.value = null

  }

}



onMounted(loadMatching)

</script>



<style scoped>

.intent-banner {

  margin-bottom: 14px;

}



.intent-banner__icon {

  background: linear-gradient(145deg, #e8f4ff, #d6e4ff);

  color: rgba(22, 119, 255, 0.45);

}



.intent-banner__meta {

  margin: 0;

  font-size: 13px;

  color: var(--color-label-secondary);

}



.price-inline {

  display: inline-flex;

  align-items: baseline;

  font-size: 15px;

}



.match-result-hint {

  margin: 0 0 10px;

  font-size: 13px;

  color: var(--color-label-tertiary);

}



.auction-prompt {

  margin-bottom: 14px;

  padding: 16px;

}



.auction-prompt__title {

  margin: 0 0 8px;

  font-size: 16px;

}



.auction-prompt__text {

  margin: 0 0 12px;

  font-size: 14px;

  color: var(--color-label-secondary);

}



.auction-prompt__actions {

  display: flex;

  flex-wrap: wrap;

  align-items: center;

  gap: 10px;

}



.auction-prompt__hint {

  font-size: 13px;

  color: var(--color-label-tertiary);

}



.product-grid--match {

  grid-template-columns: 1fr;

}



@media (min-width: 640px) {

  .product-grid--match {

    grid-template-columns: repeat(2, 1fr);

  }

}



@media (min-width: 1024px) {

  .product-grid--match {

    grid-template-columns: repeat(3, 1fr);

  }

}

</style>

