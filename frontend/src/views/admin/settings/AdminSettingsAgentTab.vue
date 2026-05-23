<template>
  <div class="admin-form-card">
    <div class="admin-form-section-title">Agent / OpenClaw（龙虾）接入</div>
    <p class="admin-form-hint" style="margin-bottom: 16px">
      控制用户端 Agent Key 签发与 MCP 接入说明。用户可在「Agent 接入」页签发 Key，并粘贴到 OpenClaw、Cursor 或 Hermes。
    </p>

    <AdminToggleRow
      v-model="form.feature_agent_enabled"
      label="开放 Agent 接入"
      hint="关闭后用户无法签发新 Key，已有 Key 仍可被管理员撤销"
    />

    <div class="admin-form-field">
      <label>每用户最大活跃 Key 数</label>
      <input v-model.number="form.agent_max_keys_per_user" type="number" min="1" max="100" />
      <p class="admin-form-hint">超出上限时需先撤销或轮换旧 Key</p>
    </div>

    <div class="admin-form-field">
      <label>Agent 身份 ID 前缀（可选）</label>
      <input v-model="form.agent_platform_user_id_prefix" placeholder="例如 openclaw-" />
      <p class="admin-form-hint">签发时自动加此前缀，便于区分平台节点，如 openclaw-seller-001</p>
    </div>

    <div class="admin-form-field">
      <label>MCP 接入文档链接</label>
      <input v-model="form.agent_mcp_docs_url" placeholder="/connect 或 https://..." />
      <p class="admin-form-hint">留空则使用默认 /connect 页面</p>
    </div>

    <div class="admin-form-field" style="margin-top: 8px">
      <p class="admin-form-hint">
        在侧边栏「Agent 接入管理」可查看全平台 Key 列表、搜索与撤销异常节点。
        <RouterLink to="/admin/agent-keys" class="admin-link-btn">前往 Agent 接入管理 →</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import type { PlatformSettings } from '@/types'
import AdminToggleRow from '@/components/admin/AdminToggleRow.vue'

const form = defineModel<PlatformSettings>({ required: true })
</script>
