# 宝塔一键上传清单（生产上线）

> 逐步部署见 **[宝塔部署指南.md](./宝塔部署指南.md)** · 完整运维见 [`baota.md`](./baota.md)

## 1. 打包上传

将以下目录/文件上传到服务器 `/www/wwwroot/capability-network/`：

- `backend/`（含 `requirements.txt`、`alembic/`、`scripts/purge_demo_data.py`）
- `frontend/dist/`（**用生产 env 构建后上传**，见下）
- `mcp-server/dist/`（可选，供 Agent 接入）
- `docs/database-schema.sql` 或 `docs/database-schema-local.sql`
- `deploy/`、`.env.example`

**不要上传**：`node_modules/`、`.env`（在服务器单独创建）、本地 `.env.development`

## 2. 本地构建前端（Windows）

```powershell
cd C:\Users\Administrator\Desktop\capability-network\frontend
copy .env.production.example .env.production
# 编辑 .env.production：VITE_API_URL=https://api.你的域名.com/api/v1
npm ci
npm run build
# 将 dist/ 上传到服务器
```

## 3. 服务器 `.env` 要点

```bash
DEBUG=false
LOCAL_SCHEMA=0
# 若未安装 pgvector 可临时 LOCAL_SCHEMA=1

JWT_SECRET_KEY=<随机32位以上>
DATABASE_URL=postgresql+asyncpg://postgres:强密码@127.0.0.1:5432/capability_network
CORS_ORIGINS=https://www.你的域名.com,https://你的域名.com
VITE_API_URL=https://api.你的域名.com/api/v1
```

软链：

```bash
ln -sf /www/wwwroot/capability-network/.env /www/wwwroot/capability-network/backend/.env
```

## 4. 初始化（生产）

```bash
cd /www/wwwroot/capability-network/backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# 若库中曾有本地演示/E2E 数据，上线前清理（勿在生产 seed 演示数据）
python scripts/purge_demo_data.py --confirm
```

Supervisor 启动：`uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2`

Nginx：

- `api.域名` → 反代 `127.0.0.1:8000`
- `www.域名` → 静态目录指向前端 `dist/`，`try_files $uri /index.html`

## 5. 验收

```bash
curl https://api.你的域名.com/health
bash deploy/scripts/baota-smoke.sh
```

浏览器：

- 官网 `https://www.你的域名.com`（登录页不应出现演示账号）
- 注册真实账号 → 控制台 `/app/market`
- SSH 提权首个账号为 admin → 运营 `/admin`
- 供给方 `/app/agent` 签发 Key

## 6. OpenClaw / 龙虾 MCP

1. 卖方注册并登录 → **Agent 接入** `/app/agent` → 签发 Key
2. 复制 MCP JSON，`BACKEND_URL` 改为 `https://api.你的域名.com`
3. 粘贴到 OpenClaw / Cursor MCP 配置

本地开发演示账号见 [`docs/DEMO-LOGIN.md`](../docs/DEMO-LOGIN.md)（**生产环境勿导入 seed**）。
