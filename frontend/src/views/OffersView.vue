<template>

  <div class="app-page">
    <ShopPageHeader
      title="我的店铺"
      subtitle="上架 AI 技能，接入 OpenClaw 自动接单交付"
    >
      <template #actions>
        <RouterLink to="/app/offers/new" class="btn btn-commerce btn-sm">上架服务</RouterLink>
      </template>
    </ShopPageHeader>
    <ShopTrustStrip />



    <HelpTip>{{ SELLER_FLOW_HINT }}</HelpTip>



    <CommerceTabs v-model="activeTab" :tabs="tabs" />



    <div v-if="error" class="error-msg">{{ error }}</div>

    <LoadingSkeleton v-if="loading" />



    <EmptyState v-else-if="displayOffers.length === 0" icon="package">

      <template v-if="activeTab === 'draft'">

        暂无草稿，<RouterLink to="/app/offers/new">创建供给</RouterLink>

      </template>

      <template v-else-if="activeTab === 'published'">

        暂无已上架供给。创建后需点击「发布」才会出现在市场。

      </template>

      <template v-else>暂无已暂停的供给</template>

    </EmptyState>



    <div v-else class="product-grid product-grid--offers">

      <ManageOfferCard

        v-for="offer in displayOffers"

        :key="offer.id"

        :offer="offer"

        :muted="activeTab === 'paused'"

        :publishing="publishingId === offer.id"

        @publish="handlePublish"

      />

    </div>

  </div>

</template>



<script setup lang="ts">

import { computed, onMounted, ref } from 'vue'

import { RouterLink } from 'vue-router'

import { listOffers, publishOffer } from '@/api'

import type { Offer } from '@/types'

import { SELLER_FLOW_HINT } from '@/utils/platformGuide'

import CommerceTabs from '@/components/CommerceTabs.vue'

import HelpTip from '@/components/HelpTip.vue'
import ShopPageHeader from '@/components/ShopPageHeader.vue'

import ManageOfferCard from '@/components/ManageOfferCard.vue'

import LoadingSkeleton from '@/components/LoadingSkeleton.vue'

import EmptyState from '@/components/EmptyState.vue'



const offers = ref<Offer[]>([])

const loading = ref(true)

const error = ref('')

const publishingId = ref<string | null>(null)

const activeTab = ref('published')



const draftOffers = computed(() => offers.value.filter((o) => o.status === 'draft'))

const publishedOffers = computed(() => offers.value.filter((o) => o.status === 'published'))

const pausedOffers = computed(() =>

  offers.value.filter((o) => o.status !== 'draft' && o.status !== 'published'),

)



const tabs = computed(() => [

  { key: 'published', label: '已上架', count: publishedOffers.value.length },

  { key: 'draft', label: '草稿', count: draftOffers.value.length },

  { key: 'paused', label: '已暂停', count: pausedOffers.value.length },

])



const displayOffers = computed(() => {

  if (activeTab.value === 'draft') return draftOffers.value

  if (activeTab.value === 'published') return publishedOffers.value

  return pausedOffers.value

})



async function loadOffers() {

  loading.value = true

  error.value = ''

  try {

    const data = await listOffers({ page: 1, page_size: 50 })

    offers.value = data.items

  } catch (e) {

    error.value = e instanceof Error ? e.message : '加载失败'

  } finally {

    loading.value = false

  }

}



async function handlePublish(offerId: string) {

  publishingId.value = offerId

  try {

    await publishOffer(offerId)

    await loadOffers()

    activeTab.value = 'published'

  } catch (e) {

    error.value = e instanceof Error ? e.message : '发布失败'

  } finally {

    publishingId.value = null

  }

}



onMounted(loadOffers)

</script>



<style scoped>

.product-grid--offers {

  grid-template-columns: repeat(2, 1fr);

}



@media (min-width: 640px) {

  .product-grid--offers {

    grid-template-columns: repeat(3, 1fr);

  }

}

</style>

