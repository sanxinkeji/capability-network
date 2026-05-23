# capability-network QA 检查清单（M4 生产前回归）

> **适用阶段**：M1–M3 已完成，M4 生产就绪前最后一轮质量检查  
> **执行人**：会话 16（或任意 QA 会话）  
> **更新**：2026-05-23

---

## 0. 前置条件

| 项 | 要求 |
|----|------|
| OS | Windows 10+（本清单以无 Docker 本地环境为准） |
| Python | 3.11+，`backend/requirements.txt` 已安装 |
| Node.js | 18+，`frontend/node_modules` 已安装 |
| PostgreSQL | 17（或 15/16），服务运行中 |
| `.env` | 项目根目录存在，密码与 PG 安装一致 |

---

## 1. 环境检查

在项目根目录执行：

```powershell
# 1.1 确认 PostgreSQL 服务
Get-Service -Name "postgresql*" | Select-Object Name, Status

# 1.2 确认 psql 可用
psql --version

# 1.3 确认 .env 存在且 DATABASE_URL 正确
Get-Content .env | Select-String "POSTGRES|DATABASE"

# 1.4 确认 Python / Node 版本
python --version
node --version
npm --version
```

**通过标准**：PG 服务 `Running`；`.env` 中 `POSTGRES_PASSWORD` 与安装时一致。

---

## 2. 数据库迁移

```powershell
cd backend
$env:LOCAL_SCHEMA = "1"
# 加载 .env（或手动设置 DATABASE_URL）
python -m alembic upgrade head
```

**通过标准**：`alembic upgrade head` 退出码 0，无报错。

也可一键 setup：

```powershell
powershell -ExecutionPolicy Bypass -File deploy\local-windows.ps1 -SetupOnly
```

---

## 3. 后端单测（pytest）

```powershell
cd backend
python -m pytest tests/ -q
```

**通过标准**：全部通过（当前基线 **19/19**）。

| 套件 | 覆盖 |
|------|------|
| `test_auth.py` | 注册 / 登录 |
| `test_deals.py` | 成交状态机、match_log_id 下单 |
| `test_deals_api.py` | HTTP 层 deals API |
| `test_e2e_flow.py` | 完整 REST 流程（含 match_log_id） |
| `test_matching.py` | 匹配打分 |
| `test_offers.py` / `test_intents.py` | 供给 / 需求 CRUD |
| `test_wallets.py` | 充值 / 冻结 / 结算 |

---

## 4. E2E Smoke（REST API 全流程）

**前置**：后端已在 `http://127.0.0.1:8000` 运行。

```powershell
# 项目根目录
powershell -ExecutionPolicy Bypass -File deploy\e2e-smoke.ps1
```

**脚本覆盖步骤**：

1. 注册/登录 buyer + seller  
2. Buyer 充值 10000 分  
3. Seller 创建并发布 offer  
4. Buyer 创建 intent  
5. 运行 matching，取 top 候选 `match_log_id`  
6. **用 `match_log_id` 创建 deal** → 支付 → 交付 → 确认  
7. 校验钱包余额、deals 列表、ledger  

**通过标准**：终端输出 `==> E2E PASSED`（绿色）。

---

## 5. 前端构建

```powershell
cd frontend
npm run build
```

**通过标准**：`vite build` 成功，`dist/` 生成，无 TypeScript / 编译错误。

---

## 6. 启动本地服务（手工浏览器测试前）

```powershell
# 方式 A：一键启动（新窗口）
powershell -ExecutionPolicy Bypass -File deploy\local-windows.ps1 -Start

# 方式 B：手动
cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd frontend && npm run dev
```

访问：`http://localhost:5173`

---

## 7. 浏览器手工用例

### 7.1 官网（未登录）

| # | 步骤 | 预期 |
|---|------|------|
| 1 | 清除 localStorage / 无痕窗口访问 `/` | 显示官网首页，**不**跳转登录页 |
| 2 | 访问 `/about` | About 页正常，Marketing 布局 |
| 3 | 访问 `/pricing` | Pricing 页正常 |
| 4 | 点击导航「登录」 | 进入 `/login` |
| 5 | 直接访问 `/app/offers`（无 token） | 重定向到 `/login?redirect=...` |

### 7.2 控制台全流程（登录后）

使用测试账号或新注册账号，在 `/app` 内完成：

| # | 步骤 | 预期 |
|---|------|------|
| 1 | 登录 → 进入 `/app` | 默认跳转 `/app/offers` |
| 2 | **钱包** → 充值 | 余额更新 |
| 3 | **供给** → 新建 → 发布 | 列表可见，状态「已发布」 |
| 4 | **需求** → 新建 intent | 列表可见 |
| 5 | 进入匹配页 `/app/matching/:intentId` | 显示候选列表与分数 |
| 6 | 点击「创建成交」 | 跳转 deal 详情，状态 pending |
| 7 | 买家支付 | 状态 → paid |
| 8 | 卖家交付 | 状态 → delivered |
| 9 | 买家确认 | 状态 → completed |

> 完整买卖需两个账号（买家 + 卖家），或同一账号自买自卖（若业务允许）。

### 7.3 移动端（375px 宽）

| # | 步骤 | 预期 |
|---|------|------|
| 1 | DevTools 设 viewport 375×812 | 布局不溢出 |
| 2 | 底部 Tab Bar | 供给 / 需求 / 成交 / 钱包 可切换 |
| 3 | 各 Tab 页内容 | 可滚动，按钮可点 |
| 4 | 官网 `/` 375px | 导航可用，无横向滚动条 |

---

## 8. 记录与汇报

执行完毕后填写 `docs/qa-report-YYYYMMDD.md`：

- **通过项** / **失败项** / **阻塞项**
- 失败截图或报错摘要
- **建议交给哪一会话**（见 `docs/project-roadmap.md` 会话分工）

汇报格式：

```
【会话 N 完成】通过 X 项 / 失败 Y 项 / 阻塞 Z 项
```

---

## 9. 已知缺口（非阻塞）

| 项 | 负责会话 |
|----|----------|
| og-image.png | 12-收尾 |
| 宝塔 + HTTPS 生产部署 | 9 |
| Git push + CI 首次绿灯 | 0-运维 |
| 场景包 scenes | 10（可选） |
| 深色模式 polish | 17（可选） |
