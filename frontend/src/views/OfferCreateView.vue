<template>
  <div class="app-page">
    <ShopPageHeader
      title="发布商品"
      subtitle="上架 AI 技能，接入 OpenClaw / Hermes 后自动接单交付"
    >
      <template #actions>
        <RouterLink to="/app/offers" class="btn btn-secondary btn-sm">返回列表</RouterLink>
      </template>
    </ShopPageHeader>

    <HelpTip>{{ SELLER_FLOW_HINT }}</HelpTip>

    <div class="inset-form">
      <div v-if="error" class="error-msg">{{ error }}</div>
      <div v-if="success" class="success-msg">服务已创建（草稿），可在店铺中发布</div>

      <form @submit.prevent="handleSubmit">
        <div class="inset-group">
          <div class="inset-row">
            <label>标题</label>
            <input v-model="form.title" required maxlength="200" placeholder="例如：品牌 Logo 设计服务" />
          </div>
          <div class="inset-row">
            <label>描述</label>
            <textarea v-model="form.description" required rows="3" placeholder="例如：提供高质量品牌视觉设计，含源文件交付" />
          </div>
          <div class="inset-row">
            <label>分类</label>
            <select v-model="form.category" required>
              <option v-for="c in CATEGORY_OPTIONS" :key="c.value" :value="c.value">
                {{ c.label }}
              </option>
            </select>
          </div>
        </div>

        <div class="inset-group inset-row--inline">
          <div class="inset-cell">
            <label>计费模式</label>
            <select v-model="form.billing_model">
              <option value="per_use">按次</option>
              <option value="per_query">按查询</option>
              <option value="per_hour">按小时</option>
            </select>
            <p class="form-hint">按次适合 API 类能力，按小时适合咨询类服务</p>
          </div>
          <div class="inset-cell">
            <label>服务类型</label>
            <p class="form-hint form-hint--static">AI 龙虾店（需接入 OpenClaw 自动交付）</p>
          </div>
        </div>

        <div class="inset-group">
          <div class="inset-row">
            <label>价格（元）</label>
            <input v-model.number="priceYuan" type="number" min="0" step="0.01" required />
            <p class="form-hint">买方下单时将按此价格从钱包支付（平台托管）</p>
          </div>
          <div class="inset-row">
            <label>交付说明</label>
            <textarea v-model="form.delivery_description" rows="2" placeholder="可选" />
          </div>
        </div>

        <div class="inset-form-actions">
          <button class="btn btn-lg btn-commerce" type="submit" :disabled="submitting">
            {{ submitting ? '提交中…' : '创建供给' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { createOffer } from '@/api'
import type { BillingModel, OfferChannel } from '@/types'
import { CATEGORY_OPTIONS } from '@/utils'
import { SELLER_FLOW_HINT } from '@/utils/platformGuide'
import HelpTip from '@/components/HelpTip.vue'
import ShopPageHeader from '@/components/ShopPageHeader.vue'

const router = useRouter()
const submitting = ref(false)
const error = ref('')
const success = ref(false)

const form = reactive({
  title: '',
  description: '',
  category: 'design',
  channel: 'agent' as OfferChannel,
  billing_model: 'per_use' as BillingModel,
  price_cents: 0,
  currency: 'CNY',
  delivery_description: '',
})

const priceYuan = computed({
  get: () => form.price_cents / 100,
  set: (v: number) => {
    form.price_cents = Math.round(v * 100)
  },
})

async function handleSubmit() {
  submitting.value = true
  error.value = ''
  success.value = false
  try {
    await createOffer(form)
    success.value = true
    setTimeout(() => router.push('/app/offers'), 800)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '创建失败'
  } finally {
    submitting.value = false
  }
}
</script>
