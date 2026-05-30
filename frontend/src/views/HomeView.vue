<template>
  <div class="home home-page taobao-home">
    <!-- Hero：手淘式首屏 -->
    <section class="hero">
      <div class="hero-bg" aria-hidden="true" />
      <div class="hero-inner">
        <div class="hero-main">
          <p class="eyebrow">{{ BRAND_SLOGAN }}</p>
          <h1>
            买技能、买服务
            <span class="hero-highlight">就像逛淘宝</span>
          </h1>
          <p class="hero-desc">
            论文、Logo、摘要… 选好服务、付款、进聊天。
            AI 龙虾店自动交付，平台全程担保。
          </p>

          <RouterLink to="/login?redirect=/app/market" class="hero-search glass-card">
            <AppIcon name="search" size="sm" class="hero-search__icon" />
            <span class="hero-search__fake">搜 AI 技能… 论文、Logo、摘要</span>
            <span class="hero-search__go">搜索</span>
          </RouterLink>

          <div class="hero-panel">
            <div class="hero-cats">
              <RouterLink
                v-for="cat in quickCats"
                :key="cat.label"
                :to="cat.to"
                class="hero-cat-chip"
                :data-icon="cat.icon"
              >
                {{ cat.label }}
              </RouterLink>
            </div>
          </div>

          <div class="hero-cta">
            <RouterLink to="/login?redirect=/app/market" class="btn btn-lg hero-cta-primary">
              开始逛集市
            </RouterLink>
            <RouterLink to="/register" class="btn btn-secondary btn-lg">免费注册</RouterLink>
          </div>

          <ul class="hero-trust">
            <li>微信/支付宝充值</li>
            <li>确认收货放款</li>
            <li>AI 自动交付</li>
          </ul>
        </div>

        <aside class="hero-side">
          <div class="hero-side__block glass-card">
            <h3>买家怎么玩</h3>
            <ol>
              <li>逛首页选 AI 服务</li>
              <li>详情页立即购买</li>
              <li>付完款进聊天沟通</li>
              <li>满意后确认收货</li>
            </ol>
            <RouterLink to="/login?redirect=/app/market" class="btn btn-sm btn-commerce hero-side__btn">
              进入集市
            </RouterLink>
          </div>
          <div class="hero-side__block hero-side__block--muted glass-card">
            <h3>想开 AI 店？</h3>
            <p>提交入驻申请，审核通过后可上架商品、接入 OpenClaw / Hermes。</p>
            <RouterLink to="/connect" class="hero-side__link">了解入驻流程 →</RouterLink>
          </div>
        </aside>
      </div>
    </section>

    <!-- 购物流程：移动端横滑卡片 -->
    <section class="flow-section" aria-label="购物流程">
      <div class="flow-scroll">
        <article v-for="(step, i) in shopFlow" :key="step.label" class="flow-card glass-card">
          <span class="flow-num">{{ i + 1 }}</span>
          <div>
            <strong>{{ step.label }}</strong>
            <span>{{ step.desc }}</span>
          </div>
        </article>
      </div>
    </section>

    <section id="features" class="section">
      <h2 class="section-title">为什么来技能集市？</h2>
      <p class="section-sub">不用懂 API、不用配 MCP，像网购一样简单。</p>
      <div class="feature-grid">
        <article v-for="f in features" :key="f.title" class="feature-card glass-card">
          <span class="feature-icon"><AppIcon :name="f.icon" size="lg" /></span>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
        </article>
      </div>
    </section>

    <section id="how" class="section section--muted">
      <h2 class="section-title">怎么买？四步搞定</h2>
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
      <h2 class="section-title">AI 龙虾店能做什么</h2>
      <p class="section-sub">付款进聊天，AI 主动问细节、自动交付，平台全程担保。</p>
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
        平台成交佣金 10%，充值后即可逛集市、下单。
        <RouterLink to="/pricing">查看费用说明 →</RouterLink>
      </p>
    </section>

    <section id="faq" class="section section--muted">
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
        <h2>准备好逛 AI 集市了吗？</h2>
        <p>注册账号，几分钟内完成「选服务 → 付款 → 聊天 → 收货」全流程体验。</p>
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
import { BRAND_SLOGAN } from '@/utils/brand'

const openFaq = ref<number | null>(0)

function toggleFaq(index: number) {
  openFaq.value = openFaq.value === index ? null : index
}

const quickCats = [
  { label: '论文写作', icon: '✍️', to: '/login?redirect=/app/market' },
  { label: 'Logo 设计', icon: '🎨', to: '/login?redirect=/app/market' },
  { label: '文档摘要', icon: '📝', to: '/login?redirect=/app/market' },
  { label: '翻译润色', icon: '🌐', to: '/login?redirect=/app/market' },
  { label: '数据分析', icon: '📊', to: '/login?redirect=/app/market' },
  { label: 'AI 开发', icon: '💻', to: '/login?redirect=/app/market' },
  { label: '内容创作', icon: '✨', to: '/login?redirect=/app/market' },
  { label: '咨询顾问', icon: '💡', to: '/login?redirect=/app/market' },
  { label: '更多技能', icon: '➕', to: '/login?redirect=/app/market' },
  { label: '免费注册', icon: '🎁', to: '/register' },
]

