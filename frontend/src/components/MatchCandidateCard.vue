<template>
  <article class="match-card glass-card">
    <div class="match-card__cover" :class="`match-card__cover--${candidate.category}`">
      <span class="match-rank">#{{ candidate.rank }}</span>
      <AppIcon :name="coverIcon" size="lg" class="cover-icon" />
      <span v-if="candidate.channel === 'agent'" class="cover-badge cover-badge--agent">智能体</span>
      <span v-if="candidate.recommend_auto" class="cover-tag tag-promo">自动推荐</span>
    </div>

    <div class="match-card__body">
      <h3 class="match-card__title">{{ candidate.title }}</h3>
      <p v-if="candidate.description" class="match-card__desc">{{ candidate.description }}</p>
      <p class="recommend-reason">{{ reason }}</p>

      <div v-if="breakdown.length > 0" class="score-breakdown">
        <span v-for="chip in breakdown" :key="chip.key" class="breakdown-chip">
          {{ chip.label }} {{ chip.value }}
        </span>
      </div>

      <div class="match-card__footer">
        <div>
          <div class="price-commerce">
            <span class="price-symbol">¥</span>
            <span class="price-int">{{ priceParts.int }}</span>
            <span class="price-dec">{{ priceParts.dec }}</span>
          </div>
          <div class="match-score">{{ (candidate.match_score * 100).toFixed(1) }}% 匹配</div>
        </div>
        <button
          class="btn btn-sm btn-commerce"
          :disabled="creating"
          @click="emit('create-deal', candidate)"
        >
          {{ creating ? '下单中…' : '下单并支付' }}
        </button>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import type { IconName } from '@/components/icons'
import type { Intent, MatchCandidate } from '@/types'
import { recommendReason } from '@/utils'

const props = defineProps<{
  candidate: MatchCandidate
  intent: Intent | null
  creating?: boolean
}>()

const emit = defineEmits<{
  'create-deal': [candidate: MatchCandidate]
}>()

const BREAKDOWN_LABELS: Record<string, string> = {
  semantic: '语义',
  alignment: '对齐',
  quality: '质量',
  price: '价格',
  trust: '信誉',
  freshness: '新鲜度',
}

const coverIcon = computed((): IconName => {
  const map: Record<string, IconName> = {
    design: 'target',
    data: 'chart',
    dev: 'agent',
    content: 'clipboard',
    consulting: 'person',
    ai: 'agent',
  }
  return map[props.candidate.category] ?? (props.candidate.channel === 'agent' ? 'agent' : 'package')
})

const reason = computed(() => recommendReason(props.candidate, props.intent))

const priceParts = computed(() => {
  const [int, dec] = (props.candidate.price_cents / 100).toFixed(2).split('.')
  return { int, dec: `.${dec}` }
})

const breakdown = computed(() => {
  const entries: { key: string; label: string; value: string }[] = []
  for (const [key, value] of Object.entries(props.candidate.score_breakdown ?? {})) {
    if (key === 'recommend_auto') continue
    entries.push({
      key,
      label: BREAKDOWN_LABELS[key] ?? key,
      value: typeof value === 'boolean' ? (value ? '是' : '否') : `${(value * 100).toFixed(0)}%`,
    })
  }
  return entries
})
</script>

<style scoped>
.match-card {
  padding: 0 !important;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.match-card__cover {
  position: relative;
  aspect-ratio: 16 / 10;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #e8f4ff 0%, #f0f4ff 50%, #fff5f0 100%);
}

.match-card__cover--design {
  background: linear-gradient(145deg, #ffe8f0, #fff0e8);
}

.match-card__cover--data {
  background: linear-gradient(145deg, #e8fff0, #e8f8ff);
}

.match-card__cover--dev,
.match-card__cover--ai {
  background: linear-gradient(145deg, #e8eeff, #f0e8ff);
}

.match-card__cover--content {
  background: linear-gradient(145deg, #fff8e8, #ffe8e8);
}

.match-rank {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-commerce);
  background: var(--color-commerce-muted);
  padding: 2px 8px;
  border-radius: 4px;
}

.cover-icon {
  color: rgba(0, 0, 0, 0.25);
  width: 44px;
  height: 44px;
}

.cover-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(52, 199, 89, 0.9);
  color: #fff;
}

.cover-tag {
  position: absolute;
  bottom: 8px;
  left: 8px;
  font-size: 10px;
  padding: 2px 6px;
}

.match-card__body {
  padding: 10px 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.match-card__title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.35;
}

.match-card__desc {
  margin: 0;
  font-size: 12px;
  color: var(--color-label-tertiary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.recommend-reason {
  margin: 0;
  font-size: 12px;
  color: var(--color-label-secondary);
  line-height: 1.45;
}

.score-breakdown {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.breakdown-chip {
  font-size: 10px;
  color: var(--color-label-secondary);
  background: var(--color-fill);
  border-radius: 4px;
  padding: 2px 6px;
}

.match-card__footer {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 8px;
  margin-top: auto;
  padding-top: 4px;
}

.match-score {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-primary);
  margin-top: 2px;
}
</style>
