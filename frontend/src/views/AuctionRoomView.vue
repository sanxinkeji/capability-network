<template>
  <div class="app-page app-page--wide">
    <div class="commerce-page-head">
      <div>
        <h1>竞价室</h1>
        <p class="commerce-page-head__sub">Agent 通道多命中时的出价与选定</p>
      </div>
      <RouterLink to="/app/intents" class="btn btn-secondary btn-sm">返回需求</RouterLink>
    </div>

    <section v-if="intent" class="deal-goods-card glass-card intent-banner">
      <div class="deal-goods-card__thumb intent-banner__icon" aria-hidden="true">竞</div>
      <div class="deal-goods-card__main">
        <h2 class="deal-goods-card__title">{{ intent.title }}</h2>
        <p class="intent-banner__meta">
          预算上限 ¥{{ (intent.budget_max / 100).toFixed(2) }}
          · 状态 {{ statusLabel(auction?.status ?? intent.status) }}
        </p>
      </div>
    </section>

    <div v-if="error" class="error-msg">{{ error }}</div>
    <LoadingSkeleton v-if="loading" />

    <template v-else>
      <HelpTip v-if="isBuyer && !auction" variant="info" title="等待报名">
        至少需 2 个 Agent 调用「报名命中」后，方可启动拍价。可将需求 ID 提供给 Agent，或使用 MCP 工具
        <code>join_auction</code>。
      </HelpTip>

      <HelpTip v-else-if="isBuyer && auction?.status === 'matched'" variant="warn" title="可启动拍价">
        已有 {{ auction.participant_count }} 个参与者，确认后即可进入出价轮。
      </HelpTip>

      <section v-if="auction" class="glass-card auction-section">
        <div class="auction-section__head">
          <h3>参与者（{{ auction.participant_count }}/8）</h3>
          <button type="button" class="btn btn-secondary btn-sm" @click="loadRoom">刷新</button>
        </div>
        <EmptyState v-if="auction.participants.length === 0" icon="users">
          暂无参与者
        </EmptyState>
        <ul v-else class="auction-list">
          <li v-for="item in auction.participants" :key="item.id">
            <span>Offer {{ shortId(item.offer_id) }}</span>
            <span class="auction-list__meta">{{ formatTime(item.joined_at) }}</span>
          </li>
        </ul>
      </section>

      <section v-if="auction && auction.bids.length > 0" class="glass-card auction-section">
        <h3>出价列表</h3>
        <ul class="auction-list auction-list--bids">
          <li v-for="bid in sortedBids" :key="bid.id">
            <div>
              <span class="auction-bid-price">¥{{ (bid.amount_cents / 100).toFixed(2) }}</span>
              <span class="auction-list__meta">Offer {{ shortId(bid.offer_id) }}</span>
            </div>
            <button
              v-if="isBuyer && auction.status === 'auctioning'"
              type="button"
              class="btn btn-primary btn-sm"
              :disabled="selectingId === bid.id"
              @click="handleSelect(bid.id)"
            >
              {{ selectingId === bid.id ? '选定中…' : '选定' }}
            </button>
          </li>
        </ul>
      </section>

      <section v-if="isParticipant && auction?.status === 'auctioning'" class="glass-card auction-section">
        <h3>提交出价</h3>
        <p class="auction-hint">出价须 ≤ 预算 ¥{{ ((auction?.budget_cents ?? 0) / 100).toFixed(2) }}</p>
        <form class="auction-bid-form" @submit.prevent="handleBid">
          <label>
            金额（元）
            <input v-model="bidYuan" type="number" min="0.01" step="0.01" required />
          </label>
          <button type="submit" class="btn btn-primary" :disabled="bidding">
            {{ bidding ? '提交中…' : '出价' }}
          </button>
        </form>
      </section>

      <div v-if="isBuyer" class="auction-actions">
        <button
          v-if="auction?.status === 'matched'"
          type="button"
          class="btn btn-primary"
          :disabled="starting"
          @click="handleStart"
        >
          {{ starting ? '启动中…' : '启动拍价' }}
        </button>
        <RouterLink
          v-if="auction?.deal_id"
          :to="`/app/deals/${auction.deal_id}`"
          class="btn btn-primary"
        >
          查看订单
        </RouterLink>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { getIntent } from '@/api'
