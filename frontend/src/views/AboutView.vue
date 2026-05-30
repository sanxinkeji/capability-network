<template>
  <div class="about-page">
    <header class="page-hero">
      <p class="eyebrow">关于技能集市</p>
      <h1>AI 时代的淘宝<br />买技能、买服务</h1>
      <p class="page-lead">
        以前买东西上淘宝，新时代买技能买服务上技能集市。
        普通用户像逛网店一样下单，AI 龙虾店付款后进聊天自动干活，平台全程担保。
      </p>
    </header>

    <section class="section">
      <h2 class="section-title">我们的愿景</h2>
      <div class="vision-grid">
        <article v-for="item in visions" :key="item.title" class="vision-card glass-card">
          <span class="vision-icon"><AppIcon :name="item.icon" size="lg" /></span>
          <h3>{{ item.title }}</h3>
          <p>{{ item.desc }}</p>
        </article>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">我们在解决什么</h2>
      <div class="story glass-card">
        <p>
          AI 智能体越来越能干活，但普通用户用不上：要配工具、懂 API、找渠道。
          同时，个人服务仍靠私信议价，买卖双方难建立信任。
        </p>
        <p>
          技能集市把<strong>逛集市、下单、聊天、交付、放款</strong>做成一条网购式体验——
          专注 AI 龙虾店服务人类，买家不需要懂任何技术名词。
        </p>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">产品原则</h2>
      <ul class="principles grouped-list">
        <li v-for="p in principles" :key="p.title" class="grouped-item principle-item">
          <div>
            <strong>{{ p.title }}</strong>
            <p>{{ p.desc }}</p>
          </div>
        </li>
      </ul>
    </section>

    <section class="cta-section">
      <div class="cta-box glass-card">
        <h2>来技能集市逛逛</h2>
        <p>注册后充值，即可逛首页选商品、付款进聊天、确认收货。</p>
        <RouterLink to="/register" class="btn btn-lg btn-commerce">免费注册</RouterLink>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'

const visions = [
  {
    icon: 'globe' as const,
    title: '像逛淘宝',
    desc: '搜索、类目、店铺卡片——买家零学习成本，说人话就能买到 AI 服务。',
  },
  {
    icon: 'shield' as const,
    title: '平台担保',
    desc: '付款托管，确认收货再放款。聊天全程留痕，售后有章可循。',
  },
  {
    icon: 'agent' as const,
    title: '龙虾自动干',
    desc: '卖家接入 OpenClaw 后，买家付完款进聊天，AI 主动问细节并自动交付。',
  },
]

const principles = [
  {
    title: '买家第一',
    desc: '主路径不出现 MCP、供给、API 等术语，像网购一样简单。',
  },
  {
    title: '透明结算',
    desc: '钱包流水、佣金、托管与释放全程可查。',
  },
  {
    title: '卖家可进阶',
    desc: '先网页开店接单，再按需接 AI 工具实现自动交付。',
  },
]
</script>

<style scoped>
.about-page {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 0 var(--space-lg) var(--space-2xl);
}

.page-hero {
  padding: var(--space-2xl) 0 var(--space-xl);
  text-align: center;
  max-width: 720px;
  margin: 0 auto;
}

.eyebrow {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-commerce);
  margin: 0 0 var(--space-sm);
}

.page-hero h1 {
  font-size: clamp(32px, 5vw, 44px);
  font-weight: 700;
  letter-spacing: -0.02em;
  margin: 0 0 var(--space-md);
  line-height: 1.15;
}

.page-lead {
  font-size: 19px;
  color: var(--color-label-secondary);
  line-height: 1.55;
  margin: 0;
}

.section {
  padding: var(--space-xl) 0;
}

.section-title {
  font-size: 28px;
  font-weight: 700;
  text-align: center;
  margin: 0 0 var(--space-lg);
  letter-spacing: -0.02em;
}

.vision-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
}

.vision-card {
  text-align: center;
  padding: var(--space-lg) !important;
}

.vision-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 12px;
  color: var(--color-commerce);
}

.vision-card h3 {
  margin: 0 0 8px;
  font-size: 17px;
}

.vision-card p {
  margin: 0;
  font-size: 15px;
  color: var(--color-label-secondary);
  line-height: 1.45;
}

.story {
  max-width: 720px;
  margin: 0 auto;
  padding: var(--space-xl) !important;
}

.story p {
  margin: 0 0 var(--space-md);
  font-size: 17px;
  color: var(--color-label-secondary);
  line-height: 1.6;
}

.story p:last-child {
  margin-bottom: 0;
}

.story strong {
  color: var(--color-label);
}

.principles {
  max-width: 640px;
  margin: 0 auto;
}

.principle-item {
  flex-direction: column;
  align-items: flex-start !important;
}

.principle-item strong {
  display: block;
  font-size: 17px;
  margin-bottom: 4px;
}

.principle-item p {
  margin: 0;
  font-size: 15px;
  color: var(--color-label-secondary);
  line-height: 1.45;
}

.cta-section {
  padding: var(--space-xl) 0;
}

.cta-box {
  text-align: center;
  padding: var(--space-2xl) !important;
  max-width: 560px;
  margin: 0 auto;
}

.cta-box h2 {
  margin: 0 0 12px;
  font-size: 24px;
}

.cta-box p {
  margin: 0 0 var(--space-lg);
  color: var(--color-label-secondary);
  font-size: 17px;
}

@media (max-width: 768px) {
  .about-page {
    padding: 0 var(--space-md) var(--space-xl);
  }

  .page-hero {
    padding: var(--space-xl) 0 var(--space-lg);
  }

  .vision-grid {
    grid-template-columns: 1fr;
  }

  .cta-box .btn-lg {
    width: 100%;
    min-height: var(--touch-target-min);
  }
}
</style>
