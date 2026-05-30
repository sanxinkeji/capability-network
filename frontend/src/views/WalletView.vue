<template>
  <div class="wallet-page app-page">
    <ShopPageHeader
      title="我的钱包"
      subtitle="充值后可在集市一键购买，平台担保托管"
    />
    <div v-if="welcomeHint" class="success-msg">{{ welcomeHint }}</div>
    <div v-if="error" class="error-msg">{{ error }}</div>
    <div v-if="success" class="success-msg">{{ success }}</div>
    <LoadingSkeleton v-if="loading" :rows="6" />

    <template v-else-if="wallet">
      <!-- 余额主卡片 -->
      <section class="wallet-card">
        <div class="wallet-card__top">
          <span class="wallet-card__label">账户余额（元）</span>
          <button type="button" class="wallet-card__eye" @click="balanceHidden = !balanceHidden">
            {{ balanceHidden ? '显示' : '隐藏' }}
          </button>
        </div>
        <div class="wallet-card__amount">
          {{ balanceHidden ? '****' : displayBalance }}
        </div>
        <div class="wallet-card__stats">
          <div class="wallet-stat">
            <span class="wallet-stat__label">冻结</span>
            <span class="wallet-stat__value">{{ balanceHidden ? '**' : formatCents(wallet.balance_frozen) }}</span>
            <span class="wallet-stat__hint">{{ WALLET_TERMS.frozen }}</span>
          </div>
          <div class="wallet-stat__divider" />
          <div class="wallet-stat">
            <span class="wallet-stat__label">不可提现</span>
            <span class="wallet-stat__value">
              {{ balanceHidden ? '**' : formatCents(wallet.points_non_withdrawable) }}
            </span>
            <span class="wallet-stat__hint">{{ WALLET_TERMS.nonWithdrawable }}</span>
          </div>
        </div>
      </section>

      <!-- 快捷入口 -->
      <section class="wallet-actions glass-card">
        <button type="button" class="wallet-action" @click="openRecharge">
          <span class="wallet-action__icon wallet-action__icon--recharge">充</span>
          <span class="wallet-action__label">充值</span>
        </button>
        <button type="button" class="wallet-action" @click="openWithdraw">
          <span class="wallet-action__icon wallet-action__icon--withdraw">提</span>
          <span class="wallet-action__label">提现</span>
        </button>
        <button type="button" class="wallet-action" @click="openRedeem">
          <span class="wallet-action__icon wallet-action__icon--recharge">卡</span>
          <span class="wallet-action__label">兑换</span>
        </button>
        <button type="button" class="wallet-action" @click="scrollToLedger">
          <span class="wallet-action__icon wallet-action__icon--bill">账</span>
          <span class="wallet-action__label">账单</span>
        </button>
      </section>

      <section class="wallet-flow glass-card">
        <h2 class="wallet-flow__title">资金怎么流转？</h2>
        <div class="wallet-flow__steps">
          <div v-for="(step, i) in WALLET_FLOW_STEPS" :key="step.label" class="wallet-flow__step">
            <span class="wallet-flow__num">{{ i + 1 }}</span>
            <div>
              <strong>{{ step.label }}</strong>
              <p>{{ step.desc }}</p>
            </div>
          </div>
        </div>
        <p class="wallet-flow__note">{{ WALLET_TERMS.commission }}</p>
      </section>

      <!-- 账单明细 -->
      <section ref="ledgerRef" class="wallet-ledger">
        <div class="wallet-ledger__head">
          <h2 class="wallet-ledger__title">账单明细</h2>
          <span class="wallet-ledger__hint">近 50 笔</span>
        </div>

        <EmptyState v-if="ledger.length === 0" icon="wallet">
          暂无账单。充值或下单后，流水会显示在这里。
        </EmptyState>

        <div v-else class="wallet-ledger__list glass-card">
          <div v-for="entry in ledger" :key="entry.id" class="wallet-bill-row">
            <div class="wallet-bill-row__icon" :class="billIconClass(entry.entry_type)">
              {{ billIconText(entry.entry_type) }}
            </div>
            <div class="wallet-bill-row__main">
              <div class="wallet-bill-row__title">{{ ledgerTypeLabel(entry.entry_type) }}</div>
              <div class="wallet-bill-row__time">{{ ledgerSubtitle(entry) }}</div>
            </div>
            <div class="wallet-bill-row__amount">
              <span :class="entry.amount_cents >= 0 ? 'bill-plus' : 'bill-minus'">
                {{ entry.amount_cents >= 0 ? '+' : '' }}{{ formatCents(Math.abs(entry.amount_cents)) }}
              </span>
              <span class="wallet-bill-row__balance">余额 {{ formatCents(entry.balance_after) }}</span>
            </div>
          </div>
        </div>
      </section>
    </template>

    <!-- 充值 -->
    <WalletBottomSheet :open="showRecharge" title="充值" @close="showRecharge = false">
      <div class="sheet-amount-display">
        <span class="sheet-amount-prefix">¥</span>
        <input
          v-model.number="depositYuan"
          class="sheet-amount-input"
          type="number"
          min="0.01"
          step="0.01"
          inputmode="decimal"
          placeholder="0.00"
        />
      </div>
      <div class="amount-chips">
        <button
          v-for="chip in amountChips"
          :key="chip"
          type="button"
          class="amount-chip"
          :class="{ 'amount-chip--active': depositYuan === chip }"
          @click="depositYuan = chip"
        >
          ¥{{ chip }}
        </button>
      </div>
      <p class="sheet-section-label">支付方式</p>
      <div class="pay-channel-grid">
        <button
          type="button"
          class="pay-channel"
          :class="{ 'pay-channel--active': depositChannel === 'wechat' }"
          @click="depositChannel = 'wechat'"
        >
          <span class="pay-channel__badge pay-channel__badge--wechat">微</span>
          <span>微信支付</span>
        </button>
        <button
          type="button"
          class="pay-channel"
          :class="{ 'pay-channel--active': depositChannel === 'alipay' }"
          @click="depositChannel = 'alipay'"
        >
          <span class="pay-channel__badge pay-channel__badge--alipay">支</span>
          <span>支付宝</span>
        </button>
      </div>
      <template #footer>
        <button class="btn btn-commerce btn-block" :disabled="depositing || depositYuan <= 0" @click="handleDeposit">
          {{ depositing ? '处理中…' : `确认充值 ¥${depositYuan.toFixed(2)}` }}
        </button>
      </template>
    </WalletBottomSheet>

    <!-- 实名认证 -->
    <WalletBottomSheet :open="showKyc" title="实名认证" @close="showKyc = false">
      <template v-if="kycPending">
        <p class="sheet-note sheet-note--center">
          您的实名信息已提交，正在人工审核中。审核通过后即可提现。
        </p>
        <p v-if="auth.user?.kyc_id_number_masked" class="sheet-available">
          {{ auth.user.kyc_real_name }} · {{ auth.user.kyc_id_number_masked }}
        </p>
      </template>
      <template v-else>
        <p class="sheet-note">提现前需完成 L1 实名认证，信息仅用于人工审核，不会对接第三方接口。</p>
        <div class="inset-group inset-group--flat">
          <div class="inset-row">
            <label>真实姓名</label>
            <input v-model="kycRealName" placeholder="与身份证一致" autocomplete="name" />
          </div>
          <div class="inset-row">
            <label>身份证号</label>
            <input v-model="kycIdNumber" placeholder="18 位身份证号" autocomplete="off" maxlength="18" />
          </div>
        </div>
      </template>
      <template #footer>
        <button
          v-if="!kycPending"
          class="btn btn-commerce btn-block"
          :disabled="submittingKyc || !kycRealName.trim() || kycIdNumber.trim().length < 15"
          @click="handleKycSubmit"
        >
          {{ submittingKyc ? '提交中…' : '提交实名信息' }}
        </button>
        <button v-else type="button" class="btn btn-secondary btn-block" @click="showKyc = false">
          知道了
        </button>
      </template>
    </WalletBottomSheet>

    <!-- 提现 -->
    <WalletBottomSheet :open="showWithdraw" title="提现到银行卡/账户" @close="showWithdraw = false">
      <div class="sheet-amount-display sheet-amount-display--compact">
        <span class="sheet-amount-prefix">¥</span>
        <input
          v-model.number="withdrawYuan"
          class="sheet-amount-input"
          type="number"
          min="100"
          step="0.01"
          inputmode="decimal"
          placeholder="最低 100"
        />
      </div>
      <p class="sheet-available">可提现 {{ formatCents(wallet?.balance_available ?? 0) }}</p>
      <div class="inset-group inset-group--flat">
        <div class="inset-row">
          <label>到账方式</label>
          <select v-model="withdrawMethod">
            <option value="alipay">支付宝</option>
            <option value="wechat">微信</option>
            <option value="bank">银行卡</option>
          </select>
        </div>
        <div class="inset-row">
          <label>收款账号</label>
          <input v-model="payoutAccount" placeholder="请输入账号" autocomplete="off" />
        </div>
        <div class="inset-row">
          <label>真实姓名</label>
          <input v-model="payoutName" placeholder="与账号实名一致" autocomplete="name" />
        </div>
      </div>
      <p class="sheet-note">提交后 1–3 个工作日审核打款，请确保信息准确。</p>
      <template #footer>
        <button
          class="btn btn-commerce btn-block"
          :disabled="withdrawing || withdrawYuan < 100 || !payoutAccount.trim() || !payoutName.trim()"
          @click="handleWithdraw"
        >
          {{ withdrawing ? '提交中…' : '确认提现' }}
        </button>
      </template>
    </WalletBottomSheet>

    <!-- 充值卡兑换 -->
    <WalletBottomSheet :open="showRedeem" title="兑换余额充值卡" @close="showRedeem = false">
      <div class="inset-group inset-group--flat">
        <div class="inset-row">
          <label>充值卡码</label>
          <input v-model="redeemCode" placeholder="请输入充值卡码" autocomplete="off" />
        </div>
      </div>
      <p class="sheet-note">每张充值卡仅可使用一次，兑换后余额立即到账。</p>
      <template #footer>
        <button class="btn btn-commerce btn-block" :disabled="redeeming || !redeemCode.trim()" @click="handleRedeem">
          {{ redeeming ? '兑换中…' : '确认兑换' }}
        </button>
      </template>
    </WalletBottomSheet>

    <!-- 支付等待 -->
    <Teleport to="body">
      <Transition name="sheet-fade">
        <div v-if="pendingOrder" class="pay-overlay" @click.self="closePayOverlay">
          <div class="pay-modal glass-card">
            <button type="button" class="pay-modal__close" aria-label="关闭" @click="closePayOverlay">
              <AppIcon name="close" size="sm" />
            </button>
            <p class="pay-modal__channel">
              {{ pendingOrder.channel === 'wechat' ? '微信支付' : '支付宝' }}
            </p>
            <p class="pay-modal__amount">{{ formatCents(pendingOrder.amount_cents) }}</p>
            <div class="pay-modal__qr-placeholder">
              <span class="pay-modal__qr-icon">扫码</span>
              <p>请在 {{ pendingOrder.channel === 'wechat' ? '微信' : '支付宝' }} 中完成支付</p>
            </div>
            <a
              v-if="pendingOrder.pay_url"
              :href="pendingOrder.pay_url"
              target="_blank"
              rel="noopener"
              class="btn btn-commerce btn-block"
            >
              打开{{ pendingOrder.channel === 'wechat' ? '微信' : '支付宝' }}支付
            </a>
            <button
              v-if="pendingOrder.pay_url"
              type="button"
              class="btn btn-secondary btn-block btn-sm"
              @click="copyPayUrl"
            >
              复制支付链接
            </button>
            <p class="pay-modal__status">
              {{ payStatusLabel(pendingOrder.status) }}
              <span v-if="pendingOrder.status === 'pending'" class="pay-modal__dot" />
            </p>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { submitKyc } from '@/api/kyc'
