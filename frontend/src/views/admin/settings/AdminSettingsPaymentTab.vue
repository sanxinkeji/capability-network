<template>
  <div class="admin-payment-settings">
    <div class="admin-form-card">
      <AdminToggleRow v-model="form.payment_enabled" label="启用支付" hint="关闭后用户无法发起充值订单" />

      <div class="admin-form-section-title" style="margin-top: 20px">商品与金额</div>
      <div class="admin-form-grid">
        <div class="admin-form-field">
          <label>商品名称前缀</label>
          <input v-model="form.payment_product_name_prefix" placeholder="Capability" />
        </div>
        <div class="admin-form-field">
          <label>商品名称后缀</label>
          <input v-model="form.payment_product_name_suffix" placeholder="CNY" />
        </div>
        <div class="admin-form-field" style="grid-column: 1 / -1">
          <label>描述</label>
          <input v-model="form.payment_product_description" placeholder="默认商品描述" />
        </div>
        <div class="admin-form-field">
          <label>最低金额（分）</label>
          <input v-model.number="form.min_deposit_cents" type="number" min="1" />
          <p class="admin-form-hint">= {{ formatCents(form.min_deposit_cents) }}</p>
        </div>
        <div class="admin-form-field">
          <label>最高金额（分）</label>
          <input v-model.number="form.max_deposit_cents" type="number" min="1" placeholder="留空不限" />
          <p class="admin-form-hint">{{ form.max_deposit_cents ? `= ${formatCents(form.max_deposit_cents)}` : '留空表示不限制' }}</p>
        </div>
        <div class="admin-form-field">
          <label>每日限额（分）</label>
          <input v-model.number="form.payment_daily_limit_cents" type="number" min="1" placeholder="留空不限" />
          <p class="admin-form-hint">单用户每日充值总额上限</p>
        </div>
        <div class="admin-form-field">
          <label>余额充值倍率（%）</label>
          <input v-model.number="form.payment_recharge_rate_percent" type="number" min="1" max="1000" />
          <p class="admin-form-hint">100 表示 1 元充值 = 1 元余额</p>
        </div>
        <div class="admin-form-field">
          <label>充值手续费率（%）</label>
          <input v-model.number="form.payment_fee_rate_percent" type="number" min="0" max="50" />
          <p class="admin-form-hint">向用户额外收取的手续费比例</p>
        </div>
        <div class="admin-form-field">
          <label>订单超时（分钟）</label>
          <input v-model.number="form.payment_order_timeout_minutes" type="number" min="1" max="1440" />
        </div>
      </div>
    </div>

    <div class="admin-form-card">
      <div class="admin-form-section-title">高级规则</div>
      <div class="admin-form-grid">
        <div class="admin-form-field">
          <label>每天最大支付次数</label>
          <input v-model.number="form.max_daily_payment_count" type="number" min="1" placeholder="留空不限" />
          <p class="admin-form-hint">仅限充值余额场景</p>
        </div>
        <div class="admin-form-field">
          <label>最大待支付订单数</label>
          <input v-model.number="form.max_pending_payment_orders" type="number" min="1" max="20" />
          <p class="admin-form-hint">同时存在的未支付订单上限</p>
        </div>
      </div>
      <AdminToggleRow
        v-model="form.payment_broadcast_mode"
        label="允许全透明广播支付"
        hint="开启后隐藏支付方式列表，使用广播模式自动路由"
      />
    </div>

    <div class="admin-form-card">
      <div class="admin-form-section-title">启用付款服务商</div>
      <p class="admin-form-hint" style="margin-bottom: 12px">选择要启用的支付渠道，下方可配置对应服务商</p>
      <div class="admin-provider-chips">
        <button
          type="button"
          class="admin-provider-chip"
          :class="{ 'admin-provider-chip--active': form.easypay_enabled }"
          @click="form.easypay_enabled = !form.easypay_enabled"
        >易支付</button>
        <button
          type="button"
          class="admin-provider-chip"
          :class="{ 'admin-provider-chip--active': form.payment_alipay_enabled }"
          @click="form.payment_alipay_enabled = !form.payment_alipay_enabled"
        >支付宝</button>
        <button
          type="button"
          class="admin-provider-chip"
          :class="{ 'admin-provider-chip--active': form.payment_wechat_enabled }"
          @click="form.payment_wechat_enabled = !form.payment_wechat_enabled"
        >微信支付</button>
        <button
          type="button"
          class="admin-provider-chip"
          :class="{ 'admin-provider-chip--active': form.stripe_enabled }"
          @click="form.stripe_enabled = !form.stripe_enabled"
        >Stripe</button>
        <button
          type="button"
          class="admin-provider-chip"
          :class="{ 'admin-provider-chip--active': form.payment_airwallex_enabled }"
          @click="form.payment_airwallex_enabled = !form.payment_airwallex_enabled"
        >Airwallex</button>
      </div>
      <p v-if="!anyProviderEnabled" class="admin-payment-warn">请至少启用一种服务商</p>
    </div>

    <div class="admin-form-card">
      <div class="admin-form-section-title">帮助内容</div>
      <div class="admin-form-grid">
        <div class="admin-form-field">
          <label>帮助图片 URL</label>
          <input v-model="form.payment_help_image_url" placeholder="https://example.com/help.png" />
        </div>
        <div class="admin-form-field" style="grid-column: 1 / -1">
          <label>帮助文本</label>
          <textarea v-model="form.payment_help_text" rows="4" placeholder="充值说明、注意事项等" />
        </div>
      </div>
    </div>

    <div class="admin-form-card">
      <div class="admin-provider-table__head">
        <div class="admin-form-section-title" style="margin: 0">服务商管理</div>
        <button type="button" class="btn btn-ghost-admin" @click="$emit('refresh')">刷新</button>
      </div>

      <div v-if="!anyProviderEnabled" class="admin-payment-empty">
        请先在上方启用至少一种服务商
      </div>

      <template v-else>
        <div class="admin-table-wrap" style="margin-bottom: 16px">
          <table class="admin-table">
            <thead>
              <tr><th>服务商</th><th>状态</th><th>回调地址</th></tr>
            </thead>
            <tbody>
              <tr v-for="row in visibleProviderRows" :key="row.id">
                <td><strong>{{ row.name }}</strong></td>
                <td>
                  <span class="admin-tag" :class="row.configured ? 'admin-tag--success' : 'admin-tag--warn'">
                    {{ row.configured ? '已配置' : '未配置' }}
                  </span>
                </td>
                <td class="admin-provider-callback">{{ row.callback || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="form.easypay_enabled" class="admin-payment-provider">
          <div class="admin-payment-provider__head">
            <span class="admin-payment-provider__title">EasyPay 易支付</span>
            <span class="admin-tag" :class="easypayConfigured ? 'admin-tag--success' : 'admin-tag--warn'">
              {{ easypayConfigured ? '已配置' : '未配置' }}
            </span>
          </div>
          <div class="admin-form-grid">
            <div class="admin-form-field"><label>商户 PID</label><input v-model="form.easypay_pid" /></div>
            <div class="admin-form-field"><label>商户密钥</label><input v-model="form.easypay_key" type="password" /></div>
            <div class="admin-form-field" style="grid-column: 1 / -1"><label>API 地址</label><input v-model="form.easypay_api_base" /></div>
            <div class="admin-form-field">
              <label>支付宝路由</label>
              <select v-model="form.payment_alipay_source" :disabled="!form.payment_alipay_enabled">
                <option value="direct">官方直连</option>
                <option value="easypay">EasyPay 聚合</option>
              </select>
            </div>
            <div class="admin-form-field">
              <label>微信路由</label>
              <select v-model="form.payment_wechat_source" :disabled="!form.payment_wechat_enabled">
                <option value="direct">官方直连</option>
                <option value="easypay">EasyPay 聚合</option>
              </select>
            </div>
            <div class="admin-form-field"><label>支付宝通道 ID</label><input v-model="form.easypay_alipay_type" placeholder="alipay" /></div>
            <div class="admin-form-field"><label>微信通道 ID</label><input v-model="form.easypay_wechat_type" placeholder="wxpay" /></div>
          </div>
        </div>

        <div v-if="form.payment_alipay_enabled" class="admin-payment-provider">
          <div class="admin-payment-provider__head">
            <span class="admin-payment-provider__title">支付宝</span>
          </div>
          <AdminAlert type="info" message="官方直连密钥请在服务器 .env 中配置 ALIPAY_* 变量" />
        </div>

        <div v-if="form.payment_wechat_enabled" class="admin-payment-provider">
          <div class="admin-payment-provider__head">
            <span class="admin-payment-provider__title">微信支付</span>
          </div>
          <AdminAlert type="info" message="官方直连密钥请在服务器 .env 中配置 WECHAT_PAY_* 变量" />
        </div>

        <div v-if="form.stripe_enabled" class="admin-payment-provider">
          <div class="admin-payment-provider__head">
            <span class="admin-payment-provider__title">Stripe</span>
            <span class="admin-tag" :class="stripeConfigured ? 'admin-tag--success' : 'admin-tag--warn'">
              {{ stripeConfigured ? '已配置' : '未配置' }}
            </span>
          </div>
          <div class="admin-form-grid">
            <div class="admin-form-field"><label>Publishable Key</label><input v-model="form.stripe_public_key" /></div>
            <div class="admin-form-field"><label>Secret Key</label><input v-model="form.stripe_secret_key" type="password" /></div>
            <div class="admin-form-field" style="grid-column: 1 / -1">
              <label>Webhook Secret</label>
              <input v-model="form.stripe_webhook_secret" type="password" placeholder="whsec_..." />
              <p class="admin-form-hint">Stripe Dashboard → Webhooks → 签名密钥，用于校验回调</p>
            </div>
          </div>
        </div>

        <div v-if="form.payment_airwallex_enabled" class="admin-payment-provider">
          <div class="admin-payment-provider__head">
            <span class="admin-payment-provider__title">Airwallex</span>
            <span class="admin-tag admin-tag--muted">即将推出</span>
          </div>
          <AdminAlert type="info" message="Airwallex 国际支付接入将在后续版本开放。" />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PaymentConfigInfo, PlatformSettings } from '@/types'
import { formatCents } from '@/utils'
import AdminToggleRow from '@/components/admin/AdminToggleRow.vue'
import AdminAlert from '@/components/admin/AdminAlert.vue'

const props = defineProps<{
  providerRows: { id: string; name: string; configured: boolean; callback: string }[]
  payment: PaymentConfigInfo | null
}>()
defineEmits<{ refresh: [] }>()
const form = defineModel<PlatformSettings>({ required: true })

const anyProviderEnabled = computed(() =>
  form.value.easypay_enabled
  || form.value.payment_alipay_enabled
  || form.value.payment_wechat_enabled
  || form.value.stripe_enabled
  || form.value.payment_airwallex_enabled,
)

const easypayConfigured = computed(() => props.payment?.easypay_configured ?? false)
const stripeConfigured = computed(() => props.payment?.stripe_configured ?? false)

const visibleProviderRows = computed(() => {
  const rows = props.providerRows
  const f = form.value
  return rows.filter((row) => {
    if (row.id === 'easypay') return f.easypay_enabled
    if (row.id === 'alipay') return f.payment_alipay_enabled
    if (row.id === 'wechat') return f.payment_wechat_enabled
    if (row.id === 'stripe') return f.stripe_enabled
    return false
  })
})
</script>

<style scoped>
.admin-provider-callback { font-size: 12px; color: #6b7280; word-break: break-all; max-width: 360px; }
.admin-provider-table__head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.admin-payment-empty {
  padding: 32px;
  text-align: center;
  color: #9ca3af;
  background: #fafafa;
  border-radius: 10px;
  border: 1px dashed #e5e7eb;
}
.admin-payment-warn {
  margin-top: 10px;
  color: #d97706;
}
</style>
