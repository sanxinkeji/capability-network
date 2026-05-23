<template>
  <div class="layout">
    <div class="mesh-bg app-mesh" aria-hidden="true" />

    <aside class="sidebar glass-card">
      <RouterLink to="/" class="brand">
        <AppIcon name="logo" size="md" filled class="brand-icon" />
        <span>{{ platform.siteName }}</span>
      </RouterLink>

      <nav class="sidebar-nav">
        <RouterLink v-for="item in tabNavItems" :key="item.to" :to="item.to">
          <AppIcon :name="item.icon" size="md" class="nav-icon" />
          {{ item.label }}
        </RouterLink>
        <RouterLink to="/app/offers" class="sidebar-secondary">
          <AppIcon name="package" size="md" class="nav-icon" />
          我的供给
        </RouterLink>
        <RouterLink v-if="platform.featureAgentEnabled" to="/app/agent" class="sidebar-secondary">
          <AppIcon name="agent" size="md" class="nav-icon" />
          Agent 接入
        </RouterLink>
      </nav>

      <div class="sidebar-footer">
        <span v-if="auth.user" class="user-name">{{ auth.user.display_name }}</span>
        <RouterLink to="/connect" class="connect-link">连接 Agent</RouterLink>
        <RouterLink v-if="auth.isAdmin" to="/admin" class="admin-link">进入运营后台</RouterLink>
        <button class="btn btn-secondary btn-sm" @click="handleLogout">退出</button>
        <RouterLink to="/" class="back-home">返回官网</RouterLink>
      </div>
    </aside>

    <div class="content-column">
      <header class="mobile-header">
        <RouterLink to="/" class="mobile-brand">
          <AppIcon name="logo" size="md" filled class="brand-icon" />
          {{ platform.siteName }}
        </RouterLink>
        <span v-if="auth.user" class="mobile-user">{{ auth.user.display_name }}</span>
      </header>
      <main class="main">
        <div v-if="platform.maintenanceMode" class="platform-banner platform-banner--warn">
          平台维护中，部分功能可能不可用。如有疑问请联系客服。
        </div>
        <div v-else-if="platform.announcement" class="platform-banner">{{ platform.announcement }}</div>
        <PlatformGuideBanner v-if="showGuide" />
        <RouterView />
      </main>
    </div>

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
      <button type="button" class="tab-item tab-item--more" @click="moreOpen = true">
        <AppIcon name="package" size="md" class="tab-icon" />
        <span class="tab-label">更多</span>
      </button>
    </nav>

    <AppMoreSheet :open="moreOpen" @close="moreOpen = false" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePlatformStore } from '@/stores/platform'
import AppIcon from '@/components/AppIcon.vue'
import AppMoreSheet from '@/components/AppMoreSheet.vue'
import PlatformGuideBanner from '@/components/PlatformGuideBanner.vue'
import type { IconName } from '@/components/icons'

const auth = useAuthStore()
const platform = usePlatformStore()
const router = useRouter()
const route = useRoute()
const moreOpen = ref(false)

const showGuide = computed(() => {
  const name = route.name
  return name === 'market' || name === 'intents' || name === 'deals' || name === 'wallet'
})

const tabNavItems = computed(() => {
  const items: { to: string; label: string; tabLabel: string; icon: IconName }[] = []
  if (platform.featureMarketplaceEnabled) {
    items.push({ to: '/app/market', label: '逛市场', tabLabel: '市场', icon: 'globe' })
  }
  items.push({ to: '/app/intents', label: '我的需求', tabLabel: '需求', icon: 'target' })
  items.push({ to: '/app/deals', label: '订单', tabLabel: '订单', icon: 'clipboard' })
  if (platform.featureWalletEnabled) {
    items.push({ to: '/app/wallet', label: '钱包', tabLabel: '钱包', icon: 'wallet' })
  }
  return items
})

function handleLogout() {
  auth.logout()
  router.push('/')
}
</script>
