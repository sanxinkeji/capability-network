<template>
  <div class="app-page">
    <div class="commerce-page-head">
      <div>
        <h1>{{ aiMode ? 'AI 发需求' : '创建需求' }}</h1>
        <p v-if="aiMode" class="commerce-page-head__sub">自然语言描述，自动解析类目与预算</p>
      </div>
      <div class="header-actions">
        <button type="button" class="btn btn-secondary btn-sm" @click="toggleMode">
          {{ aiMode ? '高级表单' : 'AI 模式' }}
        </button>
        <RouterLink to="/app/intents" class="btn btn-secondary btn-sm">返回列表</RouterLink>
      </div>
    </div>

    <div class="inset-form">
      <div v-if="error" class="error-msg">{{ error }}</div>

      <!-- AI 模式（默认） -->
      <template v-if="aiMode">
        <div class="ai-intro glass-card">
          <AppIcon name="agent" size="md" />
          <p>用自然语言描述你要什么，AI 将自动解析标题、类目、预算与渠道。</p>
        </div>

        <div class="inset-group">
          <div class="inset-row">
            <label>描述你的需求</label>
            <textarea
              v-model="naturalText"
              rows="5"
              placeholder="例如：我需要一位设计师帮我做一个现代简约风格的品牌 Logo，预算 500 元，7 天内交付，希望智能体能自动对接"
            />
          </div>
        </div>

        <div class="inset-form-actions">
          <button
            class="btn btn-lg btn-commerce"
            type="button"
            :disabled="parsing || !naturalText.trim()"
            @click="handleParse"
          >
            {{ parsing ? 'AI 解析中…' : 'AI 解析' }}
          </button>
        </div>

        <GroupedList v-if="parsed" class="parse-preview">
          <div class="grouped-item grouped-item--static grouped-item--stack">
            <div class="preview-header">
              <span class="grouped-item__title">解析结果</span>
              <span :class="parsedByBadgeClass">{{ parsedByLabel }}</span>
            </div>
            <div class="preview-row"><span class="preview-label">标题</span>{{ parsed.title }}</div>
            <div class="preview-row"><span class="preview-label">类目</span>{{ categoryLabel(parsed.category) }}</div>
            <div class="preview-row"><span class="preview-label">渠道</span>{{ channelLabel(parsed.channel) }}</div>
            <div class="preview-row">
              <span class="preview-label">预算</span>
              {{ formatCents(parsed.budget_max, parsed.currency) }}
            </div>
            <div class="preview-desc">{{ parsed.description }}</div>
          </div>
        </GroupedList>

        <div v-if="parsed" class="inset-form-actions">
          <button class="btn btn-lg btn-commerce" type="button" :disabled="submitting" @click="handleConfirmCreate">
            {{ submitting ? '创建中…' : '确认并创建' }}
          </button>
        </div>
      </template>

      <!-- 高级表单模式 -->
      <form v-else @submit.prevent="handleSubmit">
        <div class="inset-group">
          <div class="inset-row">
            <label>标题</label>
            <input v-model="form.title" required maxlength="200" placeholder="例如：需要品牌 Logo 设计" />
          </div>
          <div class="inset-row">
            <label>描述</label>
            <textarea v-model="form.description" required rows="3" placeholder="例如：寻找设计师完成品牌标识，含源文件" />
          </div>
          <div class="inset-row">
            <label>分类</label>
            <select v-model="form.category" required>
              <option v-for="c in CATEGORY_OPTIONS" :key="c.value" :value="c.value">
                {{ c.label }}
              </option>
            </select>
          </div>
        </div>

        <div class="inset-group inset-row--inline">
          <div class="inset-cell">
            <label>渠道</label>
            <select v-model="form.channel">
              <option value="human">人工</option>
              <option value="agent">智能体</option>
            </select>
          </div>
          <div class="inset-cell">
            <label>预算上限（元）</label>
            <input v-model.number="budgetYuan" type="number" min="0" step="0.01" required />
            <p class="form-hint">{{ form.budget_max }} 分</p>
          </div>
        </div>

        <div class="inset-group">
          <div class="inset-row">
            <label>验收标准</label>
            <textarea
              v-model="acceptanceCriteriaJson"
              rows="4"
              placeholder='{"deliverable": "PDF 报告", "turnaround_days": 7}'
            />
            <p class="form-hint">JSON 格式，描述交付物与验收条件</p>
          </div>
        </div>

        <div class="inset-form-actions">
          <button class="btn btn-lg" type="submit" :disabled="submitting">
            {{ submitting ? '提交中…' : '创建需求' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { createIntent, parseIntent } from '@/api'
import type { IntentChannel, IntentParseResult } from '@/types'
import { CATEGORY_OPTIONS, categoryLabel, channelLabel, formatCents, normalizeParsedCategory } from '@/utils'
import GroupedList from '@/components/GroupedList.vue'
import AppIcon from '@/components/AppIcon.vue'

const route = useRoute()
const router = useRouter()

const aiMode = ref(route.query.mode !== 'form')
const naturalText = ref('')
const parsed = ref<IntentParseResult | null>(null)
const parsing = ref(false)
const submitting = ref(false)
const error = ref('')

const form = reactive({
  title: '',
  description: '',
  category: 'design',
  channel: 'human' as IntentChannel,
  budget_max: 0,
  currency: 'CNY',
  acceptance_criteria: { deliverable: 'PDF 报告', turnaround_days: 7 } as Record<string, unknown>,
})

watch(
  () => route.query.mode,
  (mode) => {
    aiMode.value = mode !== 'form'
  },
)

onMounted(() => {
  const hint = route.query.hint
  if (typeof hint === 'string' && hint.trim() && !naturalText.value) {
    naturalText.value = `我想选用「${decodeURIComponent(hint.trim())}」，请帮我生成匹配需求`
  }
})

const budgetYuan = computed({
  get: () => form.budget_max / 100,
  set: (v: number) => {
    form.budget_max = Math.round(v * 100)
  },
})

const acceptanceCriteriaJson = computed({
  get: () => JSON.stringify(form.acceptance_criteria, null, 2),
  set: (v: string) => {
    try {
      form.acceptance_criteria = JSON.parse(v || '{}')
    } catch {
      /* 提交时校验 */
    }
  },
})

const parsedByLabel = computed(() =>
  parsed.value?.parsed_by === 'llm' ? 'LLM 解析' : '规则解析',
)

const parsedByBadgeClass = computed(() =>
  parsed.value?.parsed_by === 'llm' ? 'badge badge-published' : 'badge badge-draft',
)

function toggleMode() {
  aiMode.value = !aiMode.value
  error.value = ''
}

async function handleParse() {
  error.value = ''
  parsing.value = true
  parsed.value = null
  try {
    parsed.value = await parseIntent(naturalText.value.trim())
  } catch (e) {
    error.value = e instanceof Error ? e.message : '解析失败'
  } finally {
    parsing.value = false
  }
}

async function handleConfirmCreate() {
  if (!parsed.value) return
  error.value = ''
  submitting.value = true
  try {
    const intent = await createIntent({
      title: parsed.value.title,
      description: parsed.value.description,
      category: normalizeParsedCategory(parsed.value.category),
      channel: parsed.value.channel,
      settlement: parsed.value.settlement,
      budget_max: parsed.value.budget_max || 50000,
      currency: parsed.value.currency,
      deadline: parsed.value.deadline,
      acceptance_criteria: parsed.value.acceptance_criteria,
    })
    router.push(`/app/matching/${intent.id}`)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '创建失败'
  } finally {
    submitting.value = false
  }
}

async function handleSubmit() {
  error.value = ''
  try {
    JSON.parse(acceptanceCriteriaJson.value || '{}')
  } catch {
    error.value = '验收标准 JSON 格式无效'
    return
  }

  submitting.value = true
  try {
    const intent = await createIntent(form)
    router.push(`/app/matching/${intent.id}`)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '创建失败'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.header-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.ai-intro {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: var(--space-md) !important;
  margin-bottom: var(--space-md);
  color: var(--color-label-secondary);
  font-size: 15px;
}

.ai-intro p {
  margin: 0;
}

.parse-preview {
  margin: var(--space-md) 0;
}

.grouped-item--stack {
  flex-direction: column;
  align-items: flex-start;
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.preview-row {
  font-size: 14px;
  margin-bottom: 4px;
}

.preview-label {
  display: inline-block;
  width: 48px;
  color: var(--color-label-tertiary);
}

.preview-desc {
  margin-top: 8px;
  font-size: 14px;
  color: var(--color-label-secondary);
  line-height: 1.45;
}
</style>
