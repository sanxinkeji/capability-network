<template>
  <svg
    class="app-icon"
    :class="[`app-icon--${size}`, { 'app-icon--filled': filled }]"
    :width="dimension"
    :height="dimension"
    viewBox="0 0 24 24"
    :fill="filled ? 'currentColor' : 'none'"
    :stroke="filled ? 'none' : 'currentColor'"
    :stroke-width="filled ? 0 : 1.75"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path v-for="(d, index) in paths" :key="index" :d="d" />
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ICON_PATHS, type IconName } from './icons'

const props = withDefaults(
  defineProps<{
    name: IconName
    size?: 'sm' | 'md' | 'lg' | 'xl'
    filled?: boolean
  }>(),
  {
    size: 'md',
    filled: false,
  },
)

const SIZE_PX = { sm: 16, md: 20, lg: 32, xl: 48 } as const

const dimension = computed(() => SIZE_PX[props.size])
const paths = computed(() => ICON_PATHS[props.name])
</script>

<style scoped>
.app-icon {
  display: block;
  flex-shrink: 0;
}

.app-icon--filled.app-icon--sm {
  filter: drop-shadow(0 1px 2px rgba(0, 122, 255, 0.25));
}
</style>
