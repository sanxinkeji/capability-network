<template>

  <div class="app-page deal-detail-page">

    <div v-if="error" class="error-msg">{{ error }}</div>

    <div v-if="payPendingNotice" class="success-msg">{{ payPendingNotice }}</div>

    <LoadingSkeleton v-if="loading" :rows="4" />



    <template v-else-if="deal">

      <div class="deal-status-banner" :class="`deal-status-banner--${bannerTone}`">

        <p class="deal-status-banner__title">{{ statusLabel(deal.status) }}</p>

        <p class="deal-status-banner__hint">{{ statusHint }}</p>

      </div>



      <StatusStepper :status="deal.status" />

      <HelpTip v-if="showChatEntry" variant="info" title="订单沟通">
        可在
        <RouterLink :to="`/app/deals/${dealId}/chat`">聊天界面</RouterLink>
        与 AI 店家沟通需求与交付进度。
      </HelpTip>

      <HelpTip v-if="canPay" variant="warn" title="支付说明">
        点击底部「立即支付」将从钱包扣款并冻结，卖方收到通知后开始交付。余额不足请先到
        <RouterLink to="/app/wallet">钱包充值</RouterLink>。
      </HelpTip>



      <section class="deal-goods-card glass-card">

        <div class="deal-goods-card__thumb" aria-hidden="true">能</div>

        <div class="deal-goods-card__main">

          <h2 class="deal-goods-card__title">{{ dealOrderTitle(deal) }}</h2>

          <div class="deal-goods-card__price-row">

            <span class="price-commerce">

              <span class="price-symbol">¥</span>

              <span class="price-int">{{ priceParts.int }}</span>

              <span class="price-dec">{{ priceParts.dec }}</span>

            </span>

            <span v-if="deal.agent_auto_delivered && deal.status === 'delivered'" class="tag-promo">

              智能体已交付

            </span>

          </div>

        </div>

      </section>



      <section class="service-strip glass-card">

        <span class="service-strip__item"><span class="service-strip__dot" />资金托管</span>

        <span class="service-strip__item"><span class="service-strip__dot" />交付验收</span>

        <span class="service-strip__item"><span class="service-strip__dot" />争议仲裁</span>

        <span class="service-strip__item"><span class="service-strip__dot" />平台担保</span>

      </section>



      <section class="commerce-panel glass-card">

        <div class="commerce-panel__head">订单信息</div>

        <div class="commerce-panel__body">

          <div class="commerce-panel__row">

            <span class="commerce-panel__label">订单编号</span>

            <span class="commerce-panel__value">{{ dealShortId(deal.id) }}</span>

          </div>

          <div class="commerce-panel__row">

            <span class="commerce-panel__label">创建时间</span>

            <span class="commerce-panel__value">{{ formatDate(deal.created_at) }}</span>

          </div>

          <div v-if="deal.completed_at" class="commerce-panel__row">

            <span class="commerce-panel__label">完成时间</span>

            <span class="commerce-panel__value">{{ formatDate(deal.completed_at) }}</span>

          </div>

          <div class="commerce-panel__row">

            <span class="commerce-panel__label">我的角色</span>

            <span class="commerce-panel__value">{{ roleLabel }}</span>

          </div>

        </div>

      </section>



      <section v-if="deal.delivery_text || deal.delivery_payload_url" class="commerce-panel glass-card">

        <div class="commerce-panel__head">交付内容</div>

        <div class="commerce-panel__body">

          <div class="commerce-panel__row commerce-panel__row--stack">

            <p v-if="deal.delivery_text" class="delivery-text">{{ deal.delivery_text }}</p>

            <a v-if="deal.delivery_payload_url" :href="deal.delivery_payload_url" target="_blank" rel="noopener">

              查看交付物 →

            </a>

          </div>

        </div>

      </section>



      <section v-if="canDeliver" class="commerce-panel glass-card">

        <div class="commerce-panel__head">提交交付</div>

        <div class="commerce-panel__body">

          <div class="inset-group inset-group--flat">

            <div class="inset-row">

              <label>交付说明</label>

              <textarea v-model="deliveryText" rows="4" placeholder="描述交付内容或粘贴链接说明" />

            </div>

          </div>

        </div>

      </section>



      <section v-if="canDispute" class="commerce-panel glass-card">

        <div class="commerce-panel__head">发起争议</div>

        <div class="commerce-panel__body">

          <div class="inset-group inset-group--flat">

            <div class="inset-row">

              <label>争议原因</label>

              <textarea v-model="disputeReason" rows="3" placeholder="描述问题，管理员将介入仲裁" />

            </div>

          </div>

        </div>

      </section>



      <section class="commerce-panel glass-card">

        <button type="button" class="commerce-collapse-toggle" @click="showMore = !showMore">

          {{ showMore ? '收起更多信息' : '展开更多信息' }}

        </button>

        <div v-if="showMore" class="commerce-panel__body">

          <div class="commerce-panel__row">

            <span class="commerce-panel__label">完整订单 ID</span>

            <span class="commerce-panel__value"><code class="detail-code">{{ deal.id }}</code></span>

          </div>

          <div class="commerce-panel__row">

            <span class="commerce-panel__label">买方 ID</span>

            <span class="commerce-panel__value"><code class="detail-code">{{ deal.buyer_id }}</code></span>

          </div>

          <div class="commerce-panel__row">

            <span class="commerce-panel__label">卖方 ID</span>

            <span class="commerce-panel__value"><code class="detail-code">{{ deal.seller_id }}</code></span>

          </div>

          <div class="commerce-panel__row">

            <span class="commerce-panel__label">需求 ID</span>

            <span class="commerce-panel__value"><code class="detail-code">{{ deal.intent_id }}</code></span>

          </div>

          <div class="commerce-panel__row">

            <span class="commerce-panel__label">供给 ID</span>

            <span class="commerce-panel__value"><code class="detail-code">{{ deal.offer_id }}</code></span>

          </div>

        </div>

      </section>



      <CommerceStickyBar v-if="stickyVisible">

        <template #info>

          合计

          <span class="price-commerce">

            <span class="price-symbol">¥</span>

            <span class="price-int">{{ priceParts.int }}</span>

            <span class="price-dec">{{ priceParts.dec }}</span>

          </span>

        </template>

        <RouterLink to="/app/deals" class="btn btn-secondary btn-sm">返回</RouterLink>

        <RouterLink
          v-if="showChatEntry"
          :to="`/app/deals/${dealId}/chat`"
          class="btn btn-secondary btn-sm"
        >
          进入聊天
        </RouterLink>

        <button

          v-if="canPay"

          class="btn btn-commerce"

          :disabled="paying"

          @click="handlePay"

        >

          {{ paying ? '支付中…' : '立即支付' }}

        </button>

        <button

          v-else-if="canDeliver"

          class="btn btn-commerce"

          :disabled="delivering || !deliveryText.trim()"

          @click="handleDeliver"

        >

          {{ delivering ? '提交中…' : '提交交付' }}

        </button>

        <button

          v-else-if="canConfirm"

          class="btn btn-commerce"

          :disabled="confirming"

          @click="handleConfirm"

        >

          {{ confirming ? '确认中…' : '确认收货' }}

        </button>

        <button

          v-else-if="canDispute"

          class="btn btn-secondary btn-sm"

          :disabled="disputing || !disputeReason.trim()"

          @click="handleDispute"

        >

          {{ disputing ? '提交中…' : '发起争议' }}

        </button>

      </CommerceStickyBar>



      <div v-if="deal.status === 'completed'" class="success-msg">订单已完成，感谢您的信任</div>

    </template>

  </div>

