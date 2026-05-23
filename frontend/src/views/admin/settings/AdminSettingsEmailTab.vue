<template>
  <div>
    <AdminAlert
      v-if="!payment?.smtp_configured && form.email_verification_required"
      type="info"
      message="邮箱验证已启用但 SMTP 未配置完整，请在下方填写 SMTP 设置。"
    />
    <AdminAlert
      v-else-if="!form.email_verification_required"
      type="info"
      message="邮箱验证未启用。如需启用，请先在「安全与认证」Tab 打开邮箱验证。"
    />

    <div class="admin-form-card">
      <div class="admin-form-section-title">SMTP 配置</div>
      <div class="admin-form-grid">
        <div class="admin-form-field"><label>SMTP 主机</label><input v-model="form.smtp_host" placeholder="smtp.example.com" /></div>
        <div class="admin-form-field"><label>端口</label><input v-model.number="form.smtp_port" type="number" min="1" max="65535" /></div>
        <div class="admin-form-field"><label>用户名</label><input v-model="form.smtp_user" /></div>
        <div class="admin-form-field"><label>密码</label><input v-model="form.smtp_password" type="password" /></div>
        <div class="admin-form-field"><label>发件人地址</label><input v-model="form.smtp_from" placeholder="noreply@example.com" /></div>
      </div>
      <AdminToggleRow v-model="form.smtp_use_tls" label="启用 TLS" />
    </div>

    <div class="admin-form-card">
      <div class="admin-email-template__head">
        <div class="admin-form-section-title" style="margin: 0">邮件模板 · 邮箱验证码</div>
        <div class="admin-email-template__actions">
          <button type="button" class="btn btn-ghost-admin" @click="restoreDefault">恢复默认</button>
        </div>
      </div>
      <div class="admin-form-field">
        <label>邮件主题</label>
        <input v-model="form.email_template_verify_subject" placeholder="{{site_name}} 邮箱验证码" />
      </div>
      <div class="admin-email-split">
        <div class="admin-form-field">
          <label>HTML 模板</label>
          <textarea v-model="form.email_template_verify_html" rows="14" class="admin-code-editor" />
          <p class="admin-form-hint">可用变量：&#123;&#123;name&#125;&#125;、&#123;&#123;code&#125;&#125;、&#123;&#123;site_name&#125;&#125;</p>
        </div>
        <div class="admin-form-field">
          <label>预览</label>
          <div class="admin-email-preview" v-html="previewHtml" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PaymentConfigInfo, PlatformSettings } from '@/types'
import AdminAlert from '@/components/admin/AdminAlert.vue'
import AdminToggleRow from '@/components/admin/AdminToggleRow.vue'
import { DEFAULT_VERIFY_TEMPLATE } from '@/composables/adminSettingsForm'

const form = defineModel<PlatformSettings>({ required: true })
defineProps<{ payment: PaymentConfigInfo | null }>()

const previewHtml = computed(() => {
  const raw = form.value.email_template_verify_html || DEFAULT_VERIFY_TEMPLATE
  return raw
    .replace(/\{\{name\}\}/g, '张三')
    .replace(/\{\{code\}\}/g, '123456')
    .replace(/\{\{site_name\}\}/g, form.value.site_name || 'Capability')
})

function restoreDefault() {
  form.value.email_template_verify_subject = '{{site_name}} 邮箱验证码'
  form.value.email_template_verify_html = DEFAULT_VERIFY_TEMPLATE
}
</script>

<style scoped>
.admin-email-template__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.admin-email-template__actions { display: flex; gap: 8px; }
.admin-email-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.admin-code-editor {
  font-family: ui-monospace, monospace;
  font-size: 12px;
  line-height: 1.5;
}
.admin-email-preview {
  min-height: 280px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #fafafa;
  overflow: auto;
}
@media (max-width: 900px) {
  .admin-email-split { grid-template-columns: 1fr; }
}
</style>
