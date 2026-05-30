import { createRouter, createWebHistory } from 'vue-router'
import { TOKEN_KEY } from '@/utils'
import { useAuthStore } from '@/stores/auth'
import { usePlatformStore } from '@/stores/platform'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior() {
    return { top: 0, left: 0 }
  },
  routes: [
    {
      path: '/',
      component: () => import('@/layouts/MarketingLayout.vue'),
      children: [
        {
          path: '',
          name: 'home',
          component: () => import('@/views/HomeView.vue'),
        },
        {
          path: 'about',
          name: 'about',
          component: () => import('@/views/AboutView.vue'),
        },
        {
          path: 'pricing',
          name: 'pricing',
          component: () => import('@/views/PricingView.vue'),
        },
        {
          path: 'docs',
          name: 'docs',
          component: () => import('@/views/DocsView.vue'),
        },
        {
          path: 'connect',
          name: 'connect',
          component: () => import('@/views/ConnectView.vue'),
        },
        {
          path: 'terms',
          name: 'terms',
          component: () => import('@/views/LegalDocumentView.vue'),
          props: { docKey: 'terms' },
          meta: { title: '用户服务协议' },
        },
        {
          path: 'privacy',
          name: 'privacy',
          component: () => import('@/views/LegalDocumentView.vue'),
          props: { docKey: 'privacy' },
          meta: { title: '隐私政策' },
        },
      ],
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guest: true, authLayout: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guest: true, authLayout: true },
    },
    {
      path: '/forbidden',
      name: 'forbidden',
      component: () => import('@/views/ForbiddenView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/app',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/app/market' },
        {
          path: 'market',
          name: 'market',
          component: () => import('@/views/MarketView.vue'),
          meta: { title: '首页' },
        },
        {
          path: 'market/:offerId',
          name: 'offer-detail',
          component: () => import('@/views/OfferDetailView.vue'),
          meta: { title: '商品详情' },
        },
        {
          path: 'offers',
          name: 'offers',
          component: () => import('@/views/OffersView.vue'),
          meta: { title: '商品管理', requiresSeller: true },
        },
        {
          path: 'offers/new',
          name: 'offer-create',
          component: () => import('@/views/OfferCreateView.vue'),
          meta: { title: '发布商品', requiresSeller: true },
        },
        {
          path: 'deals',
          name: 'deals',
          component: () => import('@/views/DealsView.vue'),
          meta: { title: '我的订单' },
        },
        {
          path: 'deals/:dealId',
          name: 'deal-detail',
          component: () => import('@/views/DealDetailView.vue'),
          meta: { title: '订单详情' },
        },
        {
          path: 'deals/:dealId/chat',
          name: 'deal-chat',
          component: () => import('@/views/DealChatView.vue'),
          meta: { title: '订单沟通' },
        },
        {
          path: 'wallet',
          name: 'wallet',
          component: () => import('@/views/WalletView.vue'),
          meta: { title: '我的钱包' },
        },
        {
          path: 'me',
          name: 'me',
          component: () => import('@/views/MeView.vue'),
          meta: { title: '我的' },
        },
        {
          path: 'shop/apply',
          name: 'shop-apply',
          component: () => import('@/views/ShopApplyView.vue'),
          meta: { title: '我要开店' },
        },
        {
          path: 'seller',
          name: 'seller-hub',
          component: () => import('@/views/SellerHubView.vue'),
          meta: { title: '卖家中心', requiresSeller: true },
        },
        {
          path: 'agent',
          name: 'agent-settings',
          component: () => import('@/views/AgentSettingsView.vue'),
          meta: { title: '开店助手', requiresSeller: true },
        },
      ],
    },
    {
      path: '/admin',
      component: () => import('@/layouts/AdminLayout.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
      children: [
        {
          path: '',
          name: 'admin-dashboard',
          component: () => import('@/views/admin/AdminDashboardView.vue'),
          meta: { title: '数据概览' },
        },
        {
          path: 'ops',
          name: 'admin-ops',
          component: () => import('@/views/admin/AdminOpsView.vue'),
          meta: { title: '运维监控' },
        },
        {
          path: 'usage',
          name: 'admin-usage',
          component: () => import('@/views/admin/AdminUsageView.vue'),
          meta: { title: '使用记录' },
        },
        {
          path: 'users',
          name: 'admin-users',
          component: () => import('@/views/admin/AdminUsersView.vue'),
          meta: { title: '用户管理' },
        },
        {
          path: 'deals',
          name: 'admin-deals',
          component: () => import('@/views/admin/AdminDealsView.vue'),
          meta: { title: '订单管理' },
        },
        {
          path: 'deals/:dealId',
          name: 'admin-deal-detail',
          component: () => import('@/views/admin/AdminDealDetailView.vue'),
          meta: { title: '订单详情' },
        },
        {
          path: 'offers',
          name: 'admin-offers',
          component: () => import('@/views/admin/AdminOffersView.vue'),
          meta: { title: '供给管理' },
        },
        {
          path: 'intents',
          name: 'admin-intents',
          component: () => import('@/views/admin/AdminIntentsView.vue'),
          meta: { title: '需求管理' },
        },
        {
          path: 'withdrawals',
          name: 'admin-withdrawals',
          component: () => import('@/views/admin/AdminWithdrawalsView.vue'),
          meta: { title: '提现审核' },
        },
        {
          path: 'kyc',
          name: 'admin-kyc',
          component: () => import('@/views/admin/AdminKycView.vue'),
          meta: { title: '实名审核' },
        },
        {
          path: 'shop-applications',
          name: 'admin-shop-applications',
          component: () => import('@/views/admin/AdminShopApplicationsView.vue'),
          meta: { title: '入驻审核' },
        },
        {
          path: 'finance',
          name: 'admin-finance',
          component: () => import('@/views/admin/AdminFinanceView.vue'),
          meta: { title: '充值记录' },
        },
        {
          path: 'payments',
          name: 'admin-payments',
          component: () => import('@/views/admin/AdminPaymentOverviewView.vue'),
          meta: { title: '支付概览' },
        },
        {
          path: 'payment-orders',
          name: 'admin-payment-orders',
          component: () => import('@/views/admin/AdminPaymentOrdersView.vue'),
          meta: { title: '订单记录' },
        },
        {
          path: 'announcements',
          name: 'admin-announcements',
          component: () => import('@/views/admin/AdminAnnouncementsView.vue'),
          meta: { title: '公告管理' },
        },
        {
          path: 'agent-keys',
          name: 'admin-agent-keys',
          component: () => import('@/views/admin/AdminAgentKeysView.vue'),
          meta: { title: 'Agent 接入管理' },
        },
        {
          path: 'settings',
          name: 'admin-settings',
          component: () => import('@/views/admin/AdminSettingsView.vue'),
          meta: { title: '平台设置' },
        },
        {
          path: 'codes',
          name: 'admin-codes',
          component: () => import('@/views/admin/AdminCodesView.vue'),
          meta: { title: '邀请码 / 充值卡' },
        },
      ],
    },
    // 旧路径兼容
    { path: '/offers', redirect: '/app/shop/apply' },
    { path: '/offers/new', redirect: '/app/shop/apply' },
    { path: '/intents', redirect: '/app/market' },
    { path: '/intents/new', redirect: '/app/market' },
    { path: '/app/intents', redirect: '/app/market' },
    { path: '/app/intents/new', redirect: '/app/market' },
    { path: '/app/matching/:intentId', redirect: '/app/market' },
    { path: '/app/auctions/:intentId', redirect: '/app/market' },
    { path: '/deals', redirect: '/app/deals' },
    { path: '/wallet', redirect: '/app/wallet' },
    { path: '/matching/:intentId', redirect: '/app/market' },
    { path: '/deals/:dealId', redirect: (to) => `/app/deals/${to.params.dealId}` },
  ],
})

