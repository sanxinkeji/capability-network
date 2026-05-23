<template>
  <div class="admin-form-card">
    <div class="admin-form-section-title">用户默认值</div>
    <div class="admin-form-grid">
      <div class="admin-form-field">
        <label>默认钱包余额（分）</label>
        <input v-model.number="form.default_wallet_balance_cents" type="number" min="0" />
        <p class="admin-form-hint">= {{ formatCents(form.default_wallet_balance_cents) }}，新用户注册后自动获得</p>
      </div>
    </div>
    <AdminAlert
      type="info"
      message="更多默认值（并发限制、订阅套餐等）将在后续版本支持。"
    />
  </div>
</template>

<script setup lang="ts">
import type { PlatformSettings } from '@/types'
import { formatCents } from '@/utils'
import AdminAlert from '@/components/admin/AdminAlert.vue'

const form = defineModel<PlatformSettings>({ required: true })
</script>
