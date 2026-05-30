<template>
  <header class="shop-app-header">
    <div class="shop-app-header__inner">
      <RouterLink to="/app/market" class="shop-app-header__brand">
        <AppIcon name="logo" size="md" filled class="brand-icon" />
        <span>{{ platform.siteName }}</span>
      </RouterLink>

      <RouterLink to="/app/market" class="shop-app-header__search">
        <AppIcon name="search" size="sm" />
        <span>搜 AI 技能、论文、Logo、摘要…</span>
      </RouterLink>

      <nav class="shop-app-header__nav" aria-label="顶部导航">
        <RouterLink to="/app/market">首页</RouterLink>
        <RouterLink to="/app/deals">我的订单</RouterLink>
        <RouterLink to="/app/me">我的</RouterLink>
        <RouterLink v-if="auth.isSeller" to="/app/seller" class="shop-app-header__seller">
          卖家中心
        </RouterLink>
        <RouterLink v-else to="/app/shop/apply" class="shop-app-header__apply">
          我要开店
        </RouterLink>
      </nav>
    </div>
  </header>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'
import { useAuthStore } from '@/stores/auth'
import { usePlatformStore } from '@/stores/platform'

const auth = useAuthStore()
const platform = usePlatformStore()
</script>

<style scoped>
.shop-app-header {
  display: none;
  width: 100%;
  background: #fff;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  position: sticky;
  top: 0;
  z-index: 40;
}

.shop-app-header__inner {
  max-width: var(--shop-content-max, 1190px);
  margin: 0 auto;
  padding: 12px 24px;
  display: grid;
  grid-template-columns: auto minmax(200px, 1fr) auto;
  align-items: center;
  gap: 24px;
}

.shop-app-header__brand {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: var(--color-label);
  font-weight: 700;
  font-size: 20px;
  letter-spacing: -0.02em;
  flex-shrink: 0;
}

.shop-app-header__brand .brand-icon {
  color: var(--color-primary);
}

.shop-app-header__search {
  justify-self: stretch;
  max-width: none;
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 40px;
  padding: 0 16px;
  background: #fff;
  border: 2px solid var(--color-commerce);
  border-radius: 999px;
  color: var(--color-label-tertiary);
  font-size: 14px;
  text-decoration: none;
  min-width: 0;
}

.shop-app-header__search span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.shop-app-header__nav {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-shrink: 0;
  justify-self: end;
}

.shop-app-header__nav a {
  text-decoration: none;
  color: var(--color-label-secondary);
  font-size: 14px;
  font-weight: 500;
}

.shop-app-header__nav a.router-link-active,
.shop-app-header__nav a:hover {
  color: var(--color-primary);
}

.shop-app-header__apply {
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid rgba(238, 10, 36, 0.35);
  color: var(--color-commerce) !important;
}

.shop-app-header__seller {
  padding: 6px 14px;
  border-radius: 999px;
  background: var(--color-commerce-muted);
  color: var(--color-commerce) !important;
}

@media (min-width: 769px) {
  .shop-app-header {
    display: block;
  }
}
</style>