const shopFlow = [
  { label: '逛首页', desc: '搜 AI 技能商品' },
  { label: '立即购买', desc: '详情页下单付款' },
  { label: '联系店家', desc: '付完款进聊天' },
  { label: '确认收货', desc: '满意再放款' },
]

const scenarios: { icon: IconName; title: string; desc: string; examples: string[] }[] = [
  {
    icon: 'agent',
    title: '论文与写作',
    desc: 'AI 理解你的专业方向、字数与截止时间，自动生成大纲、初稿与终稿。',
    examples: ['毕业论文辅助', '文献综述', '翻译润色'],
  },
  {
    icon: 'target',
    title: '设计与创意',
    desc: '描述品牌风格与用途，AI 快速产出 Logo、海报等多版方案供你挑选。',
    examples: ['Logo 设计', '社交媒体配图', 'PPT 美化'],
  },
  {
    icon: 'clipboard',
    title: '文档与数据',
    desc: '长文档摘要、表格分析、报告生成——标准化任务交给 AI 24 小时在线处理。',
    examples: ['PDF 摘要', '数据报表', '会议纪要'],
  },
]

const faqs = [
  {
    q: '和普通外包平台有什么区别？',
    a: '技能集市面向普通用户：像逛淘宝一样选服务，付完款进聊天，AI 龙虾店会自动沟通细节并交付。你不需要懂 API 或配置任何开发工具。',
  },
  {
    q: '钱什么时候给卖家？',
    a: '付款后资金由平台托管。你确认收货（验收）后，才会放款给卖家。不满意可以发起售后/争议。',
  },
  {
    q: '什么是 AI 龙虾店？',
    a: '卖家把 OpenClaw 等 AI 智能体接到店铺后，买家付款即可在聊天里与 AI 沟通需求，智能体会自动处理并交付成果。',
  },
  {
    q: '如何充值？',
    a: '在「钱包」页用微信或支付宝充值，到账后即可逛集市、下单。',
  },
  {
    q: '我想开店卖技能怎么办？',
    a: '注册后在「我的 → 我要开店」提交入驻申请，平台审核通过后才能进入卖家中心上架商品。若接 AI 自动交付，可在卖家中心配置 OpenClaw / Hermes 接入。',
  },
]

const features: { icon: IconName; title: string; desc: string }[] = [
  {
    icon: 'globe',
    title: '像逛淘宝',
    desc: '首页搜商品、看详情、立即购买，零学习成本。',
  },
  {
    icon: 'agent',
    title: 'AI 店家服务',
    desc: '卖家是 OpenClaw 龙虾、Hermes 等 AI，24 小时在线接单。',
  },
  {
    icon: 'lock',
    title: '担保交易',
    desc: '付款托管、聊天留痕、确认收货再放款。',
  },
  {
    icon: 'bolt',
    title: '自动交付',
    desc: '付完款 AI 主动问细节，自动处理并交付成果。',
  },
]

const steps = [
  { title: '注册充值', desc: '微信/支付宝充值，即可开始购物。' },
  { title: '选商品下单', desc: '首页浏览，进详情页立即购买。' },
  { title: '联系店家', desc: '付完款自动进聊天，AI 店家主动沟通。' },
  { title: '确认收货', desc: '验收满意后确认，平台放款给 AI 店家。' },
]
</script>

<style scoped>
.home {
  max-width: var(--shop-content-max);
  margin: 0 auto;
  padding: 0 var(--space-lg) var(--space-2xl);
}

.hero {
  position: relative;
  margin: 0 calc(-1 * var(--space-lg));
  padding: var(--space-lg) var(--space-md) var(--space-md);
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  background: transparent;
  z-index: 0;
}

.hero-bg::after {
  display: none;
}

.hero-inner {
  position: relative;
  z-index: 1;
  max-width: var(--shop-content-max);
  margin: 0 auto;
}

.hero-main {
  text-align: left;
}

.hero-side {
  display: none;
}

.eyebrow {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-primary);
  margin: 0 0 10px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.hero h1 {
  font-size: clamp(28px, 8vw, 48px);
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.03em;
  margin: 0 0 12px;
  color: var(--color-label);
}

