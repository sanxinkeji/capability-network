# Frontend（Vue 3 + Vite）

能力网络前端，支持 Mock 与真实后端两种模式。

## 快速开始

```bash
cd frontend
npm install
npm run dev
```

默认 Mock 模式（`.env.development` 中 `VITE_USE_MOCK=true`），无需后端即可演示主路径。

## 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `VITE_API_URL` | API Base URL | `http://localhost:8000/api/v1` |
| `VITE_USE_MOCK` | 是否启用 Mock | `true`（开发环境） |

连接真实后端时，复制 `.env.example` 为 `.env.local` 并设置 `VITE_USE_MOCK=false`。

## 主路径演示

1. **登录/注册** — JWT 存入 `localStorage`
2. **供给** — 创建 Offer → 列表 → 发布
3. **需求** — 创建 Intent（含 budget、acceptance_criteria）
4. **匹配** — 对 open 状态需求展示 TOP-N，点击「创建成交」
5. **订单** — `GET /deals` 分页列表、详情、确认收货
6. **钱包** — 余额 + `GET /wallets/ledger` 流水；「模拟充值」调用 `POST /wallets/recharge`

## API 对接

| 端点 | 说明 |
|---|---|
| `GET /deals?page=&page_size=` | 当前用户订单分页列表 |
| `GET /wallets/ledger?page=&page_size=` | 钱包流水分页 |
| `POST /wallets/recharge` | 开发演示充值 |

契约详见 [docs/api-contract.md](../docs/api-contract.md)。
