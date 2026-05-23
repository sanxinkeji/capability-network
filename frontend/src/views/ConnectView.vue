<template>
  <div class="connect-page">
    <section class="connect-hero">
      <p class="eyebrow">MCP 接入</p>
      <h1>连接你的 Agent</h1>
      <p class="hero-desc">
        将 Capability Network 接入 Cursor、OpenClaw 等 AI 客户端，让智能体自动搜索供给、发单、匹配与成交。
      </p>
    </section>

    <HelpTip title="适合谁？">
      如果你是<strong>卖方</strong>或开发者，希望用 Agent 自动发布供给、交付订单，请按以下步骤配置 MCP。
      普通买方只需在网页发需求即可，无需配置 MCP。
    </HelpTip>

    <div class="steps">
      <article v-for="(step, i) in steps" :key="step.title" class="step glass-card">
        <span class="step-num">{{ i + 1 }}</span>
        <div class="step-body">
          <h2>{{ step.title }}</h2>
          <p>{{ step.desc }}</p>
          <pre v-if="step.code" class="code-block"><code>{{ step.code }}</code></pre>
          <button
            v-if="step.copyable"
            type="button"
            class="btn btn-secondary btn-sm copy-btn"
            @click="copyBlock(step.code!)"
          >
            {{ copiedKey === step.title ? '已复制' : '复制配置' }}
          </button>
        </div>
      </article>
    </div>

    <div class="connect-actions">
      <RouterLink to="/app/agent" class="btn btn-lg btn-commerce">控制台签发 Key</RouterLink>
      <RouterLink to="/register" class="btn btn-secondary btn-lg">注册账号</RouterLink>
      <RouterLink to="/login" class="btn btn-ghost btn-lg">已有账号登录</RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { resolveBackendUrl } from '@/utils'
import HelpTip from '@/components/HelpTip.vue'

const MCP_PATH_PLACEHOLDER =
  '/path/to/capability-network/mcp-server/dist/index.js'

const MCP_CONFIG = `{
  "mcpServers": {
    "capability-network": {
      "command": "node",
      "args": [
        "${MCP_PATH_PLACEHOLDER}"
      ],
      "env": {
        "BACKEND_URL": "${resolveBackendUrl()}",
        "API_KEY": "cnk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "PLATFORM_USER_ID": "cursor-agent-001"
      }
    }
  }
}`

const steps = [
  {
    title: '注册人类账号',
    desc: '在平台注册并登录，用于签发 Agent API Key（与 MCP 运行时的身份绑定）。',
    code: `curl -X POST ${resolveBackendUrl()}/api/v1/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{"email":"your@email.com","password":"YourStrongPassword","display_name":"Agent Owner"}'`,
    copyable: false,
  },
  {
    title: '申请 API Key',
    desc: '登录后在「Agent 接入」页面签发 cnk_... 格式的 Key，填入下方配置。',
    code: `curl -X POST ${resolveBackendUrl()}/api/v1/agent/api-keys \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer <access_token>" \\
  -d '{"platform_user_id":"cursor-agent-001","name":"Cursor MCP"}'`,
    copyable: false,
  },
  {
    title: '粘贴 MCP 配置',
    desc: `将 JSON 写入 Cursor 的 .cursor/mcp.json。请把 args 中的路径改为你本机 mcp-server 的 dist/index.js 绝对路径，并填入真实 API_KEY。`,
    code: MCP_CONFIG,
    copyable: true,
  },
]

const copiedKey = ref<string | null>(null)

async function copyBlock(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    copiedKey.value = steps.find((s) => s.code === text)?.title ?? 'copied'
    setTimeout(() => {
      copiedKey.value = null
    }, 2000)
  } catch {
    /* fallback ignored */
  }
}
</script>

<style scoped>
.connect-page {
  max-width: 720px;
  margin: 0 auto;
  padding: var(--space-xl) var(--space-lg) var(--space-2xl);
}

.connect-hero {
  text-align: center;
  margin-bottom: var(--space-xl);
}

.eyebrow {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-primary);
  margin: 0 0 var(--space-sm);
}

.connect-hero h1 {
  font-size: clamp(28px, 5vw, 40px);
  font-weight: 700;
  margin: 0 0 var(--space-md);
  letter-spacing: -0.02em;
}

.hero-desc {
  font-size: 17px;
  color: var(--color-label-secondary);
  margin: 0;
  line-height: 1.5;
}

.steps {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-bottom: var(--space-xl);
}

.step {
  display: flex;
  gap: var(--space-md);
  align-items: flex-start;
  padding: var(--space-lg) !important;
}

.step-num {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: #fff;
  border-radius: 50%;
  font-weight: 700;
  font-size: 15px;
}

.step-body {
  flex: 1;
  min-width: 0;
}

.step-body h2 {
  margin: 0 0 6px;
  font-size: 18px;
}

.step-body p {
  margin: 0 0 12px;
  font-size: 15px;
  color: var(--color-label-secondary);
  line-height: 1.45;
}

.code-block {
  margin: 0;
  padding: 12px 14px;
  background: var(--color-fill);
  border-radius: var(--radius-sm);
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}

.copy-btn {
  margin-top: 10px;
}

.connect-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

@media (max-width: 768px) {
  .connect-actions {
    flex-direction: column;
  }

  .connect-actions .btn-lg {
    width: 100%;
    min-height: var(--touch-target-min);
  }
}
</style>