import {
  createDepositOrder,
  createWithdrawRequest,
  getDepositOrder,
  getLedger,
  getWallet,
  redeemRechargeCard,
} from '@/api/wallets'
import type { DepositOrder, Wallet, WalletLedgerEntry } from '@/types'
import { formatCents, formatDate, ledgerDescriptionLabel, ledgerTypeLabel } from '@/utils'
import { WALLET_FLOW_STEPS, WALLET_TERMS } from '@/utils/platformGuide'
import { useAuthStore } from '@/stores/auth'
import AppIcon from '@/components/AppIcon.vue'
import WalletBottomSheet from '@/components/WalletBottomSheet.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'
import ShopPageHeader from '@/components/ShopPageHeader.vue'
import EmptyState from '@/components/EmptyState.vue'

const route = useRoute()
const auth = useAuthStore()

const wallet = ref<Wallet | null>(null)
const ledger = ref<WalletLedgerEntry[]>([])
const loading = ref(true)
const depositing = ref(false)
const withdrawing = ref(false)
const error = ref('')
const success = ref('')
const balanceHidden = ref(false)

const showRecharge = ref(false)
const showWithdraw = ref(false)
const showKyc = ref(false)
const showRedeem = ref(false)
const ledgerRef = ref<HTMLElement | null>(null)

