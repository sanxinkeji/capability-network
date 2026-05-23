<template>
  <template v-for="(item, index) in agreements" :key="item.slug">
    <RouterLink :to="legalAgreementPath(item.slug)" target="_blank">{{ item.title }}</RouterLink>
    <span v-if="index < agreements.length - 1">{{ separator }}</span>
  </template>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { usePlatformStore } from '@/stores/platform'
import { legalAgreementPath } from '@/utils/legal'
import type { LegalAgreementItem } from '@/types'

withDefaults(
  defineProps<{
    separator?: string
  }>(),
  {
    separator: '、',
  },
)

const platform = usePlatformStore()

const DEFAULT_LINKS: LegalAgreementItem[] = [
  { title: '用户服务协议', slug: '/terms', content: '' },
  { title: '隐私政策', slug: '/privacy', content: '' },
]

const agreements = computed(() => {
  const items = platform.legalAgreements
  return items.length ? items : DEFAULT_LINKS
})
</script>
