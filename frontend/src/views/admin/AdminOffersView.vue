<template>
  <div>
    <AdminPageHeader title="供给管理" subtitle="审核、下架或恢复平台供给" />

    <AdminDataTable :loading="loading" :error="error" :empty="!loading && !error && offers.length === 0">
      <template #toolbar>
        <div class="admin-toolbar" style="margin: 0; padding: 0; border: none; box-shadow: none">
          <select v-model="statusFilter" @change="reload">
            <option value="">全部状态</option>
            <option value="draft">草稿</option>
            <option value="published">已发布</option>
            <option value="paused">已暂停</option>
          </select>
        </div>
      </template>

      <template #empty>
        <EmptyState icon="package">暂无供给</EmptyState>
      </template>

      <template #head>
        <tr>
          <th>标题</th>
          <th>分类 / 价格</th>
          <th>渠道</th>
          <th>状态</th>
          <th style="text-align: right">操作</th>
        </tr>
      </template>

      <tr v-for="offer in offers" :key="offer.id">
        <td><strong>{{ offer.title }}</strong></td>
        <td>{{ categoryLabel(offer.category) }} · {{ formatCents(offer.price_cents, offer.currency) }}</td>
        <td>{{ offer.channel === 'agent' ? '智能体' : '人工' }}</td>
        <td><span :class="badgeClass(offer.status)">{{ statusLabel(offer.status) }}</span></td>
        <td style="text-align: right">
          <button
            v-if="offer.status === 'published'"
            class="btn btn-outline-danger btn-sm"
            :disabled="actingId === offer.id"
            @click="pause(offer.id)"
          >
            {{ actingId === offer.id ? '处理中…' : '下架' }}
          </button>
          <button
            v-else-if="offer.status === 'paused'"
            class="btn btn-secondary btn-sm"
            :disabled="actingId === offer.id"
            @click="republish(offer.id)"
          >
            {{ actingId === offer.id ? '处理中…' : '恢复' }}
          </button>
        </td>
      </tr>

      <template #footer>
        <AdminPager v-model:page="page" :page-size="pageSize" :total="total" @update:page="loadOffers" />
      </template>
    </AdminDataTable>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listAdminOffers, updateAdminOfferStatus } from '@/api/admin'
import type { Offer } from '@/types'
import { categoryLabel, formatCents, statusLabel } from '@/utils'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminDataTable from '@/components/admin/AdminDataTable.vue'
import EmptyState from '@/components/EmptyState.vue'
import AdminPager from '@/components/AdminPager.vue'

const offers = ref<Offer[]>([])
const loading = ref(true)
const error = ref('')
const statusFilter = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)
const actingId = ref('')

function badgeClass(status: string) {
  const map: Record<string, string> = {
    draft: 'admin-tag admin-tag--muted',
    published: 'admin-tag admin-tag--success',
    paused: 'admin-tag admin-tag--warn',
  }
  return map[status] ?? 'admin-tag admin-tag--muted'
}

async function loadOffers() {
  loading.value = true
  error.value = ''
  try {
    const data = await listAdminOffers({
      page: page.value,
      page_size: pageSize,
      status: statusFilter.value || undefined,
    })
    offers.value = data.items
    total.value = data.total
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function reload() {
  page.value = 1
  loadOffers()
}

async function pause(offerId: string) {
  if (!confirm('确认下架此供给？')) return
  actingId.value = offerId
  try {
    await updateAdminOfferStatus(offerId, 'paused')
    await loadOffers()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    actingId.value = ''
  }
}

async function republish(offerId: string) {
  actingId.value = offerId
  try {
    await updateAdminOfferStatus(offerId, 'published')
    await loadOffers()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    actingId.value = ''
  }
}

onMounted(loadOffers)
</script>
