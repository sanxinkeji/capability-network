# 商用上线勾选清单

> **用途**：发布前按 P0 / P1 逐项勾选，配合 [deploy/production-notes.md](../deploy/production-notes.md) 与 [deploy/baota.md](../deploy/baota.md) 使用。  
> **CI 基线**：PR 合并前须通过 `.github/workflows/ci.yml`（backend coverage ≥60%、frontend vitest + build）。

---

## P0 — 上线阻断项（必须全部 ✅）

### 安全与密钥

- [ ] `DEBUG=false`，且 `JWT_SECRET_KEY` 为随机 ≥32 字符（非 `change-me-in-production`）
- [ ] 生产 `.env` 仅存在于服务器，**未提交 git**
- [ ] PostgreSQL / Redis 使用强密码；数据库端口不对公网暴露
- [ ] `CORS_ORIGINS` 仅包含正式前端域名
- [ ] `RATE_LIMIT_ENABLED=true`，`REDIS_URL` 可用（限流与登录锁定依赖 Redis）
- [ ] 管理后台仅 admin 可访问；演示/测试账号已禁用或改密

### 基础设施与健康检查

- [ ] `GET /health` 返回 200（负载均衡存活探针）
- [ ] `GET /health/ready` 返回 200（DB + Redis 就绪）
- [ ] Supervisor / systemd 配置自动重启；日志路径可写
- [ ] Nginx：API 反代 + 前端静态；HTTPS 证书有效
- [ ] 数据库迁移 `alembic upgrade head` 已在生产执行

### 核心业务流程

- [ ] 注册 / 登录 / 刷新 token 正常
- [ ] 供给发布 → 需求创建 → 匹配 → 成交 → 支付 → 交付 → 确认 全链路可用
- [ ] 钱包充值、冻结、结算、佣金扣取与 ledger 一致
- [ ] 维护模式开关验证：非 admin 用户收到 503，admin 与 `/health*` 不受影响

### CI 与冒烟

- [ ] GitHub Actions CI 绿色（backend pytest + coverage、frontend vitest + build）
- [ ] 生产或预发执行 `deploy/scripts/baota-smoke.sh`（health + ready + register + login）
- [ ] 可选：commit message 含 `[smoke]` 或手动触发 workflow 的 docker compose smoke job

### 前端与 Agent

- [ ] `npm run build` 产物部署至静态目录；`VITE_API_URL` 指向生产 API
- [ ] 登录页、市场、钱包、订单、运营后台关键页面可访问
- [ ] MCP Server 配置 `BACKEND_URL` + 有效 `cnk_...` API Key（见 [mcp-server/README.md](../mcp-server/README.md)）

---

## P1 — 商用体验与运维（强烈建议 ✅）

### 可观测性

- [ ] 配置 `SENTRY_DSN`（未配置则跳过，但生产建议开启）
- [ ] 后端日志轮转；磁盘空间监控
- [ ] 管理端 `GET /api/v1/admin/ops-health` 资源探测正常

### 支付与合规

- [ ] 支付通道（微信 / 支付宝 / Stripe / Easypay）在沙箱或小额实测通过
- [ ] 支付回调 URL 公网可达且验签正确
- [ ] 法律条款 / 用户协议已配置（`legal_terms_enabled`、协议正文）
- [ ] KYC 流程与隐私说明符合业务所在地要求

### 邮件与通知

- [ ] SMTP 配置完成；注册验证码邮件可送达
- [ ] `support_email` / `support_url` 在平台设置中填写

### 备份与恢复

- [ ] S3 / 本地备份策略已启用（`backup_auto_enabled` 或 cron）
- [ ] 至少完成一次备份恢复演练

### 性能与容量

- [ ] 核心 API p95 延迟在可接受范围（建议 <500ms，不含支付第三方）
- [ ] PostgreSQL 连接池与 Redis 内存配置合理
- [ ] 静态资源 CDN 或 Nginx gzip / 缓存头已配置

### 文档与交付

- [ ] [docs/DEMO-LOGIN.md](./DEMO-LOGIN.md) 演示账号说明与生产隔离
- [ ] [docs/api-contract.md](./api-contract.md) 与线上行为一致
- [ ] 运维手册：发版步骤、回滚步骤、值班联系人

---

## 快速命令参考

```bash
# 本地 / CI 后端测试 + 覆盖率
cd backend && pytest tests/ -q --cov=app --cov-fail-under=60

# 前端单元测试
cd frontend && npm run test:ci

# 生产冒烟（替换域名）
API_BASE=https://api.example.com/api/v1 ./deploy/scripts/baota-smoke.sh

# 本地 docker 全栈 + 冒烟
cp .env.example .env   # 修改 JWT_SECRET_KEY
docker compose up -d --build --wait
HEALTH_URL=http://127.0.0.1:8000/health API_BASE=http://127.0.0.1:8000/api/v1 ./deploy/scripts/baota-smoke.sh
```

---

## 覆盖率与测试演进目标

| 区域 | 当前 CI 门槛 | 建议下一阶段 |
|------|-------------|-------------|
| Backend `app/` | ≥60% | 70%+，补齐 payment / email / backup |
| Frontend 核心模块 | vitest 单元测试 | 扩展 router guard、wallet 工具函数 |
| E2E | smoke 脚本 | 按需引入 Playwright（非 P0） |
