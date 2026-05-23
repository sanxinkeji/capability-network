<template>
  <RouterView />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { usePlatformStore } from '@/stores/platform'

const platform = usePlatformStore()

onMounted(() => {
  platform.fetchSettings().catch(() => {})
})
</script>
