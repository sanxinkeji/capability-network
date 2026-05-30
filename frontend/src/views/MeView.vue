<template>
  <div class="me-page app-page">
    <header class="me-head glass-card">
      <div class="me-head__user">
        <span class="me-head__avatar">{{ avatarLetter }}</span>
        <div>
          <h1>{{ auth.user?.display_name || '买家' }}</h1>
          <p>AI 技能集市 · 像淘宝一样买服务</p>
        </div>
      </div>
    </header>

    <section class="me-orders glass-card">
      <div class="me-orders__head">
        <h2>我的订单</h2>
        <RouterLink to="/app/deals">全部订单 →</RouterLink>
      </div>
      <div class="me-orders__grid">
        <RouterLink
          v-for="item in orderShortcuts"
          :key="item.tab"
          :to="`/app/deals?tab=${item.tab}`"
          class="me-orders__item"
        >
          <AppIcon :name="item.icon" size="md" class="me-orders__icon" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </div>
    </section>

    <RouterLink v-if="platform.featureWalletEnabled" to="/app/wallet" class="me-wallet glass-card">
      <div class="me-wallet__main">
        <span class="me-wallet__label">账户余额</span>
        <span class="me-wallet__amount">{{ balanceText }}</span>
      </div>
      <span class="me-wallet__link">充值 / 账单 →</span>
    </RouterLink>

    <section v-if="auth.isSeller" class="me-seller glass-card">
      <div class="me-seller__head">
        <h2>卖家中心</h2>
        <RouterLink to="/app/seller">进入 →</RouterLink>
      </div>
      <p class="me-seller__sub">已认证店家「{{ auth.user?.shop_name || '我的 AI 店' }}」</p>
    </section>

    <section v-else class="me-seller glass-card me-seller--apply">
      <div class="me-seller__head">
        <h2>我要开店</h2>
      </div>
      <p class="me-seller__sub">像淘宝一样提交入驻申请，审核通过后可上架 AI 技能商品</p>
      <RouterLink
        v-if="auth.shopStatus === 'pending'"
        to="/app/shop/apply"
        class="btn btn-secondary btn-sm me-seller__btn"
      >
        查看审核进度
      </RouterLink>
      <RouterLink v-else to="/app/shop/apply" class="btn btn-commerce btn-sm me-seller__btn">
        申请入驻
      </RouterLink>
    </section>

    <button type="button" class="btn btn-secondary btn-sm me-logout" @click="logout">退出登录</button>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { getWallet } from '@/api/wallets'
import AppIcon from '@/components/AppIcon.vue'
import type { IconName } from '@/components/icons'
import { useAuthStore } from '@/stores/auth'
import { usePlatformStore } from '@/stores/platform'
import { formatCents } from '@/utils'

const auth = useAuthStore()
const platform = usePlatformStore()
const router = useRouter()
const balanceCents = ref<number | null>(null)

const orderShortcuts: { tab: string; label: string; icon: IconName }[] = [
  { tab: 'pending', label: '待付款', icon: 'wallet' },
  { tab: 'active', label: '待发货', icon: 'package' },
  { tab: 'delivered', label: '待收货', icon: 'clipboard' },
  { tab: 'done', label: '已完成', icon: 'shield' },
]

const avatarLetter = computed(() => {
  const name = auth.user?.display_name?.trim()
  return name ? name.slice(0, 1).toUpperCase() : '我'
})

const balanceText = computed(() => {
  if (balanceCents.value === null) return '加载中…'
  return formatCents(balanceCents.value)
})

function logout() {
  auth.logout()
  router.push('/')
}

onMounted(async () => {
  if (!auth.user) {
    try {
      await auth.fetchProfile()
    } catch {
      return
    }
  }
  if (!platform.featureWalletEnabled) return
  try {
    const wallet = await getWallet()
    balanceCents.value = wallet.balance_available
  } catch {
    balanceCents.value = 0
  }
})
</script>

<style scoped>
.me-head {
  padding: 16px !important;
  margin-bottom: 12px;
}

.me-head__user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.me-head__avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--gradient-commerce);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
  flex-shrink: 0;
}

.me-head h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}

.me-head p {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--color-label-tertiary);
}

.me-orders {
  padding: 14px 16px !important;
  margin-bottom: 12px;
}

.me-orders__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.me-orders__head h2 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
}

.me-orders__head a {
  font-size: 12px;
  color: var(--color-label-tertiary);
  text-decoration: none;
}

.me-orders__grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.me-orders__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 8px 4px;
  border-radius: 8px;
  text-decoration: none;
  color: var(--color-label);
  font-size: 12px;
}

.me-orders__item:hover {
  background: var(--color-fill);
}

.me-orders__icon {
  color: var(--color-commerce);
}

.me-wallet {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px !important;
  margin-bottom: 12px;
  text-decoration: none;
  color: inherit;
}

.me-wallet:hover {
  border-color: rgba(238, 10, 36, 0.2);
}

.me-wallet__label {
  display: block;
  font-size: 12px;
  color: var(--color-label-tertiary);
  margin-bottom: 4px;
}

.me-wallet__amount {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-commerce);
}

.me-wallet__link {
  font-size: 13px;
  color: var(--color-label-secondary);
}

.me-seller {
  padding: 14px 16px !important;
}

.me-seller__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.me-seller__head h2 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
}

.me-seller__head a {
  font-size: 12px;
  color: var(--color-label-tertiary);
  text-decoration: none;
}

.me-seller__sub {
  margin: 0 0 12px;
  font-size: 12px;
  color: var(--color-label-tertiary);
}

.me-seller__btn {
  display: inline-flex;
}

.me-seller--apply {
  border-style: dashed;
}

.me-logout {
  display: block;
  margin: 16px auto 0;
}
</style>
