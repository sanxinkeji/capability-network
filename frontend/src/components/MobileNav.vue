<template>
  <Teleport to="body">
    <Transition name="mobile-nav">
      <div v-if="open" class="mobile-nav-root" @click.self="close">
        <div
          class="mobile-nav-panel"
          role="dialog"
          aria-modal="true"
          aria-label="站点导航"
        >
          <div class="mobile-nav-header">
            <RouterLink to="/" class="mobile-nav-brand" @click="close">
              <AppIcon name="logo" size="md" filled class="brand-icon" />
              Capability Network
            </RouterLink>
            <button
              type="button"
              class="mobile-nav-close"
              aria-label="关闭菜单"
              @click="close"
            >
              <AppIcon name="close" size="md" />
            </button>
          </div>

          <nav class="mobile-nav-links">
            <RouterLink to="/#features" @click="close">产品</RouterLink>
            <RouterLink to="/login?redirect=/app/market" @click="close">逛市场</RouterLink>
            <RouterLink to="/#how" @click="close">如何工作</RouterLink>
            <RouterLink to="/#scenarios" @click="close">场景</RouterLink>
            <RouterLink to="/pricing" @click="close">定价</RouterLink>
          <RouterLink to="/about" @click="close">关于</RouterLink>
          <RouterLink to="/connect" @click="close">连接 Agent</RouterLink>
          <RouterLink to="/docs" @click="close">API 文档</RouterLink>
          </nav>

          <div class="mobile-nav-actions">
            <template v-if="isLoggedIn">
              <RouterLink to="/app" class="btn" @click="close">进入控制台</RouterLink>
            </template>
            <template v-else>
              <RouterLink to="/login" class="btn btn-secondary" @click="close">登录</RouterLink>
              <RouterLink to="/register" class="btn" @click="close">免费注册</RouterLink>
            </template>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'

defineProps<{
  open: boolean
  isLoggedIn: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

function close() {
  emit('close')
}
</script>

<style scoped>
.mobile-nav-root {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.mobile-nav-panel {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: min(320px, 100vw);
  display: flex;
  flex-direction: column;
  background: var(--color-bg-elevated);
  backdrop-filter: blur(var(--glass-blur-heavy));
  -webkit-backdrop-filter: blur(var(--glass-blur-heavy));
  border-left: 1px solid var(--color-separator);
  padding: max(12px, env(safe-area-inset-top)) max(16px, env(safe-area-inset-right))
    max(16px, env(safe-area-inset-bottom)) max(16px, env(safe-area-inset-left));
  box-shadow: var(--shadow-glass-lg);
}

.mobile-nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: var(--space-md);
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--color-separator);
}

.mobile-nav-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 16px;
  color: var(--color-label);
  text-decoration: none;
  min-height: var(--touch-target-min);
}

.brand-icon {
  color: var(--color-primary);
}

.mobile-nav-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--touch-target-min);
  height: var(--touch-target-min);
  border: none;
  border-radius: 50%;
  background: var(--color-fill);
  color: var(--color-label-secondary);
  font-size: 18px;
  cursor: pointer;
  flex-shrink: 0;
}

.mobile-nav-links {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow-y: auto;
}

.mobile-nav-links a {
  display: flex;
  align-items: center;
  min-height: var(--touch-target-min);
  padding: 0 4px;
  font-size: 17px;
  font-weight: 500;
  color: var(--color-label);
  text-decoration: none;
  border-bottom: 1px solid var(--color-separator);
}

.mobile-nav-links a.router-link-active {
  color: var(--color-primary);
}

.mobile-nav-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-separator);
}

.mobile-nav-actions .btn {
  width: 100%;
  min-height: var(--touch-target-min);
  text-decoration: none;
}

.mobile-nav-enter-active,
.mobile-nav-leave-active {
  transition: opacity 0.2s ease;
}

.mobile-nav-enter-active .mobile-nav-panel,
.mobile-nav-leave-active .mobile-nav-panel {
  transition: transform 0.25s ease;
}

.mobile-nav-enter-from,
.mobile-nav-leave-to {
  opacity: 0;
}

.mobile-nav-enter-from .mobile-nav-panel,
.mobile-nav-leave-to .mobile-nav-panel {
  transform: translateX(100%);
}
</style>
