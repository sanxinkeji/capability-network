# Tuok 宝塔部署（www.tuokapp.com + ai.tuokapp.com）

| 域名 | 用途 |
|------|------|
| `www.tuokapp.com` | 前端官网 + 用户控制台 |
| `ai.tuokapp.com` | 后端 API（Nginx 反代 → 127.0.0.1:8000） |

Git 仓库：https://github.com/sanxinkeji/capability-network

---

## 1. DNS 解析（域名服务商）

两条 **A 记录** 都指向宝塔服务器公网 IP：

| 主机记录 | 类型 | 值 |
|----------|------|-----|
| `www` | A | 你的服务器 IP |
| `ai` | A | 你的服务器 IP |

可选：根域名 `tuokapp.com` 也做 A 记录，或 CNAME 到 `www`。

---

## 2. 宝塔安装软件

软件商店安装：**Nginx、PostgreSQL、Redis、Python 3.11、Node 18、Supervisor**

PostgreSQL 创建数据库：

- 库名：`capability_network`
- 用户：`postgres`（或自定义）
- 密码：**强密码**

---

## 3. 拉取代码

```bash
cd /www/wwwroot
git clone https://github.com/sanxinkeji/capability-network.git
cd capability-network
```

---

## 4. 生产 `.env`（复制后改密码和 JWT）

```bash
cp .env.example .env
ln -sf /www/wwwroot/capability-network/.env /www/wwwroot/capability-network/backend/.env
nano .env
```

**完整示例（请把 `你的强密码` 和 `JWT随机串` 换成真实值）：**

```bash
APP_NAME=capability-network-backend
APP_VERSION=0.1.0
DEBUG=false

BACKEND_PORT=8000

POSTGRES_USER=postgres
POSTGRES_PASSWORD=你的强密码
POSTGRES_DB=capability_network
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://postgres:你的强密码@127.0.0.1:5432/capability_network

REDIS_PORT=6379
REDIS_URL=redis://127.0.0.1:6379/0

JWT_SECRET_KEY=请换成至少32位随机字符串
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

CORS_ORIGINS=https://www.tuokapp.com,https://tuokapp.com

LOCAL_SCHEMA=0

VITE_API_URL=https://ai.tuokapp.com/api/v1

MCP_SERVER_PORT=3001
MCP_API_KEY=请换成随机字符串
```

生成随机 JWT（SSH 执行）：

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## 5. 后端

```bash
cd /www/wwwroot/capability-network/backend

/www/server/pyporject_evn/versions/3.11.9/bin/python3.11 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
alembic upgrade head
python scripts/purge_demo_data.py --confirm
```

**Supervisor 守护进程：**

| 字段 | 值 |
|------|-----|
| 名称 | `capability-network-backend` |
| 运行目录 | `/www/wwwroot/capability-network/backend` |
| 启动命令 | `/www/wwwroot/capability-network/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2` |

验证：

```bash
curl -s http://127.0.0.1:8000/health
```

---

## 6. 前端构建

### 方式 A：Windows 本地构建后上传 dist/

```powershell
cd C:\Users\Administrator\Desktop\capability-network\frontend
copy .env.production.example .env.production
```

编辑 `frontend/.env.production`：

```bash
VITE_API_URL=https://ai.tuokapp.com/api/v1
```

```powershell
npm ci
npm run build
```

将 `frontend/dist/` 上传到服务器 `/www/wwwroot/www.tuokapp.com/`

### 方式 B：服务器上构建

```bash
cd /www/wwwroot/capability-network/frontend
export VITE_API_URL=https://ai.tuokapp.com/api/v1
npm ci
npm run build
mkdir -p /www/wwwroot/www.tuokapp.com
rsync -av --delete dist/ /www/wwwroot/www.tuokapp.com/
```

---

## 7. Nginx 站点配置

### 7.1 前端 `www.tuokapp.com`

宝塔 → **网站** → **添加站点**：

- 域名：`www.tuokapp.com`
- 根目录：`/www/wwwroot/www.tuokapp.com`
- PHP：纯静态

站点配置 → 在 `server { }` 内加入：

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

**SSL** → Let's Encrypt → 申请 `www.tuokapp.com` → 开启强制 HTTPS

### 7.2 后端 API `ai.tuokapp.com`

宝塔 → **网站** → **添加站点**：

- 域名：`ai.tuokapp.com`
- 根目录：任意（仅反代）

站点配置：

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 300s;
}
```

**SSL** → 申请 `ai.tuokapp.com` → 强制 HTTPS

重载 Nginx：

```bash
nginx -t && nginx -s reload
```

---

## 8. 验收

```bash
curl -sS https://ai.tuokapp.com/health
curl -sS -o /dev/null -w "%{http_code}\n" https://www.tuokapp.com/

chmod +x /www/wwwroot/capability-network/deploy/scripts/baota-smoke.sh
HEALTH_URL=https://ai.tuokapp.com/health \
API_BASE=https://ai.tuokapp.com/api/v1 \
/www/wwwroot/capability-network/deploy/scripts/baota-smoke.sh
```

浏览器：

1. https://www.tuokapp.com — 首页正常
2. https://www.tuokapp.com/register — 注册账号
3. SSH 提权 admin（见 [宝塔部署指南.md](./宝塔部署指南.md) 第七节）
4. https://www.tuokapp.com/admin — 运营后台，设置站点名「Tuok」

---

## 9. MCP / Agent 配置

MCP 环境变量中的后端地址改为：

```json
"BACKEND_URL": "https://ai.tuokapp.com"
```

---

## 10. 常见问题

| 现象 | 处理 |
|------|------|
| 前端能开但 API 报错 | 检查 `VITE_API_URL` 是否为 `https://ai.tuokapp.com/api/v1` 并重新 build |
| CORS 错误 | `.env` 的 `CORS_ORIGINS` 含 `https://www.tuokapp.com` |
| ai 域名 502 | Supervisor 是否 RUNNING |
| pgvector 报错 | 安装 pgvector 或临时 `LOCAL_SCHEMA=1` |
