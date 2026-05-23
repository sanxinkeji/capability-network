<template>
  <Teleport to="body">
    <Transition name="sheet-fade">
      <div v-if="open" class="more-root" @click.self="emit('close')">
        <div class="more-panel glass-card">
          <header class="more-panel__head">
            <h2>更多功能</h2>
            <button type="button" class="more-panel__close" @click="emit('close')">×</button>
          </header>
          <nav class="more-panel__grid">
            <RouterLink to="/app/offers" class="more-item" @click="emit('close')">
              <span class="more-item__icon more-item__icon--sell">卖</span>
              <span>我的供给</span>
            </RouterLink>
            <RouterLink v-if="platform.featureAgentEnabled" to="/app/agent" class="more-item" @click="emit('close')">
              <span class="more-item__icon more-item__icon--agent">A</span>
              <span>Agent 接入</span>
            </RouterLink>
            <RouterLink to="/connect" class="more-item" @click="emit('close')">
              <span class="more-item__icon more-item__icon--connect">连</span>
              <span>MCP 文档</span>
            </RouterLink>
            <RouterLink to="/about" class="more-item" @click="emit('close')">
              <span class="more-item__icon more-item__icon--about">?</span>
              <span>平台介绍</span>
            </RouterLink>
            <RouterLink to="/pricing" class="more-item" @click="emit('close')">
              <span class="more-item__icon more-item__icon--price">¥</span>
              <span>费用说明</span>
            </RouterLink>
            <RouterLink to="/" class="more-item" @click="emit('close')">
              <span class="more-item__icon more-item__icon--home">官</span>
              <span>返回官网</span>
            </RouterLink>
          </nav>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { usePlatformStore } from '@/stores/platform'

defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: [] }>()
const platform = usePlatformStore()
</script>

<style scoped>
.more-root {
  position: fixed;
  inset: 0;
  z-index: 150;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.more-panel {
  width: 100%;
  max-width: 480px;
  border-radius: 16px 16px 0 0;
  padding: 0 !important;
  margin-bottom: calc(var(--tab-bar-height) + env(safe-area-inset-bottom, 0px));
}

.more-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-separator);
}

.more-panel__head h2 {
  margin: 0;
  font-size: 16px;
}

.more-panel__close {
  border: none;
  background: var(--color-fill);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
}

.more-panel__grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding: 12px 12px 16px;
}

.more-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  border-radius: 10px;
  text-decoration: none;
  color: var(--color-label);
  font-size: 12px;
  font-weight: 500;
}

.more-item:hover {
  background: var(--color-fill);
  text-decoration: none;
}

.more-item__icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: #fff;
}

.more-item__icon--sell {
  background: linear-gradient(135deg, #ff7a45, #ff4d4f);
}
.more-item__icon--agent {
  background: linear-gradient(135deg, #722ed1, #531dab);
}
.more-item__icon--connect {
  background: linear-gradient(135deg, #13c2c2, #08979c);
}
.more-item__icon--about {
  background: linear-gradient(135deg, #1677ff, #0958d9);
}
.more-item__icon--price {
  background: linear-gradient(135deg, #faad14, #d48806);
}
.more-item__icon--home {
  background: linear-gradient(135deg, #52c41a, #389e0d);
}

.sheet-fade-enter-active,
.sheet-fade-leave-active {
  transition: opacity 0.2s ease;
}
.sheet-fade-enter-from,
.sheet-fade-leave-to {
  opacity: 0;
}
</style>
