<template>
  <div class="admin-section-tabs">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      type="button"
      class="admin-section-tabs__btn"
      :class="{ 'admin-section-tabs__btn--active': modelValue === tab.id }"
      @click="$emit('update:modelValue', tab.id)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  tabs: { id: string; label: string }[]
  modelValue: string
}>()

defineEmits<{
  'update:modelValue': [id: string]
}>()
</script>
