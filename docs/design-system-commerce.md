# 全站视觉规范 v2（Glass + 逛市场）

> **统筹会话 26 权威补充**。在 `design-system-ios26.md` 基础上，统一「能力电商」体验。  
> **参考标杆**：`/app/market`（MarketView.vue）— 搜索、类目条、商品网格、价格红、立即选用。

---

## 1. 双风格分区

| 区域 | 风格 | 典型页面 |
|------|------|----------|
| **逛 / 买 / 发现** | 电商卡片网格 + 促销条 + 搜索 | 市场、匹配结果、官网 Hero |
| **管 / 办 / 设置** | iOS GroupedList + 玻璃卡片 | 我的供给/需求/订单、钱包、表单、Admin |

同一产品内：**外圈像逛淘宝，内圈像 iOS 设置** — 不混用同一页两种主布局。

---

## 2. 新增 Token（写入 `tokens.css`）

```css
--color-commerce: #ee0a24;
--color-commerce-alt: #ff6034;
--color-commerce-muted: rgba(238, 10, 36, 0.08);
--gradient-commerce: linear-gradient(135deg, #ff6034, #ee0a24);
```

| 用途 | 类名 / 用法 |
|------|-------------|
| 主购买 CTA | `.btn-commerce`（橙红渐变，白字） |
| 价格 | `.price-commerce`（红色大字 ¥） |
| 促销标签 | `.tag-promo`（小圆角红底白字） |
| 信任标签 | `.tag-trust`（蓝底「托管支付」） |

---

## 3. 必用组件

| 组件 | 路径 | 用途 |
|------|------|------|
| `AppIcon` | `components/AppIcon.vue` | **禁止 emoji**，统一 SVG |
| `PageHeader` | `components/PageHeader.vue`（26-0 新建） | 标题 + 右侧操作按钮 |
| `EmptyState` | 已有 | 空状态 |
| `LoadingSkeleton` | 已有 | 加载 |

---

## 4. 页面改版清单

### A. 控制台 `/app/*`（会话 26-1）

| 页面 | 改版要点 |
|------|----------|
| OffersView | 卡片网格或双列；历史折叠保留 |
| IntentsView | 同 Offers；突出「AI 发需求」 |
| DealsView | 订单卡片：状态色条 + 金额 + 进度 |
| WalletView | 余额大卡 + 流水列表优化 |
| MatchingView | 候选卡片对齐 Market 商品卡风格 |
| DealDetailView | 状态 Stepper + Agent 标签突出 |
| IntentCreateView / OfferCreateView | AI 模式视觉与市场一致 |
| ConnectView | 三步向导卡片化（已有，微调） |

### B. 官网 / 认证（会话 26-2）

| 页面 | 改版要点 |
|------|----------|
| HomeView | Hero 加「逛市场」入口；特性区卡片化 |
| About / Pricing / Docs | 统一 page-hero + section 间距 |
| Login / Register | 与 Connect 同系玻璃认证卡 |
| MarketingLayout / MobileNav | 顶栏「逛市场」链接 |

### C. 运营后台 `/admin/*`（会话 26-3）

| 页面 | 改版要点 |
|------|----------|
| AdminLayout | 深色侧栏保留，图标 AppIcon |
| Dashboard | 统计卡网格 |
| Users / Deals | 表格 → 卡片列表（移动端友好） |

---

## 5. 验收标准

- [ ] 全站无 emoji 图标
- [ ] `npm run build` 通过
- [ ] 375px 无横向滚动；Tab Bar 不挡内容
- [ ] 演示路径：首页 → 逛市场 → AI 发单 → 匹配 → 支付 → 自动交付 视觉一致
- [ ] Admin 与 App 用户区视觉可区分

---

## 6. 禁止

- 不引入 Element Plus / Vant
- 不改 API 契约
- 不删现有功能路由
