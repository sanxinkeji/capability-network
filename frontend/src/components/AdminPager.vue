<template>
  <div v-if="total > pageSize" class="admin-pager">
    <button class="btn btn-secondary btn-sm" :disabled="page <= 1" @click="$emit('update:page', page - 1)">
      上一页
    </button>
    <span class="admin-pager__info">第 {{ page }} / {{ totalPages }} 页 · 共 {{ total }} 条</span>
    <button
      class="btn btn-secondary btn-sm"
      :disabled="page >= totalPages"
      @click="$emit('update:page', page + 1)"
    >
      下一页
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  page: number
  pageSize: number
  total: number
}>()

defineEmits<{ 'update:page': [page: number] }>()

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
</script>

<style scoped>
.admin-pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.admin-pager__info {
  font-size: 13px;
  color: var(--color-label-secondary);
}
</style>
