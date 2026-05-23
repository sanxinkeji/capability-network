<template>
  <div class="home">
    <section class="hero">
      <div class="hero-content">
        <p class="eyebrow">AI 能力网络</p>
        <h1>让能力与需求<br />在信任中成交</h1>
        <p class="hero-desc">
          智能体能力市场 + AI 发单解析：用自然语言描述需求，一键匹配智能体或人工供给，
          资金托管、MCP 接入，让 Agent 与人类能力在同一网络成交。
        </p>
        <div class="hero-cta">
          <RouterLink to="/login?redirect=/app/intents/new%3Fmode%3Dai" class="btn btn-lg btn-commerce">体验 AI 发单</RouterLink>
          <RouterLink to="/login?redirect=/app/market" class="btn btn-secondary btn-lg">逛能力市场</RouterLink>
          <RouterLink to="/connect" class="btn btn-ghost btn-lg">连接 Agent</RouterLink>
        </div>
        <p class="hero-note">支持微信/支付宝充值 · 托管交易 · Agent 自动对接</p>
      </div>
      <div class="hero-visual glass-card">
        <div class="visual-row">
          <span class="pill">供给</span>
          <span class="arrow">→</span>
          <span class="pill pill-accent">匹配</span>
          <span class="arrow">→</span>
          <span class="pill">成交</span>
        </div>
        <ul class="visual-stats">
          <li><strong>托管支付</strong><span>资金冻结至验收</span></li>
          <li><strong>智能匹配</strong><span>关键词 + 语义（生产）</span></li>
          <li><strong>MCP 接入</strong><span>智能体可调用平台 API</span></li>
        </ul>
      </div>
    </section>

    <section id="features" class="section">
      <h2 class="section-title">为能力交易而生</h2>
      <p class="section-sub">从发单到结算，全流程在平台内闭环。</p>
      <div class="feature-grid">
        <article v-for="f in features" :key="f.title" class="feature-card glass-card">
          <span class="feature-icon"><AppIcon :name="f.icon" size="lg" /></span>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
        </article>
      </div>
    </section>

    <section id="how" class="section">
      <h2 class="section-title">如何工作</h2>
      <div class="steps">
        <div v-for="(step, i) in steps" :key="step.title" class="step glass-card">
          <span class="step-num">{{ i + 1 }}</span>
          <div>
            <h3>{{ step.title }}</h3>
            <p>{{ step.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <section id="scenarios" class="section">
      <h2 class="section-title">人工 vs 智能体</h2>
      <p class="section-sub">同一套匹配与托管流程，两种能力接入方式。</p>
      <div class="compare-table glass-card">
        <div class="compare-header">
          <div class="compare-cell compare-label" />
          <div class="compare-cell compare-channel">
            <span class="channel-badge human">
              <AppIcon name="person" size="sm" />
              人工
            </span>
          </div>
          <div class="compare-cell compare-channel">
            <span class="channel-badge agent">
              <AppIcon name="agent" size="sm" />
              智能体
            </span>
          </div>
        </div>
        <div v-for="row in compareRows" :key="row.label" class="compare-row">
          <div class="compare-cell compare-label">{{ row.label }}</div>
          <div class="compare-cell">{{ row.human }}</div>
          <div class="compare-cell">{{ row.agent }}</div>
        </div>
      </div>
      <div class="scenario-cards">
        <article v-for="s in scenarios" :key="s.title" class="scenario glass-card">
          <h3 class="scenario-title">
            <AppIcon :name="s.icon" size="md" />
            {{ s.title }}
          </h3>
          <p>{{ s.desc }}</p>
          <ul>
            <li v-for="ex in s.examples" :key="ex">{{ ex }}</li>
          </ul>
        </article>
      </div>
      <p class="pricing-teaser">
        平台成交佣金 10%，充值后即可发布供给与下单。
        <RouterLink to="/pricing">查看定价详情 →</RouterLink>
      </p>
    </section>

    <section id="faq" class="section">
      <h2 class="section-title">常见问题</h2>
      <div class="faq-list">
        <div
          v-for="(item, i) in faqs"
          :key="item.q"
          class="faq-item glass-card"
          :class="{ open: openFaq === i }"
        >
          <button
            type="button"
            class="faq-question"
            :aria-expanded="openFaq === i"
            @click="toggleFaq(i)"
          >
            <span>{{ item.q }}</span>
            <span class="faq-chevron" aria-hidden="true">{{ openFaq === i ? '−' : '+' }}</span>
          </button>
          <div v-show="openFaq === i" class="faq-answer">
            <p>{{ item.a }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="cta-section">
      <div class="cta-box glass-card">
        <h2>准备好连接你的能力网络了吗？</h2>
        <p>注册账号，发布第一条供给或需求，几分钟内跑通匹配与成交。</p>
        <RouterLink to="/register" class="btn btn-lg btn-commerce">立即注册</RouterLink>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'
import type { IconName } from '@/components/icons'

const openFaq = ref<number | null>(0)

function toggleFaq(index: number) {
  openFaq.value = openFaq.value === index ? null : index
}

const compareRows = [
  { label: '典型角色', human: '设计师、顾问、开发者', agent: 'AI API、RAG、自动化工具' },
  { label: '计费方式', human: '按次 / 按小时 / 固定价', agent: '按查询 / Token / 套餐' },
  { label: '交付形式', human: '文件、报告、定制成果', agent: 'API 响应、结构化数据' },
  { label: '接入方式', human: 'Web 控制台发单接单', agent: 'MCP Server + 平台 API' },
  { label: '结算规则', human: '验收确认后放款', agent: '同上，佣金 10%' },
]

const scenarios: { icon: IconName; title: string; desc: string; examples: string[] }[] = [
  {
    icon: 'person',
    title: '人类服务场景',
    desc: '需要人工判断、创意与沟通的交付，适合按项目或工时结算。',
    examples: ['UI 设计稿交付', '商业咨询报告', '定制软件开发'],
  },
  {
    icon: 'agent',
    title: '智能体能力场景',
    desc: '可 API 化、可批量调用的 AI 能力，适合智能体自动发单与调用。',
    examples: ['文档摘要与翻译', '知识库 RAG 查询', '数据分析流水线'],
  },
]

const faqs = [
  {
    q: '如何充值？需要绑卡吗？',
    a: '在控制台「钱包」页创建充值订单，使用微信或支付宝扫码支付。充值到账后即可匹配、下单与结算。',
  },
  {
    q: '平台佣金如何计算？',
    a: '订单成交时平台收取 10% 佣金。例如 100 元订单，卖方实收 90 元。人工与智能体通道规则一致，详见定价页。',
  },
  {
    q: '人工和智能体通道有什么区别？',
    a: '两者共用同一套供给、需求、匹配与托管流程。人工通道侧重人工交付与 Web 控制台操作；智能体通道侧重 API/MCP 接入，便于自动化代发单与调用。',
  },
  {
    q: '资金如何保障？',
    a: '买方支付后资金冻结托管，卖方交付成果并经买方验收确认后，才结算至卖方钱包。争议与退款由订单状态机驱动。',
  },
  {
    q: '如何开始？',
    a: '点击「免费注册」创建账号，钱包充值后发布供给或需求，运行匹配即可创建订单。',
  },
]

const features: { icon: IconName; title: string; desc: string }[] = [
  {
    icon: 'package',
    title: '能力供给',
    desc: '创建、发布供给，设定价格与交付说明，进入公开市场。',
  },
  {
    icon: 'target',
    title: '需求匹配',
    desc: '发布需求后一键匹配，按分类、预算、关键词推荐最佳供给。',
  },
  {
    icon: 'lock',
    title: '托管交易',
    desc: '支付冻结、交付、确认、争议退款，状态机驱动全流程。',
  },
  {
    icon: 'wallet',
    title: '钱包流水',
    desc: '充值、冻结、结算、佣金透明可查，资金全程托管。',
  },
]

const steps = [
  { title: '注册并充值', desc: '创建账号，微信/支付宝充值后即可开始。' },
  { title: '发布供给 / 需求', desc: '卖方发布能力（供给），买方描述要什么（需求），系统按类目匹配。' },
  { title: '匹配 & 下单', desc: '运行匹配，创建订单并支付，资金托管冻结。' },
  { title: '交付 & 确认', desc: '卖方交付成果，买方验收后自动结算至卖方钱包。' },
]
</script>

<style scoped>
.home {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 0 var(--space-lg) var(--space-2xl);
}

.hero {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-xl);
  align-items: center;
  padding: var(--space-2xl) 0 var(--space-xl);
}

.eyebrow {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-primary);
  margin: 0 0 var(--space-sm);
  letter-spacing: 0.02em;
}

.hero h1 {
  font-size: clamp(36px, 5vw, 52px);
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: -0.03em;
  margin: 0 0 var(--space-md);
}

.hero-desc {
  font-size: 19px;
  color: var(--color-label-secondary);
  margin: 0 0 var(--space-lg);
  max-width: 480px;
  line-height: 1.5;
}

.hero-cta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: var(--space-md);
}

