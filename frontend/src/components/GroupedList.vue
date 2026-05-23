<template>
  <div class="grouped-list" :class="{ 'grouped-list--flush': flush }">
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  flush?: boolean
}>()
</script>