const depositYuan = ref(100)
const depositChannel = ref<'wechat' | 'alipay'>('alipay')
const pendingOrder = ref<DepositOrder | null>(null)
const redeemCode = ref('')
const redeeming = ref(false)
let pollTimer: ReturnType<typeof setInterval> | null = null

const withdrawYuan = ref(100)
const withdrawMethod = ref<'alipay' | 'wechat' | 'bank'>('alipay')
const payoutAccount = ref('')
const payoutName = ref('')

const kycRealName = ref('')
const kycIdNumber = ref('')
const submittingKyc = ref(false)

const amountChips = [50, 100, 200, 500, 1000]

const kycVerified = computed(() => {
  const level = auth.user?.kyc_level
  return level === 'L1' || level === 'L2'
})

const kycPending = computed(() => auth.user?.kyc_status === 'pending')

const welcomeHint = computed(() =>
  route.query.welcome === '1'
    ? '欢迎加入！建议先充值少量余额，便于匹配下单时自动支付。'
    : '',
)

const displayBalance = computed(() => {
  if (!wallet.value) return '0.00'
  return (wallet.value.balance_available / 100).toFixed(2)
})

function openRecharge() {
  error.value = ''
  success.value = ''
  showRecharge.value = true
}

function openWithdraw() {
  error.value = ''
  success.value = ''
  if (!kycVerified.value) {
    kycRealName.value = auth.user?.kyc_real_name ?? ''
    showKyc.value = true
    return
  }
  showWithdraw.value = true
}