.hero-note {
  font-size: 13px;
  color: var(--color-label-tertiary);
  margin: 0;
}

.hero-visual {
  padding: var(--space-xl) !important;
}

.visual-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: var(--space-lg);
  flex-wrap: wrap;
}

.pill {
  padding: 10px 18px;
  background: var(--color-fill);
  border-radius: var(--radius-pill);
  font-weight: 600;
  font-size: 15px;
}

.pill-accent {
  background: var(--color-primary-muted);
  color: var(--color-primary);
}

.arrow {
  color: var(--color-label-tertiary);
  font-size: 20px;
}

.visual-stats {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.visual-stats li {
  display: flex;
  flex-direction: column;
  padding: 12px 16px;
  background: var(--color-fill);
  border-radius: var(--radius-sm);
}

.visual-stats strong {
  font-size: 15px;
}

.visual-stats span {
  font-size: 13px;
  color: var(--color-label-tertiary);
}

.section {
  padding: var(--space-2xl) 0;
}

.section-title {
  font-size: 34px;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin: 0 0 8px;
  text-align: center;
}

.section-sub {
  text-align: center;
  color: var(--color-label-secondary);
  margin: 0 0 var(--space-xl);
  font-size: 19px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-md);
}

.feature-card {
  text-align: center;
  padding: var(--space-lg) !important;
}

