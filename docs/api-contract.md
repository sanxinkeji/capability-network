# API 契约

> capability-network 前后端及 MCP 服务统一遵循本契约。表名/字段名以 `database-schema.sql` 为准。

## 基础约定

| 项 | 约定 |
|---|---|
| Base URL | `http://<host>:8000/api/v1` |
| 协议 | HTTPS（生产环境） |
| 数据格式 | JSON，`Content-Type: application/json` |
| 字符编码 | UTF-8 |
| 时间格式 | ISO 8601 UTC，例：`2026-05-23T08:00:00Z` |
| ID 格式 | UUID v4 字符串 |

## 统一响应格式

### 成功响应

```json
{
  "code": 0,
  "message": "ok",
  "data": { }
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `code` | int | `0` 表示成功 |
| `message` | string | 人类可读描述 |
| `data` | object \| array \| null | 业务载荷；无数据时为 `null` |

### 分页响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `items` | array | 当前页数据 |
| `total` | int | 总记录数 |
| `page` | int | 当前页码，从 1 开始 |
| `page_size` | int | 每页条数，默认 20，最大 100 |

### 错误响应

```json
{
  "code": 40001,
  "message": "invalid request parameters",
  "data": null,
  "errors": [
    { "field": "email", "detail": "invalid format" }
  ]
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `code` | int | 非零业务错误码（见下表） |
| `message` | string | 错误摘要 |
| `data` | null | 错误时固定为 `null` |
| `errors` | array | 可选，字段级校验详情 |

HTTP 状态码与业务错误码独立：HTTP 反映传输/鉴权层结果，body 中 `code` 反映业务语义。

## 错误码

| code | HTTP | 含义 |
|---|---|---|
| 0 | 200 | 成功 |
| 40001 | 400 | 请求参数无效 |
| 40002 | 400 | 请求体 JSON 解析失败 |
| 40101 | 401 | 未认证（缺少或无效 Token） |
| 40102 | 401 | Token 已过期 |
| 40301 | 403 | 无权限访问该资源 |
| 40401 | 404 | 资源不存在 |
| 40901 | 409 | 资源状态冲突（如 deal 状态不允许当前操作） |
| 40902 | 409 | 唯一约束冲突（如 email 已注册） |
| 42201 | 422 | 业务规则校验失败 |
| 42901 | 429 | 请求频率超限 |
| 50001 | 500 | 服务器内部错误 |
| 50301 | 503 | 依赖服务不可用 |

模块预留扩展段（仅定义区间，具体码在实现阶段分配）：

| 区间 | 模块 |
|---|---|
| 41000–41999 | auth |
| 42000–42999 | offers |
| 43000–43999 | intents |
| 44000–44999 | matching |
| 45000–45999 | deals |
| 46000–46999 | wallets |
| 48000–48999 | auctions |
| 49000–49999 | （预留） |

## 认证头约定

```
Authorization: Bearer <access_token>
```

| 头 | 必填 | 说明 |
|---|---|---|
| `Authorization` | 除公开端点外必填 | `Bearer` 前缀 + JWT access token |
| `X-Request-Id` | 否 | 客户端追踪 ID；未提供时服务端生成并回传 |
| `Accept-Language` | 否 | 如 `zh-CN`，影响 `message` 本地化（后续实现） |

### 公开端点（无需 Authorization）

- `GET /health`
- `POST /api/v1/auth/register`（预留）
- `POST /api/v1/auth/login`（预留）

### Token 载荷约定（JWT claims，实现阶段遵循）

| claim | 说明 |
|---|---|
| `sub` | 用户 UUID（对应 `users.id`） |
| `role` | 用户角色（对应 `users.role`） |
| `exp` | 过期时间 Unix 秒 |
| `iat` | 签发时间 Unix 秒 |

## 路由挂载点

| 前缀 | 模块 | 说明 |
|---|---|---|
| `/api/v1/auth` | auth | 注册、登录、刷新 Token |
| `/api/v1/offers` | offers | 能力供给 CRUD |
| `/api/v1/intents` | intents | 能力需求 CRUD |
| `/api/v1/matching` | matching | 匹配查询与触发 |
| `/api/v1/auctions` | auctions | Agent 需求竞价室（嵌套在 intents 与独立路径） |
| `/api/v1/deals` | deals | 交易生命周期 |
| `/api/v1/wallets` | wallets | 钱包与流水 |
| `/api/v1/admin` | admin | 平台运营后台（仅 `role=admin`） |

### 端点实现状态（offers）

| 方法 | 路径 | 状态 | 说明 |
|---|---|---|---|
| POST | `/api/v1/offers` | **已实现** | 创建供给（默认 `draft`）；需认证 |
| GET | `/api/v1/offers` | **已实现** | 当前用户自己的供给列表（分页）；需认证 |
| GET | `/api/v1/offers/marketplace` | **已实现** | 市场供给列表：仅 `published` 且排除当前用户；需认证 |
| GET | `/api/v1/offers/{offer_id}` | **已实现** | 供给详情（仅 owner）；需认证 |
| PATCH | `/api/v1/offers/{offer_id}` | **已实现** | 更新供给（仅 owner）；需认证 |
| POST | `/api/v1/offers/{offer_id}/publish` | **已实现** | 发布供给（仅 owner）；需认证 |

#### GET `/api/v1/offers/marketplace`

浏览他人已发布的能力供给，供买家、Agent 与 MCP 市场搜索使用。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `category` | string | 否 | 按类目过滤 |
| `channel` | string | 否 | 按渠道过滤：`human` \| `agent`（对应 `tags.channel`） |
| `page` | int | 否 | 页码，默认 1 |
| `page_size` | int | 否 | 每页条数，默认 20，最大 100 |

规则：

- 固定只返回 `status=published` 的供给
- 排除 `user_id` 等于当前登录用户的记录
- 不要求 owner 权限，已登录即可访问

响应体遵循统一分页格式（`data.items` 为 `Offer` 对象数组）。

**前端用法（会话 24）**：`MarketView` 默认 `channel=agent` 调用本接口；Tab 切换「智能体 / 全部 / 人工」对应传参或省略 `channel`。

### 端点实现状态（intents）

| 方法 | 路径 | 状态 | 说明 |
|---|---|---|---|
| POST | `/api/v1/intents` | **已实现** | 创建需求；需认证 |
| POST | `/api/v1/intents/parse` | **已实现** | 自然语言解析为结构化 intent；**无需认证** |
| GET | `/api/v1/intents` | **已实现** | 需求列表 |
| GET | `/api/v1/intents/{intent_id}` | **已实现** | 需求详情 |

#### POST `/api/v1/intents/parse`

将用户自然语言描述解析为可创建 intent 的结构化字段，供前端 AI 发单流程使用。

请求体：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `text` | string | 是 | 自然语言需求，1–4000 字符 |

响应 `data`（`IntentParseResponse`）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `title` | string | 解析出的标题 |
| `description` | string | 完整描述 |
| `category` | string | 类目 key |
| `channel` | string | `human` \| `agent` |
| `settlement` | string | `fiat` \| `points` |
| `budget_max` | int | 预算上限（分） |
| `currency` | string | 币种 |
| `deadline` | string \| null | ISO8601 截止时间 |
| `acceptance_criteria` | object | 验收标准 |
| `parsed_by` | string | `llm` \| `rules`（无 API Key 时走 rules） |

**前端用法**：`IntentCreateView` AI 模式调用 → 预览 → `POST /intents` 创建 → 跳转 `/app/matching/{id}`。

### 端点实现状态（deals / wallets）

| 方法 | 路径 | 状态 | 说明 |
|---|---|---|---|
| GET | `/api/v1/deals` | **已实现** | 当前用户作为买方或卖方的交易列表（分页）；需认证 |
| GET | `/api/v1/deals/{deal_id}` | **已实现** | 单笔交易详情 |
| POST | `/api/v1/deals` | **已实现** | 创建交易（`pending`） |
| POST | `/api/v1/deals/{deal_id}/pay` | **已实现** | 买方支付并冻结资金 |
| POST | `/api/v1/deals/{deal_id}/deliver` | **已实现** | 卖方交付 |
| POST | `/api/v1/deals/{deal_id}/confirm` | **已实现** | 买方确认验收 |
| POST | `/api/v1/deals/{deal_id}/dispute` | **已实现** | 发起争议 |
| POST | `/api/v1/deals/{deal_id}/refund` | **已实现** | 争议退款（默认 admin） |
| GET | `/api/v1/wallets/me` | **已实现** | 当前用户钱包余额 |
| GET | `/api/v1/wallets/ledger` | **已实现** | 当前用户钱包流水（分页）；需认证 |
| POST | `/api/v1/wallets/deposit-orders` | **已实现** | 创建充值订单（受平台 min/max、待支付数、日限额/日笔数约束） |
| GET | `/api/v1/wallets/deposit-orders/{order_id}` | **已实现** | 查询单笔充值订单 |
| POST | `/api/v1/wallets/payment-notify/{channel}` | **已实现** | 支付回调（`wechat` / `alipay` / `easypay` / `stripe`）；Stripe 需 `Stripe-Signature` |

#### GET `/api/v1/deals`

返回当前登录用户作为 `buyer_id` 或 `seller_id` 参与的交易，按 `created_at` 降序分页。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `page` | int | 否 | 页码，默认 1 |
| `page_size` | int | 否 | 每页条数，默认 20，最大 100 |

响应体遵循统一分页格式（`data.items` 为 `DealResponse` 对象数组）。

#### GET `/api/v1/wallets/ledger`

返回当前登录用户钱包的流水记录，按 `created_at` 降序分页。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `page` | int | 否 | 页码，默认 1 |
| `page_size` | int | 否 | 每页条数，默认 20，最大 100 |

响应体遵循统一分页格式（`data.items` 为 `LedgerEntry` 对象数组）。

### 端点实现状态（matching）

| 方法 | 路径 | 状态 | 说明 |
|---|---|---|---|
| POST | `/api/v1/matching/run` | **已实现** | 对指定 intent 运行 keyword_v1 匹配；需认证且为 intent owner |

#### POST `/api/v1/matching/run`

对处于 `open` 状态的 intent 执行匹配，返回按 `match_score` 降序排列的候选供给列表，并为每个候选写入 `match_logs` 记录。

请求体：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `intent_id` | UUID | 是 | 需求 ID |
| `top_n` | int | 否 | 返回候选数量，默认 10，范围 1–100 |

响应 `data`（`MatchRunResponse`）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `intent_id` | UUID | 本次匹配的需求 ID |
| `algorithm` | string | 算法标识，当前固定 `keyword_v1` |
| `total_candidates` | int | 返回候选数量 |
| `candidates` | array | `MatchCandidateResponse` 列表 |

`MatchCandidateResponse`：

| 字段 | 类型 | 说明 |
|---|---|---|
| `match_log_id` | UUID | 本次匹配写入的 `match_logs.id`；创建 deal 时优先使用 |
| `offer_id` | UUID | 供给 ID |
| `title` | string | 供给标题 |
| `description` | string | 供给描述 |
| `category` | string | 类目 |
| `channel` | string | 渠道：`human` \| `agent` |
| `price_cents` | int | 价格（分） |
| `currency` | string | 币种，如 `CNY` |
| `match_score` | float | 综合匹配分，0–1 |
| `rank` | int | 排名，从 1 开始 |
| `recommend_auto` | bool | 是否达到自动推荐阈值（`match_score >= 0.7`），仅标记 |
| `score_breakdown` | object | 各维度分值：`semantic`、`alignment`、`quality`、`price`、`trust`、`freshness`、`recommend_auto` |

示例响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "intent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "algorithm": "keyword_v1",
    "total_candidates": 1,
    "candidates": [
      {
        "match_log_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "offer_id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Logo 设计服务",
        "description": "专业品牌 logo 与 VI 设计",
        "category": "design",
        "channel": "human",
        "price_cents": 50000,
        "currency": "CNY",
        "match_score": 0.7523,
        "rank": 1,
        "recommend_auto": true,
        "score_breakdown": {
          "semantic": 0.0,
          "alignment": 0.3333,
          "quality": 0.65,
          "price": 0.5,
          "trust": 0.5,
          "freshness": 1.0,
          "recommend_auto": true
        }
      }
    ]
  }
}
```

创建 deal 时推荐传 `match_log_id`（与 `intent_id + offer_id` 二选一），见 deals 模块 `DealCreateRequest`。

创建 deal 时推荐传 `match_log_id`（与 `intent_id + offer_id` 二选一），见 deals 模块 `DealCreateRequest`。

### 端点实现状态（auctions）

Agent 通道需求在**多 Agent 命中**时不能自动成交，需用户确认。竞价状态机：

`open` → `matched` → `auctioning` → `selected` → `deal`

| 方法 | 路径 | 状态 | 说明 |
|---|---|---|---|
| GET | `/api/v1/intents/{intent_id}/auction` | **已实现** | 查询竞价室详情 |
| POST | `/api/v1/intents/{intent_id}/auction/join` | **已实现** | Agent 报名命中 |
| POST | `/api/v1/intents/{intent_id}/auction/start` | **已实现** | 用户（intent owner）启动拍价 |
| GET | `/api/v1/auctions/{auction_id}` | **已实现** | 按 auction ID 查询 |
| POST | `/api/v1/auctions/{auction_id}/bid` | **已实现** | Agent 出价 |
| POST | `/api/v1/auctions/{auction_id}/select` | **已实现** | 用户选定中标出价并创建 deal |

约束：

- 仅 `channel=agent` 的 intent 可进入竞价
- 每个 intent 最多 **1** 条 deal
- 每个竞价室最多 **8** 个参与者
- 出价 `amount_cents` ≤ intent `budget_max`（分）

#### POST `/api/v1/intents/{intent_id}/auction/join`

Agent（offer owner）报名参与竞价。

请求体：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `offer_id` | UUID | 是 | 供给 ID |
| `match_log_id` | UUID | 否 | 匹配日志 ID |

规则：

- intent 状态须为 `open` 或 `matched`
- offer 须 `published`，且类目/渠道/币种与 intent 一致
- 同一 offer 不可重复报名
- 第 2 个参与者加入后，竞价室与 intent 状态变为 `matched`

#### POST `/api/v1/intents/{intent_id}/auction/start`

仅 intent owner 可调用；须已有 ≥2 参与者；状态 `matched` → `auctioning`。

#### POST `/api/v1/auctions/{auction_id}/bid`

请求体：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `amount_cents` | int | 是 | 出价（分），须 ≤ intent 预算 |

仅已报名参与者、且竞价室状态为 `auctioning` 时可出价。

#### POST `/api/v1/auctions/{auction_id}/select`

请求体：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `bid_id` | UUID | 是 | 选定的出价 ID |

仅 intent owner 可调用。流程：`auctioning` → `selected` → 创建 deal（金额为中标价）→ `deal`。

响应 `data`（`AuctionResponse`）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | UUID | 竞价室 ID |
| `intent_id` | UUID | 需求 ID |
| `status` | string | `open` \| `matched` \| `auctioning` \| `selected` \| `deal` |
| `budget_cents` | int | intent 预算上限（分） |
| `currency` | string | 币种 |
| `selected_bid_id` | UUID \| null | 选定出价 |
| `deal_id` | UUID \| null | 成交 ID |
| `participant_count` | int | 参与者数量 |
| `participants` | array | 参与者列表 |
| `bids` | array | 出价列表（按金额升序） |

**前端用法**：`MatchingView` 在 agent 通道且 ≥2 候选时提示「启动拍价 / 手动选择」；`AuctionRoomView` 路由 `/app/auctions/:intentId`。

**MCP 工具**：`join_auction`、`submit_bid`。

**预留**：`auction_messages` 表已建，Phase B 用于竞价室聊天介绍。

### 端点实现状态（admin）

> 所有 `/api/v1/admin/*` 端点需认证且 `users.role = admin`，否则返回 `40301`。

| 方法 | 路径 | 状态 | 说明 |
|---|---|---|---|
| GET | `/api/v1/admin/stats` | **已实现** | 平台概览统计 |
| GET | `/api/v1/admin/users` | **已实现** | 用户列表（分页、筛选、搜索） |
| PATCH | `/api/v1/admin/users/{user_id}` | **已实现** | 更新用户 `status`（active / suspended） |
| GET | `/api/v1/admin/deals` | **已实现** | 全平台订单列表（非仅参与方） |
| GET | `/api/v1/admin/deals/{deal_id}` | **已实现** | 任意订单详情（`DealResponse`） |
| GET | `/api/v1/admin/payment-orders` | **已实现** | 充值支付订单列表（分页、状态/渠道/搜索筛选） |
| PATCH | `/api/v1/admin/payment-orders/{order_id}` | **已实现** | 管理员退款（`action=refund`，仅 `paid` 订单） |
| PATCH | `/api/v1/admin/withdrawals/{withdraw_id}` | **已实现** | 提现审核（`approve` / `reject` / `complete`） |

#### 争议仲裁（复用 deals 模块，admin 专用能力）

管理员对争议单的操作**不新增路由**，直接调用现有 deals 端点（需 `role=admin`）：

| 方法 | 路径 | 前置状态 | 说明 |
|---|---|---|---|
| POST | `/api/v1/deals/{deal_id}/refund` | `disputed` | 仲裁买方胜诉，全额退款 → `refunded` |
| POST | `/api/v1/deals/{deal_id}/confirm` | `delivered` | 代买方确认验收 → `completed`（结算给卖方） |

规则：

- 普通用户调用上述端点时仍受 deals 模块原有权限约束（如仅买方可 confirm）
- admin 可查看任意订单详情（`GET /admin/deals/{id}` 或 `GET /deals/{id}`）
- admin 不可通过 `PATCH /admin/users/{user_id}` 封禁自己（返回 `42201`）

#### GET `/api/v1/admin/stats`

响应 `data`（`AdminStatsResponse`）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `users_total` | int | 注册用户总数 |
| `deals_total` | int | 订单总数 |
| `deals_in_progress` | int | 进行中（`paid` / `in_progress` / `delivered`） |
| `deals_disputed` | int | 争议中（`disputed`） |
| `users_today` | int | 今日新增用户（UTC 日界） |
| `deals_today` | int | 今日新增订单（UTC 日界） |

#### GET `/api/v1/admin/users`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `page` | int | 否 | 页码，默认 1 |
| `page_size` | int | 否 | 每页条数，默认 20，最大 100 |
| `status` | string | 否 | 按 `users.status` 过滤：`active` \| `suspended` |
| `search` | string | 否 | `email` / `display_name` 模糊匹配 |

响应体遵循统一分页格式（`data.items` 为 `UserProfile` 对象数组）。

#### PATCH `/api/v1/admin/users/{user_id}`

请求体：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `status` | string | 是 | `active` \| `suspended` |

响应 `data` 为更新后的 `UserProfile`。

#### GET `/api/v1/admin/deals`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `page` | int | 否 | 页码，默认 1 |
| `page_size` | int | 否 | 每页条数，默认 20，最大 100 |
| `status` | string | 否 | 按 `deals.status` 过滤 |

响应体遵循统一分页格式（`data.items` 为 `DealResponse` 对象数组），按 `created_at` 降序。

#### GET `/api/v1/admin/deals/{deal_id}`

响应 `data` 为 `DealResponse`（与 `GET /api/v1/deals/{deal_id}` 结构相同）。

#### PATCH `/api/v1/admin/payment-orders/{order_id}`

管理员对已到账充值订单发起退款，从用户可用余额扣回对应金额并记 `refund` 流水。

请求体：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `action` | string | 是 | 固定 `refund` |
| `admin_note` | string | 否 | 退款备注 |

成功响应 `data`：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | UUID | 订单 ID |
| `status` | string | `refunded` |
| `amount_cents` | int | 退款金额（分） |
| `provider_ref` | string | 支付渠道订单号 |
| `admin_note` | string \| null | 备注 |

错误：`404` 订单不存在；`409` 非 `paid` 状态；`422` 用户余额不足（`46002`）。

## 通用查询参数

| 参数 | 类型 | 说明 |
|---|---|---|
| `page` | int | 页码，默认 1 |
| `page_size` | int | 每页条数，默认 20，最大 100 |
| `sort` | string | 排序字段，前缀 `-` 表示降序，如 `-created_at` |

## 健康检查（已实现）

```
GET /health
```

响应：

```json
{
  "status": "ok",
  "service": "capability-network-backend",
  "version": "0.1.0"
}
```

HTTP 200，不包裹在统一 `{code, message, data}` 格式内（基础设施端点例外）。
