import { request } from './request'
import type { DepositOrder, PaginatedData, Wallet, WalletLedgerEntry, WithdrawRequestRecord } from '@/types'

export function getWallet(): Promise<Wallet> {
  return request<Wallet>({ method: 'GET', url: '/wallets/me' })
}

export function getLedger(params?: {
  page?: number
  page_size?: number
}): Promise<PaginatedData<WalletLedgerEntry>> {
  return request<PaginatedData<WalletLedgerEntry>>({
    method: 'GET',
    url: '/wallets/ledger',
    params: { page: params?.page ?? 1, page_size: params?.page_size ?? 50 },
  })
}

export function createDepositOrder(payload: {
  amount_cents: number
  channel: 'wechat' | 'alipay'
}): Promise<DepositOrder> {
  return request<DepositOrder>({
    method: 'POST',
    url: '/wallets/deposit-orders',
    data: payload,
  })
}

export function getDepositOrder(orderId: string): Promise<DepositOrder> {
  return request<DepositOrder>({
    method: 'GET',
    url: `/wallets/deposit-orders/${orderId}`,
  })
}

export function createWithdrawRequest(payload: {
  amount_cents: number
  payout_method: 'alipay' | 'wechat' | 'bank'
  payout_account: string
  payout_name: string
}): Promise<WithdrawRequestRecord> {
  return request<WithdrawRequestRecord>({
    method: 'POST',
    url: '/wallets/withdraw',
    data: payload,
  })
}

export function listWithdrawals(params?: {
  page?: number
  page_size?: number
}): Promise<PaginatedData<WithdrawRequestRecord>> {
  return request<PaginatedData<WithdrawRequestRecord>>({
    method: 'GET',
    url: '/wallets/withdrawals',
    params: { page: params?.page ?? 1, page_size: params?.page_size ?? 20 },
  })
}

export function redeemRechargeCard(code: string): Promise<Wallet> {
  return request<Wallet>({
    method: 'POST',
    url: '/wallets/redeem',
    data: { code },
  })
}
