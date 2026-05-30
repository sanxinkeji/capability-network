<template>
  <div class="offer-detail app-page offer-detail-page">
    <div v-if="error" class="error-msg">{{ error }}</div>
    <LoadingSkeleton v-if="loading" :rows="6" />

    <template v-else-if="offer">
      <nav class="detail-crumb" aria-label="面包屑">
        <RouterLink to="/app/market">首页</RouterLink>
        <span class="detail-crumb__sep">/</span>
        <span>{{ categoryLabel(offer.category) }}</span>
        <span class="detail-crumb__sep">/</span>
        <span class="detail-crumb__current">{{ offer.title }}</span>
      </nav>

      <ShopTrustStrip class="detail-trust-strip" />

      <article class="detail-layout glass-card">
        <div class="detail-gallery">
          <div class="detail-cover" :class="`detail-cover--${offer.category}`">
            <AppIcon :name="coverIcon(offer)" size="lg" class="detail-cover__icon" />
            <span class="detail-cover__badge">AI 龙虾店</span>
            <span class="detail-cover__tag">付款进聊天</span>
          </div>
          <ul class="detail-gallery__trust">
            <li>🦞 AI 自动服务</li>
            <li>✓ 平台担保</li>
            <li>✓ 确认收货放款</li>
          </ul>
        </div>

        <div class="detail-info">
          <div class="detail-shop-row">
            <span class="detail-shop-row__name">
              {{ offer.seller_display_name || '技能集市认证店' }}
            </span>
            <span class="detail-shop-row__tag">🦞 付款进聊天</span>
          </div>

          <h1 class="detail-title">{{ offer.title }}</h1>

          <div class="detail-price-panel">
            <div class="detail-price-panel__label">价格</div>
            <span class="price-commerce detail-price">
              <span class="price-symbol">¥</span>
              <span class="price-int">{{ priceParts.int }}</span>
              <span class="price-dec">{{ priceParts.dec }}</span>
              <span class="price-unit">/ 次起</span>
            </span>
          </div>

          <div class="detail-meta">
            <span class="detail-meta__item">
              <em>类目</em>{{ categoryLabel(offer.category) }}
            </span>
            <span class="detail-meta__item">
              <em>计费</em>{{ billingLabel(offer.billing_model) }}
            </span>
            <span class="detail-meta__item detail-meta__item--trust">
              <em>保障</em>平台担保交易
            </span>
          </div>

          <div class="detail-buy-panel">
            <label class="detail-buy-panel__label" for="buyer-note">补充说明（可选）</label>
            <textarea
              id="buyer-note"
              v-model="buyerNote"
              rows="3"
              placeholder="例如：论文专业方向、字数、截止时间…"
            />

            <div class="detail-actions detail-actions--inline">
              <button
                type="button"
                class="btn btn-lg btn-commerce detail-buy-btn"
                :disabled="buying"
                @click="handleBuy"
              >
                {{ buying ? '处理中…' : '立即购买并付款' }}
              </button>
              <RouterLink to="/app/market" class="btn btn-lg btn-outline-commerce detail-back-btn">
                继续逛逛
              </RouterLink>
            </div>
            <p v-if="buyError" class="buy-error">{{ buyError }}</p>
          </div>
        </div>
      </article>

      <section class="detail-tabs glass-card">
        <div class="detail-tabs__head" role="tablist">
          <button
            v-for="tab in detailTabs"
            :key="tab.key"
            type="button"
            role="tab"
            class="detail-tabs__tab"
            :class="{ active: activeTab === tab.key }"
            :aria-selected="activeTab === tab.key"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>
        <div class="detail-tabs__body">
          <div v-show="activeTab === 'desc'" class="detail-tab-pane">
            <p class="detail-tab-lead">{{ offer.description }}</p>
            <ul class="detail-feature-list">
              <li>选好服务、详情页下单，像淘宝一样简单</li>
              <li>付完款自动进入聊天，AI 店家主动沟通需求</li>
              <li>确认收货后平台才放款给卖家</li>
            </ul>
          </div>
          <div v-show="activeTab === 'delivery'" class="detail-tab-pane">
            <p v-if="offer.delivery_description" class="detail-tab-lead">
              {{ offer.delivery_description }}
            </p>
            <p v-else class="detail-tab-muted">卖家未填写额外交付说明，付完款可在聊天中补充需求细节。</p>
          </div>
          <div v-show="activeTab === 'guide'" class="detail-tab-pane">
            <ol class="detail-guide-list">
              <li>点击「立即购买并付款」，从钱包扣款（余额不足请先充值）</li>
              <li>付款成功后自动进入订单聊天</li>
              <li>AI 龙虾店会追问专业方向、格式、截止时间等细节</li>
              <li>收到交付物后，在订单页确认收货，平台放款给店家</li>
            </ol>
          </div>
        </div>
      </section>

      <CommerceStickyBar class="detail-sticky-bar">
        <template #info>
          <span class="price-commerce detail-sticky-price">
            <span class="price-symbol">¥</span>
            <span class="price-int">{{ priceParts.int }}</span>
            <span class="price-dec">{{ priceParts.dec }}</span>
          </span>
        </template>
        <button
          type="button"
          class="btn btn-commerce detail-sticky-buy"
          :disabled="buying"
          @click="handleBuy"
        >
          {{ buying ? '处理中…' : '立即购买' }}
        </button>
      </CommerceStickyBar>

      <Teleport to="body">
        <div v-if="showPaySheet" class="pay-sheet" @click.self="closePaySheet">
          <div class="pay-sheet__panel" role="dialog" aria-modal="true" aria-label="确认付款">
            <div class="pay-sheet__handle" />
            <h2 class="pay-sheet__title">确认下单付款</h2>

            <div class="pay-sheet__product">
              <div class="pay-sheet__cover" :class="`detail-cover--${offer.category}`">
                <AppIcon :name="coverIcon(offer)" size="md" />
              </div>
              <div class="pay-sheet__product-info">
                <p class="pay-sheet__product-title">{{ offer.title }}</p>
                <p class="pay-sheet__product-shop">
                  {{ offer.seller_display_name || '技能集市认证店' }} · 🦞 付款进聊天
                </p>
              </div>
            </div>

            <dl class="pay-sheet__rows">
              <div class="pay-sheet__row">
                <dt>应付金额</dt>
                <dd class="pay-sheet__amount">
                  <span class="price-symbol">¥</span>{{ priceParts.int }}{{ priceParts.dec }}
                </dd>
              </div>
              <div class="pay-sheet__row">
                <dt>支付方式</dt>
                <dd>钱包余额</dd>
              </div>
              <div v-if="buyerNote.trim()" class="pay-sheet__row pay-sheet__row--note">
                <dt>补充说明</dt>
                <dd>{{ buyerNote.trim() }}</dd>
              </div>
            </dl>

            <p class="pay-sheet__hint">付款成功后自动进入订单聊天，确认收货前资金由平台担保。</p>
            <p v-if="buyError" class="buy-error">{{ buyError }}</p>

            <div class="pay-sheet__actions">
              <button type="button" class="btn btn-lg btn-outline-commerce" :disabled="buying" @click="closePaySheet">
                再想想
              </button>
              <button type="button" class="btn btn-lg btn-commerce pay-sheet__confirm" :disabled="buying" @click="confirmPurchase">
                {{ buying ? '处理中…' : '确认付款' }}
              </button>
            </div>
          </div>
        </div>
      </Teleport>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { getMarketplaceOffer } from '@/api'
