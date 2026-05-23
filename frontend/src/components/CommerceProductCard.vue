<template>
  <article class="product-card glass-card">
    <div class="card-cover" :class="`card-cover--${offer.category}`">
      <AppIcon :name="coverIcon(offer)" size="lg" class="cover-icon" />
      <span v-if="offer.channel === 'agent'" class="cover-badge cover-badge--agent">智能体</span>
      <span v-else class="cover-badge cover-badge--human">人工</span>
      <span v-if="offer.channel === 'agent'" class="cover-tag tag-promo">自动交付</span>
    </div>

    <div class="card-body">
      <h3 class="card-title">{{ offer.title }}</h3>
      <p v-if="offer.description" class="card-desc">{{ offer.description }}</p>

      <div class="card-tags">
        <span class="mini-tag">{{ categoryLabel(offer.category) }}</span>
        <span class="mini-tag mini-tag--muted">{{ billingLabel(offer.billing_model) }}</span>
        <span class="tag-trust">托管支付</span>
      </div>

      <div class="card-footer">
        <div class="price-commerce card-price">
          <span class="price-symbol">¥</span>
          <span class="price-int">{{ priceParts(offer.price_cents).int }}</span>
          <span class="price-dec">{{ priceParts(offer.price_cents).dec }}</span>
          <span v-if="offer.channel === 'agent'" class="price-unit">/ 次起</span>
        </div>
        <RouterLink :to="ctaTo" class="btn btn-sm btn-commerce buy-btn">
          立即选用
        </RouterLink>
      </div>
      <p class="card-flow-hint">选用后创建需求并匹配，确认后才扣款</p>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'
import type { IconName } from '@/components/icons'
import type { BillingModel, Offer } from '@/types'
import { categoryLabel } from '@/utils'

const props = defineProps<{
  offer: Offer
  ctaTo?: string
}>()

const ctaTo = computed(() => {
  if (props.ctaTo) return props.ctaTo
  const hint = encodeURIComponent(props.offer.title)
  return `/app/intents/new?mode=ai&hint=${hint}`
})

function coverIcon(offer: Offer): IconName {
  const map: Record<string, IconName> = {
    design: 'target',
    data: 'chart',
    dev: 'agent',
    content: 'clipboard',
    consulting: 'person',
    ai: 'agent',
  }
  return map[offer.category] ?? (offer.channel === 'agent' ? 'agent' : 'package')
}

function billingLabel(model: BillingModel): string {
  const map: Record<BillingModel, string> = {
    per_use: '按次',
    per_query: '按查询',
    per_hour: '按小时',
  }
  return map[model] ?? model
}

function priceParts(cents: number): { int: string; dec: string } {
  const [int, dec] = (cents / 100).toFixed(2).split('.')
  return { int, dec: `.${dec}` }
}
</script>

<style scoped>
.product-card {
  padding: 0 !important;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: transform 0.15s, box-shadow 0.15s;
}

.product-card:active {
  transform: scale(0.98);
}

.card-cover {
  position: relative;
  aspect-ratio: 4 / 3;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #e8f4ff 0%, #f0f4ff 50%, #fff5f0 100%);
}

@media (min-width: 641px) {
  .card-cover {
    aspect-ratio: 1;
  }
}

.card-cover--design {
  background: linear-gradient(145deg, #ffe8f0, #fff0e8);
}

.card-cover--data {
  background: linear-gradient(145deg, #e8fff0, #e8f8ff);
}

.card-cover--dev,
.card-cover--ai {
  background: linear-gradient(145deg, #e8eeff, #f0e8ff);
}

.card-cover--content {
  background: linear-gradient(145deg, #fff8e8, #ffe8e8);
}

.cover-icon {
  color: rgba(0, 0, 0, 0.25);
  width: 48px;
  height: 48px;
}

.cover-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}

.cover-badge--agent {
  background: rgba(52, 199, 89, 0.9);
  color: #fff;
}

.cover-badge--human {
  background: rgba(0, 122, 255, 0.9);
  color: #fff;
}

.cover-tag {
  position: absolute;
  bottom: 8px;
  left: 8px;
  font-size: 10px;
  padding: 2px 6px;
}

.card-body {
  padding: 10px 12px 12px;
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 6px;
}

.card-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  color: var(--color-label);
}

.card-desc {
  margin: 0;
  font-size: 12px;
  color: var(--color-label-tertiary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.mini-tag {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 3px;
  background: var(--color-commerce-muted);
  color: var(--color-commerce);
  border: 1px solid rgba(238, 10, 36, 0.15);
}

.mini-tag--muted {
  background: var(--color-fill);
  color: var(--color-label-secondary);
  border-color: transparent;
}

.card-footer {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
  margin-top: auto;
  padding-top: 6px;
}

.card-price {
  flex-wrap: wrap;
  row-gap: 2px;
}

.card-price .price-int {
  font-size: 18px;
}

.buy-btn {
  width: 100%;
  flex-shrink: 0;
  padding: 8px 10px !important;
  min-height: 36px;
  font-size: 13px;
  border-radius: var(--radius-pill);
}

.buy-btn:hover {
  text-decoration: none;
}

.card-flow-hint {
  margin: 0;
  padding: 0 12px 10px;
  font-size: 11px;
  color: var(--color-label-tertiary);
  text-align: center;
}

@media (min-width: 641px) {
  .card-footer {
    flex-direction: row;
    align-items: flex-end;
    justify-content: space-between;
    gap: 8px;
  }

  .card-price .price-int {
    font-size: 20px;
  }

  .buy-btn {
    width: auto;
    padding: 6px 12px !important;
    min-height: 32px;
  }
}
</style>
