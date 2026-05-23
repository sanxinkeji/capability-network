# 中文演示账号与样例数据

> **速查卡片**：[DEMO-LOGIN.md](./DEMO-LOGIN.md)（建议收藏，忘记密码先看这个）

用于本地演示与中文 UI 验收，与 E2E 脚本 `deploy/e2e-smoke.ps1` 共用同一组 QA 账号，但 seed 会**追加**中文供给/需求，不删除账号。

## 演示账号

| 角色 | 邮箱 | 密码 | 昵称（seed 后） |
|---|---|---|---|
| 卖方 | `seller_qa@test.com` | `password123` | 演示卖家 |
| 买方 | `buyer_qa@test.com` | `password123` | 演示买家 |
| 管理员 | `admin_qa@test.com` | `password123` | 演示管理员 |

## 中文样例数据

执行 seed 后会产生（或已存在则跳过重复创建）：

| 类型 | 标题 | 类目 | 金额 |
|---|---|---|---|
| 供给（已发布） | 品牌 Logo 设计服务 | design（界面显示「设计」） | ¥100.00 |
| 需求（开放） | 需要品牌 Logo 设计 | design | 预算 ¥100.00 |

供给与需求的关键词均含「品牌」「Logo」「设计」，可与 `keyword_v1` 匹配算法对接；seed **默认不创建订单**，避免重复成交污染。

若之前跑过 E2E，列表中可能仍有英文标题的旧记录。可使用 `--reset` 将演示账号下**无中文**的已发布供给暂停、开放需求关闭，再导入中文样例。

若历史数据过多（已暂停供给、已关闭/已匹配英文需求），可用 `--purge-demo` **物理删除**演示账号下的垃圾记录（跳过与订单关联的行，保留中文样例）：

```bash
python backend/scripts/seed_demo_zh.py --reset --purge-demo
```

前端列表页默认只展示**有效**条目（供给：草稿/已发布；需求：开放），历史项折叠在「已暂停」「历史需求」中。

## 执行 seed

**前置**：PostgreSQL 可用、已 `alembic upgrade head`、后端已启动（`http://127.0.0.1:8000`）。

在项目根目录：

```bash
python backend/scripts/seed_demo_zh.py
```

常用选项：

```bash
# 清理旧英文演示记录后再导入中文数据
python backend/scripts/seed_demo_zh.py --reset

# 删除已暂停供给与英文历史需求（不删订单关联数据）
python backend/scripts/seed_demo_zh.py --purge-demo

# 推荐：重置 + 清理 + 匹配验证
python backend/scripts/seed_demo_zh.py --reset --purge-demo --run-match

# 导入后跑一遍匹配（不创建 deal）
python backend/scripts/seed_demo_zh.py --run-match

# 指定 API 地址
python backend/scripts/seed_demo_zh.py --base-url http://127.0.0.1:8000/api/v1
```

Windows 本地一键环境见 `deploy/local-windows.ps1`；Setup 完成后需**先启动后端**，再执行上述 seed 命令。

## 验收步骤

1. 执行 `python backend/scripts/seed_demo_zh.py --reset --purge-demo --run-match`
2. 打开前端 `http://localhost:5173`，用卖方账号登录 → 「我的供给」默认只见中文 **品牌 Logo 设计服务**（已暂停项折叠）
3. 用买方账号登录 → 「我的需求」默认只见 **需要品牌 Logo 设计**
4. 钱包流水类型与说明应为中文（充值、结算、模拟充值等）
5. 在需求详情触发匹配 → 应命中卖方中文供给
6. 用管理员账号登录 → 自动进入 `/admin`，可查看全平台用户与订单；争议单可退款或代确认

## 与 pytest / E2E 的关系

- `pytest tests/ -q` 使用内存 SQLite，**不会**自动运行本 seed
- `deploy/e2e-smoke.ps1` 仍会写入英文样例；演示前建议再跑一遍 `--reset` 的中文 seed
