<template>
  <div class="legal-page">
    <header class="page-hero">
      <p class="eyebrow">法律文件</p>
      <h1>{{ document.title }}</h1>
      <p v-if="platform.legalTermsUpdatedAt" class="page-meta">
        最近更新：{{ platform.legalTermsUpdatedAt }}
      </p>
    </header>

    <section class="section">
      <article class="legal-content glass-card" v-html="htmlContent" />
    </section>

    <p class="back-link">
      <RouterLink to="/">← 返回首页</RouterLink>
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { usePlatformStore } from '@/stores/platform'
import { DEFAULT_LEGAL_CONTENT, findLegalAgreement, type LegalDocKey } from '@/utils/legal'
import { renderMarkdown } from '@/utils/markdown'

const props = defineProps<{
  docKey: LegalDocKey
}>()

const platform = usePlatformStore()

onMounted(() => {
  platform.fetchSettings()
})

const document = computed(() => {
  const configured = findLegalAgreement(platform.legalAgreements, props.docKey)
  if (configured?.content.trim()) {
    return { title: configured.title, content: configured.content }
  }
  if (configured?.title) {
    return { title: configured.title, content: DEFAULT_LEGAL_CONTENT[props.docKey].content }
  }
  return DEFAULT_LEGAL_CONTENT[props.docKey]
})

const htmlContent = computed(() => renderMarkdown(document.value.content))
</script>

<style scoped>
.legal-page {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 0 var(--space-lg) var(--space-2xl);
}

.page-hero {
  padding: var(--space-2xl) 0 var(--space-lg);
  text-align: center;
  max-width: 720px;
  margin: 0 auto;
}

.eyebrow {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-primary);
  margin: 0 0 var(--space-sm);
}

.page-hero h1 {
  font-size: clamp(32px, 5vw, 44px);
  font-weight: 700;
  letter-spacing: -0.02em;
  margin: 0;
}

.page-meta {
  margin: 12px 0 0;
  color: var(--color-label-tertiary);
  font-size: 14px;
}

.section {
  padding: var(--space-md) 0;
}

.legal-content {
  padding: var(--space-xl) !important;
  max-width: 760px;
  margin: 0 auto;
}

.legal-content :deep(h1),
.legal-content :deep(h2),
.legal-content :deep(h3) {
  margin: 1.2em 0 0.6em;
  letter-spacing: -0.02em;
}

.legal-content :deep(h1:first-child),
.legal-content :deep(h2:first-child),
.legal-content :deep(h3:first-child) {
  margin-top: 0;
}

.legal-content :deep(p),
.legal-content :deep(li) {
  color: var(--color-label-secondary);
  line-height: 1.7;
  font-size: 16px;
}

.legal-content :deep(ul) {
  margin: 0.5em 0 1em;
  padding-left: 1.4em;
}

.legal-content :deep(code) {
  font-size: 0.92em;
  padding: 2px 6px;
  background: var(--color-fill);
  border-radius: 6px;
}

.legal-content :deep(a) {
  color: var(--color-primary);
}

.back-link {
  text-align: center;
  margin: var(--space-lg) 0 0;
  font-size: 15px;
}
</style>
