<template>
  <component :is="tag" :class="rootClass">
    <label v-if="showCheckbox" class="legal-checkbox">
      <input v-model="checked" type="checkbox" />
      <span>
        {{ checkboxPrefix }}
        <LegalAgreementLinks />
      </span>
    </label>
    <span v-else>
      {{ textPrefix }}
      <LegalAgreementLinks />
    </span>
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import LegalAgreementLinks from '@/components/LegalAgreementLinks.vue'

const props = withDefaults(
  defineProps<{
    mode?: 'checkbox' | 'text'
    tag?: string
    checkboxPrefix?: string
    textPrefix?: string
  }>(),
  {
    mode: 'text',
    tag: 'p',
    checkboxPrefix: '我已阅读并同意',
    textPrefix: '登录即表示您同意',
  },
)

const checked = defineModel<boolean>({ default: false })

const showCheckbox = computed(() => props.mode === 'checkbox')
const rootClass = computed(() => (showCheckbox.value ? 'legal-notice legal-notice--checkbox' : 'legal-notice'))
</script>

<style scoped>
.legal-notice {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-label-tertiary);
  text-align: center;
}

.legal-notice--checkbox {
  text-align: left;
  margin: 4px 0 16px;
}

.legal-checkbox {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  color: var(--color-label-secondary);
  font-size: 14px;
}

.legal-checkbox input {
  margin-top: 3px;
  flex-shrink: 0;
}
</style>
