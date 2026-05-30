<template>
  <div class="shop-trust-strip" role="note">
    <span v-for="item in items" :key="item.text" class="shop-trust-strip__item">
      <strong>{{ item.icon }}</strong> {{ item.text }}
    </span>
  </div>
</template>

<script setup lang="ts">
const items = [
  { icon: '🦞', text: 'AI 龙虾自动服务' },
  { icon: '✓', text: '平台担保交易' },
  { icon: '✓', text: '确认收货放款' },
]
</script>
