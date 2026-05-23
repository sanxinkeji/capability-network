<template>
  <div class="admin-form-card">
    <div class="admin-form-section-title">功能开关</div>
    <AdminToggleRow v-model="form.feature_marketplace_enabled" label="能力市场" hint="关闭后用户无法浏览市场页" />
    <AdminToggleRow v-model="form.feature_matching_enabled" label="智能匹配" hint="关闭后隐藏匹配推荐功能" />
    <AdminToggleRow v-model="form.feature_wallet_enabled" label="钱包充值" hint="关闭后用户无法使用钱包充值" />
    <AdminToggleRow v-model="form.feature_referral_enabled" label="邀请返利" hint="开启后支持邀请码返利（需配置规则）" />
  </div>
</template>

<script setup lang="ts">
import type { PlatformSettings } from '@/types'
import AdminToggleRow from '@/components/admin/AdminToggleRow.vue'

const form = defineModel<PlatformSettings>({ required: true })
</script>
