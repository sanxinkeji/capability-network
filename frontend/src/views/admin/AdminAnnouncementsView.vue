<template>
  <div>
    <AdminPageHeader title="公告管理" subtitle="创建公告并配置展示与通知方式">
      <template #actions>
        <button class="btn btn-primary-admin" @click="openCreate">创建公告</button>
      </template>
    </AdminPageHeader>

    <AdminAlert v-if="error" :message="error" type="error" />
    <AdminAlert v-if="success" :message="success" type="success" />

    <AdminDataTable :loading="loading" :error="listError" :empty="!loading && !listError && items.length === 0">
      <template #toolbar>
        <div class="admin-toolbar admin-toolbar--wide" style="margin: 0; padding: 0; border: none; box-shadow: none">
          <input v-model="search" type="search" placeholder="搜索公告标题…" @keyup.enter="reload" />
          <select v-model="statusFilter" @change="reload">
            <option value="">全部状态</option>
            <option value="active">展示中</option>
            <option value="draft">草稿</option>
          </select>
          <button class="btn btn-secondary btn-sm" @click="reload">刷新</button>
        </div>
      </template>

      <template #empty>
        <EmptyState icon="clipboard">暂无公告，点击右上角创建</EmptyState>
      </template>

      <template #head>
        <tr>
          <th>标题</th>
          <th>状态</th>
          <th>通知方式</th>
          <th>显示条件</th>
          <th>有效期</th>
          <th>创建时间</th>
          <th style="text-align: right">操作</th>
        </tr>
      </template>

      <tr v-for="item in items" :key="item.id">
        <td>
          <strong>{{ item.title }}</strong>
          <div class="admin-subline">#{{ item.id }}</div>
        </td>
        <td><span class="admin-tag" :class="item.status === 'active' ? 'admin-tag--success' : 'admin-tag--muted'">{{ item.status === 'active' ? '展示中' : '草稿' }}</span></td>
        <td><span class="admin-tag admin-tag--warning">{{ item.notify_mode === 'popup' ? '弹窗' : '横幅' }}</span></td>
        <td>{{ audienceLabel(item.audience) }}</td>
        <td>
          <div class="admin-validity">
            <span>开始：{{ item.starts_at ? formatDate(item.starts_at) : '立即' }}</span>
            <span>结束：{{ item.ends_at ? formatDate(item.ends_at) : '永久' }}</span>
          </div>
        </td>
        <td>{{ formatDate(item.created_at) }}</td>
        <td style="text-align: right">
          <div class="admin-row-actions">
            <button type="button" class="admin-icon-btn" title="查看" @click="viewItem(item)">
              <AppIcon name="eye" size="sm" />
            </button>
            <button type="button" class="admin-icon-btn" title="编辑" @click="editItem(item)">
              <AppIcon name="edit" size="sm" />
            </button>
            <button type="button" class="admin-icon-btn admin-icon-btn--danger" title="删除" @click="removeItem(item)">
              <AppIcon name="trash" size="sm" />
            </button>
          </div>
        </td>
      </tr>

      <template #footer>
        <AdminPager v-model:page="page" :page-size="pageSize" :total="total" @update:page="loadItems" />
      </template>
    </AdminDataTable>

    <Teleport to="body">
      <div v-if="showModal" class="admin-modal-overlay" @click.self="closeModal">
        <div class="admin-modal admin-modal--wide" role="dialog">
          <div class="admin-modal__header">
            <h3 class="admin-modal__title">{{ editing ? '编辑公告' : '创建公告' }}</h3>
          </div>
          <div class="admin-modal__body">
            <div class="admin-form-field">
              <label>标题</label>
              <input v-model="form.title" type="text" maxlength="256" />
            </div>
            <div class="admin-form-field">
              <label>内容</label>
              <textarea v-model="form.content" rows="6" />
            </div>
            <div class="admin-form-row">
              <div class="admin-form-field">
                <label>状态</label>
                <select v-model="form.status">
                  <option value="draft">草稿</option>
                  <option value="active">展示中</option>
                </select>
              </div>
              <div class="admin-form-field">
                <label>通知方式</label>
                <select v-model="form.notify_mode">
                  <option value="popup">弹窗</option>
                  <option value="banner">横幅</option>
                </select>
              </div>
              <div class="admin-form-field">
                <label>显示条件</label>
                <select v-model="form.audience">
                  <option value="all">全部用户</option>
                </select>
              </div>
            </div>
            <div class="admin-form-row">
              <div class="admin-form-field">
                <label>开始时间（可选）</label>
                <input v-model="form.starts_at" type="datetime-local" />
              </div>
              <div class="admin-form-field">
                <label>结束时间（可选）</label>
                <input v-model="form.ends_at" type="datetime-local" />
              </div>
            </div>
          </div>
          <div class="admin-modal__footer">
            <button class="btn btn-secondary btn-sm" @click="closeModal">取消</button>
            <button class="btn btn-primary-admin btn-sm" :disabled="saving || !form.title.trim()" @click="saveItem">
              {{ saving ? '保存中…' : '保存' }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="viewing" class="admin-modal-overlay" @click.self="viewing = null">
        <div class="admin-modal admin-modal--wide" role="dialog">
          <div class="admin-modal__header">
            <h3 class="admin-modal__title">{{ viewing.title }}</h3>
          </div>
          <div class="admin-modal__body">
            <pre class="admin-announcement-preview">{{ viewing.content || '（无正文）' }}</pre>
          </div>
          <div class="admin-modal__footer">
            <button class="btn btn-secondary btn-sm" @click="viewing = null">关闭</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import {
  createAdminAnnouncement,
  deleteAdminAnnouncement,
  listAdminAnnouncements,
  updateAdminAnnouncement,
} from '@/api/admin'
import type { AnnouncementItem } from '@/types'
import { formatDate } from '@/utils'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminDataTable from '@/components/admin/AdminDataTable.vue'
import AdminAlert from '@/components/admin/AdminAlert.vue'
import EmptyState from '@/components/EmptyState.vue'
import AdminPager from '@/components/AdminPager.vue'
import AppIcon from '@/components/AppIcon.vue'

const items = ref<AnnouncementItem[]>([])
const loading = ref(true)
const listError = ref('')
const error = ref('')
const success = ref('')
const search = ref('')
const statusFilter = ref('')
const page = ref(1)
const pageSize = 10
const total = ref(0)

const showModal = ref(false)
const editing = ref<AnnouncementItem | null>(null)
const viewing = ref<AnnouncementItem | null>(null)
const saving = ref(false)

const form = reactive({
  title: '',
  content: '',
  status: 'draft' as 'draft' | 'active',
  notify_mode: 'popup' as 'popup' | 'banner',
  audience: 'all',
  starts_at: '',
  ends_at: '',
})

function audienceLabel(audience: string) {
  return audience === 'all' ? '全部用户' : audience
}

function resetForm() {
  form.title = ''
  form.content = ''
  form.status = 'draft'
  form.notify_mode = 'popup'
  form.audience = 'all'
  form.starts_at = ''
  form.ends_at = ''
}

function openCreate() {
  editing.value = null
  resetForm()
  showModal.value = true
}

function editItem(item: AnnouncementItem) {
  editing.value = item
  form.title = item.title
  form.content = item.content
  form.status = item.status
  form.notify_mode = item.notify_mode
  form.audience = item.audience
  form.starts_at = item.starts_at ? toLocalInput(item.starts_at) : ''
  form.ends_at = item.ends_at ? toLocalInput(item.ends_at) : ''
  showModal.value = true
}

function viewItem(item: AnnouncementItem) {
  viewing.value = item
}

function closeModal() {
  showModal.value = false
}

function toLocalInput(iso: string) {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function toIsoOrNull(value: string) {
  if (!value) return null
  return new Date(value).toISOString()
}

async function loadItems() {
  loading.value = true
  listError.value = ''
  try {
    const data = await listAdminAnnouncements({
      page: page.value,
      page_size: pageSize,
      status: statusFilter.value || undefined,
      search: search.value.trim() || undefined,
    })
    items.value = data.items
    total.value = data.total
  } catch (e) {
    listError.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function reload() {
  page.value = 1
  loadItems()
}

async function saveItem() {
  saving.value = true
  error.value = ''
  success.value = ''
  const payload = {
    title: form.title.trim(),
    content: form.content,
    status: form.status,
    notify_mode: form.notify_mode,
    audience: form.audience,
    starts_at: toIsoOrNull(form.starts_at),
    ends_at: toIsoOrNull(form.ends_at),
  }
  try {
    if (editing.value) {
      await updateAdminAnnouncement(editing.value.id, payload)
      success.value = '公告已更新'
    } else {
      await createAdminAnnouncement(payload)
      success.value = '公告已创建'
    }
    closeModal()
    await loadItems()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

async function removeItem(item: AnnouncementItem) {
  if (!window.confirm(`确定删除公告「${item.title}」？`)) return
  error.value = ''
  try {
    await deleteAdminAnnouncement(item.id)
    success.value = '公告已删除'
    await loadItems()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '删除失败'
  }
}

onMounted(loadItems)
</script>

<style scoped>
.admin-subline {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}

.admin-validity {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
  color: #6b7280;
}

.admin-announcement-preview {
  white-space: pre-wrap;
  font-family: inherit;
  margin: 0;
  line-height: 1.6;
}
</style>
