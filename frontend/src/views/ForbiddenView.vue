<template>
  <div class="forbidden-page">
    <div class="mesh-bg" aria-hidden="true" />
    <div class="forbidden-card glass-card">
      <h1>403</h1>
      <p>无权访问运营后台</p>
      <RouterLink to="/app" class="btn">返回控制台</RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<style scoped>
.forbidden-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.forbidden-card {
  text-align: center;
  padding: 40px;
  max-width: 400px;
}

.forbidden-card h1 {
  font-size: 48px;
  margin: 0 0 8px;
  color: var(--color-label);
}

.forbidden-card p {
  color: var(--color-label-secondary);
  margin: 0 0 24px;
}
</style>
