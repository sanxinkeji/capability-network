export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface RegisterResponse {
  verification_required: boolean
  email?: string | null
  access_token?: string | null
  refresh_token?: string | null
  token_type?: string
  expires_in?: number | null
}

export interface UserProfile {
  id: string
  email: string
  phone: string | null
  display_name: string
  avatar_url: string | null
  role: 'user' | 'seller' | 'admin'
  status: string
  kyc_level: string
  kyc_status?: 'none' | 'pending' | 'verified'
  kyc_real_name?: string | null
  kyc_id_number_masked?: string | null
  created_at: string
  wallet_balance_cents?: number
  is_seller?: boolean
  shop_status?: 'none' | 'pending' | 'approved' | 'rejected'
  shop_name?: string | null
}

export interface KycStatusInfo {
  kyc_level: string
  kyc_status: 'none' | 'pending' | 'verified'
  kyc_real_name?: string | null
  kyc_id_number_masked?: string | null
}

export interface PaymentStats {
  today_income_cents: number
  today_orders: number
  total_income_cents: number
  total_orders: number
  avg_amount_cents: number
  daily: Array<{ date: string; income_cents: number; order_count: number }>
  channels: Array<{ channel: string; amount_cents: number; order_count: number }>
  top_users: Array<{ email: string; display_name: string; amount_cents: number }>
}

export interface DashboardAnalytics {
  stats: AdminStats
  payment: PaymentStats
  deals_by_status: Array<{ status: string; count: number }>
  daily_users: Array<{ date: string; count: number }>
  daily_deals: Array<{ date: string; count: number }>
  ledger_by_type: Array<{ entry_type: string; amount_cents: number; entry_count: number }>
  top_active_users: Array<{ email: string; display_name: string; deal_count: number }>
}

export interface OpsHealth {
  health_score: number
  health_label: 'healthy' | 'risk' | 'critical'
  sla_percent: number
  disputed_rate: number
  completion_rate: number
  pending_withdrawals: number
  deals_in_progress: number
  agent_keys_active?: number
  agent_users_total?: number
  resources: Array<{ name: string; status: string; value: string }>
}

export interface AgentStats {
  keys_total: number
  keys_active: number
  keys_revoked: number
  keys_rotated: number
  users_with_keys: number
}

export interface AdminApiKeyItem {
  id: string
  user_id: string
  user_email: string
  user_display_name: string
  platform_user_id: string
  name: string | null
  key_prefix: string
  status: 'active' | 'revoked' | 'rotated'
  created_at: string
}

export interface AnnouncementItem {
  id: number
  title: string
  content: string
  status: 'draft' | 'active'
  notify_mode: 'popup' | 'banner'
  audience: string
  starts_at: string | null
  ends_at: string | null
  created_at: string
  updated_at: string
}

export interface AdminStats {
  users_total: number
  deals_total: number
  deals_in_progress: number
  deals_disputed: number
  users_today: number
  deals_today: number
  offers_published?: number
  intents_open?: number
  wallet_deposits_cents?: number
  wallet_payments_cents?: number
  wallet_commission_cents?: number
  withdrawals_pending?: number
  kyc_pending?: number
  shop_applications_pending?: number
  agent_keys_active?: number
  agent_users_total?: number
}

export type RegistrationMode = 'open' | 'invite_only' | 'closed'

export interface CustomLinkItem {
  label: string
  url: string
}

export interface LegalAgreementItem {
  title: string
  slug: string
  content: string
}

export interface PlatformCodeItem {
  id: string
  code: string
  code_type: 'invite' | 'recharge'
  value_cents: number | null
  expires_at: string | null
  used_at: string | null
  used_by_id: string | null
  batch_id: string
  status: 'active' | 'used' | 'expired'
  created_at: string
}

export interface GenerateCodesResult {
  batch_id: string
  code_type: string
  count: number
  codes: string[]
  expires_at: string | null
  value_cents: number | null
}

export interface PublicPlatformSettings {
  site_name: string
  site_tagline: string | null
  site_announcement: string | null
  maintenance_mode: boolean
  registration_mode: RegistrationMode
  registration_invite_required: boolean
  footer_text?: string | null
  custom_links_json?: string | null
  docs_url?: string | null
  support_email?: string | null
  support_url?: string | null
  feature_marketplace_enabled?: boolean
  feature_matching_enabled?: boolean
  feature_wallet_enabled?: boolean
  feature_referral_enabled?: boolean
  feature_agent_enabled?: boolean
  agent_mcp_docs_url?: string | null
  email_verification_required?: boolean
  legal_terms_enabled?: boolean
  legal_terms_updated_at?: string | null
  legal_agreements?: LegalAgreementItem[]
}