import { getIntentAuction, selectBid, startAuction, submitBid } from '@/api/auctions'
import { payDeal } from '@/api/deals'
import type { AuctionRoom, Intent } from '@/types'
import { useAuthStore } from '@/stores/auth'
import HelpTip from '@/components/HelpTip.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'
import EmptyState from '@/components/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const intentId = route.params.intentId as string

const intent = ref<Intent | null>(null)
const auction = ref<AuctionRoom | null>(null)
const loading = ref(true)
const error = ref('')
const starting = ref(false)
const bidding = ref(false)
const selectingId = ref<string | null>(null)
const bidYuan = ref('')

const isBuyer = computed(() => intent.value?.user_id === auth.user?.id)
const isParticipant = computed(
  () =>
    !!auction.value?.participants.some((item) => item.user_id === auth.user?.id),
)
const sortedBids = computed(() =>
  [...(auction.value?.bids ?? [])].sort((a, b) => a.amount_cents - b.amount_cents),
)

function statusLabel(status: string) {
  const map: Record<string, string> = {
    open: '开放报名',
    matched: '已多命中',
    auctioning: '出价中',
    selected: '已选定',
    deal: '已成交',
  }
  return map[status] ?? status
}

function shortId(id: string) {
  return id.slice(0, 8)
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString()
}

async function loadRoom() {
  loading.value = true
  error.value = ''
  try {
    if (!auth.user) await auth.fetchProfile()
    intent.value = await getIntent(intentId)
    try {
      auction.value = await getIntentAuction(intentId)
      if (auction.value.deal_id && auction.value.status === 'deal') {
        router.replace(`/app/deals/${auction.value.deal_id}`)
      }
    } catch (e) {
      if (e instanceof Error && e.message.includes('auction not found')) {
        auction.value = null
      } else if (e instanceof Error && e.message.includes('404')) {
        auction.value = null
      } else {
        throw e
      }
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function handleStart() {
  starting.value = true
  error.value = ''
  try {
    auction.value = await startAuction(intentId)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '启动拍价失败'
  } finally {
    starting.value = false
  }
}

async function handleBid() {
  if (!auction.value) return
  const cents = Math.round(Number(bidYuan.value) * 100)
  if (!Number.isFinite(cents) || cents <= 0) {
    error.value = '请输入有效金额'
    return
  }
  bidding.value = true
  error.value = ''
  try {
    auction.value = await submitBid(auction.value.id, cents)
    bidYuan.value = ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : '出价失败'
  } finally {
    bidding.value = false
  }
}

async function handleSelect(bidId: string) {
  if (!auction.value) return
  const ok = confirm('确认选定该出价并创建订单？')
  if (!ok) return
  selectingId.value = bidId
  error.value = ''
  try {
    auction.value = await selectBid(auction.value.id, bidId)
    if (auction.value.deal_id) {
      try {
        await payDeal(auction.value.deal_id)
      } catch {
        router.push({ path: `/app/deals/${auction.value.deal_id}`, query: { pay_pending: '1' } })
        return
      }
      router.push(`/app/deals/${auction.value.deal_id}`)
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '选定失败'
  } finally {
    selectingId.value = null
  }
}

onMounted(loadRoom)
</script>

<style scoped>
.intent-banner {
  margin-bottom: 14px;
}

.intent-banner__icon {
  background: linear-gradient(145deg, #fff7e6, #ffe7ba);
  color: rgba(250, 140, 22, 0.5);
}

.intent-banner__meta {
  margin: 0;
  font-size: 13px;
  color: var(--color-label-secondary);
}

.auction-section {
  margin-bottom: 14px;
  padding: 16px;
}

.auction-section__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.auction-section h3 {
  margin: 0 0 10px;
  font-size: 15px;
}

.auction-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.auction-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--color-border-subtle);
}

.auction-list li:last-child {
  border-bottom: none;
}

.auction-list__meta {
  font-size: 12px;
  color: var(--color-label-tertiary);
}

.auction-bid-price {
  font-weight: 600;
  margin-right: 8px;
}

.auction-hint {
  margin: 0 0 10px;
  font-size: 13px;
  color: var(--color-label-secondary);
}

.auction-bid-form {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  gap: 12px;
}

.auction-bid-form label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
}

.auction-bid-form input {
  min-width: 140px;
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
}

.auction-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 8px;
}
</style>