import AppIcon from '@/components/AppIcon.vue'
import CommerceStickyBar from '@/components/CommerceStickyBar.vue'
import ShopTrustStrip from '@/components/ShopTrustStrip.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'
import { useBuyFromOffer } from '@/composables/useBuyFromOffer'
import type { IconName } from '@/components/icons'
import type { BillingModel, MarketplaceOffer } from '@/types'
import { categoryLabel } from '@/utils'

const route = useRoute()
const offerId = route.params.offerId as string

const offer = ref<MarketplaceOffer | null>(null)
const loading = ref(true)
const error = ref('')
const buyerNote = ref('')
const activeTab = ref<'desc' | 'delivery' | 'guide'>('desc')
const showPaySheet = ref(false)

const detailTabs = [
  { key: 'desc' as const, label: '商品详情' },
  { key: 'delivery' as const, label: '交付说明' },
  { key: 'guide' as const, label: '购买须知' },
]

const { buying, error: buyError, purchaseAndPay } = useBuyFromOffer()

const priceParts = computed(() => {
  const cents = offer.value?.price_cents ?? 0
  const [int, dec] = (cents / 100).toFixed(2).split('.')
  return { int, dec: `.${dec}` }
})

function coverIcon(item: MarketplaceOffer): IconName {
  const map: Record<string, IconName> = {
    design: 'target',
    data: 'chart',
    dev: 'agent',
    content: 'clipboard',
    writing: 'clipboard',
    consulting: 'person',
    ai: 'agent',
  }
  return map[item.category] ?? (item.channel === 'agent' ? 'agent' : 'package')
}

