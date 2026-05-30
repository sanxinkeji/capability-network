<template>
  <div class="admin-layout admin-shell">
    <aside class="admin-sidenav">
      <RouterLink to="/admin" class="admin-sidenav__brand">
        <AppIcon name="logo" size="md" filled class="admin-sidenav__brand-icon" />
        <span>{{ platform.siteName }} 运营</span>
      </RouterLink>

      <nav class="admin-sidenav__nav">
        <div v-for="section in navSections" :key="section.title" class="admin-sidenav__section">
          <div class="admin-sidenav__section-title">{{ section.title }}</div>
          <RouterLink
            v-for="item in section.items"
            :key="item.to"
            :to="item.to"
            class="admin-sidenav__link"
          >
            <AppIcon :name="item.icon" size="md" class="admin-sidenav__icon" />
            <span>{{ item.label }}</span>
            <span v-if="item.badge" class="admin-nav-badge">{{ item.badge }}</span>
          </RouterLink>
        </div>
      </nav>

      <div class="admin-sidenav__footer">
        <div v-if="auth.user" class="admin-sidenav__user">{{ auth.user.display_name }}</div>
        <RouterLink to="/app" class="admin-topbar__link" style="display: block; text-align: center">
          返回用户端
        </RouterLink>
      </div>
    </aside>

    <div class="admin-shell__main">
      <header class="admin-topbar">
        <div class="admin-topbar__breadcrumb">
          运营后台 / <strong>{{ pageTitle }}</strong>
        </div>
        <div class="admin-topbar__actions">
          <RouterLink to="/app" class="admin-topbar__link">用户端</RouterLink>
          <button type="button" class="admin-topbar__logout" @click="handleLogout">退出</button>
        </div>
      </header>

      <main class="admin-content admin-main">
        <div class="admin-page">
          <RouterView />
        </div>
      </main>
    </div>

    <nav class="admin-mobile-tabbar" aria-label="运营导航">
      <RouterLink v-for="item in mobileNav" :key="item.to" :to="item.to">
        <AppIcon :name="item.icon" size="md" />
        <span>{{ item.tabLabel }}</span>
      </RouterLink>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { getAdminStats } from '@/api/admin'
import { useAuthStore } from '@/stores/auth'
import { usePlatformStore } from '@/stores/platform'
import AppIcon from '@/components/AppIcon.vue'
import type { IconName } from '@/components/icons'

const auth = useAuthStore()
const platform = usePlatformStore()
const router = useRouter()
const route = useRoute()
const pendingWithdrawals = ref(0)
const pendingKyc = ref(0)
const pendingShopApplications = ref(0)
const disputedDeals = ref(0)

type NavItem = { to: string; label: string; icon: IconName; title: string; badge?: number }

const navSections = computed(() => {
  const sections: { title: string; items: NavItem[] }[] = [
    {
      title: '运营',
      items: [
        { to: '/admin', label: '数据概览', icon: 'chart', title: '数据概览' },
        { to: '/admin/ops', label: '运维监控', icon: 'shield', title: '运维监控' },
        { to: '/admin/usage', label: '使用记录', icon: 'clipboard', title: '使用记录' },
        { to: '/admin/users', label: '用户管理', icon: 'users', title: '用户管理' },
        {
          to: '/admin/kyc',
          label: '实名审核',
          icon: 'lock',
          title: '实名审核',
          badge: pendingKyc.value || undefined,
        },
        {
          to: '/admin/shop-applications',
          label: '入驻审核',
          icon: 'package',
          title: '入驻审核',
          badge: pendingShopApplications.value || undefined,
        },
        { to: '/admin/agent-keys', label: 'Agent 接入管理', icon: 'agent', title: 'Agent 接入管理' },
      ],
    },
    {
      title: '交易',
      items: [
        { to: '/admin/offers', label: '供给管理', icon: 'package', title: '供给管理' },
        { to: '/admin/intents', label: '需求管理', icon: 'target', title: '需求管理' },
        {
          to: '/admin/deals',
          label: '订单管理',
          icon: 'clipboard',
          title: '订单管理',
          badge: disputedDeals.value || undefined,
        },
        {
          to: '/admin/withdrawals',
          label: '提现审核',
          icon: 'wallet',
          title: '提现审核',
          badge: pendingWithdrawals.value || undefined,
        },
      ],
    },
    {
      title: '订单与支付',
      items: [
        { to: '/admin/payments', label: '支付概览', icon: 'chart', title: '支付概览' },
        { to: '/admin/payment-orders', label: '订单记录', icon: 'clipboard', title: '订单记录' },
        { to: '/admin/finance', label: '充值记录', icon: 'wallet', title: '充值记录' },
      ],
    },
    {
      title: '系统',
      items: [
        { to: '/admin/announcements', label: '公告管理', icon: 'inbox', title: '公告管理' },
        { to: '/admin/codes', label: '邀请码 / 充值卡', icon: 'inbox', title: '邀请码 / 充值卡' },
        { to: '/admin/settings', label: '平台设置', icon: 'agent', title: '平台设置' },
      ],
    },
  ]
  return sections
})

const flatNav = computed(() => navSections.value.flatMap((s) => s.items))

const mobileNav = [
  { to: '/admin', tabLabel: '概览', icon: 'chart' as IconName },
  { to: '/admin/deals', tabLabel: '订单', icon: 'clipboard' as IconName },
  { to: '/admin/withdrawals', tabLabel: '提现', icon: 'wallet' as IconName },
  { to: '/admin/settings', tabLabel: '设置', icon: 'agent' as IconName },
]

const pageTitle = computed(() => {
  const metaTitle = route.meta.title as string | undefined
  if (metaTitle) return metaTitle
  const match = flatNav.value.find((item) => item.to === route.path || route.path.startsWith(`${item.to}/`))
  return match?.title ?? '运营后台'
})

async function loadBadges() {
  try {
    const stats = await getAdminStats()
    pendingWithdrawals.value = stats.withdrawals_pending ?? 0
    pendingKyc.value = stats.kyc_pending ?? 0
    pendingShopApplications.value = stats.shop_applications_pending ?? 0
    disputedDeals.value = stats.deals_disputed ?? 0
  } catch {
    /* ignore */
  }
}

onMounted(() => {
  auth.fetchProfile().catch(() => {})
  loadBadges()
})

function handleLogout() {
  auth.logout()
  router.push('/')
}
</script>
