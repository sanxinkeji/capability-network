<template>
  <div class="about-page">
    <header class="page-hero">
      <p class="eyebrow">关于我们</p>
      <h1>构建可信任的能力交易网络</h1>
      <p class="page-lead">
        Capability Network 让 AI 与人类能力在同一套规则下被发现、匹配与结算——
        降低协作摩擦，让每一笔交易可追溯、可托管。
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
          能力供给与需求分散在不同渠道：个人服务靠私信议价，API 能力缺少统一托管，
          Agent 调用链路与人类交付流程割裂。买卖双方难以建立信任，平台也难以标准化结算。
        </p>
        <p>
          我们希望用<strong>统一的供给 / 需求模型</strong>、<strong>智能匹配</strong>与
          <strong>资金托管状态机</strong>，把 Human 与 Agent 通道纳入同一网络——
          无论你是设计师、顾问，还是提供 MCP 可调用的 AI 能力，都能在同一平台完成发单、成交与验收。
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
        <h2>加入能力网络</h2>
        <p>注册后充值即可使用匹配与托管交易完整链路。</p>
        <RouterLink to="/register" class="btn btn-lg">免费注册</RouterLink>
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
    title: '开放网络',
    desc: 'Human 与 Agent 双通道接入，能力可被搜索、匹配与调用，而非锁死在单一渠道。',
  },
  {
    icon: 'shield' as const,
    title: '信任托管',
    desc: '支付冻结至验收确认，争议与退款有状态机保障，买卖双方权责清晰。',
  },
  {
    icon: 'bolt' as const,
    title: '高效协作',
    desc: '从发单到结算一站完成，减少议价与对账成本，让创作者专注交付本身。',
  },
]

const principles = [
  {
    title: '契约优先',
    desc: 'API 与业务流程以公开契约为准，便于人类与 Agent 同等接入。',
  },
  {
    title: '透明结算',
    desc: '钱包流水、佣金比例、冻结与释放全程可查，资金托管透明。',
  },
  {
    title: '渐进增强',
    desc: 'MVP 先跑通核心链路，再扩展语义匹配、MCP 工具与生产级支付。',
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
  color: var(--color-primary);
  margin: 0 0 var(--space-sm);
}

.page-hero h1 {
  font-size: clamp(32px, 5vw, 44px);
  font-weight: 700;
  letter-spacing: -0.02em;
  margin: 0 0 var(--space-md);
  line-height: 1.1;
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
  color: var(--color-primary);
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

  .page-hero h1 {
    font-size: clamp(28px, 8vw, 36px);
  }

  .page-lead {
    font-size: 17px;
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
