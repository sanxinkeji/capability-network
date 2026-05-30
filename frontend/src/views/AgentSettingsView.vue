<template>

  <div class="app-page app-page--wide">
    <ShopPageHeader
      title="开店助手"
      subtitle="签发 API Key，连接 OpenClaw 实现 AI 自动接单"
    >
      <template #actions>
        <RouterLink to="/connect" class="btn btn-secondary btn-sm">接入文档</RouterLink>
      </template>
    </ShopPageHeader>



    <div class="notice glass-card">

      <AppIcon name="agent" size="md" />

      <div>

        <strong>供给端龙虾 / OpenClaw 接入步骤</strong>

        <p>1. 下方签发 Key → 2. 复制 MCP 配置 → 3. 粘贴到 OpenClaw、Cursor 或 Hermes → 4. 用工具发布供给、交付订单</p>

      </div>

    </div>



    <div v-if="error" class="error-msg">{{ error }}</div>

    <div v-if="listWarning" class="warning-msg">{{ listWarning }}</div>

    <div v-if="newKey" class="success-msg key-banner">

      <strong>新 Key 仅显示一次，请立即复制：</strong>

      <code>{{ newKey }}</code>

      <button type="button" class="btn btn-sm btn-secondary" @click="copyKey">复制 Key</button>

    </div>



    <p class="grouped-section-label">签发新 Key</p>

    <div class="inset-group glass-card issue-form">

      <div class="inset-row">

        <label>Agent 身份 ID</label>

        <input v-model="form.platform_user_id" placeholder="例如 openclaw-seller-001" />

        <p class="form-hint">用于 MCP 配置中的 PLATFORM_USER_ID，区分不同 Agent 实例</p>

      </div>

      <div class="inset-row">

        <label>备注名称</label>

        <input v-model="form.name" placeholder="例如 龙虾供给节点" />

      </div>

      <button class="btn btn-commerce" :disabled="issuing || !form.platform_user_id.trim()" @click="handleIssue">

        {{ issuing ? '签发中…' : '签发 API Key' }}

      </button>

    </div>



    <p class="grouped-section-label">MCP 配置</p>

    <div class="config-tabs">

      <button

        type="button"

        class="config-tab"

        :class="{ 'config-tab--active': configTab === 'cursor' }"

        @click="configTab = 'cursor'"

      >

        OpenClaw / Cursor

      </button>

      <button

        type="button"

        class="config-tab"

        :class="{ 'config-tab--active': configTab === 'hermes' }"

        @click="configTab = 'hermes'"

      >

        Hermes

      </button>

    </div>

    <div class="glass-card config-block">

      <p class="config-hint">

        请将 <code>args</code> 中的路径替换为本机

        <code>mcp-server/dist/index.js</code> 的绝对路径；MCP 需直连后端

        <code>{{ backendUrl }}</code>。

      </p>

      <pre class="code-block"><code>{{ activeConfig }}</code></pre>

      <button type="button" class="btn btn-secondary btn-sm" @click="copyConfig">复制配置</button>

    </div>



    <p class="grouped-section-label">已签发的 Key</p>

    <LoadingSkeleton v-if="loading" />

    <EmptyState v-else-if="keys.length === 0" icon="agent">暂无 Key，请先签发</EmptyState>

    <GroupedList v-else>

      <div v-for="key in keys" :key="key.id" class="grouped-item grouped-item--static key-row">

        <div class="grouped-item__main">

          <div class="grouped-item__title">{{ key.name || key.platform_user_id }}</div>

          <div class="grouped-item__subtitle">

            {{ key.key_prefix }}… · {{ key.platform_user_id }} · {{ formatDate(key.created_at) }}

          </div>

        </div>

        <div class="grouped-item__meta">

          <span :class="statusBadge(key.status)">{{ formatAgentKeyStatus(key.status) }}</span>

          <button

            v-if="key.status === 'active'"

            class="btn btn-secondary btn-sm"

            :disabled="revokingId === key.id"

            @click="handleRevoke(key.id)"

          >

            撤销

          </button>

        </div>

      </div>

    </GroupedList>

  </div>

</template>



<script setup lang="ts">

import { computed, onMounted, reactive, ref } from 'vue'

import { RouterLink } from 'vue-router'

import { createApiKey, listApiKeys, revokeApiKey, type ApiKeyInfo } from '@/api/agent'

import AppIcon from '@/components/AppIcon.vue'
import ShopPageHeader from '@/components/ShopPageHeader.vue'

import GroupedList from '@/components/GroupedList.vue'

import LoadingSkeleton from '@/components/LoadingSkeleton.vue'

import EmptyState from '@/components/EmptyState.vue'

import { formatDate, resolveBackendUrl } from '@/utils'
import { formatAgentKeyStatus } from '@/utils/platformGuide'



const MCP_SERVER_PATH = '/path/to/capability-network/mcp-server/dist/index.js'



const keys = ref<ApiKeyInfo[]>([])

const loading = ref(true)

const issuing = ref(false)

const revokingId = ref<string | null>(null)

const error = ref('')

const listWarning = ref('')

const newKey = ref('')

const configTab = ref<'cursor' | 'hermes'>('cursor')



const form = reactive({

  platform_user_id: 'openclaw-seller-001',

  name: '龙虾供给节点',

})



const backendUrl = computed(() => resolveBackendUrl())