function billingLabel(model: BillingModel): string {
  const map: Record<BillingModel, string> = {
    per_use: '按次',
    per_query: '按查询',
    per_hour: '按小时',
  }
  return map[model] ?? model
}

async function loadOffer() {
  loading.value = true
  error.value = ''
  try {
    offer.value = await getMarketplaceOffer(offerId)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function handleBuy() {
  if (!offer.value) return
  buyError.value = ''
  showPaySheet.value = true
}

function closePaySheet() {
  if (buying.value) return
  showPaySheet.value = false
}

async function confirmPurchase() {
  try {
    await purchaseAndPay(offerId, buyerNote.value.trim() || undefined)
  } catch {
    /* error shown via buyError */
  }
}

onMounted(loadOffer)
</script>

<style scoped>
.offer-detail-page {
  max-width: var(--shop-content-max, 1190px);
  margin: 0 auto;
  padding-bottom: calc(80px + env(safe-area-inset-bottom, 0px));
}

.detail-crumb {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
  font-size: 13px;
  color: var(--color-label-tertiary);
}

.detail-trust-strip {
  margin-bottom: 12px;
}

.pay-sheet {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
  animation: pay-sheet-fade 0.18s ease;
}

.pay-sheet__panel {
  width: 100%;
  max-width: 480px;
  background: #fff;
  border-radius: 20px 20px 0 0;
  padding: 8px 20px calc(20px + env(safe-area-inset-bottom, 0px));
  box-shadow: 0 -8px 40px rgba(0, 0, 0, 0.18);
  animation: pay-sheet-rise 0.24s cubic-bezier(0.32, 0.72, 0, 1);
}

.pay-sheet__handle {
  width: 40px;
  height: 4px;
  border-radius: 2px;
  background: var(--color-separator, rgba(0, 0, 0, 0.12));
  margin: 6px auto 14px;
}

.pay-sheet__title {
  margin: 0 0 16px;
  font-size: 18px;
  font-weight: 700;
  text-align: center;
  color: var(--color-label);
}

.pay-sheet__product {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-separator);
}

.pay-sheet__cover {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(238, 10, 36, 0.5);
  flex-shrink: 0;
  background: linear-gradient(145deg, #e8f4ff, #fff5f0);
}

.pay-sheet__product-info {
  min-width: 0;
}

.pay-sheet__product-title {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-label);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.pay-sheet__product-shop {
  margin: 0;
  font-size: 12px;
  color: var(--color-commerce);
}

.pay-sheet__rows {
  margin: 16px 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pay-sheet__row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  font-size: 14px;
  color: var(--color-label);
}

.pay-sheet__row dt {
  color: var(--color-label-tertiary);
  flex-shrink: 0;
}

.pay-sheet__row dd {
  margin: 0;
  text-align: right;
}

.pay-sheet__row--note dd {
  color: var(--color-label-secondary);
}

.pay-sheet__amount {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-commerce);
}

.pay-sheet__amount .price-symbol {
  font-size: 14px;
}

.pay-sheet__hint {
  margin: 0 0 16px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--color-label-tertiary);
}

