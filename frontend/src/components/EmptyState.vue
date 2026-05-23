<template>
  <div class="empty-state-card">
    <AppIcon :name="icon" size="xl" class="empty-icon" />
    <p class="empty-text"><slot /></p>
  </div>
</template>

<script setup lang="ts">
import AppIcon from '@/components/AppIcon.vue'
import type { IconName } from '@/components/icons'

withDefaults(
  defineProps<{
    icon?: IconName
  }>(),
  { icon: 'inbox' },
)
</script>
