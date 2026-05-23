<template>
  <div class="commerce-tabs" role="tablist">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      type="button"
      role="tab"
      class="commerce-tabs__item"
      :class="{ 'commerce-tabs__item--active': modelValue === tab.key }"
      :aria-selected="modelValue === tab.key"
      @click="emit('update:modelValue', tab.key)"
    >
      {{ tab.label }}
      <span v-if="tab.count != null && tab.count > 0" class="commerce-tabs__badge">{{ tab.count }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
export interface CommerceTab {
  key: string
  label: string
  count?: number
}

defineProps<{
  tabs: CommerceTab[]
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [key: string]
}>()
</script>
