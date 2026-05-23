<template>

  <article class="intent-card glass-card" :class="{ 'intent-card--muted': muted }">

    <div class="intent-card__head">

      <span class="intent-card__badge">需求</span>

      <span :class="badgeClass(intent.status)">{{ statusLabel(intent.status) }}</span>

    </div>

    <div class="intent-card__body">

      <div class="intent-card__thumb" aria-hidden="true">需</div>

      <div class="intent-card__info">

        <h3 class="intent-card__title">{{ intent.title }}</h3>

        <p class="intent-card__meta">

          {{ categoryLabel(intent.category) }} · 预算

          <span class="price-commerce price-inline">

            <span class="price-symbol">¥</span>

            <span class="price-int">{{ priceParts(intent.budget_max).int }}</span>

            <span class="price-dec">{{ priceParts(intent.budget_max).dec }}</span>

          </span>

        </p>

      </div>

    </div>

    <div v-if="intent.status === 'open' && !muted" class="intent-card__foot">

      <RouterLink :to="`/app/matching/${intent.id}`" class="order-card__btn order-card__btn--primary">

        去匹配

      </RouterLink>

    </div>

  </article>

</template>



<script setup lang="ts">

import { RouterLink } from 'vue-router'

import type { Intent } from '@/types'

import { categoryLabel, statusLabel } from '@/utils'



defineProps<{

  intent: Intent

  muted?: boolean

}>()



function priceParts(cents: number): { int: string; dec: string } {

  const [int, dec] = (cents / 100).toFixed(2).split('.')

  return { int, dec: `.${dec}` }

}



function badgeClass(status: string) {

  const map: Record<string, string> = {

    open: 'badge badge-open',

    matched: 'badge badge-published',

    closed: 'badge badge-default',

  }

  return map[status] ?? 'badge badge-default'

}

</script>



<style scoped>

.intent-card {

  padding: 0 !important;

  overflow: hidden;

}



.intent-card--muted {

  opacity: 0.75;

}



.intent-card__head {

  display: flex;

  align-items: center;

  justify-content: space-between;

  padding: 10px 12px;

  border-bottom: 1px solid var(--color-separator);

  background: rgba(0, 0, 0, 0.015);

}



.intent-card__badge {

  font-size: 13px;

  font-weight: 600;

  color: var(--color-label);

}



.intent-card__body {

  display: flex;

  gap: 10px;

  padding: 12px;

}



.intent-card__thumb {

  width: 56px;

  height: 56px;

  border-radius: 8px;

  background: linear-gradient(145deg, #e8f4ff, #d6e4ff);

  display: flex;

  align-items: center;

  justify-content: center;

  flex-shrink: 0;

  font-size: 18px;

  font-weight: 700;

  color: rgba(22, 119, 255, 0.45);

}



.intent-card__info {

  flex: 1;

  min-width: 0;

}



.intent-card__title {

  margin: 0 0 4px;

  font-size: 15px;

  font-weight: 600;

  line-height: 1.35;

  display: -webkit-box;

  -webkit-line-clamp: 2;

  -webkit-box-orient: vertical;

  overflow: hidden;

}



.intent-card__meta {

  margin: 0;

  font-size: 12px;

  color: var(--color-label-tertiary);

}



.price-inline {

  display: inline-flex;

  align-items: baseline;

  font-size: 14px;

}



.intent-card__foot {

  display: flex;

  justify-content: flex-end;

  padding: 0 12px 12px;

}

</style>

