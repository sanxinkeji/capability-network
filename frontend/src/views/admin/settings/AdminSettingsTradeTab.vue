<template>
  <div class="admin-form-card">
    <div class="admin-form-section-title">交易参数</div>
    <div class="admin-form-grid">
      <div class="admin-form-field">
        <label>平台佣金（%）</label>
        <input v-model.number="form.commission_rate_percent" type="number" min="0" max="50" />
      </div>
      <div class="admin-form-field">
        <label>最低充值（分）</label>
        <input v-model.number="form.min_deposit_cents" type="number" min="1" />
        <p class="admin-form-hint">= {{ formatCents(form.min_deposit_cents) }}</p>
      </div>
      <div class="admin-form-field">
        <label>最高充值（分）</label>
        <input v-model.number="form.max_deposit_cents" type="number" min="1" placeholder="留空不限" />
        <p class="admin-form-hint">{{ form.max_deposit_cents ? `= ${formatCents(form.max_deposit_cents)}` : '不限制单笔充值上限' }}</p>
      </div>
      <div class="admin-form-field">
        <label>最低提现（分）</label>
        <input v-model.number="form.min_withdraw_cents" type="number" min="1" />
        <p class="admin-form-hint">= {{ formatCents(form.min_withdraw_cents) }}</p>
      </div>
      <div class="admin-form-field">
        <label>最高提现（分）</label>
        <input v-model.number="form.max_withdraw_cents" type="number" min="1" />
        <p class="admin-form-hint">= {{ formatCents(form.max_withdraw_cents) }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PlatformSettings } from '@/types'
import { formatCents } from '@/utils'

const form = defineModel<PlatformSettings>({ required: true })
</script>
