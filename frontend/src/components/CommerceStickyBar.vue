<template>
  <div class="commerce-sticky-bar">
    <div class="commerce-sticky-bar__inner">
      <div v-if="$slots.info" class="commerce-sticky-bar__info">
        <slot name="info" />
      </div>
      <div class="commerce-sticky-bar__actions">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts"></script>