router.beforeEach(async (to) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (to.meta.requiresAuth && !token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guest && token) {
    const auth = useAuthStore()
    if (!auth.user) {
      try {
        await auth.fetchProfile()
      } catch {
        return true
      }
    }
    if (auth.isAdmin && !to.query.redirect) {
      return { path: '/admin' }
    }
    return { path: '/app/market' }
  }
  if (to.meta.requiresAdmin) {
    const auth = useAuthStore()
    if (!auth.user) {
      try {
        await auth.fetchProfile()
      } catch {
        return { name: 'login', query: { redirect: to.fullPath } }
      }
    }
    if (!auth.isAdmin) {
      return { name: 'forbidden' }
    }
  }

  const platform = usePlatformStore()
  if (!platform.loaded) {
    await platform.fetchSettings()
  }
  if (to.name === 'wallet' && !platform.featureWalletEnabled) {
    return { path: '/app/me' }
  }
  if (to.name === 'market' && !platform.featureMarketplaceEnabled) {
    return { path: '/app/deals' }
  }
  if (to.name === 'agent-settings' && !platform.featureAgentEnabled) {
    return { path: '/app/me' }
  }
  if (to.meta.requiresSeller) {
    const auth = useAuthStore()
    if (!auth.user) {
      try {
        await auth.fetchProfile()
      } catch {
        return { name: 'login', query: { redirect: to.fullPath } }
      }
    }
    if (!auth.isSeller) {
      return { name: 'shop-apply', query: { redirect: to.fullPath } }
    }
  }
})

router.afterEach((to) => {
  const platform = usePlatformStore()
  const siteName = platform.siteName
  const pageTitle = to.meta.title as string | undefined
  document.title = pageTitle ? `${pageTitle} · ${siteName}` : siteName
})

export default router
