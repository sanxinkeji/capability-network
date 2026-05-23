<template>
  <article class="manage-card glass-card" :class="{ 'manage-card--muted': muted }">
    <div class="manage-card__cover" :class="`manage-card__cover--${offer.category}`">
      <AppIcon :name="coverIcon(offer)" size="lg" class="cover-icon" />
      <span v-if="offer.channel === 'agent'" class="cover-badge cover-badge--agent">智能体</span>
      <span v-else class="cover-badge cover-badge--human">人工</span>
    </div>
    <div class="manage-card__body">
      <h3 class="manage-card__title">{{ offer.title }}</h3>
      <p class="manage-card__subtitle">
        {{ categoryLabel(offer.category) }} ·
        <span class="price-commerce price-inline">
          <span class="price-symbol">¥</span>
          <span class="price-int">{{ priceParts(offer.price_cents).int }}</span>
          <span class="price-dec">{{ priceParts(offer.price_cents).dec }}</span>
        </span>
      </p>
      <div class="manage-card__footer">
        <span :class="badgeClass(offer.status)">{{ statusLabel(offer.status) }}</span>
        <button
          v-if="offer.status === 'draft' && !muted"
          class="btn btn-sm btn-commerce"
          :disabled="publishing"
          @click="emit('publish', offer.id)"
        >
          {{ publishing ? '发布中…' : '发布' }}
        </button>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import AppIcon from '@/components/AppIcon.vue'
import type { IconName } from '@/components/icons'
import type { Offer } from '@/types'
import { categoryLabel, statusLabel } from '@/utils'

defineProps<{
  offer: Offer
  muted?: boolean
  publishing?: boolean
}>()

const emit = defineEmits<{
  publish: [offerId: string]
}>()

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

function priceParts(cents: number): { int: string; dec: string } {
  const [int, dec] = (cents / 100).toFixed(2).split('.')
  return { int, dec: `.${dec}` }
}

function badgeClass(status: string) {
  const map: Record<string, string> = {
    draft: 'badge badge-draft',
    published: 'badge badge-published',
    paused: 'badge badge-default',
  }
  return map[status] ?? 'badge badge-default'
}
</script>

<style scoped>
.manage-card {
  padding: 0 !important;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.manage-card--muted {
  opacity: 0.75;
}

.manage-card__cover {
  position: relative;
  aspect-ratio: 16 / 9;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #e8f4ff 0%, #f0f4ff 50%, #fff5f0 100%);
}

.manage-card__cover--design {
  background: linear-gradient(145deg, #ffe8f0, #fff0e8);
}

.manage-card__cover--data {
  background: linear-gradient(145deg, #e8fff0, #e8f8ff);
}

.manage-card__cover--dev,
.manage-card__cover--ai {
  background: linear-gradient(145deg, #e8eeff, #f0e8ff);
}

.manage-card__cover--content {
  background: linear-gradient(145deg, #fff8e8, #ffe8e8);
}

.cover-icon {
  color: rgba(0, 0, 0, 0.25);
  width: 40px;
  height: 40px;
}

.cover-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  font-size: 10px;
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

.manage-card__body {
  padding: 10px 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.manage-card__title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.manage-card__subtitle {
  margin: 0;
  font-size: 12px;
  color: var(--color-label-tertiary);
}

.price-inline {
  display: inline-flex;
  align-items: baseline;
  font-size: 14px;
}

.manage-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: auto;
  padding-top: 4px;
}
</style>
