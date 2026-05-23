<template>
  <div v-if="message" class="admin-alert" :class="`admin-alert--${type}`" role="alert">
    {{ message }}
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    message?: string
    type?: 'error' | 'success' | 'info'
  }>(),
  { type: 'error' },
)
</script>
