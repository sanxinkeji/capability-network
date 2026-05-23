<template>
  <div>
    <AdminPageHeader title="邀请码 / 充值卡" subtitle="批量生成注册邀请码与余额充值卡，可设置有效期与数量">
      <template #actions>
        <button class="btn btn-primary-admin" @click="showGenerate = true">批量生成</button>
      </template>
    </AdminPageHeader>

    <AdminAlert v-if="error" :message="error" type="error" />
    <AdminAlert v-if="success" :message="success" type="success" />

    <AdminDataTable :loading="loading" :error="listError" :empty="!loading && !listError && codes.length === 0">
      <template #toolbar>
        <div class="admin-toolbar" style="margin: 0; padding: 0; border: none; box-shadow: none">
          <select v-model="typeFilter" @change="reload">
            <option value="">全部类型</option>
            <option value="invite">邀请码</option>
            <option value="recharge">充值卡</option>
          </select>
          <select v-model="statusFilter" @change="reload">
            <option value="">全部状态</option>
            <option value="active">可用</option>
            <option value="used">已使用</option>
            <option value="expired">已过期</option>
          </select>
          <button class="btn btn-secondary btn-sm" @click="reload">刷新</button>
        </div>
      </template>

      <template #empty>
        <EmptyState icon="inbox">暂无码券，点击右上角批量生成</EmptyState>
      </template>

      <template #head>
        <tr>
          <th>码值</th>
          <th>类型</th>
          <th>面值</th>
          <th>状态</th>
          <th>过期时间</th>
          <th>使用时间</th>
          <th>批次</th>
        </tr>
      </template>

      <tr v-for="item in codes" :key="item.id">
        <td><code class="admin-code">{{ item.code }}</code></td>
        <td>{{ item.code_type === 'invite' ? '邀请码' : '充值卡' }}</td>
        <td>{{ item.value_cents ? formatCents(item.value_cents) : '—' }}</td>
        <td><span class="admin-tag" :class="statusClass(item.status)">{{ statusLabel(item.status) }}</span></td>
        <td>{{ item.expires_at ? formatDate(item.expires_at) : '永久' }}</td>
        <td>{{ item.used_at ? formatDate(item.used_at) : '—' }}</td>
        <td class="admin-batch-id">{{ item.batch_id.slice(0, 8) }}…</td>
      </tr>

      <template #footer>
        <AdminPager v-model:page="page" :page-size="pageSize" :total="total" @update:page="loadCodes" />
      </template>
    </AdminDataTable>

    <Teleport to="body">
      <div v-if="showGenerate" class="admin-modal-overlay" @click.self="showGenerate = false">
        <div class="admin-modal admin-modal--wide" role="dialog">
          <div class="admin-modal__header">
            <h3 class="admin-modal__title">批量生成</h3>
          </div>
          <div class="admin-modal__body">
            <div class="admin-form-field">
              <label>类型</label>
              <select v-model="genForm.code_type">
                <option value="invite">邀请码（注册用）</option>
                <option value="recharge">余额充值卡</option>
              </select>
            </div>
            <div class="admin-form-field">
              <label>生成数量</label>
              <input v-model.number="genForm.count" type="number" min="1" max="500" />
            </div>
            <div v-if="genForm.code_type === 'recharge'" class="admin-form-field">
              <label>面值（元）</label>
              <input v-model.number="genForm.valueYuan" type="number" min="0.01" step="0.01" />
            </div>
            <div class="admin-form-field">
              <label>有效期至（可选）</label>
              <input v-model="genForm.expires_at" type="datetime-local" />
              <p class="admin-form-hint">留空表示永久有效</p>
            </div>
          </div>
          <div class="admin-modal__footer">
            <button type="button" class="btn btn-secondary btn-sm" @click="showGenerate = false">取消</button>
            <button type="button" class="btn btn-primary-admin btn-sm" :disabled="generating" @click="handleGenerate">
              {{ generating ? '生成中…' : '生成' }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="showResult" class="admin-modal-overlay" @click.self="showResult = false">
        <div class="admin-modal admin-modal--wide" role="dialog">
          <div class="admin-modal__header">
            <h3 class="admin-modal__title">生成成功</h3>
          </div>
          <div class="admin-modal__body">
            <p class="admin-form-hint">共 {{ generatedCodes.length }} 个，请妥善保存：</p>
            <textarea class="admin-code-result" readonly :value="generatedCodes.join('\n')" rows="8" />
          </div>
          <div class="admin-modal__footer">
            <button type="button" class="btn btn-secondary btn-sm" @click="showResult = false">关闭</button>
            <button type="button" class="btn btn-primary-admin btn-sm" @click="copyGenerated">复制全部</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { generateAdminCodes, listAdminCodes } from '@/api/admin'
import type { PlatformCodeItem } from '@/types'
import { formatCents, formatDate } from '@/utils'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminDataTable from '@/components/admin/AdminDataTable.vue'
import AdminAlert from '@/components/admin/AdminAlert.vue'
import AdminPager from '@/components/AdminPager.vue'
import EmptyState from '@/components/EmptyState.vue'

const codes = ref<PlatformCodeItem[]>([])
const loading = ref(true)
const listError = ref('')
const error = ref('')
const success = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)
const typeFilter = ref('')
const statusFilter = ref('')

const showGenerate = ref(false)
const showResult = ref(false)
const generating = ref(false)
const generatedCodes = ref<string[]>([])

const genForm = reactive({
  code_type: 'invite' as 'invite' | 'recharge',
  count: 10,
  valueYuan: 10,
  expires_at: '',
})

function statusLabel(status: string) {
  return ({ active: '可用', used: '已使用', expired: '已过期' } as Record<string, string>)[status] ?? status
}

function statusClass(status: string) {
  if (status === 'active') return 'admin-tag--success'
  if (status === 'used') return 'admin-tag--muted'
  return 'admin-tag--warn'
}

async function loadCodes() {
  loading.value = true
  listError.value = ''
  try {
    const data = await listAdminCodes({
      page: page.value,
      page_size: pageSize,
      code_type: typeFilter.value || undefined,
      status: statusFilter.value || undefined,
    })
    codes.value = data.items
    total.value = data.total
  } catch (e) {
    listError.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function reload() {
  page.value = 1
  loadCodes()
}

async function handleGenerate() {
  generating.value = true
  error.value = ''
  try {
    const result = await generateAdminCodes({
      code_type: genForm.code_type,
      count: genForm.count,
      expires_at: genForm.expires_at ? new Date(genForm.expires_at).toISOString() : null,
      value_cents: genForm.code_type === 'recharge' ? Math.round(genForm.valueYuan * 100) : undefined,
    })
    generatedCodes.value = result.codes
    showGenerate.value = false
    showResult.value = true
    success.value = `已生成 ${result.count} 个${genForm.code_type === 'invite' ? '邀请码' : '充值卡'}`
    await loadCodes()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '生成失败'
  } finally {
    generating.value = false
  }
}

async function copyGenerated() {
  await navigator.clipboard.writeText(generatedCodes.value.join('\n'))
  success.value = '已复制到剪贴板'
  showResult.value = false
}

onMounted(loadCodes)
</script>

<style scoped>
.admin-code {
  font-family: ui-monospace, monospace;
  font-size: 13px;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
}
.admin-batch-id {
  font-size: 12px;
  color: #9ca3af;
}
.admin-code-result {
  width: 100%;
  font-family: ui-monospace, monospace;
  font-size: 12px;
  padding: 10px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-top: 8px;
}
.admin-modal--wide {
  max-width: 480px;
}
</style>
