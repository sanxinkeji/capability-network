# iOS 26 设计系统（Liquid Glass）

capability-network 前端视觉规范，参考 Apple iOS 26 / Liquid Glass 语言：**半透明材质、大圆角、系统蓝、分层背景**。

---

## 1. 设计 token

定义于 `frontend/src/styles/tokens.css`。

| Token | 值 | 用途 |
|-------|-----|------|
| `--color-primary` | `#007AFF` | 主操作、链接 |
| `--color-bg-base` | `#F2F2F7` | 页面底色（systemGroupedBackground） |
| `--color-bg-elevated` | `rgba(255,255,255,0.72)` | 玻璃卡片 |
| `--glass-blur` | `20px` | backdrop-filter |
| `--radius-card` | `20px` | 卡片 |
| `--radius-pill` | `999px` | 按钮 |
| `--shadow-glass` | 多层轻阴影 | 浮起感 |

---

## 2. 组件类名（global）

| 类名 | 说明 |
|------|------|
| `.glass-card` | 磨砂玻璃容器 |
| `.btn` / `.btn-primary` | 填充主按钮（pill） |
| `.btn-secondary` | 玻璃描边按钮 |
| `.grouped-list` | iOS Inset Grouped 列表 |
| `.grouped-item` | 列表行 |
| `.page-header` | 大标题区（Large Title 风格） |
| `.site-nav` | 官网顶栏 |

---

## 3. 布局

### 官网（MarketingLayout）

- 顶栏：Logo + 锚点导航 + 登录 / 注册
- Hero：渐变 mesh + 玻璃 CTA 卡片
- 区块：特性三列、流程四步、底部 CTA
- 页脚：链接 + 版权

### 控制台（AppLayout）

- 桌面：左侧玻璃侧栏 + 主内容
- 移动（会话 11）：底部 Tab Bar
- 背景：`--color-bg-base`，内容区 `--color-bg-elevated` 卡片

---

## 4.  Typography

```css
font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', system-ui, sans-serif;
```

| 级别 | 大小 | 字重 |
|------|------|------|
| Large Title | 34px | 700 |
| Title 1 | 28px | 700 |
| Title 2 | 22px | 600 |
| Body | 17px | 400 |
| Caption | 13px | 400，secondary label |

---

## 5. 状态色

与 iOS Human Interface Guidelines 对齐：

- Success: `#34C759`
- Warning: `#FF9500`
- Destructive: `#FF3B30`
- Secondary label: `#8E8E93`

---

## 6. 禁止事项

- 不使用 Element Plus / Ant Design（保持包体小）
- 不在业务页使用 `#2563eb` 等非系统蓝
- 官网与 `/app` 共用 token，不另起一套色板

---

## 7. 电商风格补充

逛市场、匹配候选等「买 / 发现」场景的视觉与组件规范见 **[design-system-commerce.md](./design-system-commerce.md)**（橙红促销色、商品卡、`.btn-commerce` 等）。
