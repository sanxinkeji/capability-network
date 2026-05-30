<template>
  <div class="market-page app-page">
    <div class="market-layout">
      <aside class="market-sidebar" aria-label="商品类目">
        <button
          type="button"
          class="market-sidebar__item"
          :class="{ active: categoryFilter === 'all' }"
          @click="categoryFilter = 'all'"
        >
          全部商品
        </button>
        <button
          v-for="cat in CATEGORY_OPTIONS"
          :key="cat.value"
          type="button"
          class="market-sidebar__item"
          :class="{ active: categoryFilter === cat.value }"
          @click="categoryFilter = cat.value"
        >
          {{ cat.label }}
        </button>
      </aside>

      <div class="market-main">
        <div class="market-kingkong" aria-label="快捷类目">
          <button
            type="button"
            class="market-kingkong__item"
            :class="{ active: categoryFilter === 'all' }"
            @click="categoryFilter = 'all'"
          >
            <span class="market-kingkong__icon">🏠</span>
            全部
          </button>
          <button
            v-for="cat in kingkongCats"
            :key="cat.value"
            type="button"
            class="market-kingkong__item"
            :class="{ active: categoryFilter === cat.value }"
            @click="categoryFilter = cat.value"
          >
            <span class="market-kingkong__icon">{{ cat.icon }}</span>
            {{ cat.label }}
          </button>
        </div>

        <div class="market-banner">
          <div>
            <strong>AI 龙虾店 24 小时在线</strong>
            <span>付款进聊天 · 确认收货放款 · 平台全程担保</span>
          </div>
          <RouterLink to="/app/wallet" class="market-banner__tag">去充值</RouterLink>
        </div>

        <div class="market-top glass-card">
          <div class="search-row">
            <span class="search-icon" aria-hidden="true">
              <AppIcon name="search" size="sm" />
            </span>
            <input
              v-model="searchQuery"
              type="search"
              class="search-input"
              placeholder="搜 AI 技能，如 论文、Logo、摘要…"
              enterkeyhint="search"
            />
            <button v-if="searchQuery" type="button" class="search-clear" @click="searchQuery = ''">
              清除
            </button>
          </div>
        </div>

        <div class="market-sortbar toolbar">
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

        <h2 v-if="!loading && !error" class="market-feed-head">
          <span class="market-feed-head__title">猜你喜欢</span>
          <span class="result-hint">共 {{ filteredOffers.length }} 件</span>
        </h2>

        <div v-if="error" class="error-msg">{{ error }}</div>
        <LoadingSkeleton v-if="loading" />

        <EmptyState v-else-if="filteredOffers.length === 0" icon="globe">
          <template v-if="offers.length === 0">
            暂无店铺上架，稍后再来
          </template>
          <template v-else>没有符合条件的服务，试试换个关键词或类目</template>
        </EmptyState>

        <div v-else class="product-grid product-grid--market">
          <CommerceProductCard
            v-for="offer in filteredOffers"
            :key="offer.id"
            :offer="offer"
            feed
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { listMarketplaceOffers } from '@/api'
import AppIcon from '@/components/AppIcon.vue'
import CommerceProductCard from '@/components/CommerceProductCard.vue'
import type { Offer } from '@/types'
import { CATEGORY_OPTIONS } from '@/utils'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'
import EmptyState from '@/components/EmptyState.vue'

const kingkongIcons: Record<string, string> = {
  writing: '✍️',
  design: '🎨',
  data: '📊',
  dev: '💻',
  content: '📝',
  consulting: '💡',
  ai: '🤖',
}

const kingkongCats = CATEGORY_OPTIONS.slice(0, 4).map((c) => ({
  ...c,
  icon: kingkongIcons[c.value] ?? '✨',
}))

type SortKey = 'default' | 'price_asc' | 'price_desc' | 'newest'

const sortOptions: { value: SortKey; label: string }[] = [
  { value: 'default', label: '综合' },
  { value: 'price_asc', label: '价格↑' },
  { value: 'price_desc', label: '价格↓' },
  { value: 'newest', label: '最新' },
]

const categoryFilter = ref<string>('all')
const searchQuery = ref('')
const sortBy = ref<SortKey>('default')
const offers = ref<Offer[]>([])
const loading = ref(true)
const error = ref('')

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
      list.sort((a, b) => a.price_cents - b.price_cents)
  }
  return list
})

async function loadMarket() {
  loading.value = true
  error.value = ''
  try {
    const data = await listMarketplaceOffers({
      page: 1,
      page_size: 50,
      channel: 'agent',
    })
    offers.value = data.items
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadMarket)
</script>

<style scoped>
.market-page {
  max-width: none;
  margin: 0;
}

.market-layout {
  display: block;
}

.market-sidebar {
  display: none;
}

.market-main {
  min-width: 0;
}

@media (min-width: 769px) {
  .market-layout {
    display: grid;
    grid-template-columns: 168px minmax(0, 1fr);
    gap: 20px;
    align-items: start;
  }

  .market-sidebar {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 12px 0;
    background: var(--shop-card-bg);
    border-radius: var(--shop-card-radius);
    border: 1px solid rgba(0, 0, 0, 0.05);
    position: sticky;
    top: 72px;
  }

  .market-sidebar__item {
    text-align: left;
    border: none;
    background: transparent;
    padding: 10px 16px;
    font-size: 14px;
    color: var(--color-label-secondary);
    cursor: pointer;
    font-family: inherit;
    border-left: 3px solid transparent;
  }

  .market-sidebar__item:hover {
    color: var(--color-commerce);
    background: var(--color-commerce-muted);
  }

  .market-sidebar__item.active {
    color: var(--color-commerce);
    font-weight: 600;
    border-left-color: var(--color-commerce);
    background: var(--color-commerce-muted);
  }

  .market-top {
    display: none;
  }

  .category-scroll {
    display: none;
  }
}

.market-top {
  padding: 12px;
  margin-bottom: 10px;
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
  margin: 0;
  font-size: 12px;
  color: #999;
  font-weight: 400;
}

@media (max-width: 768px) {
  .market-top,
  .category-scroll {
    display: none;
  }

  .market-feed-head {
    padding-top: 4px;
  }
}
</style>
