<template>
  <div class="skeleton-wrap" :aria-label="label" role="status">
    <div v-for="i in rows" :key="i" class="skeleton-row">
      <div class="skeleton-block skeleton-title" />
      <div class="skeleton-block skeleton-sub" />
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    rows?: number
    label?: string
  }>(),
  { rows: 4, label: '加载中' },
)
</script>
