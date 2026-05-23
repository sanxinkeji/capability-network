<template>
  <article class="admin-stat-card" :class="{ 'admin-stat-card--warn': warn }">
    <div class="admin-stat-card__icon" :class="`admin-stat-card__icon--${tone}`">
      <AppIcon :name="icon" size="md" />
    </div>
    <div class="admin-stat-card__body">
      <span class="admin-stat-card__label">{{ label }}</span>
      <span class="admin-stat-card__value" :class="{ 'admin-stat-card__value--sm': smallValue }">{{ value }}</span>
      <span v-if="sub" class="admin-stat-card__sub">{{ sub }}</span>
      <RouterLink v-if="linkTo" :to="linkTo" class="admin-stat-card__link">{{ linkLabel || '查看详情' }}</RouterLink>
    </div>
  </article>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'
import type { IconName } from '@/components/icons'

withDefaults(
  defineProps<{
    icon: IconName
    label: string
    value: string | number
    sub?: string
    tone?: 'primary' | 'success' | 'warning' | 'danger'
    warn?: boolean
    smallValue?: boolean
    linkTo?: string
    linkLabel?: string
  }>(),
  { tone: 'primary' },
)
</script>
