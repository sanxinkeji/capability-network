<template>
  <Teleport to="body">
    <Transition name="sheet-fade">
      <div v-if="open" class="sheet-root" @click.self="emit('close')">
        <Transition name="sheet-slide">
          <div v-if="open" class="sheet-panel" role="dialog" :aria-label="title">
            <div class="sheet-handle" aria-hidden="true" />
            <header class="sheet-header">
              <h2 class="sheet-title">{{ title }}</h2>
              <button type="button" class="sheet-close" aria-label="关闭" @click="emit('close')">
                <AppIcon name="close" size="sm" />
              </button>
            </header>
            <div class="sheet-body">
              <slot />
            </div>
            <footer v-if="$slots.footer" class="sheet-footer">
              <slot name="footer" />
            </footer>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import AppIcon from '@/components/AppIcon.vue'

defineProps<{ open: boolean; title: string }>()
const emit = defineEmits<{ close: [] }>()
</script>

<style scoped>
.sheet-root {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.sheet-panel {
  width: 100%;
  max-width: 480px;
  max-height: min(88vh, 720px);
  background: var(--color-bg-elevated);
  border-radius: 20px 20px 0 0;
  display: flex;
  flex-direction: column;
  box-shadow: 0 -8px 32px rgba(0, 0, 0, 0.12);
}

.sheet-handle {
  width: 36px;
  height: 4px;
  margin: 10px auto 0;
  border-radius: 2px;
  background: var(--color-separator);
}

.sheet-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px 8px;
}

.sheet-title {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
}

.sheet-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: var(--color-fill);
  cursor: pointer;
  color: var(--color-label-secondary);
}

.sheet-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px 20px 16px;
}

.sheet-footer {
  padding: 12px 20px calc(16px + env(safe-area-inset-bottom, 0px));
  border-top: 1px solid var(--color-separator);
}

.sheet-fade-enter-active,
.sheet-fade-leave-active {
  transition: opacity 0.25s ease;
}
.sheet-fade-enter-from,
.sheet-fade-leave-to {
  opacity: 0;
}

.sheet-slide-enter-active,
.sheet-slide-leave-active {
  transition: transform 0.28s cubic-bezier(0.32, 0.72, 0, 1);
}
.sheet-slide-enter-from,
.sheet-slide-leave-to {
  transform: translateY(100%);
}
</style>
