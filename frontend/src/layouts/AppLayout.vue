<template>
  <div class="layout">
    <ShopAppHeader />

    <header class="shop-mobile-header">
      <div class="shop-mobile-header__row">
        <RouterLink to="/app/market" class="shop-mobile-header__brand">
          <AppIcon name="logo" size="md" filled class="brand-icon" />
          {{ platform.siteName }}
        </RouterLink>
        <div class="shop-mobile-header__actions">
          <RouterLink
            :to="auth.isSeller ? '/app/seller' : '/app/shop/apply'"
            class="shop-mobile-header__action shop-mobile-header__action--accent"
          >
            {{ auth.isSeller ? '卖家中心' : '我要开店' }}
          </RouterLink>
          <RouterLink to="/app/deals" class="shop-mobile-header__action">订单</RouterLink>
          <RouterLink to="/app/me" class="shop-mobile-header__action">我的</RouterLink>
        </div>
      </div>
      <div class="shop-mobile-header__search-row">
        <RouterLink to="/app/market" class="shop-mobile-header__search">
          <AppIcon name="search" size="sm" />
          搜 AI 技能，论文、Logo、摘要…
        </RouterLink>
        <button type="button" class="shop-mobile-header__search-btn" @click="goMarket">搜索</button>
      </div>
    </header>

    <main class="main">
      <div class="main-inner">
        <div v-if="platform.maintenanceMode" class="platform-banner platform-banner--warn">
          平台维护中，部分功能可能不可用。如有疑问请联系客服。
        </div>
        <div v-else-if="platform.announcement" class="platform-banner">{{ platform.announcement }}</div>
        <PlatformGuideBanner v-if="showGuide" />
        <RouterView />
      </div>
    </main>

    <nav class="tab-bar" aria-label="主导航">
      <RouterLink
        v-for="item in tabNavItems"
        :key="item.to"
        :to="item.to"
        class="tab-item"
      >
        <AppIcon :name="item.icon" size="md" class="tab-icon" />
        <span class="tab-label">{{ item.tabLabel }}</span>
      </RouterLink>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { usePlatformStore } from '@/stores/platform'
import { useAuthStore } from '@/stores/auth'
import AppIcon from '@/components/AppIcon.vue'
import PlatformGuideBanner from '@/components/PlatformGuideBanner.vue'
import ShopAppHeader from '@/components/ShopAppHeader.vue'
import type { IconName } from '@/components/icons'

const platform = usePlatformStore()
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

function goMarket() {
  router.push('/app/market')
}

const showGuide = computed(() => {
  const name = route.name
  return name === 'market' || name === 'deals' || name === 'me'
})

const tabNavItems = computed(() => {
  const items: { to: string; label: string; tabLabel: string; icon: IconName }[] = []
  if (platform.featureMarketplaceEnabled) {
    items.push({ to: '/app/market', label: '首页', tabLabel: '首页', icon: 'globe' })
  }
  items.push({ to: '/app/deals', label: '订单', tabLabel: '订单', icon: 'clipboard' })
  items.push({ to: '/app/me', label: '我的', tabLabel: '我的', icon: 'person' })
  return items
})
</script>
