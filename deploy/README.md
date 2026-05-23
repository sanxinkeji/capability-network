# Deploy

部署相关配置与文档。

| 文件 / 目录 | 说明 |
|---|---|
| [`baota.md`](./baota.md) | **宝塔面板** 生产环境手把手部署（Nginx、SSL、Supervisor、M4 验收） |
| [`BAOTA-UPLOAD.md`](./BAOTA-UPLOAD.md) | **上传测试清单**（打包、构建、验收步骤） |
| [`production-notes.md`](./production-notes.md) | **会话 9** 部署记录：域名、路径、踩坑、生产实测回填 |
| [`scripts/baota-smoke.sh`](./scripts/baota-smoke.sh) | 生产冒烟：`/health` + 注册 + 登录 |
| [`scripts/backup_db.sh`](./scripts/backup_db.sh) | PostgreSQL 备份（读取根目录 `.env` 中 `POSTGRES_*`） |
| [`scripts/restart_backend.sh`](./scripts/restart_backend.sh) | 通过 Supervisor 重启 uvicorn 后端 |
| [`e2e-smoke.ps1`](./e2e-smoke.ps1) | 本地 Windows 全链路 E2E（买卖成交） |
| 项目根目录 [`docker-compose.yml`](../docker-compose.yml) | 本地开发：PostgreSQL、Redis、Backend |

环境变量命名以根目录 [`.env.example`](../.env.example) 为准，Docker 与宝塔生产保持一致。
