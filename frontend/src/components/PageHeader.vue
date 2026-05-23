<template>
  <div class="page-header">
    <div>
      <h1>{{ title }}</h1>
      <p v-if="subtitle" class="page-header__subtitle">{{ subtitle }}</p>
    </div>
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
}>()
</script>

<style scoped>
.page-header__subtitle {
  margin: 4px 0 0;
  font-size: 15px;
  font-weight: 400;
  color: var(--color-label-tertiary);
}
</style>