export interface PlatformSettings extends PublicPlatformSettings {
  support_email: string | null
  support_url: string | null
  docs_url: string | null
  api_public_url: string | null
  footer_text: string | null
  custom_links_json: string | null
  default_page_size: number
  page_size_options: string
  legal_terms_enabled: boolean
  legal_terms_mode: 'popup' | 'redirect'
  legal_terms_updated_at: string | null
  legal_agreements_json: string | null
  feature_marketplace_enabled: boolean
  feature_matching_enabled: boolean
  feature_wallet_enabled: boolean
  feature_referral_enabled: boolean
  feature_agent_enabled: boolean
  agent_max_keys_per_user: number
  agent_platform_user_id_prefix: string | null
  agent_mcp_docs_url: string | null
  email_verification_required: boolean
  registration_email_domains: string | null
  registration_invite_required: boolean
  two_factor_allowed: boolean
  trust_proxy_ip: boolean
  default_wallet_balance_cents: number
  smtp_host: string | null
  smtp_port: number
  smtp_user: string | null
  smtp_password: string | null
  smtp_from: string | null
  smtp_use_tls: boolean
  email_template_verify_subject: string | null
  email_template_verify_html: string | null
  backup_s3_endpoint: string | null
  backup_s3_region: string | null
  backup_s3_bucket: string | null
  backup_s3_prefix: string | null
  backup_s3_access_key: string | null
  backup_s3_secret_key: string | null
  backup_auto_enabled: boolean
  backup_cron: string
  backup_retention_days: number
  backup_max_count: number
  commission_rate_percent: number
  min_deposit_cents: number
  max_deposit_cents: number | null
  min_withdraw_cents: number
  max_withdraw_cents: number
  payment_wechat_enabled: boolean
  payment_alipay_enabled: boolean
  payment_enabled: boolean
  payment_product_name_prefix: string | null
  payment_product_name_suffix: string | null
  payment_product_description: string | null
  payment_order_timeout_minutes: number
  max_pending_payment_orders: number
  payment_daily_limit_cents: number | null
  payment_fee_rate_percent: number
  payment_recharge_rate_percent: number
  max_daily_payment_count: number | null
  payment_broadcast_mode: boolean
  payment_help_text: string | null
  payment_help_image_url: string | null
  easypay_enabled: boolean
  payment_airwallex_enabled: boolean
  payment_alipay_source: 'direct' | 'easypay'
  payment_wechat_source: 'direct' | 'easypay'
  easypay_pid: string | null
  easypay_key: string | null
  easypay_api_base: string | null
  easypay_alipay_type: string | null
  easypay_wechat_type: string | null
  stripe_enabled: boolean
  stripe_public_key: string | null
  stripe_secret_key: string | null
  stripe_webhook_secret: string | null
  registration_invite_codes: string | null
  updated_at: string | null
}

export interface PaymentConfigInfo {
  public_base_url: string
  payment_provider: string
  payment_enabled: boolean
  payment_alipay_source: string
  payment_wechat_source: string
  wechat_configured: boolean
  alipay_configured: boolean
  easypay_configured: boolean
  stripe_configured: boolean
  wechat_enabled: boolean
  alipay_enabled: boolean
  stripe_enabled: boolean
  notify_wechat_url: string
  notify_alipay_url: string
  notify_easypay_url: string
  notify_stripe_url: string
  smtp_configured: boolean
}

export interface AdminWithdrawItem {
  id: string
  user_id: string
  amount_cents: number
  status: string
  payout_method: string
  payout_account: string
  payout_name: string
  admin_note: string | null
  provider_ref: string | null
  created_at: string
  processed_at: string | null
}

export interface AdminKycItem {
  user_id: string
  email: string
  display_name: string
  real_name: string | null
  id_number: string | null
  id_number_masked: string | null
  kyc_level: string
  kyc_status: string
  submitted_at: string
}

export interface AdminAuditLog {
  id: string
  admin_id: string
  action: string
  target_type: string | null
  target_id: string | null
  detail: string | null
  created_at: string
}

export interface DatabaseBackupItem {
  id: string
  status: string
  filename: string | null
  file_path: string | null
  object_key: string | null
  size_bytes: number | null
  trigger_type: string
  error_message: string | null
  started_at: string
  finished_at: string | null
  created_by_admin_id: string | null
  created_at: string
}

export type OfferChannel = 'human' | 'agent'
export type BillingModel = 'per_use' | 'per_query' | 'per_hour'
export type OfferStatus = 'draft' | 'published' | 'paused'

export interface Offer {
  id: string
  user_id: string
  title: string
  description: string
  category: string
  channel: OfferChannel
  billing_model: BillingModel
  price_cents: number
  currency: string
  budget_min_cents: number | null
  budget_max_cents: number | null
  delivery_description: string | null
  acceptance_sample_url: string | null
  status: OfferStatus
  created_at: string
  updated_at: string
}

