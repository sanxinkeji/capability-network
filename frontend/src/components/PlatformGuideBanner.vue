<template>
  <section v-if="visible" class="guide-banner glass-card">
    <button type="button" class="guide-banner__close" aria-label="关闭引导" @click="dismiss">
      ×
    </button>
    <p class="guide-banner__title">{{ title }}</p>
    <p class="guide-banner__sub">{{ PLATFORM_TAGLINE }}</p>
    <div class="guide-banner__steps">
      <RouterLink
        v-for="step in PLATFORM_STEPS"
        :key="step.key"
        :to="step.to"
        class="guide-step"
        @click="emit('navigate')"
      >
        <span class="guide-step__label">{{ step.label }}</span>
        <span class="guide-step__desc">{{ step.desc }}</span>
      </RouterLink>
    </div>
    <p class="guide-banner__foot">
      <RouterLink to="/about">了解平台</RouterLink>
      ·
      <RouterLink to="/pricing">费用说明</RouterLink>
      ·
      <RouterLink to="/connect">Agent 接入</RouterLink>
    </p>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { ONBOARDING_STORAGE_KEY, PLATFORM_STEPS, PLATFORM_TAGLINE } from '@/utils/platformGuide'

const props = withDefaults(
  defineProps<{
    title?: string
    storageKey?: string
  }>(),
  {
    title: '新手快速上手',
    storageKey: ONBOARDING_STORAGE_KEY,
  },
)

const emit = defineEmits<{ navigate: [] }>()

const visible = ref(false)

onMounted(() => {
  visible.value = localStorage.getItem(props.storageKey) !== '1'
})

function dismiss() {
  visible.value = false
  localStorage.setItem(props.storageKey, '1')
}
</script>

<style scoped>
.guide-banner {
  position: relative;
  padding: 14px 16px 12px !important;
  margin-bottom: 14px;
  background: linear-gradient(135deg, rgba(255, 96, 52, 0.08), rgba(22, 119, 255, 0.06)) !important;
}

.guide-banner__close {
  position: absolute;
  top: 8px;
  right: 10px;
  border: none;
  background: transparent;
  font-size: 20px;
  line-height: 1;
  color: var(--color-label-tertiary);
  cursor: pointer;
  padding: 4px;
}

.guide-banner__title {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 700;
  color: var(--color-label);
}

.guide-banner__sub {
  margin: 0 0 12px;
  font-size: 12px;
  color: var(--color-label-secondary);
  line-height: 1.45;
}

.guide-banner__steps {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 6px;
  margin-bottom: 10px;
}

.guide-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 8px 4px;
  border-radius: 8px;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-separator);
  text-decoration: none;
  color: inherit;
  transition: border-color 0.15s, transform 0.1s;
}

.guide-step:hover {
  text-decoration: none;
  border-color: rgba(255, 96, 52, 0.35);
  transform: translateY(-1px);
}

.guide-step__label {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-commerce);
}

.guide-step__desc {
  font-size: 10px;
  color: var(--color-label-tertiary);
  margin-top: 2px;
  line-height: 1.3;
}

.guide-banner__foot {
  margin: 0;
  font-size: 12px;
  text-align: center;
  color: var(--color-label-tertiary);
}

@media (max-width: 640px) {
  .guide-banner__steps {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
