<template>
  <div class="admin-form-card">
    <div class="admin-form-row">
      <div>
        <div class="admin-form-row__label">登录条款确认</div>
        <p class="admin-form-hint">用户登录/注册前需阅读并同意条款</p>
      </div>
      <AdminToggle v-model="form.legal_terms_enabled" />
    </div>

    <template v-if="form.legal_terms_enabled">
      <div class="admin-form-field" style="margin-top: 16px">
        <label>展示形式</label>
        <AdminSegmentedControl
          v-model="form.legal_terms_mode"
          :options="[
            { value: 'popup', label: '弹窗' },
            { value: 'redirect', label: '重定向' },
          ]"
        />
      </div>
      <div class="admin-form-field">
        <label>条款更新日期</label>
        <input v-model="form.legal_terms_updated_at" type="date" />
        <p class="admin-form-hint">用户上次同意早于此日期时需重新确认</p>
      </div>
    </template>

    <div class="admin-form-section-title" style="margin-top: 20px">协议列表</div>
    <div v-for="(item, idx) in agreements" :key="idx" class="admin-agreement-card">
      <div class="admin-agreement-card__head">
        <span class="admin-form-section-title" style="margin: 0">协议 {{ idx + 1 }}</span>
        <button type="button" class="btn btn-ghost-admin" @click="removeAgreement(idx)">删除</button>
      </div>
      <div class="admin-form-grid">
        <div class="admin-form-field">
          <label>标题</label>
          <input v-model="item.title" placeholder="服务条款" />
        </div>
        <div class="admin-form-field">
          <label>路由别名</label>
          <input v-model="item.slug" placeholder="/terms" />
        </div>
        <div class="admin-form-field" style="grid-column: 1 / -1">
          <label>Markdown 内容</label>
          <textarea v-model="item.content" rows="6" placeholder="支持 Markdown" />
        </div>
      </div>
    </div>
    <button type="button" class="admin-add-btn" @click="addAgreement">+ 添加协议</button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PlatformSettings } from '@/types'
import AdminToggle from '@/components/admin/AdminToggle.vue'
import AdminSegmentedControl from '@/components/admin/AdminSegmentedControl.vue'
import { parseLegalAgreements, serializeLegalAgreements } from '@/composables/adminSettingsForm'

const form = defineModel<PlatformSettings>({ required: true })

const agreements = computed({
  get: () => parseLegalAgreements(form.value.legal_agreements_json),
  set: (items) => { form.value.legal_agreements_json = serializeLegalAgreements(items) ?? '' },
})

function addAgreement() {
  agreements.value = [...agreements.value, { title: '', slug: '', content: '' }]
}

function removeAgreement(idx: number) {
  agreements.value = agreements.value.filter((_, i) => i !== idx)
}
</script>
