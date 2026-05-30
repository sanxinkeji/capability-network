<template>
  <div class="marketing">
    <div class="mesh-bg" aria-hidden="true" />
    <header class="site-nav glass-card">
      <RouterLink to="/" class="brand">
        <AppIcon name="logo" size="md" filled class="brand-icon" />
        <span class="brand-text">{{ platform.siteName }}</span>
      </RouterLink>
      <nav class="nav-links">
        <RouterLink to="/#features">亮点</RouterLink>
        <RouterLink to="/login?redirect=/app/market">首页</RouterLink>
        <RouterLink to="/#how">怎么买</RouterLink>
        <RouterLink to="/#scenarios">AI 店家</RouterLink>
        <RouterLink to="/pricing">费用</RouterLink>
        <RouterLink to="/about">关于</RouterLink>
        <RouterLink to="/connect">卖家入驻</RouterLink>
      </nav>
      <div class="nav-actions">
        <template v-if="isLoggedIn">
          <RouterLink to="/app/market" class="btn btn-sm btn-commerce">进入集市</RouterLink>
        </template>
        <template v-else>
          <RouterLink to="/login" class="btn btn-ghost btn-sm nav-login">登录</RouterLink>
          <RouterLink to="/register" class="btn btn-sm btn-commerce">免费注册</RouterLink>
        </template>
      </div>
      <button
        type="button"
        class="nav-toggle"
        :aria-expanded="menuOpen"
        aria-label="打开菜单"
        @click="menuOpen = true"
      >
        <span class="nav-toggle-bar" />
        <span class="nav-toggle-bar" />
        <span class="nav-toggle-bar" />
      </button>
    </header>

    <MobileNav
      :open="menuOpen"
      :is-logged-in="isLoggedIn"
      @close="menuOpen = false"
    />

    <main>
      <RouterView />
    </main>
    <footer class="site-footer">
      <div class="footer-inner">
        <div class="footer-brand">
          <strong>{{ platform.siteName }}</strong>
          <p>{{ platform.footerText || defaultFooter }}</p>
        </div>
        <div class="footer-links">
          <RouterLink to="/">首页</RouterLink>
          <RouterLink to="/login?redirect=/app/market">逛集市</RouterLink>
          <RouterLink to="/#features">亮点</RouterLink>
          <RouterLink to="/pricing">定价</RouterLink>
          <RouterLink to="/about">关于我们</RouterLink>
          <RouterLink :to="platform.docsUrl">API 文档</RouterLink>
          <template v-for="link in platform.customLinks" :key="link.url + link.label">
            <a v-if="link.url.startsWith('http')" :href="link.url" target="_blank" rel="noopener">{{ link.label }}</a>
            <RouterLink v-else :to="link.url">{{ link.label }}</RouterLink>
          </template>
          <RouterLink to="/login">登录</RouterLink>
          <RouterLink to="/register">注册</RouterLink>
        </div>
      </div>
      <p class="copyright">© {{ year }} {{ platform.siteName }}. All rights reserved.</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onUnmounted } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { TOKEN_KEY } from '@/utils'
import { usePlatformStore } from '@/stores/platform'
import MobileNav from '@/components/MobileNav.vue'
import AppIcon from '@/components/AppIcon.vue'

import { BRAND_FOOTER } from '@/utils/brand'

const year = new Date().getFullYear()
const platform = usePlatformStore()
const defaultFooter = BRAND_FOOTER
const isLoggedIn = computed(() => !!localStorage.getItem(TOKEN_KEY))
const menuOpen = ref(false)
const route = useRoute()

watch(
  () => route.fullPath,
  () => {
    menuOpen.value = false
  },
)

watch(menuOpen, (open) => {
  document.body.style.overflow = open ? 'hidden' : ''
})

onUnmounted(() => {
  document.body.style.overflow = ''
})
</script>

<style scoped>
.marketing {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
}

.site-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  margin: 0;
  width: 100%;
  max-width: none;
  padding: 0 !important;
  display: flex;
  align-items: center;
  gap: var(--space-md);
  border-radius: 0 !important;
  border: none;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

@media (min-width: 769px) {
  .site-nav {
    padding: 0 max(24px, calc((100% - var(--shop-content-max)) / 2)) !important;
    min-height: 56px;
  }
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 800;
  font-size: 20px;
  color: var(--color-commerce);
  text-decoration: none;
  flex-shrink: 0;
}

.brand-icon {
  color: var(--color-commerce);
  font-size: 14px;
}

.nav-links {
  display: flex;
  gap: var(--space-lg);
  flex: 1;
  justify-content: center;
}

.nav-links a {
  color: var(--color-label-secondary);
  font-size: 15px;
  font-weight: 500;
  text-decoration: none;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  color: var(--color-commerce);
}

.nav-login {
  color: var(--color-label-secondary) !important;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.nav-toggle {
  display: none;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 5px;
  width: var(--touch-target-min);
  height: var(--touch-target-min);
  padding: 0;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  cursor: pointer;
  flex-shrink: 0;
  margin-left: auto;
}

.nav-toggle-bar {
  display: block;
  width: 22px;
  height: 2px;
  background: var(--color-label);
  border-radius: 1px;
}

main {
  flex: 1;
  min-width: 0;
}

.site-footer {
  margin-top: var(--space-2xl);
  padding: var(--space-xl) var(--space-lg) max(var(--space-lg), env(safe-area-inset-bottom));
  border-top: 1px solid var(--color-separator);
}

.footer-inner {
  max-width: var(--shop-content-max);
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  gap: var(--space-lg);
  flex-wrap: wrap;
}

.footer-brand p {
  margin: 8px 0 0;
  color: var(--color-label-tertiary);
  font-size: 15px;
  max-width: 320px;
}

.footer-links {
  display: flex;
  gap: var(--space-md) var(--space-lg);
  flex-wrap: wrap;
  align-items: flex-start;
}

.footer-links a {
  color: var(--color-label-secondary);
  font-size: 15px;
  min-height: var(--touch-target-min);
  display: inline-flex;
  align-items: center;
}

.copyright {
  text-align: center;
  margin: var(--space-lg) 0 0;
  font-size: 13px;
  color: var(--color-label-tertiary);
}

@media (max-width: 768px) {
  .site-nav {
    top: max(8px, env(safe-area-inset-top));
    margin: 12px auto 0;
    width: calc(100% - 24px);
    max-width: var(--content-max);
    padding: 8px 12px !important;
    border-radius: var(--radius-card) !important;
    border: 1px solid rgba(0, 0, 0, 0.06);
  }

  .brand-text {
    font-size: 15px;
  }

  .nav-links,
  .nav-actions {
    display: none;
  }

  .nav-toggle {
    display: flex;
  }

  .footer-inner {
    flex-direction: column;
  }

  .footer-links {
    gap: var(--space-sm) var(--space-md);
  }
}
</style>