</template>



<script setup lang="ts">

import { computed, onMounted, ref } from 'vue'

import { RouterLink, useRoute, useRouter } from 'vue-router'

import { confirmDeal, deliverDeal, disputeDeal, getDeal, payDeal } from '@/api/deals'

import { useAuthStore } from '@/stores/auth'

import type { Deal } from '@/types'

import {

  dealOrderTitle,

  dealShortId,

  dealStatusBannerTone,

  dealStatusHint,

  formatDate,

  statusLabel,

} from '@/utils'

import CommerceStickyBar from '@/components/CommerceStickyBar.vue'
import HelpTip from '@/components/HelpTip.vue'

import LoadingSkeleton from '@/components/LoadingSkeleton.vue'

import StatusStepper from '@/components/StatusStepper.vue'



const route = useRoute()

const router = useRouter()

const auth = useAuthStore()

const dealId = route.params.dealId as string



const deal = ref<Deal | null>(null)

const loading = ref(true)

const error = ref('')

const paying = ref(false)

const delivering = ref(false)

const confirming = ref(false)

const disputing = ref(false)

const deliveryText = ref('')

const disputeReason = ref('')

const showMore = ref(false)



const currentUserId = computed(() => auth.user?.id ?? '')



const isBuyer = computed(

  () => !!deal.value && deal.value.buyer_id === currentUserId.value,

)

