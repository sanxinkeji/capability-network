<template>
  <div class="status-stepper" role="list" aria-label="订单进度">
    <div
      v-for="(step, index) in steps"
      :key="step.key"
      class="step"
      :class="stepClass(index)"
      role="listitem"
    >
      <div class="step-indicator">
        <span class="step-dot">{{ stepIcon(index) }}</span>
        <span v-if="index < steps.length - 1" class="step-line" />
      </div>
      <span class="step-label">{{ step.label }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
}>()

const steps = [
  { key: 'pending', label: '待支付' },
  { key: 'in_progress', label: '进行中' },
  { key: 'delivered', label: '已交付' },
  { key: 'completed', label: '已完成' },
]

const activeIndex = computed(() => {
  const map: Record<string, number> = {
    pending: 0,
    in_progress: 1,
    delivered: 2,
    completed: 3,
    paid: 1,
  }
  return map[props.status] ?? 0
})

function stepClass(index: number) {
  if (index < activeIndex.value) return 'step--done'
  if (index === activeIndex.value) return 'step--active'
  return 'step--pending'
}

function stepIcon(index: number) {
  if (index < activeIndex.value) return '✓'
  if (index === activeIndex.value) return '●'
  return '○'
}
</script>
