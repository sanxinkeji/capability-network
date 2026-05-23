# 宝塔面板生产部署指南（会话 9 / M4）

本文档面向已购买 Linux 服务器并安装 [宝塔面板](https://www.bt.cn/) 的运维场景，将 **capability-network** 从零部署到：

1. **`GET https://api.xxx.com/health` → HTTP 200**
2. **注册 + 登录 API 冒烟通过**（见 [第 9 节](#9-部署后验收m4-标准)）
3. **前端 `dist/` 由 Nginx 托管 + Let's Encrypt HTTPS**

> 环境变量命名与项目根目录 `docker-compose.yml`、`.env.example` **完全一致**。部署完成后填写 [`production-notes.md`](./production-notes.md)。

### 部署前前提（向运维确认）

- [ ] Linux 服务器 + 宝塔已安装并可 SSH
- [ ] 域名已解析：`api.xxx.com`（后端）、`www.xxx.com`（前端）
- [ ] 已生成 PostgreSQL 强密码与 `JWT_SECRET_KEY`（≥32 字符）
- [ ] **勿将 `.env` 提交 git**（已在 `.gitignore`）

---

## 0. 前置条件

| 项 | 要求 |
|---|---|
| 服务器 | CentOS 7+ / Ubuntu 20.04+ / Debian 10+，公网 IP |
| 宝塔 | 7.x 或 8.x，已绑定面板账号 |
| 域名 | 示例：`api.example.com`（后端）、`www.example.com`（前端） |
| DNS | 两条 A 记录均指向服务器公网 IP |
| 项目路径（建议） | `/www/wwwroot/capability-network` |

下文将 `example.com` 替换为你的真实域名。

---

## 1. 宝塔安装软件

登录面板 → **软件商店**，安装以下组件（版本尽量接近）：

| 软件 | 版本建议 | 用途 |
|---|---|---|
| **Nginx** | 最新稳定版 | 反向代理、SSL、静态站点 |
| **PostgreSQL** | 16（或 14+） | 主数据库 |
| **Redis** | 7.x | 缓存 / 队列 |
| **Python 项目管理器** | 最新 | Python 3.11 虚拟环境 |
| **Node 版本管理器** | 最新 | Node.js 18（前端构建） |
| **Supervisor 管理器** | 最新 | 守护 uvicorn 进程 |

### 1.1 安装 Python 3.11

1. 打开 **Python 项目管理器** → **版本管理** → 安装 **Python 3.11.x**。
2. 记录解释器路径，例如：`/www/server/pyporject_evn/versions/3.11.9/bin/python3.11`。

### 1.2 安装 Node 18

1. 打开 **Node 版本管理器** → 安装 **v18.x** → 设为默认。
2. 终端验证：`node -v` 应输出 `v18.x.x`。

### 1.3 启动 PostgreSQL 与 Redis

1. **数据库** → **PostgreSQL** → 启动服务，记下端口（默认 `5432`）。
2. **软件商店** → **Redis** → 启动，记下端口（默认 `6379`）。
3. 在 PostgreSQL 中创建业务库与用户（与 `.env.example` 默认值一致，生产请改强密码）：

```sql
CREATE USER postgres WITH PASSWORD '你的强密码';
CREATE DATABASE capability_network OWNER postgres;
```

> **pgvector 扩展（M4 必知）**：生产 `.env` 须 **`LOCAL_SCHEMA=0`**，迁移使用 `docs/database-schema.sql`（含 `CREATE EXTENSION vector`）。宝塔 PostgreSQL 常未内置 pgvector。
>
> **Workaround A（推荐）**：[编译安装 pgvector](https://github.com/pgvector/pgvector#installation) 后：
>
> ```sql
> \c capability_network
> CREATE EXTENSION IF NOT EXISTS vector;
> CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
> ```
>
> 再 `alembic upgrade head`。
>
> **Workaround B（应急）**：临时 `LOCAL_SCHEMA=1` 使用无 vector 的 `database-schema-local.sql` 跑通服务；**正式生产应回到 A 并改回 `LOCAL_SCHEMA=0`**。详见 [`production-notes.md`](./production-notes.md)。

---

## 2. 拉取代码与生产 `.env`

```bash
cd /www/wwwroot
git clone <你的仓库地址> capability-network
cd capability-network
cp .env.example .env
```

编辑 `/www/wwwroot/capability-network/.env`（见 [第 7 节检查清单](#7-生产-env-检查清单)）。

**关键：后端从 `backend/` 目录启动**，需让进程能读到根目录 `.env`：

```bash
ln -sf /www/wwwroot/capability-network/.env /www/wwwroot/capability-network/backend/.env
```

---

## 3. 后端：虚拟环境、依赖、迁移

```bash
cd /www/wwwroot/capability-network/backend

# 使用宝塔 Python 3.11 创建 venv（路径按实际解释器调整）
/www/server/pyporject_evn/versions/3.11.9/bin/python3.11 -m venv .venv
source .venv/bin/activate

pip install -U pip
pip install -r requirements.txt

# 确认生产 schema 模式（.env 中 LOCAL_SCHEMA=0）
grep LOCAL_SCHEMA ../.env

# 数据库迁移（需 PostgreSQL 已启动且 DATABASE_URL 正确）
alembic upgrade head

# 本地冒烟（可选，确认 /health）
uvicorn app.main:app --host 127.0.0.1 --port 8000
# 另开终端: curl -s http://127.0.0.1:8000/health
# 期望: {"status":"ok",...}
# Ctrl+C 停止，改由 Supervisor 守护
```

---

## 4. Supervisor 守护 uvicorn

### 4.1 宝塔界面配置

**软件商店** → **Supervisor 管理器** → **添加守护进程**：

| 字段 | 值 |
|---|---|
| 名称 | `capability-network-backend` |
| 运行目录 | `/www/wwwroot/capability-network/backend` |
| 启动命令 | `/www/wwwroot/capability-network/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2` |
| 进程数量 | 1 |

保存并 **启动**。状态应为 `RUNNING`。

### 4.2 等价配置文件（可选）

若手动编辑 Supervisor，可在 `/etc/supervisor/conf.d/capability-network.conf` 写入：

```ini
[program:capability-network-backend]
directory=/www/wwwroot/capability-network/backend
command=/www/wwwroot/capability-network/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
autostart=true
autorestart=true
startsecs=5
stopwaitsecs=10
user=www
stdout_logfile=/www/wwwlogs/capability-network-backend.log
stderr_logfile=/www/wwwlogs/capability-network-backend.err.log
environment=PATH="/www/wwwroot/capability-network/backend/.venv/bin"
```

重载：

```bash
supervisorctl reread && supervisorctl update
supervisorctl status capability-network-backend
```

### 4.3 重启脚本

```bash
chmod +x /www/wwwroot/capability-network/deploy/scripts/restart_backend.sh
/www/wwwroot/capability-network/deploy/scripts/restart_backend.sh
```

---

## 5. 前端：构建与静态目录

Vue 3 前端在服务器上构建，产物部署到 Nginx 静态根目录。

### 5.1 构建

```bash
cd /www/wwwroot/capability-network/frontend

# 与根目录 .env 中 VITE_API_URL 一致（构建时注入）
export VITE_API_URL=https://api.example.com/api/v1

npm ci
npm run build
```

构建产物通常在 `frontend/dist/`（以实际 `vite.config` 为准）。

### 5.2 部署静态文件

**网站** → **添加站点**：

| 字段 | 值 |
|---|---|
| 域名 | `www.example.com` |
| 根目录 | `/www/wwwroot/www.example.com` |
| PHP | 纯静态，可不创建 |

将构建物同步到站点目录：

```bash
mkdir -p /www/wwwroot/www.example.com
rsync -av --delete /www/wwwroot/capability-network/frontend/dist/ /www/wwwroot/www.example.com/
```

构建成功后 `frontend/dist/` 含 `index.html` 与 `assets/`。

---

## 6. Nginx 反向代理与 SSL

### 6.1 后端站点 `api.example.com`

**网站** → **添加站点** → 域名 `api.example.com`，根目录任意（仅反代，可不放文件）。

进入站点 → **配置文件**，在 `server { ... }` 内使用：

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

**SSL** → **Let's Encrypt** → 勾选 `api.example.com` → **申请**，并开启 **强制 HTTPS**。

### 6.2 前端站点 `www.example.com`

静态站点默认 Nginx 已配置 `root` 指向 `/www/wwwroot/www.example.com`。

典型 SPA 需增加 fallback（有前端路由时）：

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

同样申请 Let's Encrypt 证书并强制 HTTPS。

### 6.3 验证 Nginx

```bash
nginx -t && nginx -s reload
curl -sS https://api.example.com/health
# 期望 HTTP 200，JSON 含 "status":"ok"
```

---

## 7. 生产 `.env` 检查清单

部署前逐项确认 `/www/wwwroot/capability-network/.env`（变量名与 `docker-compose.yml` / `.env.example` 一致）：

| 变量 | 生产要求 | 说明 |
|---|---|---|
| `JWT_SECRET_KEY` | **必改** | 随机长字符串（≥32 字符）。项目使用此名，**不是** `SECRET_KEY` |
| `DATABASE_URL` | **必改** | 指向本机 PostgreSQL，与 `POSTGRES_*` 一致，例如：<br>`postgresql+asyncpg://postgres:强密码@127.0.0.1:5432/capability_network` |
| `REDIS_URL` | 建议确认 | 默认 `redis://127.0.0.1:6379/0` |
| `CORS_ORIGINS` | **必改** | 前端站点来源，逗号分隔，例如：<br>`https://www.example.com,https://example.com` |
| `POSTGRES_USER` | 与库一致 | 备份脚本 `backup_db.sh` 会读取 |
| `POSTGRES_PASSWORD` | 强密码 | 勿使用 `postgres` |
| `POSTGRES_DB` | `capability_network` | 与库名一致 |
| `DEBUG` | `false` | 生产关闭调试 |
| `LOCAL_SCHEMA` | `0` | **生产必须为 0**；`1` 仅本地无 pgvector 应急 |
| `VITE_API_URL` | 构建用 | `https://api.example.com/api/v1`（前端 `npm run build` 前 export） |

**快速自检命令：**

```bash
grep -E '^(JWT_SECRET_KEY|DATABASE_URL|CORS_ORIGINS|DEBUG|LOCAL_SCHEMA)=' /www/wwwroot/capability-network/.env
# JWT_SECRET_KEY 不应仍为 change-me-in-production
# DATABASE_URL 主机应为 127.0.0.1（非 docker 服务名 postgres）
# CORS_ORIGINS 应含 https://www.example.com
# LOCAL_SCHEMA 应为 0
```

---

## 8. 运维脚本

### 8.1 数据库备份

```bash
chmod +x /www/wwwroot/capability-network/deploy/scripts/backup_db.sh

# 默认备份到 /www/wwwroot/capability-network/backups/
/www/wwwroot/capability-network/deploy/scripts/backup_db.sh

# 自定义备份目录
BACKUP_DIR=/data/backups/capability-network /www/wwwroot/capability-network/deploy/scripts/backup_db.sh
```

建议宝塔 **计划任务** → **Shell 脚本**，每日凌晨执行上述命令。

### 8.2 重启后端

```bash
/www/wwwroot/capability-network/deploy/scripts/restart_backend.sh
```

可通过环境变量指定 Supervisor 程序名：

```bash
SUPERVISOR_PROGRAM=capability-network-backend /www/wwwroot/capability-network/deploy/scripts/restart_backend.sh
```

---

## 9. 部署后验收（M4 标准）

按顺序执行，全部通过即 **M4 宝塔项** 达标。结果写入 [`production-notes.md`](./production-notes.md)。

### 9.1 基础设施

```bash
# 1. 本机后端进程
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/health
# 期望: 200

# 2. 经 Nginx + HTTPS 公网访问
curl -sS -o /dev/null -w "%{http_code}\n" https://api.example.com/health
# 期望: 200

# 3. 响应体
curl -sS https://api.example.com/health
# 期望: {"status":"ok",...}

# 4. Supervisor 状态
supervisorctl status capability-network-backend
# 期望: RUNNING

# 5. 前端静态
curl -sS -o /dev/null -w "%{http_code}\n" https://www.example.com/
# 期望: 200
```

### 9.2 注册 + 登录冒烟（一键脚本）

```bash
chmod +x /www/wwwroot/capability-network/deploy/scripts/baota-smoke.sh

HEALTH_URL=https://api.example.com/health \
API_BASE=https://api.example.com/api/v1 \
/www/wwwroot/capability-network/deploy/scripts/baota-smoke.sh
```

或手动 curl：

```bash
# 注册
curl -sS -X POST https://api.example.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"smoke@example.com","password":"password123","display_name":"Smoke"}'

# 登录（期望 code=0 且 data.access_token 存在）
curl -sS -X POST https://api.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"account":"smoke@example.com","password":"password123"}'
```

---

## 10. 常见问题

| 现象 | 排查 |
|---|---|
| `/health` 502 | `supervisorctl status` 是否 RUNNING；`ss -lntp \| grep 8000` 是否监听 |
| 数据库连接失败 | `.env` 中 `DATABASE_URL` 用户名密码是否与 PostgreSQL 一致；防火墙是否放行本机 5432 |
| CORS 报错 | 浏览器 Origin 是否已写入 `CORS_ORIGINS`（含 `https://` 前缀） |
| `vector` 扩展错误 | 见 [1.3 节 pgvector](#13-启动-postgresql-与-redis) 与 `production-notes.md` |
| 注册 409 / 邮箱已存在 | 冒烟脚本每次用新邮箱；或换 `SMOKE_EMAIL` 环境变量 |
| SSL 申请失败 | 域名 DNS 是否生效；80/443 是否放行；是否暂时关闭 CDN 橙云 |

---

## 11. 与 Docker 开发环境对照

| 本地 Docker | 宝塔生产 |
|---|---|
| 服务名 `postgres` | `127.0.0.1:5432` |
| 服务名 `redis` | `127.0.0.1:6379` |
| `BACKEND_PORT=8000` | uvicorn 监听 `127.0.0.1:8000`，Nginx 反代 |
| 根目录 `.env` | 同路径约定，并 `ln -sf` 到 `backend/.env` |
| `docker compose up` | Supervisor + Nginx + 宝塔 PostgreSQL/Redis |

本地验证通过后，仅需替换 `.env` 中的主机与密钥即可复用同一套变量名上线。
