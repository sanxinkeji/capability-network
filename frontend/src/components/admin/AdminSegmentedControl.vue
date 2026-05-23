<template>
  <div class="admin-segmented">
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      class="admin-segmented__btn"
      :class="{ 'admin-segmented__btn--active': modelValue === opt.value }"
      @click="$emit('update:modelValue', opt.value)"
    >
      {{ opt.label }}
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: string
  options: { value: string; label: string }[]
}>()

defineEmits<{ 'update:modelValue': [value: string] }>()
</script>
