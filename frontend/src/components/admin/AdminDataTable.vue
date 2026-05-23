<template>
  <div class="admin-table-card">
    <div v-if="$slots.toolbar" class="admin-table-toolbar">
      <slot name="toolbar" />
    </div>

    <div v-if="loading" class="admin-table-state">
      <LoadingSkeleton :rows="4" />
    </div>
    <div v-else-if="error" class="admin-table-state">
      <AdminAlert :message="error" type="error" />
    </div>
    <div v-else-if="empty" class="admin-table-state">
      <slot name="empty">
        <EmptyState icon="clipboard">暂无数据</EmptyState>
      </slot>
    </div>

    <div v-else class="admin-table-wrap">
      <table class="admin-table">
        <thead>
          <slot name="head" />
        </thead>
        <tbody>
          <slot />
        </tbody>
      </table>
    </div>

    <div v-if="$slots.footer && !loading" class="admin-table-footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
import AdminAlert from '@/components/admin/AdminAlert.vue'
import EmptyState from '@/components/EmptyState.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'

defineProps<{
  loading?: boolean
  error?: string
  empty?: boolean
}>()
</script>
