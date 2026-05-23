<template>
  <div class="market-page">
    <!-- 顶部逛店区：搜索 + 促销条 -->
    <div class="market-top glass-card">
      <div class="search-row">
        <span class="search-icon" aria-hidden="true">
          <AppIcon name="search" size="sm" />
        </span>
        <input
          v-model="searchQuery"
          type="search"
          class="search-input"
          placeholder="搜索能力、关键词，如 Logo、摘要、API…"
          enterkeyhint="search"
        />
        <button v-if="searchQuery" type="button" class="search-clear" @click="searchQuery = ''">
          清除
        </button>
      </div>
      <div class="promo-strip">
        <span class="tag-promo">平台托管</span>
        <span class="promo-text">智能体能力 · 支付后自动交付 · 验收放款</span>
      </div>
    </div>

    <HelpTip title="如何下单？">
      {{ MARKET_BUY_HINT }}
      也可直接 <RouterLink to="/app/intents/new?mode=ai">AI 发需求</RouterLink> 再匹配。
    </HelpTip>

    <!-- 类目横滑（淘宝/拼多多频道条） -->
    <div class="category-scroll">
      <button
        type="button"
        class="category-chip"
        :class="{ active: categoryFilter === 'all' }"
        @click="categoryFilter = 'all'"
      >
        全部
      </button>
      <button
        v-for="cat in CATEGORY_OPTIONS"
        :key="cat.value"
        type="button"
        class="category-chip"
        :class="{ active: categoryFilter === cat.value }"
        @click="categoryFilter = cat.value"
      >
        {{ cat.label }}
      </button>
    </div>

    <!-- 通道 + 排序 -->
    <div class="toolbar">
      <div class="channel-tabs">
        <button
          v-for="tab in channelTabs"
          :key="tab.value"
          type="button"
          class="channel-tab"
          :class="{ active: channelFilter === tab.value }"
          @click="setChannel(tab.value)"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="sort-tabs">
        <button
          v-for="s in sortOptions"
          :key="s.value"
          type="button"
          class="sort-tab"
          :class="{ active: sortBy === s.value }"
          @click="sortBy = s.value"
        >
          {{ s.label }}
        </button>
      </div>
    </div>

    <p v-if="!loading && !error" class="result-hint">
      共 {{ filteredOffers.length }} 件能力
      <span v-if="channelFilter !== 'all'"> · 当前：{{ channelLabel }}</span>
      <span v-if="searchQuery"> · 搜索「{{ searchQuery }}」</span>
    </p>

    <div v-if="error" class="error-msg">{{ error }}</div>
    <LoadingSkeleton v-if="loading" />

    <EmptyState v-else-if="filteredOffers.length === 0" icon="globe">
      <template v-if="offers.length === 0">
        暂无已发布供给，稍后再来或
        <RouterLink to="/app/offers/new">发布你的能力</RouterLink>
      </template>
      <template v-else>没有符合条件的供给，试试换个关键词或类目</template>
    </EmptyState>

    <!-- 商品网格 -->
    <div v-else class="product-grid product-grid--market">
      <CommerceProductCard
        v-for="offer in filteredOffers"
        :key="offer.id"
        :offer="offer"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { listMarketplaceOffers } from '@/api'
import AppIcon from '@/components/AppIcon.vue'
import CommerceProductCard from '@/components/CommerceProductCard.vue'
import type { Offer, OfferChannel } from '@/types'
import { CATEGORY_OPTIONS } from '@/utils'
import { MARKET_BUY_HINT } from '@/utils/platformGuide'
import HelpTip from '@/components/HelpTip.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'
import EmptyState from '@/components/EmptyState.vue'

type ChannelFilter = OfferChannel | 'all'
type SortKey = 'default' | 'price_asc' | 'price_desc' | 'newest'

const channelTabs: { value: ChannelFilter; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'agent', label: '智能体' },
  { value: 'human', label: '人工' },
]

const sortOptions: { value: SortKey; label: string }[] = [
  { value: 'default', label: '综合' },
  { value: 'price_asc', label: '价格↑' },
  { value: 'price_desc', label: '价格↓' },
  { value: 'newest', label: '最新' },
]

const channelFilter = ref<ChannelFilter>('all')
const categoryFilter = ref<string>('all')
const searchQuery = ref('')
const sortBy = ref<SortKey>('default')
const offers = ref<Offer[]>([])
const loading = ref(true)
const error = ref('')