const isSeller = computed(

  () => !!deal.value && deal.value.seller_id === currentUserId.value,

)



const viewerRole = computed(() => {

  if (isBuyer.value) return 'buyer' as const

  if (isSeller.value) return 'seller' as const

  return 'other' as const

})



const canPay = computed(

  () => deal.value?.status === 'pending' && isBuyer.value,

)

const showChatEntry = computed(

  () =>

    deal.value &&

    ['in_progress', 'delivered', 'disputed', 'completed'].includes(deal.value.status),

)

const canDeliver = computed(

  () => deal.value?.status === 'in_progress' && isSeller.value,

)

const canConfirm = computed(

  () => deal.value?.status === 'delivered' && isBuyer.value,

)

const canDispute = computed(

  () =>

    (deal.value?.status === 'in_progress' || deal.value?.status === 'delivered') &&

    (isBuyer.value || isSeller.value),

)



const stickyVisible = computed(

  () => canPay.value || canDeliver.value || canConfirm.value || canDispute.value,

)



const payPendingNotice = computed(() => {

  if (route.query.pay_pending === '1' && deal.value?.status === 'pending' && isBuyer.value) {

    return '已创建待支付，请完成支付'

  }

  return ''

})



const priceParts = computed(() => {

  const cents = deal.value?.amount_cents ?? 0

  const [int, dec] = (cents / 100).toFixed(2).split('.')

  return { int, dec: `.${dec}` }

})



const bannerTone = computed(() =>

  deal.value ? dealStatusBannerTone(deal.value.status) : 'info',

)



const statusHint = computed(() =>

  deal.value ? dealStatusHint(deal.value.status, viewerRole.value) : '',

)



const roleLabel = computed(() => {

  if (isBuyer.value) return '买方'

  if (isSeller.value) return '卖方'

  return '访客'

})



async function loadDeal() {

  loading.value = true

  error.value = ''

  try {

    if (!auth.user) await auth.fetchProfile()

    deal.value = await getDeal(dealId)

    const skipChatRedirect = route.query.pay_pending === '1' || route.query.detail === '1'

    if (
      deal.value &&
      !skipChatRedirect &&
      ['in_progress', 'delivered', 'disputed'].includes(deal.value.status)
    ) {
      router.replace(`/app/deals/${dealId}/chat`)
      return
    }

  } catch (e) {

    error.value = e instanceof Error ? e.message : '加载失败'

  } finally {

    loading.value = false

  }

}



async function handlePay() {

  paying.value = true

  error.value = ''

  try {

    deal.value = await payDeal(dealId)

    router.push(`/app/deals/${dealId}/chat`)

  } catch (e) {

    error.value = e instanceof Error ? e.message : '支付失败，请检查钱包余额'

  } finally {

    paying.value = false

  }

}



async function handleDeliver() {

  delivering.value = true

  error.value = ''

  try {

    deal.value = await deliverDeal(dealId, { text: deliveryText.value.trim() })

  } catch (e) {

    error.value = e instanceof Error ? e.message : '交付失败'

  } finally {

    delivering.value = false

  }

}



async function handleConfirm() {

  confirming.value = true

  error.value = ''

  try {

    deal.value = await confirmDeal(dealId)

  } catch (e) {

    error.value = e instanceof Error ? e.message : '确认失败'

  } finally {

    confirming.value = false

  }

}



async function handleDispute() {

  disputing.value = true

  error.value = ''

  try {

    deal.value = await disputeDeal(dealId, disputeReason.value.trim())

  } catch (e) {

    error.value = e instanceof Error ? e.message : '争议提交失败'

  } finally {

    disputing.value = false

  }

}



onMounted(loadDeal)

</script>



<style scoped>

.commerce-panel__row--stack {

  flex-direction: column;

  align-items: flex-start;

}



.delivery-text {

  margin: 0;

  font-size: 14px;

  line-height: 1.5;

  white-space: pre-wrap;

  width: 100%;

}



.detail-code {

  font-size: 11px;

  background: var(--color-fill);

  padding: 2px 6px;

  border-radius: 4px;

  word-break: break-all;

}



.inset-group--flat {

  margin: 0;

  border: none;

  box-shadow: none;

  background: transparent;

}

</style>

