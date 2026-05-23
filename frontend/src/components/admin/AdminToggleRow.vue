<template>
  <div class="admin-form-row">
    <div class="admin-form-row__body">
      <div class="admin-form-row__label">{{ label }}</div>
      <p v-if="hint" class="admin-form-hint">{{ hint }}</p>
    </div>
    <AdminToggle :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" />
  </div>
</template>

<script setup lang="ts">
import AdminToggle from '@/components/admin/AdminToggle.vue'

defineProps<{ label: string; hint?: string; modelValue: boolean }>()
defineEmits<{ 'update:modelValue': [value: boolean] }>()
</script>
