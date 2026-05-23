<template>
  <div class="admin-page-header">
    <div class="admin-page-header__main">
      <h1 class="admin-page-header__title">{{ title }}</h1>
      <p v-if="subtitle" class="admin-page-header__subtitle">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.actions" class="admin-page-header__actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
}>()
</script>
