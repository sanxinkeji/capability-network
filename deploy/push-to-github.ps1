# 一键推送到 GitHub（Windows）
# 用法：在 PowerShell 中右键「使用 PowerShell 运行」，或在项目根目录执行：
#   powershell -ExecutionPolicy Bypass -File deploy\push-to-github.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Git = "C:\Program Files\Git\bin\git.exe"
$Gh = "C:\Program Files\GitHub CLI\gh.exe"

if (-not (Test-Path $Git)) { throw "未找到 Git，请先安装 Git for Windows" }
if (-not (Test-Path $Gh)) { throw "未找到 GitHub CLI，请先安装 gh" }

Write-Host "`n=== capability-network 推送到 GitHub ===`n" -ForegroundColor Cyan

# 1. 检查 gh 登录
$authOk = $false
try {
    & $Gh auth status 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $authOk = $true }
} catch {}

if (-not $authOk) {
    Write-Host "需要授权 GitHub CLI（只需做一次）。" -ForegroundColor Yellow
    Write-Host "即将打开浏览器，请登录 GitHub 并粘贴终端里显示的验证码。`n"
    Start-Process "https://github.com/login/device"
    & $Gh auth login --hostname github.com --git-protocol https --web
    if ($LASTEXITCODE -ne 0) { throw "GitHub 授权失败" }
}

$user = (& $Gh api user -q .login).Trim()
Write-Host "已登录 GitHub 用户: $user`n" -ForegroundColor Green

# 2. 创建仓库并推送（若 remote 已存在则只 push）
$remote = & $Git remote get-url origin 2>$null
if (-not $remote) {
    Write-Host "正在创建私有仓库 github.com/$user/capability-network ..." -ForegroundColor Cyan
    & $Gh repo create capability-network --private --source=. --remote=origin --push
    if ($LASTEXITCODE -ne 0) { throw "创建仓库或推送失败" }
} else {
    Write-Host "远程仓库已存在: $remote" -ForegroundColor Cyan
    & $Git push -u origin main
    if ($LASTEXITCODE -ne 0) { throw "推送失败" }
}

$url = "https://github.com/$user/capability-network"
Write-Host "`n完成！仓库地址：`n  $url`n" -ForegroundColor Green
