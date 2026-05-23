<template>
  <div class="admin-settings-tabs">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      type="button"
      class="admin-settings-tabs__btn"
      :class="{ 'admin-settings-tabs__btn--active': modelValue === tab.id, 'admin-settings-tabs__btn--disabled': tab.disabled }"
      :disabled="tab.disabled"
      @click="!tab.disabled && $emit('update:modelValue', tab.id)"
    >
      {{ tab.label }}
      <span v-if="tab.badge" class="admin-settings-tabs__badge">{{ tab.badge }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  tabs: { id: string; label: string; disabled?: boolean; badge?: string }[]
  modelValue: string
}>()

defineEmits<{ 'update:modelValue': [id: string] }>()
</script>