function openRedeem() {
  error.value = ''
  success.value = ''
  redeemCode.value = ''
  showRedeem.value = true
}

function scrollToLedger() {
  ledgerRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function billIconText(type: string) {
  const map: Record<string, string> = {
    deposit: '入',
    withdraw: '出',
    payment: '付',
    refund: '退',
    freeze: '冻',
    unfreeze: '解',
    fee: '费',
  }
  return map[type] ?? '·'
}

function billIconClass(type: string) {
  if (type === 'deposit' || type === 'unfreeze' || type === 'refund') return 'wallet-bill-row__icon--in'
  if (type === 'withdraw' || type === 'payment' || type === 'freeze' || type === 'fee') {
    return 'wallet-bill-row__icon--out'
  }
  return ''
}

function payStatusLabel(status: string) {
  const map: Record<string, string> = {
    pending: '等待支付中',
    paid: '支付成功',
    failed: '支付失败',
  }
  return map[status] ?? status
}

function ledgerSubtitle(entry: WalletLedgerEntry): string {
  const desc = ledgerDescriptionLabel(entry.description)
  const when = formatDate(entry.created_at)
  return desc ? `${desc} · ${when}` : when
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function closePayOverlay() {
  if (pendingOrder.value?.status === 'pending') {
    if (!confirm('支付尚未完成，确定关闭？')) return
  }
  pendingOrder.value = null
  stopPolling()
}

async function copyPayUrl() {
  if (pendingOrder.value?.pay_url) {
    await navigator.clipboard.writeText(pendingOrder.value.pay_url)
    success.value = '支付链接已复制'
  }
}

async function pollOrder(orderId: string) {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const order = await getDepositOrder(orderId)
      pendingOrder.value = order
      if (order.status === 'paid' && order.wallet) {
        wallet.value = order.wallet
        success.value = '充值成功'
        showRecharge.value = false
        stopPolling()
        setTimeout(() => {
          pendingOrder.value = null
        }, 1500)
        const ledgerData = await getLedger()
        ledger.value = ledgerData.items
      }
    } catch {
      /* ignore */
    }
  }, 3000)
}