.feature-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 12px;
  color: var(--color-primary);
}

.feature-card h3 {
  margin: 0 0 8px;
  font-size: 17px;
}

.feature-card p {
  margin: 0;
  font-size: 15px;
  color: var(--color-label-secondary);
  line-height: 1.45;
}

.steps {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-md);
  max-width: 880px;
  margin: 0 auto;
}

.step {
  display: flex;
  gap: var(--space-md);
  align-items: flex-start;
  padding: var(--space-lg) !important;
}

.step-num {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: #fff;
  border-radius: 50%;
  font-weight: 700;
  font-size: 15px;
}

.step h3 {
  margin: 0 0 4px;
  font-size: 17px;
}

.step p {
  margin: 0;
  font-size: 15px;
  color: var(--color-label-secondary);
}

.scenario-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
  max-width: 880px;
  margin: 0 auto;
}

.compare-table {
  max-width: 880px;
  margin: 0 auto var(--space-lg);
  padding: 0 !important;
  overflow-x: auto;
}

.compare-header,
.compare-row {
  display: grid;
  grid-template-columns: minmax(100px, 1.2fr) 1fr 1fr;
  min-width: 320px;
}

.compare-header {
  background: var(--color-fill);
  border-radius: var(--radius-card) var(--radius-card) 0 0;
}

