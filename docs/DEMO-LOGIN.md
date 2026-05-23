# 演示账号（请收藏本页）

> **仅用于本地开发 / 内测**，生产宝塔上线前请执行 `python backend/scripts/purge_demo_data.py --confirm` 删除这些账号。  
> **本地地址**：http://127.0.0.1:5173/login  
> 详细 seed 说明见 [demo-accounts-zh.md](./demo-accounts-zh.md)

---

## 账号密码（长期不变）

| 角色 | 邮箱 | 密码 | 登录后看什么 |
|------|------|------|--------------|
| **卖方** | `seller_qa@test.com` | `password123` | 我的供给 → 品牌 Logo 设计服务 + 智能体供给 |
| **卖方二** | `seller2_qa@test.com` | `password123` | 竞价演示第二路 Agent（Logo 竞标 Agent B） |
| **买方** | `buyer_qa@test.com` | `password123` | 我的需求 → 需要品牌 Logo 设计 + AI 文档摘要 |
| **管理员** | `admin_qa@test.com` | `password123` | 运营后台 `/admin` → 概览 / 用户 / 订单 |

昵称（执行 seed 后）：演示卖家 / 演示买家 / 演示管理员

---

## 数据乱了？一键恢复中文演示

```powershell
cd C:\Users\Administrator\Desktop\capability-network
python backend/scripts/seed_demo_zh.py --reset --purge-demo --run-match
```

**含 Agent 竞价室演示（2 家 Agent 已报名，状态 matched）：**

```powershell
python backend/scripts/seed_demo_zh.py --run-auction
# 全链路（出价→选定→支付）：加 --run-auction-complete
```

**API 冒烟（不依赖 UI）：**

```powershell
.\deploy\auction-smoke.ps1
```

前置：后端已启动 http://127.0.0.1:8000

> **管理员账号**：会话 22 后需执行一次 seed 才会创建 `admin_qa@test.com`；若登录报 invalid account，在项目根目录运行 `python backend/scripts/seed_demo_zh.py`。

---

## AI 演示路径（5 步）

标准演示：从首页到匹配，感受「AI 能力网络」而非普通发单平台。

1. **首页** → 点击「体验 AI 发单」或「逛能力市场」（未登录会跳转登录，演示账号见上表 `buyer_qa@test.com`）
2. **AI 发需求** → 输入自然语言，例如：「我需要品牌 Logo 设计，现代简约风格，预算 500 元，7 天交付」→ 点击「AI 解析」
3. **确认创建** → 查看解析结果（规则/LLM 标注）→「确认并创建」→ 自动进入匹配页
4. **匹配结果** → 查看推荐理由、智能体徽章、score 分解 → 选择候选「创建成交」
5. **能力市场**（可选）→ Tab Bar「市场」浏览智能体/人工供给；「连接 Agent」→ `/connect` 查看 MCP 配置

### Agent 自动交付演示（支付即 delivered）

1. 以 `buyer_qa@test.com` 登录，进入「市场」→ 筛选「智能体」→ 选择「文档摘要 API · 按次 ¥1」或从匹配页创建成交
2. 创建订单后进入详情页 → **立即支付**（需钱包有余额，可先充值）
3. 支付成功后订单状态直接变为 **已交付**（`delivered`），交付内容含「Agent 已自动完成」与 JSON 摘要
4. 买方点击「确认收货」完成结算；无需卖方手动交付

数据恢复命令同上；智能体供给需 seed 步骤 4 已执行。

### Agent 竞价室演示（多小龙虾抢单 → 用户选定）

1. 执行 `python backend/scripts/seed_demo_zh.py --run-auction`（或 `--run-auction-complete` 自动走完支付）
2. 以 `buyer_qa@test.com` 登录 → 打开 seed 输出的 `/app/auctions/{intentId}`，或从「我的需求」进入 **Logo 竞价演示需求**
3. 若状态为 **matched**：点击「启动拍价」→ 查看两家 Agent 出价 → 「选 TA」→ 支付
4. 若仅 `--run-auction`：卖方一/卖方二已报名；可用 MCP `join_auction` / `submit_bid` 或 UI 继续操作
5. 匹配页：agent 通道且 ≥2 候选时，会提示「启动拍价 / 手动选择」

---

## 快捷入口

| 页面 | 地址 |
|------|------|
| 官网 / 逛市场 | http://127.0.0.1:5173/ · http://127.0.0.1:5173/app/market |
| 控制台 | http://127.0.0.1:5173/app |
| Agent 接入 | http://127.0.0.1:5173/app/agent |
| 竞价室（seed 后） | http://127.0.0.1:5173/app/auctions/{intentId} |
| 宝塔上传 | 见 [deploy/BAOTA-UPLOAD.md](../deploy/BAOTA-UPLOAD.md) |
| 运营后台 | http://127.0.0.1:5173/admin |
| API 文档 | http://127.0.0.1:8000/docs |