async function loadWallet() {
  loading.value = true
  error.value = ''
  try {
    const [w, ledgerData] = await Promise.all([getWallet(), getLedger(), auth.fetchProfile()])
    wallet.value = w
    ledger.value = ledgerData.items
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function handleKycSubmit() {
  submittingKyc.value = true
  error.value = ''
  try {
    await submitKyc({
      real_name: kycRealName.value.trim(),
      id_number: kycIdNumber.value.trim(),
    })
    await auth.fetchProfile()
    success.value = '实名信息已提交，请等待审核通过后再提现'
    showKyc.value = false
    kycIdNumber.value = ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : '提交失败'
  } finally {
    submittingKyc.value = false
  }
}

async function handleDeposit() {
  depositing.value = true
  error.value = ''
  try {
    const amountCents = Math.round(depositYuan.value * 100)
    const order = await createDepositOrder({
      amount_cents: amountCents,
      channel: depositChannel.value,
    })
    if (order.status === 'paid' && order.wallet) {
      wallet.value = order.wallet
      success.value = '充值成功'
      showRecharge.value = false
      const ledgerData = await getLedger()
      ledger.value = ledgerData.items
    } else if (order.pay_url) {
      pendingOrder.value = order
      showRecharge.value = false
      await pollOrder(order.id)
    } else {
      error.value = '支付渠道未就绪，请联系客服'
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '充值失败'
  } finally {
    depositing.value = false
  }
}

async function handleWithdraw() {
  withdrawing.value = true
  error.value = ''
  try {
    const result = await createWithdrawRequest({
      amount_cents: Math.round(withdrawYuan.value * 100),
      payout_method: withdrawMethod.value,
      payout_account: payoutAccount.value.trim(),
      payout_name: payoutName.value.trim(),
    })
    wallet.value = result.wallet
    success.value = '提现申请已提交，请等待审核'
    showWithdraw.value = false
    const ledgerData = await getLedger()
    ledger.value = ledgerData.items
  } catch (e) {
    error.value = e instanceof Error ? e.message : '提现失败'
  } finally {
    withdrawing.value = false
  }
}

async function handleRedeem() {
  redeeming.value = true
  error.value = ''
  try {
    wallet.value = await redeemRechargeCard(redeemCode.value.trim())
    success.value = '充值卡兑换成功'
    showRedeem.value = false
    const ledgerData = await getLedger()
    ledger.value = ledgerData.items
  } catch (e) {
    error.value = e instanceof Error ? e.message : '兑换失败'
  } finally {
    redeeming.value = false
  }
}

onMounted(loadWallet)
onUnmounted(stopPolling)
</script>

<style scoped>
.wallet-stat__hint {
  display: block;
  font-size: 10px;
  font-weight: 400;
  opacity: 0.85;
  margin-top: 4px;
  line-height: 1.3;
  color: rgba(255, 255, 255, 0.78);
}

.wallet-flow {
  padding: 14px 16px !important;
  margin-bottom: 16px;
}

.wallet-flow__title {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 600;
}

.wallet-flow__steps {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.wallet-flow__step {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  font-size: 13px;
}

.wallet-flow__step p {
  margin: 2px 0 0;
  color: var(--color-label-secondary);
  line-height: 1.4;
}

.wallet-flow__num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--color-commerce-muted);
  color: var(--color-commerce);
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.wallet-flow__note {
  margin: 12px 0 0;
  font-size: 12px;
  color: var(--color-label-tertiary);
  line-height: 1.45;
}

.wallet-page {
  max-width: 520px;
  margin: 0 auto;
}

.wallet-card {
  padding: 24px 20px 20px;
  margin-bottom: 16px;
  border-radius: 16px;
  background: var(--shop-header-gradient);
  color: #fff;
  box-shadow: 0 12px 32px rgba(238, 10, 36, 0.25);
}

.wallet-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.wallet-card__label {
  font-size: 14px;
  opacity: 0.88;
}

.wallet-card__eye {
  border: none;
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 12px;
  cursor: pointer;
}

.wallet-card__amount {
  font-size: 40px;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.1;
  margin-bottom: 20px;
}

.wallet-card__stats {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.wallet-stat {
  flex: 1;
}

.wallet-stat__label {
  display: block;
  font-size: 12px;
  opacity: 0.75;
  margin-bottom: 4px;
}

.wallet-stat__value {
  font-size: 16px;
  font-weight: 600;
}

.wallet-stat__divider {
  width: 1px;
  height: 28px;
  background: rgba(255, 255, 255, 0.25);
}

.wallet-actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding: 20px 12px !important;
  margin-bottom: 24px;
}

.wallet-action {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 8px 4px;
  border-radius: var(--radius-sm);
  transition: background 0.15s;
}

.wallet-action:hover {
  background: var(--color-fill);
}

.wallet-action__icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}

.wallet-action__icon--recharge {
  background: linear-gradient(135deg, #1677ff, #4096ff);
}
.wallet-action__icon--withdraw {
  background: linear-gradient(135deg, #ff7a45, #ff4d4f);
}
.wallet-action__icon--bill {
  background: linear-gradient(135deg, #52c41a, #389e0d);
}

.wallet-action__label {
  font-size: 13px;
  color: var(--color-label);
  font-weight: 500;
}

.wallet-ledger__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 10px;
}

.wallet-ledger__title {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
}

.wallet-ledger__hint {
  font-size: 13px;
  color: var(--color-label-tertiary);
}

.wallet-ledger__list {
  padding: 4px 0 !important;
  overflow: hidden;
}

.wallet-bill-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-separator);
}

.wallet-bill-row:last-child {
  border-bottom: none;
}

.wallet-bill-row__icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  background: var(--color-fill);
  color: var(--color-label-secondary);
  flex-shrink: 0;
}

.wallet-bill-row__icon--in {
  background: rgba(82, 196, 26, 0.12);
  color: #389e0d;
}

.wallet-bill-row__icon--out {
  background: rgba(255, 77, 79, 0.1);
  color: #cf1322;
}

.wallet-bill-row__main {
  flex: 1;
  min-width: 0;
}

.wallet-bill-row__title {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-label);
}