const mcpEnv = computed(() => ({

  BACKEND_URL: backendUrl.value,

  API_KEY: newKey.value || 'cnk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',

  PLATFORM_USER_ID: form.platform_user_id,

}))



const cursorConfig = computed(() =>

  JSON.stringify(

    {

      mcpServers: {

        'capability-network': {

          command: 'node',

          args: [MCP_SERVER_PATH],

          env: mcpEnv.value,

        },

      },

    },

    null,

    2,

  ),

)



const hermesConfig = computed(() => {

  const lines = [

    '# 写入 ~/.hermes/config.yaml（或 Hermes 指定的配置文件）',

    'agents:',

    '  default:',

    '    mcpServers:',

    '      capability-network:',

    '        command: node',

    '        args:',

    `          - ${MCP_SERVER_PATH}`,

    '        env:',

    `          BACKEND_URL: ${mcpEnv.value.BACKEND_URL}`,

    `          API_KEY: ${mcpEnv.value.API_KEY}`,

    `          PLATFORM_USER_ID: ${mcpEnv.value.PLATFORM_USER_ID}`,

    '# Hermes 调用工具时会加前缀，例如 mcp_capability-network_list_offers',

  ]

  return lines.join('\n')

})



const activeConfig = computed(() => (configTab.value === 'hermes' ? hermesConfig.value : cursorConfig.value))



function statusBadge(status: string) {

  const map: Record<string, string> = {

    active: 'badge badge-published',

    revoked: 'badge badge-default',

    rotated: 'badge badge-default',

  }

  return map[status] ?? 'badge badge-default'

}



function upsertKey(key: ApiKeyInfo) {

  keys.value = [key, ...keys.value.filter((item) => item.id !== key.id)]

}



async function loadKeys(silent = false) {

  if (!silent) loading.value = true

  if (!silent) listWarning.value = ''

  try {

    const data = await listApiKeys()

    keys.value = data.items

  } catch (e) {

    const message = e instanceof Error ? e.message : '加载 Key 列表失败'

    if (keys.value.length === 0) {

      listWarning.value = message

    } else {

      listWarning.value = `${message}（下方为本地缓存，刷新页面后重试）`

    }

  } finally {

    if (!silent) loading.value = false

  }

}



async function handleIssue() {

  issuing.value = true

  error.value = ''

  newKey.value = ''

  try {

    const created = await createApiKey({

      platform_user_id: form.platform_user_id.trim(),

      name: form.name.trim() || undefined,

    })

    newKey.value = created.api_key

    upsertKey({

      id: created.id,

      platform_user_id: created.platform_user_id,

      name: created.name,

      key_prefix: created.key_prefix,

      status: created.status,

      created_at: created.created_at,

    })

    await loadKeys(true)

  } catch (e) {

    error.value = e instanceof Error ? e.message : '签发失败'

  } finally {

    issuing.value = false

  }

}



async function handleRevoke(keyId: string) {

  if (!confirm('确认撤销此 Key？撤销后 MCP 将无法连接。')) return

  revokingId.value = keyId

  error.value = ''

  try {

    await revokeApiKey(keyId)

    await loadKeys(true)

  } catch (e) {

    error.value = e instanceof Error ? e.message : '撤销失败'

  } finally {

    revokingId.value = null

  }

}



async function copyKey() {

  if (newKey.value) await navigator.clipboard.writeText(newKey.value)

}



async function copyConfig() {

  await navigator.clipboard.writeText(activeConfig.value)

}



onMounted(() => loadKeys())

</script>



<style scoped>

.notice {

  display: flex;

  gap: 12px;

  align-items: flex-start;

  padding: 14px 16px !important;

  margin-bottom: var(--space-md);

  color: var(--color-primary);

}



.notice p {

  margin: 4px 0 0;

  font-size: 14px;

  color: var(--color-label-secondary);

}



.warning-msg {

  margin-bottom: var(--space-md);

  padding: 10px 14px;

  border-radius: var(--radius-sm);

  background: #fff8e6;

  color: #8a6d00;

  font-size: 14px;

}



.key-banner code {

  display: block;

  margin: 8px 0;

  word-break: break-all;

  font-size: 12px;

}



.issue-form {

  padding: 16px !important;

  margin-bottom: var(--space-md);

}



.config-tabs {

  display: flex;

  gap: 8px;

  margin-bottom: 8px;

}



.config-tab {

  padding: 6px 12px;

  border: 1px solid var(--color-separator);

  border-radius: var(--radius-sm);

  background: var(--color-fill);

  color: var(--color-label-secondary);

  cursor: pointer;

  font-size: 13px;

}



.config-tab--active {

  border-color: var(--color-primary);

  color: var(--color-primary);

  background: rgba(255, 59, 48, 0.08);

}



.config-block {

  padding: 16px !important;

  margin-bottom: var(--space-lg);

}



.config-hint {

  margin: 0 0 10px;

  font-size: 13px;

  color: var(--color-label-secondary);

  line-height: 1.5;

}



.code-block {

  margin: 0 0 10px;

  padding: 12px;

  background: var(--color-fill);

  border-radius: var(--radius-sm);

  overflow-x: auto;

  font-size: 12px;

  white-space: pre-wrap;

  word-break: break-all;

}



.key-row {

  justify-content: space-between;

  gap: 12px;

}

</style>