export interface MarketplaceOffer extends Offer {
  seller_display_name?: string | null
}

export interface OfferCreatePayload {
  title: string
  description: string
  category: string
  channel: OfferChannel
  billing_model: BillingModel
  price_cents: number
  currency?: string
  budget_min_cents?: number | null
  budget_max_cents?: number | null
  delivery_description?: string | null
  acceptance_sample_url?: string | null
}

export type IntentChannel = 'human' | 'agent'
export type IntentSettlement = 'fiat' | 'points'
export type IntentStatus =
  | 'open'
  | 'matching'
  | 'matched'
  | 'auctioning'
  | 'selected'
  | 'deal'
  | 'closed'

export interface Intent {
  id: string
  user_id: string
  title: string
  description: string
  category: string
  channel: IntentChannel
  settlement: IntentSettlement
  budget_max: number
  currency: string
  deadline: string | null
  acceptance_criteria: Record<string, unknown>
  status: IntentStatus
  match_id: string | null
  created_at: string
  updated_at: string
}

export interface IntentCreatePayload {
  title: string
  description: string
  category: string
  channel?: IntentChannel
  settlement?: IntentSettlement
  budget_max: number
  currency?: string
  deadline?: string | null
  acceptance_criteria?: Record<string, unknown>
}

export interface IntentParseResult {
  title: string
  description: string
  category: string
  channel: IntentChannel
  settlement: IntentSettlement
  budget_max: number
  currency: string
  deadline: string | null
  acceptance_criteria: Record<string, unknown>
  parsed_by: 'llm' | 'rules'
}

export interface MatchCandidate {
  match_log_id: string
  offer_id: string
  title: string
  description: string
  category: string
  channel: string
  price_cents: number
  currency: string
  match_score: number
  rank: number
  recommend_auto: boolean
  score_breakdown: Record<string, number | boolean>
}

export interface MatchRunResult {
  intent_id: string
  algorithm: string
  total_candidates: number
  candidates: MatchCandidate[]
}

export type AuctionStatus = 'open' | 'matched' | 'auctioning' | 'selected' | 'deal'

export interface AuctionParticipant {
  id: string
  offer_id: string
  user_id: string
  match_log_id: string | null
  joined_at: string
}

export interface AuctionBid {
  id: string
  participant_id: string
  offer_id: string
  user_id: string
  amount_cents: number
  created_at: string
}

export interface AuctionRoom {
  id: string
  intent_id: string
  status: AuctionStatus
  budget_cents: number
  currency: string
  selected_bid_id: string | null
  deal_id: string | null
  participant_count: number
  participants: AuctionParticipant[]
  bids: AuctionBid[]
  created_at: string
  updated_at: string
}

export type DealStatus =
  | 'pending'
  | 'paid'
  | 'in_progress'
  | 'delivered'
  | 'completed'
  | 'disputed'
  | 'refunded'
  | 'cancelled'

export interface Deal {
  id: string
  offer_id: string
  intent_id: string
  buyer_id: string
  seller_id: string
  amount_cents: number
  currency: string
  status: DealStatus
  auto_confirm: boolean
  match_log_id: string | null
  delivery_payload_url: string | null
  delivery_text: string | null
  dispute_reason: string | null
  refund_amount_cents: number | null
  auto_confirm_deadline: string | null
  agent_auto_delivered?: boolean
  created_at: string
  updated_at: string
  completed_at: string | null
}

export type DealMessageSenderRole = 'system' | 'buyer' | 'seller' | 'agent'
export type DealMessageKind = 'text' | 'delivery' | 'status'

export interface DealMessage {
  id: string
  deal_id: string
  sender_role: DealMessageSenderRole
  sender_id: string | null
  body: string
  kind: DealMessageKind
  created_at: string
}

export interface DealMessageList {
  items: DealMessage[]
  total: number
}

export interface Wallet {
  id: string
  user_id: string
  balance_available: number
  balance_frozen: number
  points_non_withdrawable: number
  currency: string
  created_at: string
  updated_at: string
}

export interface WalletLedgerEntry {
  id: string
  wallet_id?: string
  entry_type: string
  amount_cents: number
  balance_after: number
  deal_id: string | null
  description: string | null
  created_at: string
}

export interface DepositOrder {
  id: string
  user_id?: string
  user_email?: string
  user_display_name?: string
  amount_cents: number
  currency: string
  channel: string
  status: string
  provider?: string
  provider_ref: string
  pay_url: string | null
  expires_at?: string | null
  paid_at: string | null
  created_at: string
  wallet?: Wallet
}

export interface WithdrawRequestRecord {
  id: string
  amount_cents: number
  status: string
  payout_method: string
  payout_account: string
  payout_name: string
  admin_note: string | null
  provider_ref: string | null
  created_at: string
  processed_at: string | null
  wallet: Wallet
}
