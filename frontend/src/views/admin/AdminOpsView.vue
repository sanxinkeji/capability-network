<template>
  <div>
    <AdminPageHeader title="运维监控" subtitle="平台健康度、SLA 与系统资源状态">
      <template #actions>
        <button class="btn btn-secondary btn-sm" :disabled="loading" @click="loadData">刷新</button>
      </template>
    </AdminPageHeader>

    <AdminAlert v-if="error" :message="error" type="error" />
    <LoadingSkeleton v-if="loading" :rows="2" />

    <template v-else-if="health">
      <div class="admin-ops-top">
        <div class="admin-health-card">
          <div class="admin-health-gauge" :class="`admin-health-gauge--${health.health_label}`">
            <span class="admin-health-gauge__score">{{ health.health_score }}</span>
            <span class="admin-health-gauge__label">{{ healthLabel(health.health_label) }}</span>
          </div>
          <div class="admin-health-meta">
            <div><span>完成率</span><strong>{{ health.completion_rate }}%</strong></div>
            <div><span>争议率</span><strong>{{ health.disputed_rate }}%</strong></div>
            <div><span>SLA</span><strong>{{ health.sla_percent }}%</strong></div>
          </div>
        </div>

        <div class="admin-stat-grid admin-stat-grid--4 admin-stat-grid--compact">
          <div class="admin-metric-card">
            <span class="admin-metric-card__label">进行中订单</span>
            <strong class="admin-metric-card__value">{{ health.deals_in_progress }}</strong>
            <span class="admin-metric-card__sub">paid / in_progress / delivered</span>
          </div>
          <div class="admin-metric-card">
            <span class="admin-metric-card__label">待审提现</span>
            <strong class="admin-metric-card__value">{{ health.pending_withdrawals }}</strong>
            <RouterLink to="/admin/withdrawals" class="admin-link-btn">立即处理</RouterLink>
          </div>
          <div class="admin-metric-card">
            <span class="admin-metric-card__label">SLA 达标</span>
            <strong class="admin-metric-card__value">{{ health.sla_percent }}%</strong>
            <div class="admin-progress"><span :style="{ width: `${health.sla_percent}%` }" /></div>
          </div>
          <div class="admin-metric-card">
            <span class="admin-metric-card__label">争议占比</span>
            <strong class="admin-metric-card__value">{{ health.disputed_rate }}%</strong>
            <div class="admin-progress admin-progress--warn"><span :style="{ width: `${Math.min(health.disputed_rate, 100)}%` }" /></div>
          </div>
          <div class="admin-metric-card">
            <span class="admin-metric-card__label">活跃 Agent Key</span>
            <strong class="admin-metric-card__value">{{ health.agent_keys_active ?? 0 }}</strong>
            <RouterLink to="/admin/agent-keys" class="admin-link-btn">{{ health.agent_users_total ?? 0 }} 用户接入</RouterLink>
          </div>
        </div>
      </div>

      <div class="admin-panel">
        <div class="admin-panel__header"><h3>系统资源</h3></div>
        <div class="admin-resource-grid">
          <div v-for="item in health.resources" :key="item.name" class="admin-resource-card">
            <span class="admin-resource-card__name">{{ item.name }}</span>
            <span class="admin-status-dot admin-status-dot--on">{{ item.value }}</span>
          </div>
        </div>
      </div>

      <div class="admin-panel">
        <div class="admin-panel__header"><h3>运维建议</h3></div>
        <ul class="admin-tips-list">
          <li v-if="health.pending_withdrawals > 0">有 {{ health.pending_withdrawals }} 笔提现待审核，建议优先处理。</li>
          <li v-if="health.disputed_rate > 5">争议订单占比 {{ health.disputed_rate }}%，请关注纠纷处理效率。</li>
          <li v-if="health.deals_in_progress > 10">进行中订单较多（{{ health.deals_in_progress }}），可检查匹配与交付流程。</li>
          <li v-if="health.health_score >= 80 && health.pending_withdrawals === 0 && health.disputed_rate <= 5">系统运行正常，暂无紧急运维事项。</li>
        </ul>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { getAdminOpsHealth } from '@/api/admin'
import type { OpsHealth } from '@/types'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminAlert from '@/components/admin/AdminAlert.vue'
import LoadingSkeleton from '@/components/LoadingSkeleton.vue'

const health = ref<OpsHealth | null>(null)
const loading = ref(true)
const error = ref('')

function healthLabel(label: string) {
  const map: Record<string, string> = { healthy: '健康', risk: '风险', critical: '严重' }
  return map[label] ?? label
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    health.value = await getAdminOpsHealth()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>
