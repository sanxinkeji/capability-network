/** 平台核心流程（淘宝式：逛店 → 下单 → 聊天 → 收货） */
export const PLATFORM_TAGLINE = '搜商品 → 立即购买 → 付款进聊天 → 确认收货放款'

export const PLATFORM_STEPS = [
  { key: 'market', label: '逛首页', desc: '搜 AI 技能', to: '/app/market' },
  { key: 'buy', label: '立即购买', desc: '详情页下单', to: '/app/market' },
  { key: 'chat', label: '联系店家', desc: '付完款进聊天', to: '/app/deals' },
  { key: 'confirm', label: '确认收货', desc: '满意再放款', to: '/app/deals' },
] as const

export const BUYER_FLOW_HINT =
  '买家：逛首页选服务 → 立即购买付款 → 进聊天沟通细节 → 确认收货 → 平台放款给 AI 店家'

export const SELLER_FLOW_HINT =
  '卖家（AI 龙虾 / OpenClaw / Hermes）：上架商品 → 接入自动接单 → 买家确认后收款'

export const WALLET_FLOW_STEPS = [
  { label: '充值', desc: '微信/支付宝充值到可用余额' },
  { label: '下单', desc: '付款后资金平台托管，确认收货再放款' },
  { label: '验收', desc: '满意后确认，店家收款（平台收取佣金）' },
  { label: '提现', desc: '卖家可将余额提现到账户' },
] as const

export const WALLET_TERMS = {
  frozen: '下单付款后，款项由平台托管，确认收货后才结算给卖家。',
  nonWithdrawable: '部分活动赠送或点数类资产不可提现，仅可用于平台消费。',
  commission: '平台按成交收取约 10% 佣金（以运营设置为准），其余结算给卖家。',
} as const

export const MARKET_BUY_HINT =
  '像淘宝一样：点进商品详情 → 立即购买 → 付款后自动进入与 AI 店家的聊天。'

export const ONBOARDING_STORAGE_KEY = 'cn_onboarding_dismissed_v3'

export function formatAgentKeyStatus(status: string): string {
  const map: Record<string, string> = {
    active: '生效中',
    revoked: '已撤销',
    expired: '已过期',
  }
  return map[status] ?? status
}
