import { request } from './request'
import type {
  AdminAuditLog,
  AdminStats,
  AdminWithdrawItem,
  AnnouncementItem,
  DatabaseBackupItem,
  Deal,
  DepositOrder,
  Intent,
  Offer,
  PaginatedData,
  PaymentConfigInfo,
  PaymentStats,
  PlatformSettings,
  DashboardAnalytics,
  OpsHealth,
  UserProfile,
  WalletLedgerEntry,
} from '@/types'

export function getAdminStats(): Promise<AdminStats> {
  return request<AdminStats>({ method: 'GET', url: '/admin/stats' })
}

export function getAdminPaymentStats(days = 7): Promise<PaymentStats> {
  return request<PaymentStats>({ method: 'GET', url: '/admin/payment-stats', params: { days } })
}

export function getAdminDashboard(days = 7): Promise<DashboardAnalytics> {
  return request<DashboardAnalytics>({ method: 'GET', url: '/admin/dashboard', params: { days } })
}

export function getAdminOpsHealth(): Promise<OpsHealth> {
  return request<OpsHealth>({ method: 'GET', url: '/admin/ops-health' })
}

export function listAdminUsers(params?: {
  page?: number
  page_size?: number
  status?: string
  search?: string
}): Promise<PaginatedData<UserProfile>> {
  return request<PaginatedData<UserProfile>>({
    method: 'GET',
    url: '/admin/users',
    params: {
      page: params?.page ?? 1,
      page_size: params?.page_size ?? 20,
      status: params?.status || undefined,
      search: params?.search || undefined,
    },
  })
}

export function updateAdminUserStatus(
  userId: string,
  status: 'active' | 'suspended',
): Promise<UserProfile> {
  return request<UserProfile>({
    method: 'PATCH',
    url: `/admin/users/${userId}`,
    data: { status },
  })
}

export function creditAdminUser(
  userId: string,
  payload: { amount_cents: number; note?: string },
): Promise<{ balance_cents: number }> {
  return request({
    method: 'POST',
    url: `/admin/users/${userId}/credit`,
    data: payload,
  })
}

export function listAdminDeals(params?: {
  page?: number
  page_size?: number
  status?: string
}): Promise<PaginatedData<Deal>> {
  return request<PaginatedData<Deal>>({
    method: 'GET',
    url: '/admin/deals',
    params: {
      page: params?.page ?? 1,
      page_size: params?.page_size ?? 20,
      status: params?.status || undefined,
    },
  })
}

export function getAdminDeal(dealId: string): Promise<Deal> {
  return request<Deal>({ method: 'GET', url: `/admin/deals/${dealId}` })
}

export function listAdminOffers(params?: {
  page?: number
  page_size?: number
  status?: string
}): Promise<PaginatedData<Offer>> {
  return request<PaginatedData<Offer>>({
    method: 'GET',
    url: '/admin/offers',
    params: {
      page: params?.page ?? 1,
      page_size: params?.page_size ?? 20,
      status: params?.status || undefined,
    },
  })
}

export function updateAdminOfferStatus(offerId: string, status: 'published' | 'paused'): Promise<Offer> {
  return request<Offer>({
    method: 'PATCH',
    url: `/admin/offers/${offerId}/status`,
    data: { status },
  })
}

export function listAdminIntents(params?: {
  page?: number
  page_size?: number
  status?: string
}): Promise<PaginatedData<Intent>> {
  return request<PaginatedData<Intent>>({
    method: 'GET',
    url: '/admin/intents',
    params: {
      page: params?.page ?? 1,
      page_size: params?.page_size ?? 20,
      status: params?.status || undefined,
    },
  })
}

export function updateAdminIntentStatus(intentId: string, status: 'closed'): Promise<Intent> {
  return request<Intent>({
    method: 'PATCH',
    url: `/admin/intents/${intentId}/status`,
    data: { status },
  })
}

export function listAdminWithdrawals(params?: {
  page?: number
  page_size?: number
  status?: string
}): Promise<PaginatedData<AdminWithdrawItem>> {
  return request<PaginatedData<AdminWithdrawItem>>({
    method: 'GET',
    url: '/admin/withdrawals',
    params: {
      page: params?.page ?? 1,
      page_size: params?.page_size ?? 20,
      status: params?.status || undefined,
    },
  })
}

export function processAdminWithdraw(
  withdrawId: string,
  payload: { action: 'approve' | 'reject' | 'complete'; admin_note?: string; provider_ref?: string },
): Promise<{ id: string; status: string }> {
  return request({
    method: 'PATCH',
    url: `/admin/withdrawals/${withdrawId}`,
    data: payload,
  })
}

export function getAdminSettings(): Promise<{ settings: PlatformSettings; payment: PaymentConfigInfo }> {
  return request({ method: 'GET', url: '/admin/settings' })
}

export function updateAdminSettings(
  payload: Partial<PlatformSettings>,
): Promise<{ settings: PlatformSettings; payment: PaymentConfigInfo }> {
  return request({
    method: 'PATCH',
    url: '/admin/settings',
    data: payload,
  })
}

export function listAdminPaymentOrders(params?: {
  page?: number
  page_size?: number
  status?: string
  channel?: string
  search?: string
}): Promise<PaginatedData<DepositOrder>> {
  return request<PaginatedData<DepositOrder>>({
    method: 'GET',
    url: '/admin/payment-orders',
    params: {
      page: params?.page ?? 1,
      page_size: params?.page_size ?? 20,
      status: params?.status || undefined,
      channel: params?.channel || undefined,
      search: params?.search || undefined,
    },
  })
}

