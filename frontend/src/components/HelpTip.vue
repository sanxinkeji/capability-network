<template>
  <div class="help-tip" :class="`help-tip--${variant}`">
    <span class="help-tip__icon" aria-hidden="true">i</span>
    <div class="help-tip__body">
      <p v-if="title" class="help-tip__title">{{ title }}</p>
      <p class="help-tip__text"><slot /></p>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    title?: string
    variant?: 'info' | 'warn' | 'success'
  }>(),
  { variant: 'info' },
)
</script>

<style scoped>
.help-tip {
  display: flex;
  gap: 10px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  margin-bottom: 12px;
  font-size: 13px;
  line-height: 1.45;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.help-tip--info {
  background: rgba(0, 122, 255, 0.1);
  border: 1px solid rgba(0, 122, 255, 0.18);
  box-shadow: var(--shadow-inner);
}

.help-tip--warn {
  background: rgba(255, 149, 0, 0.1);
  border: 1px solid rgba(255, 149, 0, 0.2);
}

.help-tip--success {
  background: rgba(82, 196, 26, 0.1);
  border: 1px solid rgba(82, 196, 26, 0.2);
}

.help-tip__icon {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 1px;
}

.help-tip--warn .help-tip__icon {
  background: #fa8c16;
}

.help-tip--success .help-tip__icon {
  background: #52c41a;
}

.help-tip__title {
  margin: 0 0 2px;
  font-weight: 600;
  color: var(--color-label);
}

.help-tip__text {
  margin: 0;
  color: var(--color-label-secondary);
}

.help-tip__text :deep(a) {
  font-weight: 600;
}
</style>
