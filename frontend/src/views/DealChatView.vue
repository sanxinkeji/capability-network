<template>
  <div class="deal-chat-page">
    <header class="chat-header glass-card">
      <RouterLink :to="`/app/deals/${dealId}`" class="chat-header__back" aria-label="返回订单">
        ←
      </RouterLink>
      <div class="chat-header__main">
        <h1>{{ headerTitle }}</h1>
        <p v-if="deal" class="chat-header__meta">
          <span :class="['chat-status', `chat-status--${deal.status}`]">{{ statusLabel(deal.status) }}</span>
          <span v-if="isAgentDeal" class="chat-agent-badge">🦞 智能体</span>
          · 资金托管中
        </p>
      </div>
      <RouterLink :to="`/app/deals/${dealId}`" class="chat-header__detail">订单</RouterLink>
    </header>

    <div v-if="error" class="error-msg chat-error">{{ error }}</div>
    <LoadingSkeleton v-if="loading" :rows="6" />

    <template v-else>
      <div ref="messageListEl" class="chat-messages">
        <p v-if="messages.length === 0" class="chat-empty">暂无消息，发送第一条开始沟通</p>
        <article
          v-for="msg in messages"
          :key="msg.id"
          :class="['chat-bubble-wrap', bubbleAlign(msg.sender_role)]"
        >
          <div v-if="msg.sender_role === 'system'" class="chat-bubble chat-bubble--system">
            {{ msg.body }}
          </div>
          <div
            v-else
            :class="['chat-bubble', bubbleClass(msg)]"
          >
            <p v-if="msg.kind === 'delivery'" class="chat-bubble__tag">📦 交付物</p>
            <p class="chat-bubble__body">{{ messageText(msg.body) }}</p>
            <a
              v-for="(link, idx) in messageLinks(msg.body)"
              :key="idx"
              :href="link"
              class="chat-bubble__link"
              target="_blank"
              rel="noopener"
            >
              打开链接 →
            </a>
            <button
              v-if="msg.kind === 'delivery' && canConfirm"
              type="button"
              class="btn btn-sm btn-commerce chat-bubble__confirm"
              :disabled="confirming"
              @click="handleConfirm"
            >
              {{ confirming ? '确认中…' : '确认收货' }}
            </button>
            <time class="chat-bubble__time">{{ formatTime(msg.created_at) }}</time>
          </div>
        </article>
      </div>

      <footer v-if="canWrite" class="chat-composer glass-card">
        <textarea
          v-model="draft"
          rows="2"
          placeholder="补充需求细节，智能体会主动跟进…"
          @keydown.enter.exact.prevent="handleSend"
        />
        <button type="button" class="btn btn-commerce" :disabled="sending || !draft.trim()" @click="handleSend">
          {{ sending ? '发送中…' : '发送' }}
        </button>
      </footer>

      <CommerceStickyBar v-else-if="canConfirm">
        <template #info>智能体已交付，请验收</template>
        <template #actions>
          <button type="button" class="btn btn-commerce" :disabled="confirming" @click="handleConfirm">
            {{ confirming ? '确认中…' : '确认验收' }}
          </button>
        </template>
      </CommerceStickyBar>

      <footer v-else class="chat-composer chat-composer--readonly glass-card">
        <p class="chat-closed-hint">订单已结束，无法继续发送消息</p>
      </footer>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { listDealMessages, postDealMessage } from '@/api/dealMessages'
import { confirmDeal, getDeal } from '@/api/deals'
import CommerceStickyBar from '@/components/CommerceStickyBar.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'
import { useAuthStore } from '@/stores/auth'
import type { Deal, DealMessage, DealMessageSenderRole } from '@/types'
import { dealOrderTitle, statusLabel } from '@/utils'

const route = useRoute()
const auth = useAuthStore()

const dealId = route.params.dealId as string
const deal = ref<Deal | null>(null)
const messages = ref<DealMessage[]>([])
const loading = ref(true)
const error = ref('')
const draft = ref('')
const sending = ref(false)
const confirming = ref(false)
const messageListEl = ref<HTMLElement | null>(null)

let pollTimer: ReturnType<typeof setInterval> | null = null

const isBuyer = computed(() => deal.value && auth.user && deal.value.buyer_id === auth.user.id)
const isSeller = computed(() => deal.value && auth.user && deal.value.seller_id === auth.user.id)

const isAgentDeal = computed(() =>
  messages.value.some((m) => m.sender_role === 'agent') || deal.value?.agent_auto_delivered,
)

const headerTitle = computed(() => (deal.value ? dealOrderTitle(deal.value) : '订单沟通'))

const canWrite = computed(() => {
  if (!deal.value) return false
  if (!['in_progress', 'delivered', 'disputed'].includes(deal.value.status)) return false
  if (deal.value.status === 'delivered' && isBuyer.value) return false
  return isBuyer.value || isSeller.value
})

const canConfirm = computed(() => deal.value?.status === 'delivered' && isBuyer.value)

function bubbleAlign(role: DealMessageSenderRole) {
  if (role === 'system') return 'chat-bubble-wrap--center'
  if (role === 'buyer') return 'chat-bubble-wrap--right'
  return 'chat-bubble-wrap--left'
}

function bubbleClass(msg: DealMessage) {
  if (msg.kind === 'delivery') return 'chat-bubble--delivery'
  if (msg.sender_role === 'agent') return 'chat-bubble--agent'
  if (msg.sender_role === 'seller') return 'chat-bubble--seller'
  return 'chat-bubble--buyer'
}