export function refundAdminPaymentOrder(
  orderId: string,
  payload: { admin_note?: string } = {},
): Promise<{ id: string; status: string; amount_cents: number }> {
  return request({
    method: 'PATCH',
    url: `/admin/payment-orders/${orderId}`,
    data: { action: 'refund', ...payload },
  })
}

export function listAdminAnnouncements(params?: {
  page?: number
  page_size?: number
  status?: string
  search?: string
}): Promise<PaginatedData<AnnouncementItem>> {
  return request<PaginatedData<AnnouncementItem>>({
    method: 'GET',
    url: '/admin/announcements',
    params: {
      page: params?.page ?? 1,
      page_size: params?.page_size ?? 20,
      status: params?.status || undefined,
      search: params?.search || undefined,
    },
  })
}

export function createAdminAnnouncement(
  payload: Partial<AnnouncementItem> & { title: string },
): Promise<AnnouncementItem> {
  return request({ method: 'POST', url: '/admin/announcements', data: payload })
}

export function updateAdminAnnouncement(
  id: number,
  payload: Partial<AnnouncementItem>,
): Promise<AnnouncementItem> {
  return request({ method: 'PATCH', url: `/admin/announcements/${id}`, data: payload })
}

export function deleteAdminAnnouncement(id: number): Promise<void> {
  return request({ method: 'DELETE', url: `/admin/announcements/${id}` })
}

export function listAdminLedger(params?: {
  page?: number
  page_size?: number
  entry_type?: string
}): Promise<PaginatedData<WalletLedgerEntry>> {
  return request<PaginatedData<WalletLedgerEntry>>({
    method: 'GET',
    url: '/admin/ledger',
    params: {
      page: params?.page ?? 1,
      page_size: params?.page_size ?? 20,
      entry_type: params?.entry_type || undefined,
    },
  })
}

export function listAdminAuditLogs(params?: {
  page?: number
  page_size?: number
}): Promise<PaginatedData<AdminAuditLog>> {
  return request<PaginatedData<AdminAuditLog>>({
    method: 'GET',
    url: '/admin/audit-logs',
    params: { page: params?.page ?? 1, page_size: params?.page_size ?? 20 },
  })
}

export function listAdminCodes(params?: {
  page?: number
  page_size?: number
  code_type?: string
  status?: string
  batch_id?: string
}): Promise<PaginatedData<import('@/types').PlatformCodeItem>> {
  return request({
    method: 'GET',
    url: '/admin/codes',
    params: {
      page: params?.page ?? 1,
      page_size: params?.page_size ?? 20,
      code_type: params?.code_type || undefined,
      status: params?.status || undefined,
      batch_id: params?.batch_id || undefined,
    },
  })
}

export function generateAdminCodes(payload: {
  code_type: 'invite' | 'recharge'
  count: number
  expires_at?: string | null
  value_cents?: number
}): Promise<import('@/types').GenerateCodesResult> {
  return request({
    method: 'POST',
    url: '/admin/codes/generate',
    data: payload,
  })
}

export function getAdminAgentStats(): Promise<import('@/types').AgentStats> {
  return request({ method: 'GET', url: '/admin/agent-stats' })
}

export function listAdminAgentKeys(params?: {
  page?: number
  page_size?: number
  status?: string
  search?: string
}): Promise<PaginatedData<import('@/types').AdminApiKeyItem>> {
  return request({
    method: 'GET',
    url: '/admin/agent-keys',
    params: {
      page: params?.page ?? 1,
      page_size: params?.page_size ?? 20,
      status: params?.status || undefined,
      search: params?.search || undefined,
    },
  })
}

export function revokeAdminAgentKey(keyId: string): Promise<import('@/types').AdminApiKeyItem> {
  return request({ method: 'DELETE', url: `/admin/agent-keys/${keyId}` })
}

export function listAdminBackups(params?: {
  page?: number
  page_size?: number
}): Promise<PaginatedData<DatabaseBackupItem>> {
  return request<PaginatedData<DatabaseBackupItem>>({
    method: 'GET',
    url: '/admin/backups',
    params: { page: params?.page ?? 1, page_size: params?.page_size ?? 20 },
  })
}

export function triggerAdminBackup(dryRun = false): Promise<DatabaseBackupItem> {
  return request<DatabaseBackupItem>({
    method: 'POST',
    url: '/admin/backups/trigger',
    params: dryRun ? { dry_run: true } : undefined,
  })
}

export function listAdminKyc(params?: {
  page?: number
  page_size?: number
  status?: string
}): Promise<PaginatedData<import('@/types').AdminKycItem>> {
  return request({
    method: 'GET',
    url: '/admin/kyc',
    params: {
      page: params?.page ?? 1,
      page_size: params?.page_size ?? 20,
      status: params?.status || undefined,
    },
  })
}

export function reviewAdminKyc(
  userId: string,
  payload: { action: 'approve' | 'reject'; admin_note?: string },
): Promise<import('@/types').KycStatusInfo> {
  return request({
    method: 'PATCH',
    url: `/admin/kyc/${userId}`,
    data: payload,
  })
}

