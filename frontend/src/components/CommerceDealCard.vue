<template>

  <article class="order-card glass-card" :class="{ 'order-card--disputed': deal.status === 'disputed' }">

    <RouterLink :to="to" class="order-card__link">

      <div class="order-card__head">

        <div class="order-card__shop">

          <span class="order-card__shop-icon">店</span>

          <span class="order-card__shop-name">{{ shopLabel }}</span>

        </div>

        <span class="order-card__status" :class="statusClass">{{ statusLabel(deal.status) }}</span>

      </div>



      <div class="order-card__body">

        <div class="order-card__thumb" aria-hidden="true">能</div>

        <div class="order-card__info">

          <h3 class="order-card__title">{{ dealOrderTitle(deal) }}</h3>

          <p class="order-card__meta">订单 {{ dealShortId(deal.id) }} · {{ formatDate(deal.created_at) }}</p>

          <span v-if="deal.agent_auto_delivered && deal.status === 'delivered'" class="tag-promo">

            智能体已交付

          </span>

        </div>

      </div>

    </RouterLink>



    <div class="order-card__foot">

      <div class="order-card__total">

        实付

        <span class="price-commerce">

          <span class="price-symbol">¥</span>

          <span class="price-int">{{ priceParts.int }}</span>

          <span class="price-dec">{{ priceParts.dec }}</span>

        </span>

      </div>

      <div class="order-card__actions">

        <RouterLink :to="to" class="order-card__btn">查看详情</RouterLink>

        <RouterLink

          v-if="primaryAction"

          :to="to"

          class="order-card__btn order-card__btn--primary"

        >

          {{ primaryAction }}

        </RouterLink>

      </div>

    </div>

  </article>

</template>



<script setup lang="ts">

import { computed } from 'vue'

import { RouterLink } from 'vue-router'

import type { Deal } from '@/types'

import type { DealViewerRole } from '@/utils'

import {

  dealListActionLabel,

  dealOrderTitle,

  dealShortId,

  formatDate,

  statusLabel,

} from '@/utils'



const props = defineProps<{

  deal: Deal

  to: string

  viewerRole?: DealViewerRole

}>()



const priceParts = computed(() => {

  const [int, dec] = (props.deal.amount_cents / 100).toFixed(2).split('.')

  return { int, dec: `.${dec}` }

})



const shopLabel = computed(() => {

  const id = props.viewerRole === 'seller' ? props.deal.buyer_id : props.deal.seller_id

  return props.viewerRole === 'seller' ? `买家 ${dealShortId(id)}` : `卖家 ${dealShortId(id)}`

})



const primaryAction = computed(() =>

  dealListActionLabel(props.deal.status, props.viewerRole ?? 'other'),

)



const statusClass = computed(() => {

  if (props.deal.status === 'completed' || props.deal.status === 'refunded') {

    return 'order-card__status--done'

  }

  if (props.deal.status === 'pending' || props.deal.status === 'delivered') {

    return 'order-card__status--warn'

  }

  if (props.deal.status === 'disputed') return 'order-card__status--danger'

  return ''

})

</script>



<style scoped>

.order-card__link {

  display: block;

  text-decoration: none;

  color: inherit;

}



.order-card__link:hover {

  text-decoration: none;

}



.order-card--disputed {

  border-color: rgba(255, 59, 48, 0.25);

}

</style>

