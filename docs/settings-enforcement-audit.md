# platform_settings 配置一致性审计

> 审计日期：2026-05-23  
> 目标：**后台能配 = 代码生效**（Admin 保存后，公开 API / 业务逻辑 / 前台路由应一致响应）

## Admin Tab 与字段对照

| Tab | 表单项（字段） |
|-----|----------------|
| **General** | `site_name`, `site_tagline`, `api_public_url`, `docs_url`, `default_page_size`, `page_size_options`, `site_announcement`, `support_email`, `support_url`, `footer_text`, `custom_links_json`, `maintenance_mode` |
| **Features** | `feature_marketplace_enabled`, `feature_matching_enabled`, `feature_wallet_enabled`, `feature_referral_enabled` |
| **Security** | `registration_mode`, `registration_invite_required`, `email_verification_required`, `registration_email_domains`, `two_factor_allowed`, `trust_proxy_ip` |
| **Email** | `smtp_*`, `email_template_verify_*` |
| **Defaults** | `default_wallet_balance_cents` |
| **Trade** | `commission_rate_percent`, `min/max_deposit_cents`, `min/max_withdraw_cents` |
| **Payment** | `payment_enabled`, 商品/限额/费率字段, `payment_*_enabled`, 易支付/Stripe 密钥, `payment_help_*` |
| **Agent** | `feature_agent_enabled`, `agent_max_keys_per_user`, `agent_platform_user_id_prefix`, `agent_mcp_docs_url` |
| **Legal** | `legal_terms_enabled`, `legal_terms_mode`, `legal_terms_updated_at`, `legal_agreements_json` |
| **Backup** | `backup_s3_*`, `backup_auto_enabled`, `backup_cron`, `backup_retention_days`, `backup_max_count` |

---

## 全字段 enforcement 状态

| 字段 | Admin UI | 后端 enforcement | 前台 UI | 状态 |
|------|----------|------------------|---------|------|
| `site_name` | General | 公开 API → `platformStore.siteName`、页标题 | 导航/标题 | ✅ 生效 |
| `site_tagline` | General | 公开 API | 官网 | ✅ 生效 |
| `site_announcement` | General | 公开 API | AppLayout 横幅 | ✅ 生效 |
| `support_email` / `support_url` | General | 公开 API | 页脚/帮助 | ✅ 生效 |
| `docs_url` | General | 公开 API | `platformStore.docsUrl` | ✅ 生效 |
| `api_public_url` | General | Admin 只读展示 | — | ⚠️ 仅存储（无运行时读取） |
| `footer_text` | General | 公开 API | 页脚 | ✅ 生效 |
| `custom_links_json` | General | 公开 API | 页脚链接 | ✅ 生效 |
| `default_page_size` | General | — | — | ⚠️ 仅存储（列表仍用请求参数默认 20） |
| `page_size_options` | General | — | — | ⚠️ 仅存储 |
| `maintenance_mode` | General | `MaintenanceModeMiddleware` | `platform.maintenanceMode` | ✅ 生效 |
| `legal_terms_enabled` | Legal | 公开 API | 登录/注册勾选 | ✅ 生效 |
| `legal_terms_mode` | Legal | 公开 API | 弹窗/跳转模式 | ⚠️ 部分（UI 以 checkbox 为主） |
| `legal_terms_updated_at` | Legal | 公开 API | 法律页日期 | ⚠️ 部分（重确认流程待完善） |
| `legal_agreements_json` | Legal | 公开 API 解析 | 法律文档页 | ✅ 生效 |
| `feature_marketplace_enabled` | Features | `GET /offers/marketplace` 403 | 路由守卫 `market`、侧栏 | ✅ **本次补齐** |
| `feature_matching_enabled` | Features | `POST /matching/run` 403 | 路由守卫 `matching` | ✅ **本次补齐** |
| `feature_wallet_enabled` | Features | 充值/兑换 403 | 路由守卫 `wallet`、侧栏 | ✅ **本次补齐** |
| `feature_referral_enabled` | Features | `require_referral_enabled()` 预留 | Store getter；无独立路由 | ⚠️ 待业务 API（开关已公开） |
| `feature_agent_enabled` | Agent | Agent Key 签发/列表/撤销/API Key 认证 403 | 路由守卫、侧栏/More | ✅ **本次补齐** |
| `agent_max_keys_per_user` | Agent | `create_api_key` 上限 | — | ✅ 生效 |
| `agent_platform_user_id_prefix` | Agent | 签发时自动前缀 | — | ✅ 生效 |
| `agent_mcp_docs_url` | Agent | 公开 API | Connect/文档链接 | ✅ 生效 |
| `email_verification_required` | Security | 注册发码、登录拦截、`/auth/verify-email` | 公开 API；注册后跳转登录 | ✅ **本次实现** |
| `registration_email_domains` | Security | 注册白名单校验 40310 | — | ✅ **本次实现** |
| `registration_mode` | Security | `assert_registration_allowed` | RegisterView | ✅ 生效 |
| `registration_invite_required` | Security | 同上 + 公开 API | RegisterView | ✅ 生效 |
| `registration_invite_codes` | —（已迁移至 Codes 页） | 废弃文本字段 | — | 🗑️ 废弃 |
| `two_factor_allowed` | Security | — | — | ❌ 未实现（无 TOTP 流程） |
| `trust_proxy_ip` | Security | `resolve_client_ip` 读 X-Forwarded-For | — | ✅ **本次实现** |
| `default_wallet_balance_cents` | Defaults | 注册赠金 | — | ✅ 生效 |
| `smtp_*` / `email_template_verify_*` | Email | `send_verification_email`（未配 SMTP 则日志 mock） | Admin 提示 | ✅ **本次接入** |
| `commission_rate_percent` | Trade | 成交结算 `get_commission_rate` | — | ✅ 生效 |
| `min/max_deposit_cents` | Trade/Payment | `create_deposit_order` | 钱包页（间接） | ✅ 生效 |
| `min/max_withdraw_cents` | Trade | `create_withdraw_request` | — | ✅ 生效 |
| `payment_enabled` | Payment | 充值下单 503 | 钱包页 | ✅ 生效 |
| `payment_wechat/alipay_enabled` | Payment | 渠道校验 | 钱包页 | ✅ 生效 |
| `stripe_enabled` | Payment | Stripe 渠道校验 | — | ✅ 生效 |
| `payment_*_source` / `easypay_*` / `stripe_*` | Payment | `payment_provider` 路由 | Admin 概览 | ✅ 生效 |
| `payment_product_name_prefix/suffix` | Payment | 支付商品名 | — | ✅ 生效 |
| `payment_product_description` | Payment | — | — | ⚠️ 仅存储 |
| `payment_order_timeout_minutes` | Payment | 订单过期时间 | — | ✅ 生效 |
| `max_pending_payment_orders` | Payment | 待支付订单数上限 | — | ✅ 生效 |
| `payment_daily_limit_cents` | Payment | 用户日充值限额 | — | ✅ 生效 |
| `max_daily_payment_count` | Payment | 日充值次数 | — | ✅ 生效 |
| `payment_fee_rate_percent` | Payment | — | — | ⚠️ 仅存储 |
| `payment_recharge_rate_percent` | Payment | — | — | ⚠️ 仅存储 |
| `payment_broadcast_mode` | Payment | — | — | ⚠️ 仅存储 |
| `payment_help_text` / `payment_help_image_url` | Payment | — | — | ⚠️ 仅存储（待钱包页展示） |
| `payment_airwallex_enabled` | Payment | — | — | ⚠️ 仅存储（无 Airwallex provider） |
| `backup_s3_*` | Backup | `platform/backups.py` 上传 | — | ✅ 生效 |
| `backup_auto_enabled` / `backup_cron` | Backup | — | — | ⚠️ 仅存储（无定时任务） |
| `backup_retention_days` / `backup_max_count` | Backup | — | — | ⚠️ 仅存储 |

