<template>
  <div class="app-page">
    <div class="commerce-page-head">
      <div>
        <h1>我的需求</h1>
        <p class="commerce-page-head__sub">描述你要什么，系统帮你匹配合适供给</p>
      </div>
      <div class="header-actions">
        <RouterLink to="/app/intents/new" class="btn btn-secondary btn-sm">表单发需求</RouterLink>
        <RouterLink to="/app/intents/new?mode=ai" class="btn btn-commerce btn-sm">AI 发需求</RouterLink>
      </div>
    </div>

    <HelpTip>{{ BUYER_FLOW_HINT }}</HelpTip>

    <CommerceTabs v-model="activeTab" :tabs="tabs" />

    <div v-if="error" class="error-msg">{{ error }}</div>
    <LoadingSkeleton v-if="loading" />

    <EmptyState v-else-if="displayIntents.length === 0" icon="target">
      <template v-if="activeTab === 'open'">
        暂无进行中的需求，
        <RouterLink to="/app/intents/new?mode=ai">AI 发第一个需求</RouterLink>
        或从
        <RouterLink to="/app/market">能力市场</RouterLink>
        选用能力。
      </template>
      <template v-else>暂无历史需求</template>
    </EmptyState>

    <div v-else class="order-list">
      <IntentManageCard
        v-for="intent in displayIntents"
        :key="intent.id"
        :intent="intent"
        :muted="activeTab === 'history'"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { listIntents } from '@/api'
import type { Intent } from '@/types'
import { BUYER_FLOW_HINT } from '@/utils/platformGuide'
import CommerceTabs from '@/components/CommerceTabs.vue'
import HelpTip from '@/components/HelpTip.vue'
import IntentManageCard from '@/components/IntentManageCard.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'
import EmptyState from '@/components/EmptyState.vue'

const intents = ref<Intent[]>([])
const loading = ref(true)
const error = ref('')
const activeTab = ref('open')

const openIntents = computed(() => intents.value.filter((i) => i.status === 'open'))
const historyIntents = computed(() =>
  intents.value.filter((i) => i.status === 'matched' || i.status === 'closed'),
)

const tabs = computed(() => [
  { key: 'open', label: '进行中', count: openIntents.value.length },
  { key: 'history', label: '历史', count: historyIntents.value.length },
])

const displayIntents = computed(() =>
  activeTab.value === 'open' ? openIntents.value : historyIntents.value,
)

async function loadIntents() {
  loading.value = true
  error.value = ''
  try {
    intents.value = await listIntents()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadIntents)
</script>