function formatTime(iso: string) {
  const d = new Date(iso)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const URL_RE = /https?:\/\/[^\s]+/g

function messageLinks(body: string): string[] {
  return body.match(URL_RE) ?? []
}

function messageText(body: string): string {
  return body.replace(URL_RE, '').replace(/📎 交付物：\s*/g, '').trim()
}

async function scrollToBottom() {
  await nextTick()
  const el = messageListEl.value
  if (el) el.scrollTop = el.scrollHeight
}

async function loadMessages(silent = false) {
  if (!silent) error.value = ''
  try {
    const data = await listDealMessages(dealId)
    const prevCount = messages.value.length
    messages.value = data.items
    if (data.items.length !== prevCount) await scrollToBottom()
  } catch (e) {
    if (!silent) error.value = e instanceof Error ? e.message : '加载消息失败'
  }
}

async function loadAll(silent = false) {
  if (!silent) {
    loading.value = true
    error.value = ''
  }
  try {
    if (!auth.user) await auth.fetchProfile()
    deal.value = await getDeal(dealId)
    await loadMessages(true)
  } catch (e) {
    if (!silent) error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    if (!silent) loading.value = false
    await scrollToBottom()
  }
}

async function handleSend() {
  const text = draft.value.trim()
  if (!text || sending.value) return
  sending.value = true
  error.value = ''
  try {
    await postDealMessage(dealId, text)
    draft.value = ''
    await loadAll(true)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '发送失败'
  } finally {
    sending.value = false
  }
}

async function handleConfirm() {
  confirming.value = true
  error.value = ''
  try {
    deal.value = await confirmDeal(dealId)
    await loadAll(true)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '确认失败'
  } finally {
    confirming.value = false
  }
}

watch(
  () => deal.value?.status,
  () => {
    if (pollTimer) clearInterval(pollTimer)
    if (deal.value && ['in_progress', 'delivered'].includes(deal.value.status)) {
      pollTimer = setInterval(() => loadAll(true), 3000)
    }
  },
)

onMounted(async () => {
  await loadAll()
  pollTimer = setInterval(() => loadAll(true), 3000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.deal-chat-page {
  display: flex;
  flex-direction: column;
  min-height: calc(100dvh - 120px);
  max-width: 720px;
  margin: 0 auto;
  gap: 12px;
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
}

.chat-header__back,
.chat-header__detail {
  flex-shrink: 0;
  font-size: 14px;
  color: var(--color-accent);
  text-decoration: none;
}

.chat-header__main {
  flex: 1;
  min-width: 0;
}

.chat-header h1 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-header__meta {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--color-label-secondary);
}

.chat-agent-badge {
  color: #e8590c;
  font-weight: 500;
}

.chat-status--in_progress {
  color: #1677ff;
}

.chat-status--delivered {
  color: #52c41a;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 8px 4px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 320px;
  max-height: calc(100dvh - 280px);
}

.chat-empty {
  text-align: center;
  color: var(--color-label-secondary);
  font-size: 14px;
  margin: auto;
}

.chat-bubble-wrap {
  display: flex;
  width: 100%;
}

.chat-bubble-wrap--center {
  justify-content: center;
}

.chat-bubble-wrap--left {
  justify-content: flex-start;
}

.chat-bubble-wrap--right {
  justify-content: flex-end;
}

.chat-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-bubble--system {
  background: rgba(0, 0, 0, 0.04);
  color: var(--color-label-secondary);
  font-size: 12px;
  border-radius: 999px;
  padding: 6px 12px;
}

.chat-bubble--agent {
  background: linear-gradient(145deg, #fff4e6, #ffe8cc);
  border: 1px solid rgba(232, 89, 12, 0.15);
  border-bottom-left-radius: 4px;
}

.chat-bubble--seller {
  background: #f0f5ff;
  border-bottom-left-radius: 4px;
}

.chat-bubble--buyer {
  background: #1677ff;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.chat-bubble--delivery {
  background: linear-gradient(145deg, #f6ffed, #d9f7be);
  border: 1px solid rgba(82, 196, 26, 0.25);
  border-bottom-left-radius: 4px;
}

.chat-bubble__tag {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 600;
  color: #389e0d;
}

.chat-bubble__body {
  margin: 0;
}

.chat-bubble__time {
  display: block;
  margin-top: 6px;
  font-size: 11px;
  opacity: 0.65;
}

.chat-bubble__link {
  display: inline-block;
  margin-top: 8px;
  font-size: 13px;
  color: var(--color-primary);
}

.chat-bubble__confirm {
  display: block;
  margin-top: 10px;
  width: 100%;
}

.chat-composer {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  padding: 12px;
  position: sticky;
  bottom: 0;
}

.chat-composer textarea {
  flex: 1;
  resize: none;
  border: 1px solid var(--color-separator);
  border-radius: 12px;
  padding: 10px 12px;
  font: inherit;
  background: var(--color-bg-elevated, #fff);
}

.chat-composer--readonly {
  justify-content: center;
}

.chat-closed-hint {
  margin: 0;
  font-size: 13px;
  color: var(--color-label-secondary);
}

.chat-error {
  margin: 0;
}

@media (max-width: 480px) {
  .chat-messages {
    max-height: calc(100dvh - 240px);
  }

  .chat-composer .btn {
    padding-inline: 14px;
  }
}
</style>