**图例**：✅ 已 enforcement · ⚠️ 部分/仅存储 · ❌ 未实现 · 🗑️ 废弃

---

## 本次新增/修复要点

### 1. 邮箱验证 `email_verification_required`

- 注册：生成 6 位验证码；SMTP 未配置时 **日志 mock**（`email verification (mock/log mode)`）
- 响应：`verification_required: true`，不签发 token
- 登录：未验证用户返回 `41016`
- 新接口：`POST /auth/verify-email`、`POST /auth/resend-verification`
- 迁移：`017_email_verification`（`users.email_verified_at` 等）

### 2. 邮箱域名白名单 `registration_email_domains`

- 注册前 `assert_email_domain_allowed()`，拒绝码 `40310`
- 支持 `@qq.com,gmail.com` 或换行分隔

### 3. 功能开关 `feature_*`

| 开关 | 后端 | 前台路由/导航 |
|------|------|---------------|
| marketplace | `offers/marketplace` | `/app/market` |
| matching | `matching/run` | `/app/matching/:id` |
| wallet | `wallets/deposit-orders`, `/redeem` | `/app/wallet`、侧栏 |
| agent | Agent Key CRUD + API Key 认证 | `/app/agent`、侧栏/More |
| referral | 辅助函数就绪 | 无独立页面（待返利 API） |

### 4. 信任代理 IP `trust_proxy_ip`

- 开启后：限流/登录锁定使用 `X-Forwarded-For` 首段
- 关闭时：仅用 `request.client.host`
- 5s 内存缓存，Admin 保存后 `invalidate_platform_settings_cache()`

---

## 测试覆盖

`backend/tests/test_settings_enforcement.py`：

- 邮箱域名白名单
- 邮箱验证注册 / 登录拦截 / 验证后登录
- `feature_marketplace/matching/wallet/agent` API 403
- 公开 settings 暴露 `email_verification_required`
- `trust_proxy_ip`（monkeypatch 启用）

运行：

```bash
cd backend
python -m pytest tests/test_settings_enforcement.py -q
```

---

## 后续建议（非本次范围）

1. **two_factor_allowed**：实现 TOTP 绑定/校验流程  
2. **payment_help_*** / **payment_recharge_rate_percent** 等：钱包页读取公开 payment UX settings  
3. **feature_referral_enabled**：邀请返利 API + 前台入口  
4. **default_page_size** / **page_size_options**：Admin 列表与前台分页默认值统一  
5. **backup_auto_enabled** + **backup_cron**：接入 scheduler 自动备份  
6. **legal_terms_mode=redirect** 与更新日期后的强制重确认
