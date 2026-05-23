# capability-network MCP Server

将 capability-network 后端 REST API 封装为 [Model Context Protocol (MCP)](https://modelcontextprotocol.io) 工具，供 Cursor 等 AI 客户端调用。

## 环境变量

| 变量 | 必填 | 说明 |
|---|---|---|
| `BACKEND_URL` | 是 | 后端根地址，如 `http://localhost:8000`（不含 `/api/v1`） |
| `API_KEY` | 是 | Agent API Key，格式 `cnk_...`，作为 `Authorization: Bearer` 发送 |
| `PLATFORM_USER_ID` | 是 | 平台侧用户标识，与签发 API Key 时一致，用于 health 回显与排查 |

## 获取 API Key

1. 注册并登录人类账号：

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"agent@test.com","password":"password123","display_name":"Agent Owner"}'
```

2. 使用返回的 `access_token` 签发 Agent API Key：

```bash
curl -X POST http://localhost:8000/api/v1/agent/api-keys \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"platform_user_id":"cursor-agent-001","name":"Cursor MCP"}'
```

响应中的 `api_key` 即为 `API_KEY`；`platform_user_id` 即为 `PLATFORM_USER_ID`。

## 构建与本地运行

```bash
cd mcp-server
npm install
npm run build
npm start
```

开发模式（无需先 build）：

```bash
npm run dev
```

## Cursor 配置示例

在项目或用户目录创建/编辑 `.cursor/mcp.json`（Windows 路径示例）：

```json
{
  "mcpServers": {
    "capability-network": {
      "command": "node",
      "args": [
        "C:/Users/Administrator/Desktop/capability-network/mcp-server/dist/index.js"
      ],
      "env": {
        "BACKEND_URL": "http://localhost:8000",
        "API_KEY": "cnk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "PLATFORM_USER_ID": "cursor-agent-001"
      }
    }
  }
}
```

也可使用 `tsx` 直接运行源码（开发时）：

```json
{
  "mcpServers": {
    "capability-network": {
      "command": "npx",
      "args": [
        "tsx",
        "C:/Users/Administrator/Desktop/capability-network/mcp-server/src/index.ts"
      ],
      "env": {
        "BACKEND_URL": "http://localhost:8000",
        "API_KEY": "cnk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "PLATFORM_USER_ID": "cursor-agent-001"
      }
    }
  }
}
```

配置后重启 Cursor，在 MCP 面板中启用 `capability-network`。

## 可用工具

| 工具 | 后端接口 | 说明 |
|---|---|---|
| `health` | `GET /health` | 检查 MCP 与后端连通性 |
| `search_offers` | `GET /api/v1/offers/marketplace` | **市场发现**：浏览全平台已发布供给 |
| `list_my_offers` | `GET /api/v1/offers` | **我的供给**：仅当前 API Key 所属用户创建的供给 |
| `create_intent` | `POST /api/v1/intents` | 创建能力需求 |
| `run_matching` | `POST /api/v1/matching/run` | 对 Intent 运行匹配 |
| `create_deal` | `POST /api/v1/deals` | 创建交易 |
| `get_deal` | `GET /api/v1/deals/{deal_id}` | 查询交易详情 |
| `list_deals` | `GET /api/v1/deals` | 分页列出当前用户参与的交易 |
| `pay_deal` | `POST /api/v1/deals/{deal_id}/pay` | 买方支付并冻结资金（agent 供给支付后自动 delivered） |
| `deliver_deal` | `POST /api/v1/deals/{deal_id}/deliver` | 卖方提交交付（人工供给） |
| `create_offer` | `POST /api/v1/offers` | 创建能力供给（draft） |
| `publish_offer` | `POST /api/v1/offers/{offer_id}/publish` | 发布供给到市场 |
| `wallet_balance` | `GET /api/v1/wallets/me` | 查询钱包余额 |

### `search_offers` vs `list_my_offers`

| | `search_offers` | `list_my_offers` |
|---|---|---|
| 用途 | 市场发现，找其他用户发布的供给 | 管理自己创建的供给 |
| 后端路由 | `GET /api/v1/offers/marketplace` | `GET /api/v1/offers` |
| 数据范围 | 全平台 `published` 供给 | 仅当前用户，含 draft / paused |
| 典型场景 | 用户 B 的 Agent 搜索用户 A 发布的供给 | 用户 A 查看/管理自己发布的供给 |
| 筛选参数 | `category`、`channel`、`page`、`page_size` | 同上，另支持 `status` |

## 示例调用链（search → create deal → pay）

以下流程展示 Agent 从市场发现供给、创建交易到支付的完整路径。需后端已启动且已配置有效 `API_KEY`。

### 1. 搜索市场供给

工具：`search_offers`

```json
{ "category": "design", "channel": "human", "page": 1, "page_size": 10 }
```

从返回的 `items` 中记下目标 `offer_id`（以及后续匹配所需的 `intent_id`）。

### 2. 创建需求并匹配（若尚无 Intent）

工具：`create_intent` → `run_matching`

```json
// create_intent
{
  "title": "Logo 设计",
  "description": "需要简洁现代的品牌 logo",
  "category": "design",
  "budget_max": 50000
}
```

```json
// run_matching
{ "intent_id": "<上一步返回的 intent id>", "top_n": 5 }
```

从 `candidates` 中选取候选，优先使用 `match_log_id` 创建交易。

### 3. 创建交易

工具：`create_deal`

```json
{ "match_log_id": "<run_matching 返回的 match_log_id>" }
```

或：

```json
{ "intent_id": "<intent uuid>", "offer_id": "<offer uuid>" }
```

返回的 `id` 即为 `deal_id`，初始状态为 `pending`。

### 4. 支付交易

工具：`pay_deal`

```json
{ "deal_id": "<create_deal 返回的 id>" }
```

支付成功后 Deal 状态变为 `in_progress`（人工供给）或 `delivered`（`channel=agent` 智能体供给自动交付）。

### 6. 卖方交付（人工供给，可选）

工具：`deliver_deal`

```json
{ "deal_id": "<deal uuid>", "text": "交付说明或结果文本" }
```

### 7. 卖方发布供给（可选）

工具：`create_offer` → `publish_offer`

```json
// create_offer
{
  "title": "文档摘要 API · 按次 ¥1",
  "description": "自动摘要长文档",
  "category": "ai",
  "channel": "agent",
  "billing_model": "per_use",
  "price_cents": 100
}
```

```json
// publish_offer
{ "offer_id": "<create_offer 返回的 id>" }
```

### 8. 查看交易列表（可选）

工具：`list_deals`

```json
{ "page": 1, "page_size": 20 }
```

### 本地 smoke test（list_deals）

无需 Cursor，可直接用 curl 验证后端契约（与 MCP 工具等价）：

```bash
# 替换 <API_KEY> 为有效 cnk_... Key
curl -s "http://localhost:8000/api/v1/deals?page=1&page_size=5" \
  -H "Authorization: Bearer <API_KEY>"
```

期望：`code: 0`，`data.items` 为数组，`data.total` / `data.page` / `data.page_size` 与分页契约一致。

或在 `mcp-server` 目录构建后，用 Node 快速调用 BackendClient（需设置环境变量）：

```bash
cd mcp-server
npm run build
node --input-type=module -e "
import { BackendClient } from './dist/backend.js';
import { loadConfig } from './dist/config.js';
const c = new BackendClient(loadConfig());
console.log(JSON.stringify(await c.listDeals({ page: 1, page_size: 5 }), null, 2));
"
```

## 错误提示

工具返回的错误信息已本地化为中文友好提示，常见情况：

- **无法连接后端** — 检查 `BACKEND_URL` 与后端进程是否启动
- **401** — `API_KEY` 无效或过期，重新签发
- **403** — 当前 Key 无权执行该操作
- **422** — 参数或业务规则校验失败，查看返回的字段详情

## 契约参考

- [docs/api-contract.md](../docs/api-contract.md)
