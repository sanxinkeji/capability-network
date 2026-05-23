<template>
  <div>
    <div class="admin-form-card">
      <div class="admin-form-section-title">S3 存储配置</div>
      <p class="admin-form-hint" style="margin-bottom: 14px">支持 S3 兼容存储（如 Cloudflare R2）</p>
      <div class="admin-form-grid">
        <div class="admin-form-field" style="grid-column: 1 / -1">
          <label>Endpoint URL</label>
          <input v-model="form.backup_s3_endpoint" placeholder="https://xxx.r2.cloudflarestorage.com" />
        </div>
        <div class="admin-form-field"><label>Region</label><input v-model="form.backup_s3_region" placeholder="auto" /></div>
        <div class="admin-form-field"><label>Bucket</label><input v-model="form.backup_s3_bucket" /></div>
        <div class="admin-form-field"><label>Key 前缀</label><input v-model="form.backup_s3_prefix" placeholder="backups/" /></div>
        <div class="admin-form-field"><label>Access Key</label><input v-model="form.backup_s3_access_key" /></div>
        <div class="admin-form-field"><label>Secret Key</label><input v-model="form.backup_s3_secret_key" type="password" /></div>
      </div>
      <AdminToggleRow v-model="form.backup_auto_enabled" label="启用自动备份" />
    </div>

    <div class="admin-form-card">
      <div class="admin-form-section-title">定期备份</div>
      <div class="admin-form-grid">
        <div class="admin-form-field">
          <label>Cron 表达式</label>
          <input v-model="form.backup_cron" placeholder="0 2 * * *" />
          <p class="admin-form-hint">默认每天凌晨 2 点</p>
        </div>
        <div class="admin-form-field">
          <label>保留天数</label>
          <input v-model.number="form.backup_retention_days" type="number" min="1" max="365" />
        </div>
        <div class="admin-form-field">
          <label>最大备份数</label>
          <input v-model.number="form.backup_max_count" type="number" min="1" max="100" />
        </div>
      </div>
    </div>

    <div class="admin-form-card">
      <div class="admin-provider-table__head">
        <div class="admin-form-section-title" style="margin: 0">备份记录</div>
        <button
          type="button"
          class="btn btn-ghost-admin"
          :disabled="triggering"
          @click="createBackup"
        >
          {{ triggering ? '备份中…' : '创建备份' }}
        </button>
      </div>

      <AdminAlert v-if="backupError" :message="backupError" type="error" style="margin-bottom: 12px" />
      <AdminAlert v-if="backupSuccess" :message="backupSuccess" type="success" style="margin-bottom: 12px" />

      <div class="admin-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>ID</th><th>状态</th><th>文件名</th><th>大小</th><th>触发方式</th><th>开始时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loadingBackups">
              <td colspan="6" class="admin-table-empty">加载中…</td>
            </tr>
            <tr v-else-if="backups.length === 0">
              <td colspan="6" class="admin-table-empty">暂无备份记录</td>
            </tr>
            <tr v-for="item in backups" v-else :key="item.id">
              <td><code class="admin-code">{{ shortId(item.id) }}</code></td>
              <td>
                <span class="admin-tag" :class="statusClass(item.status)">{{ statusLabel(item.status) }}</span>
                <span v-if="item.error_message" class="admin-form-hint" :title="item.error_message">（失败）</span>
              </td>
              <td>{{ item.filename || '—' }}</td>
              <td>{{ formatSize(item.size_bytes) }}</td>
              <td>{{ triggerLabel(item.trigger_type) }}</td>
              <td>{{ formatTime(item.started_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listAdminBackups, triggerAdminBackup } from '@/api/admin'
import type { DatabaseBackupItem, PlatformSettings } from '@/types'
import AdminAlert from '@/components/admin/AdminAlert.vue'
import AdminToggleRow from '@/components/admin/AdminToggleRow.vue'

const form = defineModel<PlatformSettings>({ required: true })

const backups = ref<DatabaseBackupItem[]>([])
const loadingBackups = ref(false)
const triggering = ref(false)
const backupError = ref('')
const backupSuccess = ref('')

function shortId(id: string): string {
  return id.slice(0, 8)
}

function formatSize(bytes: number | null): string {
  if (bytes == null) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatTime(value: string): string {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    completed: '完成',
    failed: '失败',
    dry_run: '演练',
    running: '进行中',
    pending: '等待中',
  }
  return map[status] || status
}

function statusClass(status: string): string {
  if (status === 'completed') return 'admin-tag--success'
  if (status === 'failed') return 'admin-tag--danger'
  if (status === 'running') return 'admin-tag--warning'
  return ''
}

function triggerLabel(trigger: string): string {
  return trigger === 'scheduled' ? '定时' : '手动'
}

async function loadBackups() {
  loadingBackups.value = true
  backupError.value = ''
  try {
    const data = await listAdminBackups({ page: 1, page_size: 20 })
    backups.value = data.items
  } catch (e) {
    backupError.value = e instanceof Error ? e.message : '加载备份记录失败'
  } finally {
    loadingBackups.value = false
  }
}

async function createBackup() {
  triggering.value = true
  backupError.value = ''
  backupSuccess.value = ''
  try {
    const item = await triggerAdminBackup(false)
    backupSuccess.value =
      item.status === 'completed'
        ? `备份完成：${item.filename || item.id}`
        : item.status === 'failed'
          ? `备份失败：${item.error_message || '未知错误'}`
          : `备份任务已创建（${statusLabel(item.status)}）`
    await loadBackups()
  } catch (e) {
    backupError.value = e instanceof Error ? e.message : '创建备份失败'
  } finally {
    triggering.value = false
  }
}

onMounted(loadBackups)
</script>

<style scoped>
.admin-provider-table__head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.admin-table-empty { text-align: center; color: #9ca3af; padding: 32px !important; }
</style>