.wallet-bill-row__time {
  font-size: 12px;
  color: var(--color-label-tertiary);
  margin-top: 2px;
}

.wallet-bill-row__amount {
  text-align: right;
  flex-shrink: 0;
}

.bill-plus {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-success);
}

.bill-minus {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-label);
}

.wallet-bill-row__balance {
  display: block;
  font-size: 11px;
  color: var(--color-label-tertiary);
  margin-top: 2px;
}

/* Sheet internals */
.sheet-amount-display {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
  padding: 16px 0 8px;
}

.sheet-amount-display--compact {
  padding-top: 8px;
}

.sheet-amount-prefix {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-label-secondary);
}

.sheet-amount-input {
  border: none;
  background: transparent;
  font-size: 42px;
  font-weight: 700;
  width: min(240px, 60vw);
  text-align: center;
  color: var(--color-label);
  outline: none;
}

.sheet-amount-input::placeholder {
  color: var(--color-label-tertiary);
}

.amount-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-bottom: 20px;
}

.amount-chip {
  padding: 8px 16px;
  border-radius: 20px;
  border: 1px solid var(--color-separator);
  background: var(--color-fill);
  font-size: 14px;
  cursor: pointer;
}

.amount-chip--active {
  border-color: #1677ff;
  background: rgba(22, 119, 255, 0.1);
  color: #1677ff;
  font-weight: 600;
}