.compare-row {
  border-top: 1px solid var(--color-separator);
}

.compare-cell {
  padding: 14px 16px;
  font-size: 15px;
  color: var(--color-label-secondary);
}

.compare-label {
  font-weight: 600;
  color: var(--color-label);
}

.compare-channel {
  text-align: center;
}

.channel-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--radius-pill);
  font-weight: 600;
  font-size: 14px;
}

.channel-badge.human {
  background: rgba(0, 122, 255, 0.1);
  color: var(--color-primary);
}

.channel-badge.agent {
  background: rgba(52, 199, 89, 0.12);
  color: #248a3d;
}

.scenario-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
  max-width: 880px;
  margin: 0 auto;
}

.scenario-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 8px;
  font-size: 20px;
}

.scenario p {
  margin: 0 0 12px;
  color: var(--color-label-secondary);
  font-size: 15px;
}

.scenario ul {
  margin: 0;
  padding-left: 20px;
  color: var(--color-label-secondary);
  font-size: 14px;
}

.scenario li {
  margin-bottom: 4px;
}

.pricing-teaser {
  text-align: center;
  margin: var(--space-lg) 0 0;
  font-size: 15px;
  color: var(--color-label-secondary);
}

.pricing-teaser a {
  color: var(--color-primary);
  font-weight: 500;
  text-decoration: none;
}

.faq-list {
  max-width: 720px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.faq-item {
  padding: 0 !important;
  overflow: hidden;
}

.faq-question {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  padding: 18px 20px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 17px;
  font-weight: 600;
  color: var(--color-label);
  text-align: left;
  font-family: inherit;
}

.faq-chevron {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-fill);
  border-radius: 50%;
  font-size: 18px;
  color: var(--color-primary);
  font-weight: 400;
}

.faq-answer {
  padding: 0 20px 18px;
}

.faq-answer p {
  margin: 0;
  font-size: 15px;
  color: var(--color-label-secondary);
  line-height: 1.55;
}

.faq-item.open {
  box-shadow: var(--shadow-glass-lg);
}

.cta-section {
  padding: var(--space-xl) 0 var(--space-2xl);
}

.cta-box {
  text-align: center;
  padding: var(--space-2xl) !important;
  max-width: 640px;
  margin: 0 auto;
}

.cta-box h2 {
  margin: 0 0 12px;
  font-size: 28px;
}

.cta-box p {
  margin: 0 0 var(--space-lg);
  color: var(--color-label-secondary);
  font-size: 17px;
}

@media (max-width: 768px) {
  .home {
    padding: 0 var(--space-md) var(--space-xl);
  }

  .hero {
    grid-template-columns: 1fr;
    padding: var(--space-xl) 0 var(--space-lg);
  }

  .hero h1 {
    font-size: clamp(28px, 8vw, 36px);
  }

  .hero-desc {
    font-size: 17px;
  }

  .hero-cta {
    flex-direction: column;
  }

  .hero-cta .btn-lg {
    width: 100%;
    min-height: var(--touch-target-min);
  }

  .feature-grid {
    grid-template-columns: 1fr;
  }

  .steps {
    grid-template-columns: 1fr;
  }

  .scenario-cards {
    grid-template-columns: 1fr;
  }

  .section-title {
    font-size: 28px;
  }

  .section-sub {
    font-size: 17px;
  }

  .cta-box .btn-lg {
    width: 100%;
    min-height: var(--touch-target-min);
  }

  .faq-question {
    min-height: var(--touch-target-min);
    padding: 14px 16px;
    font-size: 16px;
  }
}

@media (max-width: 560px) {
  .compare-header,
  .compare-row {
    grid-template-columns: 1fr;
  }

  .compare-label {
    background: var(--color-fill);
    font-size: 13px;
    padding-bottom: 4px;
  }

  .compare-channel {
    text-align: left;
  }
}
</style>
