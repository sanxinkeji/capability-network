import type { LegalAgreementItem } from '@/types'

export type LegalDocKey = 'terms' | 'privacy'

const DOC_KEY_ALIASES: Record<LegalDocKey, string[]> = {
  terms: ['terms', '/terms', '/legal/terms', 'legal/terms'],
  privacy: ['privacy', '/privacy', '/legal/privacy', 'legal/privacy'],
}

export function normalizeLegalSlug(slug: string): string {
  return slug.trim().replace(/^\/+/, '').replace(/\/+$/, '')
}

export function legalAgreementPath(slug: string): string {
  const normalized = normalizeLegalSlug(slug)
  if (DOC_KEY_ALIASES.terms.includes(normalized) || normalized.endsWith('/terms') || normalized === 'terms') {
    return '/terms'
  }
  if (DOC_KEY_ALIASES.privacy.includes(normalized) || normalized.endsWith('/privacy') || normalized === 'privacy') {
    return '/privacy'
  }
  return slug.startsWith('/') ? slug : `/${slug}`
}

export function findLegalAgreement(
  agreements: LegalAgreementItem[],
  docKey: LegalDocKey,
): LegalAgreementItem | null {
  const aliases = new Set(DOC_KEY_ALIASES[docKey].map(normalizeLegalSlug))
  return (
    agreements.find((item) => {
      const normalized = normalizeLegalSlug(item.slug)
      return aliases.has(normalized) || normalized.endsWith(`/${docKey}`)
    }) ?? null
  )
}

export const DEFAULT_LEGAL_CONTENT: Record<LegalDocKey, { title: string; content: string }> = {
  terms: {
    title: '用户服务协议',
    content: `# 用户服务协议

欢迎使用本平台。注册或使用本服务，即表示您同意以下条款：

## 1. 服务说明
本平台提供能力供需匹配、订单托管与钱包结算等 SaaS 服务。

## 2. 账号与安全
您应妥善保管账号密码，对账号下的操作负责。

## 3. 交易与资金
订单资金由平台托管，按平台规则完成支付、交付与结算。

## 4. 禁止行为
不得利用平台从事违法、欺诈、侵权或干扰系统运行的行为。

## 5. 协议变更
平台有权更新本协议，更新后将通过站内公告或注册/登录页提示。

## 6. 联系我们
如有疑问，请通过平台公示的客服渠道联系。`,
  },
  privacy: {
    title: '隐私政策',
    content: `# 隐私政策

我们重视您的个人信息保护。本政策说明我们如何收集、使用与保护您的信息。

## 1. 收集的信息
包括注册邮箱、登录记录、交易与钱包相关数据，以及为保障安全所需的设备与日志信息。

## 2. 使用目的
用于账号认证、交易履约、风控安全、客服支持及法律合规要求。

## 3. 信息共享
除法律法规要求或经您同意外，我们不会向第三方出售您的个人信息。

## 4. 信息存储与安全
我们采取合理的技术与管理措施保护数据安全，并在法定或业务必要期限内保存。

## 5. 您的权利
您可依法查询、更正或删除个人信息，具体可通过客服渠道申请。

## 6. 政策更新
我们可能适时更新本政策，重大变更将通过站内提示告知。`,
  },
}
