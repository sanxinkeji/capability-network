export const TOKEN_KEY = 'cn_access_token'
export const REFRESH_TOKEN_KEY = 'cn_refresh_token'
export const DEAL_IDS_KEY = 'cn_deal_ids'

export function isMockEnabled(): boolean {
  return import.meta.env.VITE_USE_MOCK === 'true'
}

/** MCP 客户端直连后端的根地址（不含 /api/v1） */
export function resolveBackendUrl(): string {
  const env = import.meta.env.VITE_API_URL as string | undefined
  if (env?.startsWith('http://') || env?.startsWith('https://')) {
    return env.replace(/\/api\/v1\/?$/, '')
  }
  if (env?.startsWith('/')) {
    if (import.meta.env.DEV) return 'http://127.0.0.1:8000'
    if (typeof window !== 'undefined') return window.location.origin
  }
  if (typeof window !== 'undefined' && !import.meta.env.DEV) {
    return window.location.origin
  }
  return 'http://127.0.0.1:8000'
}

export function formatCents(cents: number, currency = 'CNY'): string {
  const amount = (cents / 100).toFixed(2)
  return currency === 'CNY' ? `¥${amount}` : `${amount} ${currency}`
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN')
}

export function statusLabel(status: string): string {
  const map: Record<string, string> = {
    draft: '草稿',
    published: '已发布',
    paused: '已暂停',
    open: '开放',
    matching: '匹配中',
    matched: '已匹配',
    closed: '已关闭',
    pending: '待付款',
    paid: '待发货',
    in_progress: '待发货',
    delivered: '待收货',
    completed: '交易成功',
    disputed: '退款/售后',
    refunded: '已退款',
    cancelled: '交易关闭',
  }
  return map[status] ?? status
}

/** 买家订单列表状态（淘宝用语） */
export function buyerDealStatusLabel(status: string): string {
  return statusLabel(status)
}

export type DealViewerRole = 'buyer' | 'seller' | 'other'

export function dealShortId(id: string): string {
  return id.slice(0, 8).toUpperCase()
}

export function dealOrderTitle(deal: { offer_id: string }): string {
  return `能力服务 #${dealShortId(deal.offer_id)}`
}

export function dealTabKey(status: string): string {
  if (status === 'pending') return 'pending'
  if (status === 'paid' || status === 'in_progress') return 'active'
  if (status === 'delivered') return 'delivered'
  if (status === 'completed' || status === 'refunded' || status === 'cancelled') return 'done'
  if (status === 'disputed') return 'dispute'
  return 'all'
}

export function dealStatusBannerTone(status: string): 'warn' | 'info' | 'done' | 'danger' {
  if (status === 'pending') return 'warn'
  if (status === 'in_progress' || status === 'paid') return 'info'
  if (status === 'delivered') return 'warn'
  if (status === 'completed') return 'done'
  if (status === 'disputed') return 'danger'
  return 'info'
}

export function dealStatusHint(status: string, role: DealViewerRole): string {
  const hints: Record<string, Record<DealViewerRole, string>> = {
    pending: {
      buyer: '请尽快完成支付，支付后卖方将开始交付',
      seller: '等待买方付款，付款后将自动进入交付阶段',
      other: '订单待支付',
    },
    paid: {
      buyer: '支付成功，卖方正在准备交付',
      seller: '买方已付款，请尽快开始交付',
      other: '订单已支付',
    },
    in_progress: {
      buyer: '卖方正在交付中，请耐心等待',
      seller: '请提交交付内容，买方确认后完成交易',
      other: '订单进行中',
    },
    delivered: {
      buyer: '卖方已交付，请验收后确认收货',
      seller: '已提交交付，等待买方确认收货',
      other: '订单待确认',
    },
    completed: {
      buyer: '交易已完成，感谢使用',
      seller: '交易已完成，款项已结算',
      other: '订单已完成',
    },
    disputed: {
      buyer: '争议处理中，平台将介入仲裁',
      seller: '争议处理中，平台将介入仲裁',
      other: '订单争议中',
    },
    refunded: {
      buyer: '订单已退款',
      seller: '订单已退款',
      other: '订单已退款',
    },
    cancelled: {
      buyer: '订单已取消',
      seller: '订单已取消',
      other: '订单已取消',
    },
  }
  return hints[status]?.[role] ?? statusLabel(status)
}

export function dealListActionLabel(
  status: string,
  role: DealViewerRole,
): string | null {
  if (role === 'buyer' && status === 'pending') return '去付款'
  if (role === 'buyer' && status === 'delivered') return '确认收货'
  if (role === 'buyer' && (status === 'paid' || status === 'in_progress')) return '联系店家'
  if (role === 'seller' && (status === 'in_progress' || status === 'paid')) return '去交付'
  return null
}

/** 业务分类（API 存英文 key，界面显示中文） */
export const CATEGORY_OPTIONS = [
  { value: 'design', label: '设计' },
  { value: 'data', label: '数据' },
  { value: 'dev', label: '开发' },
  { value: 'content', label: '内容' },
  { value: 'writing', label: '写作' },
  { value: 'consulting', label: '咨询' },
  { value: 'ai', label: 'AI 技能' },
] as const