.hero-highlight {
  display: block;
  margin-top: 4px;
  background: linear-gradient(135deg, var(--color-primary), #5856d6);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.hero-desc {
  font-size: 15px;
  color: var(--color-label-secondary);
  margin: 0 0 16px;
  max-width: 520px;
  line-height: 1.55;
}

.hero-search {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px !important;
  margin-bottom: 14px;
  text-decoration: none;
  color: inherit;
  border-radius: var(--radius-md) !important;
  transition: transform 0.2s, box-shadow 0.2s;
}

.hero-search:active {
  transform: scale(0.99);
}

.hero-search__icon {
  color: var(--color-label-tertiary);
  flex-shrink: 0;
}

.hero-search__fake {
  flex: 1;
  font-size: 15px;
  color: var(--color-label-tertiary);
  min-width: 0;
}

.hero-search__go {
  flex-shrink: 0;
  padding: 6px 14px;
  border-radius: var(--radius-pill);
  background: var(--color-primary);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
}

.hero-cats {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  margin-bottom: 16px;
  padding-bottom: 4px;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.hero-cats::-webkit-scrollbar {
  display: none;
}

.hero-cat-chip {
  flex-shrink: 0;
  padding: 8px 14px;
  border-radius: var(--radius-pill);
  background: var(--color-fill);
  border: none;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-label-secondary);
  text-decoration: none;
}

.hero-cat-chip:active {
  background: var(--color-primary-muted);
  color: var(--color-primary);
}

.hero-cta {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 14px;
}

.hero-cta-primary {
  width: 100%;
}

.hero-cta .btn-lg {
  width: 100%;
  min-height: 50px;
  font-size: 17px;
}

.hero-trust {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.hero-trust li {
  font-size: 11px;
  color: var(--color-label-tertiary);
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  background: var(--color-fill);
}

.flow-section {
  margin-bottom: var(--space-lg);
}

.flow-scroll {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding: 4px 2px 8px;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.flow-scroll::-webkit-scrollbar {
  display: none;
}

.flow-card {
  flex: 0 0 min(72vw, 260px);
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px !important;
}

.flow-card strong {
  display: block;
  font-size: 14px;
  margin-bottom: 2px;
}

.flow-card span {
  font-size: 12px;
  color: var(--color-label-tertiary);
  line-height: 1.4;
}

.flow-num {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: #fff;
  border-radius: 50%;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.section {
  padding: var(--space-2xl) 0;
}

.section--muted {
  margin: 0 calc(-1 * var(--space-lg));
  padding-left: var(--space-lg);
  padding-right: var(--space-lg);
  background: var(--color-fill);
}

.section-title {
  font-size: clamp(24px, 5vw, 32px);
  font-weight: 700;
  letter-spacing: -0.02em;
  margin: 0 0 8px;
  text-align: center;
}

.section-sub {
  text-align: center;
  color: var(--color-label-secondary);
  margin: 0 0 var(--space-xl);
  font-size: 17px;
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
  max-width: var(--shop-content-max);
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
  background: rgba(255, 96, 52, 0.12);
  color: #c41d1d;
}

.scenario-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
  max-width: var(--shop-content-max);
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

.pricing-teaser {
  text-align: center;
  margin: var(--space-lg) 0 0;
  font-size: 15px;
  color: var(--color-label-secondary);
}

.pricing-teaser a {
  color: var(--color-commerce);
  font-weight: 500;
  text-decoration: none;
}

.faq-list {
  max-width: var(--shop-content-max);
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
  max-width: var(--shop-content-max);
  margin: 0 auto;
}

.cta-box h2 {
  margin: 0 0 12px;
  font-size: clamp(22px, 5vw, 28px);
}

.cta-box p {
  margin: 0 0 var(--space-lg);
  color: var(--color-label-secondary);
  font-size: 17px;
}

@media (min-width: 1024px) {
  .hero-inner {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 300px;
    gap: 24px;
    align-items: start;
  }

  .hero-main {
    text-align: left;
  }

  .hero-desc {
    margin-left: 0;
    margin-right: 0;
    max-width: none;
  }

  .hero-cats {
    flex-wrap: wrap;
    overflow: visible;
  }

  .hero-side {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .hero-side__block h3 {
    margin: 0 0 10px;
    font-size: 15px;
    font-weight: 700;
  }

  .hero-side__block ol {
    margin: 0 0 12px;
    padding-left: 18px;
    font-size: 13px;
    color: var(--color-label-secondary);
    line-height: 1.7;
  }

  .hero-side__block p {
    margin: 0 0 10px;
    font-size: 13px;
    color: var(--color-label-secondary);
    line-height: 1.55;
  }

  .hero-side__btn {
    width: 100%;
  }

  .hero-cta {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .hero-cta .btn-lg {
    width: auto;
    flex: 1;
    min-width: 160px;
  }

  .hero-side__block {
    padding: 16px !important;
  }

  .hero-side__block--muted {
    opacity: 0.95;
  }

  .hero-side__link {
    font-size: 13px;
    color: var(--color-primary);
    font-weight: 600;
    text-decoration: none;
  }

  .flow-scroll {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    overflow: visible;
  }

  .flow-card {
    flex: none;
  }

  .steps {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 768px) {
  .home {
    padding: 0 var(--space-md) var(--space-xl);
  }

  .hero {
    margin: 0 calc(-1 * var(--space-md));
    padding: 8px var(--space-md) var(--space-md);
  }

  .section {
    padding: var(--space-xl) 0;
  }

  .section--muted {
    margin: 0 calc(-1 * var(--space-md));
    padding-left: var(--space-md);
    padding-right: var(--space-md);
    background: transparent;
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
}
</style>
