<template>
  <div class="pricing-page">
    <header class="page-hero">
      <p class="eyebrow">定价说明</p>
      <h1>简单透明，按成交计费</h1>
      <p class="page-lead">
        无订阅费，支持微信/支付宝充值。平台仅在订单成交时收取
        <strong class="highlight">10% 佣金</strong>，所有 AI 龙虾店统一规则。
      </p>
    </header>

    <section class="section">
      <div class="pricing-highlight glass-card">
        <div class="price-main">
          <span class="price-value">10%</span>
          <span class="price-label">成交佣金</span>
        </div>
        <ul class="price-features">
          <li>无月费 / 无开户费</li>
          <li>微信 / 支付宝充值</li>
          <li>托管支付冻结至买方验收</li>
          <li>钱包流水完整可查</li>
        </ul>
        <RouterLink to="/register" class="btn btn-lg">免费开始</RouterLink>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">AI 龙虾店怎么收费</h2>
      <p class="section-sub">按次 / 套餐计费，下单、聊天、放款流程统一透明。</p>
      <div class="channel-grid">
        <article v-for="ch in channels" :key="ch.name" class="channel-card glass-card">
          <div class="channel-header">
            <AppIcon :name="ch.icon" size="md" class="channel-icon" />
            <h3>{{ ch.name }}</h3>
          </div>
          <p class="channel-desc">{{ ch.desc }}</p>
          <ul class="channel-details">
            <li v-for="d in ch.details" :key="d">
              <span class="check">✓</span>
              {{ d }}
            </li>
          </ul>
        </article>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">费用示例</h2>
      <div class="example-table glass-card">
        <table>
          <thead>
            <tr>
              <th>订单金额</th>
              <th>平台佣金 (10%)</th>
              <th>卖方实收</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in examples" :key="row.amount">
              <td>¥{{ row.amount }}</td>
              <td>¥{{ row.fee }}</td>
              <td class="receive">¥{{ row.receive }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="table-note">以上为示意计算，实际以订单确认时的钱包流水为准。</p>
    </section>

    <section class="section">
      <h2 class="section-title">充值与提现</h2>
      <div class="mock-info glass-card">
        <p>
          注册后在控制台「钱包」页创建充值订单，使用<strong>微信或支付宝</strong>扫码支付。
          余额用于下单托管，卖方验收后结算至钱包。
        </p>
        <p>
          提现需提交收款账号，平台审核后 1–3 个工作日内打款。最低提现 ¥100。
        </p>
      </div>
    </section>

    <section class="faq-link glass-card">
      <p>还有疑问？查看首页 <RouterLink to="/#faq">常见问题</RouterLink>，或阅读<RouterLink to="/about">关于我们</RouterLink>。</p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'

const channels = [
  {
    icon: 'agent' as const,
    name: 'AI 龙虾店',
    desc: '接入 OpenClaw 等 AI 工具，付完款进聊天，自动问细节并交付成果。',
    details: [
      '按次 / 套餐计费',
      '付款后进聊天沟通',
      'AI 自动处理并交付',
      '适合论文、摘要、Logo 生成等',
    ],
  },
]

const examples = [
  { amount: 100, fee: 10, receive: 90 },
  { amount: 500, fee: 50, receive: 450 },
  { amount: 2000, fee: 200, receive: 1800 },
]
</script>

<style scoped>
.pricing-page {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 0 var(--space-lg) var(--space-2xl);
}

.page-hero {
  padding: var(--space-2xl) 0 var(--space-xl);
  text-align: center;
  max-width: 640px;
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
}

.page-lead {
  font-size: 19px;
  color: var(--color-label-secondary);
  line-height: 1.55;
  margin: 0;
}

.highlight {
  color: var(--color-primary);
}

.section {
  padding: var(--space-lg) 0;
}

.section-title {
  font-size: 28px;
  font-weight: 700;
  text-align: center;
  margin: 0 0 8px;
}

.section-sub {
  text-align: center;
  color: var(--color-label-secondary);
  margin: 0 0 var(--space-lg);
  font-size: 17px;
}

.pricing-highlight {
  max-width: 480px;
  margin: 0 auto;
  text-align: center;
  padding: var(--space-2xl) !important;
}

.price-main {
  margin-bottom: var(--space-lg);
}

.price-value {
  display: block;
  font-size: 56px;
  font-weight: 700;
  color: var(--color-primary);
  letter-spacing: -0.03em;
  line-height: 1;
}

.price-label {
  font-size: 17px;
  color: var(--color-label-secondary);
}

.price-features {
  list-style: none;
  margin: 0 0 var(--space-lg);
  padding: 0;
  text-align: left;
}

.price-features li {
  padding: 10px 0;
  border-bottom: 1px solid var(--color-separator);
  font-size: 15px;
  color: var(--color-label-secondary);
}

.price-features li:last-child {
  border-bottom: none;
}

.channel-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
  max-width: 880px;
  margin: 0 auto;
}

.channel-card {
  padding: var(--space-lg) !important;
}

.channel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.channel-icon {
  display: flex;
  color: var(--color-primary);
}

.channel-header h3 {
  margin: 0;
  font-size: 20px;
}

.channel-desc {
  margin: 0 0 var(--space-md);
  font-size: 15px;
  color: var(--color-label-secondary);
  line-height: 1.45;
}

.channel-details {
  list-style: none;
  margin: 0;
  padding: 0;
}

.channel-details li {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  padding: 8px 0;
  font-size: 15px;
  color: var(--color-label-secondary);
}

.check {
  color: var(--color-success);
  font-weight: 700;
  flex-shrink: 0;
}

.example-table {
  max-width: 560px;
  margin: 0 auto;
  padding: 0 !important;
  overflow-x: auto;
}

.example-table table {
  width: 100%;
  min-width: 320px;
}

.receive {
  font-weight: 600;
  color: var(--color-success);
}

.table-note {
  text-align: center;
  font-size: 13px;
  color: var(--color-label-tertiary);
  margin: var(--space-md) 0 0;
}

.mock-info {
  max-width: 640px;
  margin: 0 auto;
  padding: var(--space-xl) !important;
}

.mock-info p {
  margin: 0 0 var(--space-md);
  font-size: 17px;
  color: var(--color-label-secondary);
  line-height: 1.55;
}

.mock-info p:last-child {
  margin-bottom: 0;
}

.mock-info strong {
  color: var(--color-label);
}

.faq-link {
  max-width: 640px;
  margin: var(--space-xl) auto 0;
  text-align: center;
  padding: var(--space-lg) !important;
}

.faq-link p {
  margin: 0;
  font-size: 15px;
  color: var(--color-label-secondary);
}

.faq-link a {
  color: var(--color-primary);
  font-weight: 500;
}

@media (max-width: 768px) {
  .pricing-page {
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

  .channel-grid {
    grid-template-columns: 1fr;
  }

  .pricing-highlight .btn-lg {
    width: 100%;
    min-height: var(--touch-target-min);
  }
}
</style>
