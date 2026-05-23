# 会话 9 — 宝塔生产部署记录

> **更新时间**：2026-05-23  
> **执行环境**：本机 Windows 开发机（可本地冒烟）；**宝塔 Linux 生产机需运维按 [`baota.md`](./baota.md) 逐步执行并回填下文「生产实测」**

---

## 前提确认（部署前）

| 项 | 状态 | 说明 |
|---|---|---|
| Linux + 宝塔已安装 | ⏳ **待确认** | 需运维提供面板地址与 SSH |
| 域名解析 | ⏳ **待确认** | `api.xxx.com` → 后端；`www.xxx.com` → 前端 |
| 强密码 / `JWT_SECRET_KEY` | ⏳ **待确认** | 仅写入服务器 `/www/wwwroot/capability-network/.env`，**勿提交 git** |
| 仓库代码 | ✅ | 含 `deploy/baota.md`、运维脚本、前端可 `npm run build` |

请将下文 `xxx.com` 替换为实际主域名后再执行宝塔步骤。

---

## URL 与路径（规划）

| 项 | 值 |
|---|---|
| **API URL** | `https://api.xxx.com` |
| **API Base** | `https://api.xxx.com/api/v1` |
| **前端 URL** | `https://www.xxx.com` |
| **Health（存活）** | `https://api.xxx.com/health` |
| **Health（就绪，含 DB/Redis）** | `https://api.xxx.com/health/ready` |
| **项目根目录** | `/www/wwwroot/capability-network` |
| **后端 venv** | `/www/wwwroot/capability-network/backend/.venv` |
| **前端构建物** | `/www/wwwroot/capability-network/frontend/dist` |
| **Nginx 静态根** | `/www/wwwroot/www.xxx.com` |
| **Supervisor 程序名** | `capability-network-backend` |
| **后端日志** | `/www/wwwlogs/capability-network-backend.log` |

---

## 生产 `.env` 要点（M4）

与 [`.env.example`](../.env.example) 命名一致，服务器上 `cp .env.example .env` 后修改：

```bash
DEBUG=false
LOCAL_SCHEMA=0
JWT_SECRET_KEY=<随机≥32字符>
DATABASE_URL=postgresql+asyncpg://<用户>:<强密码>@127.0.0.1:5432/capability_network
REDIS_URL=redis://127.0.0.1:6379/0
CORS_ORIGINS=https://www.xxx.com,https://xxx.com
VITE_API_URL=https://api.xxx.com/api/v1

# API 安全（Redis 必填；限流与登录锁定依赖 REDIS_URL）
RATE_LIMIT_ENABLED=true
LOGIN_MAX_ATTEMPTS=5
LOGIN_LOCKOUT_SECONDS=900
LOGIN_LOCKOUT_SCOPE=account

# 可选：Sentry 错误监控（未配置则跳过）
# SENTRY_DSN=https://xxx@o000.ingest.sentry.io/000
# SENTRY_ENVIRONMENT=production
# SENTRY_TRACES_SAMPLE_RATE=0.1
```

**安全说明**：

- `DEBUG=false` 时后端**拒绝启动**若 `JWT_SECRET_KEY` 仍为默认值 `change-me-in-production`
- `DEBUG=false` 时 `/docs`、`/redoc` **不可访问**（开发环境 `DEBUG=true` 可保留）
- 登录 / 注册 / 支付回调 / Agent Key 签发 均受 Redis 滑动窗口限流；连续登录失败会临时锁定（账号或 IP，见 `LOGIN_LOCKOUT_SCOPE`）
- **`GET /health`**：轻量存活探针，不访问 DB/Redis，适合负载均衡心跳
- **`GET /health/ready`**：就绪探针，执行 PostgreSQL `SELECT 1` 与 Redis `PING`；任一失败返回 **503**
- **`GET /api/v1/admin/ops-health`**：管理端运维面板，`resources` 含数据库 / Redis / 支付通道真实探测结果（非占位）
- **维护模式**：后台 `maintenance_mode=true` 时，非 admin 用户的 `/api/v1/*` 返回 **503**（`code=50301`）；admin、公开 settings、登录/刷新、支付回调、`/health*` 不受限
- **Sentry**：配置 `SENTRY_DSN` 后自动上报异常；未配置则跳过

软链（Supervisor 从 `backend/` 启动）：

```bash
ln -sf /www/wwwroot/capability-network/.env /www/wwwroot/capability-network/backend/.env
```

---

## 本机预检（已完成）

在 **Windows 开发机** 上验证，不代表生产已上线：

| 检查项 | 结果 |
|---|---|
| `npm run build`（frontend） | ✅ 通过 |
| `GET http://127.0.0.1:8000/health` | ✅ **200** — `{"status":"ok","service":"capability-network-backend","version":"0.1.0"}` |
| `GET http://127.0.0.1:8000/health/ready` | ✅ **200** — `status=ok`，含 `checks.database` / `checks.redis` |
| `deploy/admin-smoke.ps1`（含 ops-health 资源探测） | ✅ 本机 admin 账号可用时通过 |
| `POST /api/v1/auth/register` + `/auth/login` | ✅ `code=0`，返回 `access_token` |
| `GET /docs`（`DEBUG=false` 时应 404） | ⏳ 生产部署后验证 |

---

## 生产实测（宝塔执行后回填）

> 在服务器完成 [`baota.md`](./baota.md) 后，运行冒烟脚本并填写本节。

