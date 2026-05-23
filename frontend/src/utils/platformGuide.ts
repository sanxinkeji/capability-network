/** 平台核心流程说明（应用内复用） */
export const PLATFORM_TAGLINE =
  '能力网络：发布能力 → 发需求匹配 → 下单托管 → 验收放款'

export const PLATFORM_STEPS = [
  {
    key: 'market',
    label: '逛市场',
    desc: '浏览人工/智能体能力',
    to: '/app/market',
  },
  {
    key: 'intent',
    label: '发需求',
    desc: 'AI 描述要什么',
    to: '/app/intents/new?mode=ai',
  },
  {
    key: 'match',
    label: '匹配下单',
    desc: '选供给并创建订单',
    to: '/app/intents',
  },
  {
    key: 'wallet',
    label: '钱包充值',
    desc: '余额支付与托管',
    to: '/app/wallet',
  },
  {
    key: 'sell',
    label: '发布供给',
    desc: '卖方上架能力',
    to: '/app/offers',
  },
] as const

export const BUYER_FLOW_HINT =
  '买方路径：逛市场或发需求 → 匹配候选 → 下单支付（钱包扣款/冻结）→ 验收确认 → 卖方收款'

export const SELLER_FLOW_HINT =
  '卖方路径：发布供给 → 等待匹配/被选用 → 交付内容 → 买方确认后结算入账'

export const WALLET_FLOW_STEPS = [
  { label: '充值', desc: '微信/支付宝充值到可用余额' },
  { label: '下单', desc: '支付时从余额扣款，资金进入冻结' },
  { label: '验收', desc: '确认收货后放款给卖方（平台收取佣金）' },
  { label: '提现', desc: '卖方可将可用余额提现到账户' },
] as const

export const WALLET_TERMS = {
  frozen: '下单支付后，款项暂存平台托管账户，待验收后结算。',
  nonWithdrawable: '部分活动赠送或点数类资产不可提现，仅可用于平台消费。',
  commission: '平台按成交收取约 10% 佣金（以运营设置为准），其余结算给卖方。',
} as const

export const MARKET_BUY_HINT =
  '「立即选用」会帮你创建需求并进入匹配，不是直接付款。确认供给后才会从钱包扣款。'

export const MATCH_PAY_HINT =
  '点击后将创建订单并尝试从钱包支付。余额不足会进入待支付，请先到钱包充值。'

export const ONBOARDING_STORAGE_KEY = 'cn_onboarding_dismissed_v1'

export function formatAgentKeyStatus(status: string): string {
  const map: Record<string, string> = {
    active: '生效中',
    revoked: '已撤销',
    expired: '已过期',
  }
  return map[status] ?? status
}