.pay-sheet__actions {
  display: flex;
  gap: 12px;
}

.pay-sheet__actions .btn {
  flex: 1;
  border-radius: 999px;
  font-weight: 700;
}

.pay-sheet__confirm {
  flex: 1.4;
}

@keyframes pay-sheet-fade {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes pay-sheet-rise {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}

@media (min-width: 769px) {
  .pay-sheet {
    align-items: center;
  }

  .pay-sheet__panel {
    border-radius: 20px;
    animation: pay-sheet-fade 0.2s ease;
  }

  .pay-sheet__handle {
    display: none;
  }
}

.detail-crumb a {
  color: var(--color-label-secondary);
  text-decoration: none;
}

.detail-crumb a:hover {
  color: var(--color-commerce);
}

.detail-crumb__sep {
  color: var(--color-label-tertiary);
  user-select: none;
}

.detail-crumb__current {
  color: var(--color-label-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: min(480px, 50vw);
}

.detail-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0;
  padding: 0 !important;
  overflow: hidden;
  margin-bottom: 16px;
}

.detail-gallery {
  min-width: 0;
}

.detail-cover {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 1;
  max-height: 420px;
  background: linear-gradient(145deg, #e8f4ff 0%, #f0f4ff 50%, #fff5f0 100%);
}

.detail-cover--design {
  background: linear-gradient(145deg, #ffe8f0, #fff0e8);
}

.detail-cover--data {
  background: linear-gradient(145deg, #e8fff0, #e8f8ff);
}

.detail-cover--dev,
.detail-cover--ai {
  background: linear-gradient(145deg, #e8eeff, #f0e8ff);
}

.detail-cover--content,
.detail-cover--writing {
  background: linear-gradient(145deg, #fff8e8, #ffe8e8);
}

.detail-cover__icon {
  color: rgba(238, 10, 36, 0.35);
  width: 72px;
  height: 72px;
}

.detail-cover__badge {
  position: absolute;
  top: 14px;
  left: 14px;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(238, 10, 36, 0.92);
  color: #fff;
}

.detail-cover__tag {
  position: absolute;
  bottom: 14px;
  left: 14px;
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  background: var(--gradient-commerce);
  color: #fff;
  font-weight: 600;
}

.detail-gallery__trust {
  display: none;
  list-style: none;
  margin: 0;
  padding: 12px 16px;
  gap: 12px;
  font-size: 13px;
  color: var(--color-label-secondary);
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.detail-gallery__trust li {
  display: flex;
  align-items: center;
  gap: 4px;
}

.detail-info {
  padding: 16px;
  min-width: 0;
}

.detail-shop-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.detail-shop-row__name {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-commerce);
}

.detail-shop-row__tag {
  font-size: 12px;
  color: #e8590c;
  background: rgba(255, 96, 52, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
}

.detail-title {
  margin: 0 0 14px;
  font-size: 20px;
  font-weight: 700;
  line-height: 1.4;
  color: var(--color-label);
}

.detail-price-panel {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 10px 16px;
  padding: 14px 16px;
  margin-bottom: 14px;
  background: rgba(255, 96, 52, 0.08);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: var(--radius-md);
  border: 1px solid rgba(255, 96, 52, 0.15);
  box-shadow: var(--shadow-inner);
}

.detail-price-panel__label {
  font-size: 14px;
  color: var(--color-label-secondary);
}

.detail-price .price-int {
  font-size: 32px;
}

.price-unit {
  font-size: 14px;
  color: var(--color-label-tertiary);
  margin-left: 4px;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 20px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  font-size: 13px;
  color: var(--color-label);
}

.detail-meta__item em {
  font-style: normal;
  color: var(--color-label-tertiary);
  margin-right: 6px;
}

.detail-meta__item--trust {
  color: #389e0d;
}

.detail-buy-panel {
  background: var(--color-fill);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: var(--radius-md);
  padding: 14px;
  border: 1px solid var(--color-separator);
  box-shadow: var(--shadow-inner);
}

.detail-buy-panel__label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-label);
}

.detail-buy-panel textarea {
  width: 100%;
  border: 1px solid var(--color-separator);
  border-radius: 8px;
  padding: 10px 12px;
  font: inherit;
  resize: vertical;
  background: #fff;
  margin-bottom: 14px;
}

.detail-buy-panel textarea:focus {
  outline: none;
  border-color: rgba(238, 10, 36, 0.45);
}

.detail-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-actions--inline {
  display: none;
}

.detail-buy-btn,
.detail-back-btn {
  border-radius: 999px;
  font-weight: 700;
}

.detail-back-btn {
  text-align: center;
  text-decoration: none;
}

.buy-error {
  margin: 10px 0 0;
  color: #cf1322;
  font-size: 14px;
}

.detail-tabs {
  padding: 0 !important;
  overflow: hidden;
}

.detail-tabs__head {
  display: flex;
  border-bottom: 1px solid var(--color-separator);
  background: var(--color-fill);
}

.detail-tabs__tab {
  flex: 1;
  border: none;
  background: transparent;
  padding: 14px 16px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-label-secondary);
  cursor: pointer;
  font-family: inherit;
  position: relative;
}

.detail-tabs__tab.active {
  color: var(--color-primary);
  background: var(--shop-glass-strong, rgba(255, 255, 255, 0.78));
}

.detail-tabs__tab.active::after {
  content: '';
  position: absolute;
  left: 20%;
  right: 20%;
  bottom: 0;
  height: 2px;
  background: var(--color-primary);
  border-radius: 2px 2px 0 0;
}

.detail-tabs__body {
  padding: 20px;
}

.detail-tab-lead {
  margin: 0 0 14px;
  font-size: 15px;
  line-height: 1.65;
  color: var(--color-label-secondary);
}

.detail-tab-muted {
  margin: 0;
  font-size: 14px;
  color: var(--color-label-tertiary);
  line-height: 1.6;
}

.detail-feature-list,
.detail-guide-list {
  margin: 0;
  padding-left: 20px;
  color: var(--color-label-secondary);
  font-size: 14px;
  line-height: 1.75;
}

.detail-sticky-bar {
  display: block;
}

.detail-sticky-price .price-int {
  font-size: 22px;
}

.detail-sticky-buy {
  min-width: 140px;
  border-radius: 999px;
  font-weight: 700;
}

@media (min-width: 769px) {
  .offer-detail-page {
    padding-bottom: 40px;
  }

  .detail-layout {
    grid-template-columns: 420px minmax(0, 1fr);
    align-items: start;
  }

  .detail-gallery {
    position: sticky;
    top: 72px;
  }

  .detail-gallery__trust {
    display: flex;
    flex-direction: column;
  }

  .detail-info {
    padding: 24px 28px;
  }

  .detail-title {
    font-size: 24px;
  }

  .detail-actions--inline {
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
  }

  .detail-buy-btn {
    flex: 1;
    min-width: 200px;
  }

  .detail-back-btn {
    flex-shrink: 0;
  }

  .detail-sticky-bar {
    display: none;
  }
}

@media (min-width: 1024px) {
  .detail-layout {
    grid-template-columns: 480px minmax(0, 1fr);
  }

  .detail-cover {
    max-height: none;
  }
}

@media (max-width: 768px) {
  .offer-detail-page {
    padding-bottom: calc(80px + var(--tab-bar-height) + env(safe-area-inset-bottom, 0px));
  }

  .detail-crumb__current {
    max-width: 40vw;
  }

  .detail-tabs__tab {
    padding: 12px 8px;
    font-size: 14px;
  }
}
</style>
