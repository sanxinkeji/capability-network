<template>

  <div>

    <div class="admin-form-card">

      <div class="admin-form-section-title">注册设置</div>

      <div class="admin-form-field">

        <label>注册状态</label>

        <select v-model="form.registration_mode">

          <option value="open">开放注册（邮箱 + 密码）</option>

          <option value="closed">关闭注册</option>

        </select>

      </div>

      <AdminToggleRow

        v-if="form.registration_mode === 'open'"

        v-model="form.registration_invite_required"

        label="注册需要邀请码"

        hint="开启后用户注册需填写有效邀请码（邮箱 + 密码 + 邀请码）"

      />

      <AdminAlert

        v-if="form.registration_mode === 'open'"

        type="info"

        message="邀请码与充值卡请在「邀请码 / 充值卡」页面批量生成。"

      />

      <AdminToggleRow

        v-model="form.email_verification_required"

        label="邮箱验证"

        hint="注册后必须验证邮箱（需配置 SMTP）"

      />

      <div class="admin-form-field">

        <label>邮箱域名白名单</label>

        <input v-model="form.registration_email_domains" placeholder="@qq.com, @gmail.com" />

        <p class="admin-form-hint">留空表示不限制</p>

      </div>

      <AdminToggleRow v-model="form.two_factor_allowed" label="双因素认证 (2FA)" hint="允许用户使用 TOTP 二次验证" />

    </div>



    <div class="admin-form-card">

      <div class="admin-form-section-title">访问控制</div>

      <AdminToggleRow

        v-model="form.trust_proxy_ip"

        label="信任反向代理 IP"

        hint="使用 Cloudflare/Nginx 时启用"

      />

    </div>

  </div>

</template>



<script setup lang="ts">

import type { PlatformSettings } from '@/types'

import AdminToggleRow from '@/components/admin/AdminToggleRow.vue'

import AdminAlert from '@/components/admin/AdminAlert.vue'



const form = defineModel<PlatformSettings>({ required: true })

</script>

