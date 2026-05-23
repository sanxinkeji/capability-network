# 上传到 Git 仓库

## 一、在 GitHub / Gitee 创建空仓库

1. 登录 [GitHub](https://github.com/new) 或 [Gitee](https://gitee.com/projects/new)
2. 仓库名建议：`capability-network`
3. **不要**勾选「Initialize with README」（保持空仓库）
4. 复制仓库地址，例如：
   - GitHub：`https://github.com/你的用户名/capability-network.git`
   - Gitee：`https://gitee.com/你的用户名/capability-network.git`

## 二、本地首次推送（Windows）

在项目根目录执行（Git 已安装后）：

```powershell
cd C:\Users\Administrator\Desktop\capability-network

# 若尚未初始化（已由助手完成可跳过）
git init
git add .
git commit -m "Initial commit: capability-network production-ready"

# 绑定远程并推送（把 URL 换成你的）
git branch -M main
git remote add origin https://github.com/你的用户名/capability-network.git
git push -u origin main
```

推送时输入 GitHub/Gitee 用户名与 **Personal Access Token**（不是登录密码）。

### 生成 Token（GitHub）

Settings → Developer settings → Personal access tokens → Generate new token → 勾选 `repo` 权限。

## 三、后续更新

```powershell
git add .
git commit -m "描述本次改动"
git push
```

## 四、宝塔服务器拉取

```bash
cd /www/wwwroot
git clone https://github.com/你的用户名/capability-network.git
cd capability-network
# 后续更新：git pull
```

部署步骤见 **[宝塔部署指南.md](./宝塔部署指南.md)**。

## 五、切勿提交的文件

已在 `.gitignore` 中排除：

- `.env`、`backend/.env`（含数据库密码、JWT 密钥）
- `node_modules/`、`.venv/`
- 本地构建缓存、备份目录

服务器上单独 `cp .env.example .env` 并修改生产配置。
