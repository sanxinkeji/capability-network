# capability-network

能力网络 monorepo — 能力交易、匹配、钱包与 Agent 接入。

## 宝塔生产部署

**[deploy/宝塔部署指南.md](deploy/宝塔部署指南.md)** · 上传 Git：[deploy/GIT-UPLOAD.md](deploy/GIT-UPLOAD.md) · 上传清单 [deploy/BAOTA-UPLOAD.md](deploy/BAOTA-UPLOAD.md)

上线前清理演示数据：`python backend/scripts/purge_demo_data.py --confirm`

---

## 本地开发

### 演示账号（仅本地）

| 角色 | 邮箱 | 密码 |
|------|------|------|
| 卖方 | `seller_qa@test.com` | `password123` |
| 买方 | `buyer_qa@test.com` | `password123` |
| 管理员 | `admin_qa@test.com` | `password123` |

登录：http://127.0.0.1:5173/login · 完整说明见 **[docs/DEMO-LOGIN.md](docs/DEMO-LOGIN.md)**

```powershell
# 恢复中文演示数据（仅本地，生产勿执行）
python backend/scripts/seed_demo_zh.py --reset --purge-demo --run-match
```

---
```
capability-network/
├── backend/          # FastAPI + SQLAlchemy 2
├── frontend/         # Vue 3 + Vite + Pinia
├── mcp-server/       # MCP Server（Agent 工具封装）
├── deploy/           # 部署配置与冒烟脚本
├── docs/             # 契约文档（权威）
│   ├── api-contract.md
│   ├── database-schema.sql
│   ├── deal-state-machine.md
│   └── COMMERCIAL-CHECKLIST.md
└── docker-compose.yml
```

## 快速启动

```bash
cp .env.example .env
docker compose up -d --build
curl http://localhost:8000/health
```

后端启动后，可导入中文演示数据（账号与说明见 [docs/demo-accounts-zh.md](docs/demo-accounts-zh.md)）：

```bash
python backend/scripts/seed_demo_zh.py
```

前端开发：

```bash
cd frontend
npm install
npm run dev
```

## 测试与 CI

| 命令 | 说明 |
|------|------|
| `cd backend && pytest tests/ -q --cov=app --cov-fail-under=60` | 后端单元测试 + 覆盖率 |
| `cd frontend && npm run test:ci` | 前端 Vitest 单元测试 |
| `./deploy/scripts/baota-smoke.sh` | 生产/本地 API 冒烟（health + auth） |

GitHub Actions 见 [`.github/workflows/ci.yml`](.github/workflows/ci.yml)。可选 docker compose 冒烟：手动触发 workflow 勾选 **Run docker compose smoke test**，或 commit message 含 `[smoke]`。

商用发布前勾选清单：**[docs/COMMERCIAL-CHECKLIST.md](docs/COMMERCIAL-CHECKLIST.md)**

## 契约文档

- [API 契约](docs/api-contract.md)
- [数据库 Schema](docs/database-schema.sql)
- [Deal 状态机](docs/deal-state-machine.md)

## 数据库迁移

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
```

## Agent / MCP

Cursor 等客户端可通过 MCP 调用后端 API，配置见 **[mcp-server/README.md](mcp-server/README.md)**。

## 并行开发约定

- 表名/字段名以 `docs/database-schema.sql` 为准，不得擅自改名
- API 响应格式以 `docs/api-contract.md` 为准
- Deal 状态转移以 `docs/deal-state-machine.md` 为准
- 各模块 router 已预留：`auth`, `offers`, `intents`, `matching`, `deals`, `wallets`
