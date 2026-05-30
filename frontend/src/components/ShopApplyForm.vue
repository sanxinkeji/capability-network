<template>
  <form class="apply-form glass-card" @submit.prevent="handleSubmit">
    <div class="form-group">
      <label>店铺名称</label>
      <input v-model="shopName" required maxlength="100" placeholder="例如：龙虾论文写作店" />
    </div>
    <div class="form-group">
      <label>AI 接入平台</label>
      <select v-model="agentPlatform" required>
        <option value="openclaw">OpenClaw（龙虾）</option>
        <option value="hermes">Hermes</option>
        <option value="other">其他 AI Agent 平台</option>
      </select>
      <p class="form-hint">买家付款后，由接入的 AI 在聊天中自动沟通与交付</p>
    </div>
    <div class="form-group">
      <label>店铺介绍与主营技能</label>
      <textarea
        v-model="description"
        required
        rows="4"
        minlength="10"
        placeholder="说明您提供的 AI 服务类型、交付方式、典型商品…"
      />
    </div>
    <label class="apply-agree">
      <input v-model="agreed" type="checkbox" required />
      我已阅读并同意平台卖家入驻规范，所售服务由 AI 自动或半自动交付
    </label>
    <button class="btn btn-lg btn-commerce" type="submit" :disabled="submitting || !agreed">
      {{ submitting ? '提交中…' : '提交入驻申请' }}
    </button>
  </form>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  submit: [payload: { shop_name: string; agent_platform: 'openclaw' | 'hermes' | 'other'; description: string }]
}>()

const shopName = ref('')
const agentPlatform = ref<'openclaw' | 'hermes' | 'other'>('openclaw')
const description = ref('')
const agreed = ref(false)
const submitting = ref(false)

async function handleSubmit() {
  submitting.value = true
  try {
    emit('submit', {
      shop_name: shopName.value.trim(),
      agent_platform: agentPlatform.value,
      description: description.value.trim(),
    })
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.apply-form {
  padding: 20px !important;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--color-label-tertiary);
}

.apply-agree {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 12px 0 16px;
  font-size: 13px;
  color: var(--color-label-secondary);
  line-height: 1.45;
}

.apply-agree input {
  margin-top: 3px;
}
</style>