```bash
chmod +x /www/wwwroot/capability-network/deploy/scripts/baota-smoke.sh
HEALTH_URL=https://api.xxx.com/health \
READY_URL=https://api.xxx.com/health/ready \
API_BASE=https://api.xxx.com/api/v1 \
/www/wwwroot/capability-network/deploy/scripts/baota-smoke.sh
```

| 检查项 | HTTP | 结果 |
|---|---|---|
| `GET https://api.xxx.com/health` | ⏳ | |
| `GET https://api.xxx.com/health/ready` | ⏳ | |
| `POST .../auth/register` | ⏳ | |
| `POST .../auth/login` | ⏳ | |
| `GET https://www.xxx.com/` | ⏳ | |
| Supervisor `RUNNING` | ⏳ | |
| Let's Encrypt 有效 | ⏳ | |

---

## 踩坑与 Workaround

### 1. pgvector 扩展（`alembic upgrade head`）

**现象**：`ERROR: extension "vector" is not available`

**原因**：宝塔 PostgreSQL 默认未带 [pgvector](https://github.com/pgvector/pgvector)。

**Workaround A（推荐生产）**：编译安装 pgvector 后：

```sql
\c capability_network
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

再执行 `LOCAL_SCHEMA=0 alembic upgrade head`（或 `.env` 中 `LOCAL_SCHEMA=0`）。

**Workaround B（仅应急，不符合 M4 完整 schema）**：临时 `LOCAL_SCHEMA=1` 使用 `docs/database-schema-local.sql`（无 vector 列）。**生产正式环境应回到 Workaround A 并 `LOCAL_SCHEMA=0`。**

### 2. `.env` 未被后端读取

**现象**：数据库连不上或仍用默认密钥。

**处理**：确认 `backend/.env` 软链指向项目根 `.env`；Supervisor「运行目录」为 `backend/`。

### 3. CORS 浏览器报错

**现象**：前端能打开，登录请求被 CORS 拦截。

**处理**：`CORS_ORIGINS` 必须含 `https://www.xxx.com`（带协议，无尾斜杠）；改后 `restart_backend.sh`。

### 4. 前端 API 地址错误

**现象**：静态页加载正常，接口 404 或连错域。

**处理**：构建前 `export VITE_API_URL=https://api.xxx.com/api/v1`，再 `npm run build` 并 `rsync dist/`。

### 5. SSL 申请失败

**处理**：DNS 生效、关闭 CDN 橙云、安全组放行 80/443，宝塔站点先能 HTTP 访问再申请 Let's Encrypt。

---

## 未完成项

| 项 | 负责人 | 说明 |
|---|---|---|
| 宝塔服务器实际部署 | 运维 | 本记录在本机完成预检；需在 Linux 按 `baota.md` 执行 |
| 填写「生产实测」表 | 运维 | 部署完成后运行 `baota-smoke.sh` 并更新上文表格 |
| 替换 `xxx.com` 为真实域名 | 运维 | API / 前端 URL、CORS、VITE_API_URL |
| 计划任务：每日 `backup_db.sh` | 运维 | 见下文「定时备份」 |
| CI 首次 push 绿灯 | 会话 0 | 见 `docs/project-roadmap.md` M4 |

---

## 定时备份（cron）

后台「数据备份」Tab 可手动触发 `POST /api/v1/admin/backups/trigger`；生产环境建议同时配置系统 cron，与 `deploy/scripts/backup_db.sh` 逻辑一致（`pg_dump | gzip` → 本地 `backups/` 目录）。

若已在后台配置 S3/R2（`backup_s3_*`），手动触发会自动上传；**cron 脚本目前仅写本地文件**，如需自动上传可改为调用 Admin API（需 admin JWT）或后续扩展脚本。

### 宝塔 / Linux cron 示例（每日凌晨 2 点）

```bash
# crontab -e
0 2 * * * cd /www/wwwroot/capability-network && BACKUP_DIR=/www/wwwroot/capability-network/backups /bin/bash deploy/scripts/backup_db.sh >> /www/wwwlogs/capability-network-backup.log 2>&1
```

说明：

- 与后台默认 `backup_cron=0 2 * * *` 对齐（每天 02:00）
- 确保服务器已安装 `pg_dump`，且 `.env` 中 `POSTGRES_*` / `DATABASE_URL` 正确
- 备份文件默认：`/www/wwwroot/capability-network/backups/<db>_YYYYMMDD_HHMMSS.sql.gz`
- 日志：`/www/wwwlogs/capability-network-backup.log`

### 可选：通过 API 触发（含 S3 上传与历史记录）

```bash
# 需先登录获取 admin access_token
curl -sS -X POST "https://api.xxx.com/api/v1/admin/backups/trigger" \
  -H "Authorization: Bearer <ADMIN_ACCESS_TOKEN>"
```

演练模式（不写盘、不上传）：`?dry_run=true`（测试或权限校验用）。

---

## 快速命令索引

```bash
# 迁移（生产 LOCAL_SCHEMA=0）
cd /www/wwwroot/capability-network/backend && source .venv/bin/activate
alembic upgrade head

# 前端构建 + 发布
cd /www/wwwroot/capability-network/frontend
export VITE_API_URL=https://api.xxx.com/api/v1
npm ci && npm run build
rsync -av --delete dist/ /www/wwwroot/www.xxx.com/

# 重启后端
/www/wwwroot/capability-network/deploy/scripts/restart_backend.sh
```