.sheet-section-label {
  font-size: 13px;
  color: var(--color-label-secondary);
  margin: 0 0 10px;
}

.pay-channel-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.pay-channel {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px;
  border: 2px solid var(--color-separator);
  border-radius: 12px;
  background: var(--color-bg-elevated);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.pay-channel--active {
  border-color: #1677ff;
  background: rgba(22, 119, 255, 0.06);
}

.pay-channel__badge {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
  font-weight: 700;
}

.pay-channel__badge--wechat {
  background: #07c160;
}

.pay-channel__badge--alipay {
  background: #1677ff;
}

.sheet-available {
  text-align: center;
  font-size: 13px;
  color: var(--color-label-secondary);
  margin: 0 0 16px;
}

.inset-group--flat {
  margin-bottom: 12px;
}

.sheet-note {
  font-size: 12px;
  color: var(--color-label-tertiary);
  margin: 0;
  line-height: 1.5;
}

.sheet-note--center {
  text-align: center;
  padding: 12px 0;
}

.sheet-note--center + .sheet-available {
  margin-top: 0;
}

.btn-block {
  width: 100%;
}

/* Pay overlay */
.pay-overlay {
  position: fixed;
  inset: 0;
  z-index: 300;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.pay-modal {
  position: relative;
  width: 100%;
  max-width: 340px;
  padding: 28px 24px 24px !important;
  text-align: center;
}

.pay-modal__close {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: var(--color-fill);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pay-modal__channel {
  margin: 0 0 4px;
  font-size: 14px;
  color: var(--color-label-secondary);
}

.pay-modal__amount {
  margin: 0 0 20px;
  font-size: 36px;
  font-weight: 700;
  color: var(--color-label);
}

.pay-modal__qr-placeholder {
  padding: 24px;
  margin-bottom: 16px;
  border-radius: 12px;
  background: var(--color-fill);
}

.pay-modal__qr-icon {
  display: inline-flex;
  width: 64px;
  height: 64px;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: #fff;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-label-secondary);
  margin-bottom: 8px;
  border: 2px dashed var(--color-separator);
}

.pay-modal__qr-placeholder p {
  margin: 0;
  font-size: 13px;
  color: var(--color-label-secondary);
}

.pay-modal__status {
  margin: 12px 0 0;
  font-size: 13px;
  color: var(--color-label-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.pay-modal__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #1677ff;
  animation: pulse 1.2s ease infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.3;
  }
  50% {
    opacity: 1;
  }
}

.sheet-fade-enter-active,
.sheet-fade-leave-active {
  transition: opacity 0.25s ease;
}
.sheet-fade-enter-from,
.sheet-fade-leave-to {
  opacity: 0;
}
</style>