const channelLabel = computed(() => {
  const tab = channelTabs.find((t) => t.value === channelFilter.value)
  return tab?.label ?? '全部'
})

const filteredOffers = computed(() => {
  let list = [...offers.value]
  const q = searchQuery.value.trim().toLowerCase()

  if (categoryFilter.value !== 'all') {
    list = list.filter((o) => o.category === categoryFilter.value)
  }
  if (q) {
    list = list.filter(
      (o) =>
        o.title.toLowerCase().includes(q) ||
        o.description.toLowerCase().includes(q) ||
        (o.delivery_description?.toLowerCase().includes(q) ?? false),
    )
  }

  switch (sortBy.value) {
    case 'price_asc':
      list.sort((a, b) => a.price_cents - b.price_cents)
      break
    case 'price_desc':
      list.sort((a, b) => b.price_cents - a.price_cents)
      break
    case 'newest':
      list.sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at))
      break
    default:
      list.sort((a, b) => {
        if (a.channel === 'agent' && b.channel !== 'agent') return -1
        if (b.channel === 'agent' && a.channel !== 'agent') return 1
        return a.price_cents - b.price_cents
      })
  }
  return list
})

function setChannel(value: ChannelFilter) {
  channelFilter.value = value
}

async function loadMarket() {
  loading.value = true
  error.value = ''
  try {
    const params: { page: number; page_size: number; channel?: OfferChannel } = {
      page: 1,
      page_size: 50,
    }
    if (channelFilter.value !== 'all') {
      params.channel = channelFilter.value
    }
    const data = await listMarketplaceOffers(params)
    offers.value = data.items
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

watch(channelFilter, loadMarket)
onMounted(loadMarket)
</script>

<style scoped>
.market-page {
  max-width: 1200px;
  margin: 0 auto;
}

.market-top {
  padding: var(--space-md) !important;
  margin-bottom: var(--space-md);
}

.search-row {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--color-fill);
  border-radius: var(--radius-pill);
  padding: 0 14px;
  min-height: 44px;
}

.search-icon {
  display: flex;
  color: var(--color-label-tertiary);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 16px;
  font-family: inherit;
  color: var(--color-label);
  outline: none;
  min-width: 0;
}

.search-input::placeholder {
  color: var(--color-label-tertiary);
}

.search-clear {
  border: none;
  background: none;
  color: var(--color-primary);
  font-size: 14px;
  cursor: pointer;
  font-family: inherit;
  flex-shrink: 0;
}

.promo-strip {
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 6px 8px;
  margin-top: 10px;
  font-size: 13px;
}

.promo-text {
  color: var(--color-label-secondary);
  flex: 1;
  min-width: 0;
  line-height: 1.4;
}

.category-scroll {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
  margin-bottom: var(--space-md);
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.category-scroll::-webkit-scrollbar {
  display: none;
}

.category-chip {
  flex-shrink: 0;
  padding: 8px 16px;
  border: none;
  border-radius: var(--radius-pill);
  background: var(--color-bg-secondary);
  color: var(--color-label-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  transition: background 0.15s, color 0.15s, transform 0.1s;
}

.category-chip.active {
  background: var(--gradient-commerce);
  color: #fff;
  font-weight: 600;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.channel-tabs,
.sort-tabs {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.channel-tab,
.sort-tab {
  padding: 6px 12px;
  border: 1px solid var(--color-separator);
  border-radius: var(--radius-pill);
  background: var(--color-fill);
  color: var(--color-label-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.channel-tab.active {
  background: var(--color-commerce-muted);
  color: var(--color-commerce);
  border-color: rgba(238, 10, 36, 0.35);
}

.sort-tab.active {
  background: var(--color-commerce-muted);
  color: var(--color-commerce);
  border-color: rgba(238, 10, 36, 0.35);
}

.result-hint {
  margin: 0 0 var(--space-md);
  font-size: 13px;
  color: var(--color-label-tertiary);
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .channel-tabs,
  .sort-tabs {
    overflow-x: auto;
    flex-wrap: nowrap;
    padding-bottom: 2px;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
  }

  .channel-tabs::-webkit-scrollbar,
  .sort-tabs::-webkit-scrollbar {
    display: none;
  }

  .channel-tab,
  .sort-tab {
    flex-shrink: 0;
  }
}
</style>
