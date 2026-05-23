<template>
  <div class="admin-form-card">
    <div class="admin-form-section-title">站点设置</div>
    <div class="admin-form-grid">
      <div class="admin-form-field">
        <label>站点名称</label>
        <input v-model="form.site_name" />
        <p class="admin-form-hint">保存后立即同步到官网、用户端标题与导航栏</p>
      </div>
      <div class="admin-form-field">
        <label>站点副标题</label>
        <input v-model="form.site_tagline" placeholder="可选" />
      </div>
      <div class="admin-form-field">
        <label>API 公开地址</label>
        <input v-model="form.api_public_url" placeholder="https://api.example.com" />
      </div>
      <div class="admin-form-field">
        <label>文档链接</label>
        <input v-model="form.docs_url" placeholder="https://docs.example.com" />
      </div>
      <div class="admin-form-field">
        <label>默认分页条数</label>
        <input v-model.number="form.default_page_size" type="number" min="5" max="200" />
      </div>
      <div class="admin-form-field">
        <label>可选分页条数</label>
        <input v-model="form.page_size_options" placeholder="10,20,50" />
      </div>
      <div class="admin-form-field" style="grid-column: 1 / -1">
        <label>全站公告</label>
        <textarea v-model="form.site_announcement" rows="3" placeholder="显示在用户控制台顶部" />
      </div>
      <div class="admin-form-field">
        <label>客服邮箱</label>
        <input v-model="form.support_email" type="email" />
      </div>
      <div class="admin-form-field">
        <label>客服链接</label>
        <input v-model="form.support_url" placeholder="https://" />
      </div>
      <div class="admin-form-field" style="grid-column: 1 / -1">
        <label>页脚内容</label>
        <textarea v-model="form.footer_text" rows="2" placeholder="显示在页面底部" />
      </div>
    </div>

    <div class="admin-form-section-title" style="margin-top: 20px">自定义链接</div>
    <div class="admin-link-list">
      <div v-for="(link, idx) in links" :key="idx" class="admin-link-item">
        <input v-model="link.label" placeholder="链接名称" />
        <input v-model="link.url" placeholder="https://" />
        <button type="button" class="btn btn-ghost-admin admin-link-item__remove" @click="removeLink(idx)">删除</button>
      </div>
      <button type="button" class="admin-add-btn" @click="addLink">+ 添加链接</button>
    </div>

    <AdminToggleRow v-model="form.maintenance_mode" label="维护模式" hint="开启后用户控制台显示维护提示" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PlatformSettings } from '@/types'
import AdminToggleRow from '@/components/admin/AdminToggleRow.vue'
import { parseCustomLinks, serializeCustomLinks } from '@/composables/adminSettingsForm'

const form = defineModel<PlatformSettings>({ required: true })

const links = computed({
  get: () => parseCustomLinks(form.value.custom_links_json),
  set: (items) => { form.value.custom_links_json = serializeCustomLinks(items) ?? '' },
})

function addLink() {
  links.value = [...links.value, { label: '', url: '' }]
}

function removeLink(idx: number) {
  links.value = links.value.filter((_, i) => i !== idx)
}
</script>