export function categoryLabel(category: string): string {
  const found = CATEGORY_OPTIONS.find((c) => c.value === category)
  return found?.label ?? category
}

export function channelLabel(channel: string): string {
  const map: Record<string, string> = {
    agent: 'AI 龙虾店',
    human: 'AI 龙虾店',
  }
  return map[channel] ?? 'AI 龙虾店'
}

/** 将 AI 解析返回的 category 映射为平台标准 key */
export function normalizeParsedCategory(category: string): string {
  const map: Record<string, string> = {
    development: 'dev',
    general: 'design',
    writing: 'content',
  }
  return map[category] ?? category
}

const KEYWORD_HINTS = ['logo', '设计', '品牌', 'ui', 'ux', 'api', '数据', '文案', '翻译', '开发', '分析']

/** 匹配页推荐理由文案 */
export function recommendReason(
  candidate: {
    title: string
    description: string
    category: string
    channel: string
    match_score: number
    recommend_auto: boolean
    score_breakdown?: Record<string, number | boolean>
  },
  intent?: { title: string; description: string; category: string; budget_max: number } | null,
): string {
  const parts: string[] = []

  if (intent && candidate.category === intent.category) {
    parts.push('类目一致')
  }

  const keywordHit = extractKeywordHit(intent, candidate)
  if (keywordHit) {
    parts.push(`关键词命中 ${keywordHit}`)
  } else if (
    typeof candidate.score_breakdown?.alignment === 'number' &&
    candidate.score_breakdown.alignment > 0.2
  ) {
    parts.push('关键词相关')
  }

  const priceScore = candidate.score_breakdown?.price
  if (typeof priceScore === 'number' && priceScore >= 0.5) {
    parts.push('价格在预算内')
  } else if (intent && candidate.match_score > 0) {
    parts.push('价格在预算内')
  }

  parts.push(`综合匹配 ${(candidate.match_score * 100).toFixed(0)}%`)

  let reason = `推荐因为：${parts.join('、')}`
  if (candidate.recommend_auto) {
    reason += '，适合 Agent 自动调用'
  }
  return reason
}

function extractKeywordHit(
  intent: { title: string; description: string } | null | undefined,
  candidate: { title: string; description: string },
): string | null {
  if (!intent) return null
  const intentText = `${intent.title} ${intent.description}`.toLowerCase()
  const offerText = `${candidate.title} ${candidate.description}`.toLowerCase()

  for (const kw of KEYWORD_HINTS) {
    if (intentText.includes(kw.toLowerCase()) && offerText.includes(kw.toLowerCase())) {
      return kw === 'logo' ? 'Logo/设计' : kw
    }
  }
  return null
}

export function billingModelLabel(model: string): string {
  const map: Record<string, string> = {
    per_use: '按次',
    per_query: '按查询',
    per_hour: '按小时',
  }
  return map[model] ?? model
}

/** 钱包流水类型（与 backend LedgerEntryType 对齐） */
export function ledgerTypeLabel(entryType: string): string {
  const map: Record<string, string> = {
    deposit: '充值',
    withdraw: '提现',
    freeze: '冻结',
    unfreeze: '解冻',
    payment: '结算',
    refund: '退款',
    fee: '佣金',
    points_credit: '点数入账',
    points_debit: '点数扣减',
  }
  return map[entryType] ?? entryType
}

const UUID_RE =
  /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi

/** 钱包流水说明（解析后端固定英文句式，无法解析时去掉 UUID） */
export function ledgerDescriptionLabel(
  description: string | null | undefined,
): string | null {
  if (!description?.trim()) return null

  const d = description.trim()

  if (/^deposit\b/i.test(d)) return '账户充值'
  if (/^withdraw request\b/i.test(d)) return '提现申请'
  if (/^withdraw\b/i.test(d) && /rejected refund/i.test(d)) return '提现驳回退款'
  if (/^points credit$/i.test(d)) return '点数入账'

  if (/^freeze deal .+ points portion$/i.test(d)) return '订单冻结（点数部分）'
  if (/^freeze deal .+ available portion$/i.test(d)) return '订单冻结（余额部分）'
  if (/^unfreeze deal .+ points portion$/i.test(d)) return '订单解冻（点数部分）'
  if (/^unfreeze deal .+ available portion$/i.test(d)) return '订单解冻（余额部分）'

  if (/^settle deal .+ payment$/i.test(d)) return '订单结算付款'
  if (/^settle deal .+ commission \d+ cents$/i.test(d)) return '订单结算佣金'
  if (/^settle deal .+ net after \d+ fee$/i.test(d)) return '订单结算入账'

  if (/[\u4e00-\u9fff]/.test(d)) return d

  const stripped = d.replace(UUID_RE, '').replace(/\s+/g, ' ').trim()
  return stripped.length > 0 ? stripped : null
}

export function getStoredDealIds(): string[] {
  try {
    const raw = localStorage.getItem(DEAL_IDS_KEY)
    return raw ? (JSON.parse(raw) as string[]) : []
  } catch {
    return []
  }
}

export function addStoredDealId(id: string): void {
  const ids = getStoredDealIds()
  if (!ids.includes(id)) {
    ids.unshift(id)
    localStorage.setItem(DEAL_IDS_KEY, JSON.stringify(ids))
  }
}
