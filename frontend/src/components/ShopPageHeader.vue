<template>
  <header class="shop-page-head">
    <div class="shop-page-head__main">
      <p v-if="eyebrow" class="shop-page-head__eyebrow">{{ eyebrow }}</p>
      <h1>{{ title }}</h1>
      <p v-if="subtitle" class="shop-page-head__sub">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.actions" class="shop-page-head__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
  eyebrow?: string
}>()
</script>
