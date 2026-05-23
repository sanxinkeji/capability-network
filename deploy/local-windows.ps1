#Requires -Version 5.1
<#
.SYNOPSIS
  本地 Windows 无 Docker 启动 capability-network（Python + PostgreSQL）

.USAGE
  powershell -ExecutionPolicy Bypass -File deploy\local-windows.ps1
  powershell -ExecutionPolicy Bypass -File deploy\local-windows.ps1 -SetupOnly
  powershell -ExecutionPolicy Bypass -File deploy\local-windows.ps1 -Start
#>
param(
    [switch]$SetupOnly,
    [switch]$Start
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$EnvFile = Join-Path $Root ".env"

function Find-Psql {
    $candidates = @(
        "C:\Program Files\PostgreSQL\17\bin\psql.exe",
        "C:\Program Files\PostgreSQL\16\bin\psql.exe",
        "C:\Program Files\PostgreSQL\15\bin\psql.exe"
    )
    foreach ($p in $candidates) {
        if (Test-Path $p) { return $p }
    }
    $found = Get-Command psql -ErrorAction SilentlyContinue
    if ($found) { return $found.Source }
    return $null
}

Write-Host "==> capability-network 本地部署（无 Docker）" -ForegroundColor Cyan
Write-Host "项目目录: $Root"

# 同步 .env 到 backend
Copy-Item $EnvFile (Join-Path $Backend ".env") -Force

# 安装 Python 依赖
Write-Host "`n==> 安装后端依赖..." -ForegroundColor Cyan
Set-Location $Backend
python -m pip install -U pip -q
python -m pip install -r requirements.txt -q

# PostgreSQL
$psql = Find-Psql
if (-not $psql) {
    Write-Host "未找到 psql。请先安装 PostgreSQL 17：" -ForegroundColor Yellow
    Write-Host "  winget install -e --id PostgreSQL.PostgreSQL.17"
    exit 1
}
Write-Host "使用 psql: $psql"

$pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pgService -and $pgService.Status -ne "Running") {
    Write-Host "启动 PostgreSQL 服务: $($pgService.Name)"
    Start-Service $pgService.Name
}

# 读取 .env 中的数据库配置
$envContent = Get-Content $EnvFile -Raw
function Get-EnvVal($key) {
    if ($envContent -match "(?m)^$key=(.+)$") { return $Matches[1].Trim() }
    return $null
}
$pgUser = Get-EnvVal "POSTGRES_USER"
$pgPass = Get-EnvVal "POSTGRES_PASSWORD"
$pgDb   = Get-EnvVal "POSTGRES_DB"
$pgPort = Get-EnvVal "POSTGRES_PORT"
if (-not $pgPort) { $pgPort = "5432" }

$env:PGPASSWORD = $pgPass
$dbExists = & $psql -U $pgUser -h localhost -p $pgPort -tAc "SELECT 1 FROM pg_database WHERE datname='$pgDb'" 2>$null
if ($dbExists -ne "1") {
    Write-Host "创建数据库: $pgDb"
    & $psql -U $pgUser -h localhost -p $pgPort -c "CREATE DATABASE $pgDb;" 2>&1
}

# 数据库迁移（LOCAL_SCHEMA=1 使用无 pgvector 的 schema）
Write-Host "`n==> 运行数据库迁移..." -ForegroundColor Cyan
$env:LOCAL_SCHEMA = "1"
# 加载 .env 到当前进程
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        Set-Item -Path "env:$($Matches[1].Trim())" -Value $Matches[2].Trim()
    }
}
python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "迁移失败。若密码不对，请编辑 .env 中 POSTGRES_PASSWORD（安装 PG 时设置的密码）" -ForegroundColor Red
    exit 1
}

Write-Host "`n==> 后端单测..." -ForegroundColor Cyan
python -m pytest tests/ -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "单测未全部通过，请检查。" -ForegroundColor Yellow
}

if ($SetupOnly) {
    Write-Host "`nSetup 完成。启动命令：" -ForegroundColor Green
    Write-Host "  后端: cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    Write-Host "  前端: cd frontend && npm run dev"
    Write-Host "  中文演示数据（后端启动后）: python backend/scripts/seed_demo_zh.py"
    exit 0
}

if (-not $Start) {
    Write-Host "`nSetup 完成。运行带 -Start 参数可启动前后端，或手动启动。" -ForegroundColor Green
    Write-Host "  powershell -File deploy\local-windows.ps1 -Start"
    Write-Host "  中文演示数据（后端启动后）: python backend/scripts/seed_demo_zh.py"
    exit 0
}

# 启动后端（新窗口）+ 前端
Write-Host "`n==> 启动后端 (8000) 与前端 (5173)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Backend'; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Set-Location $Frontend
if (-not (Test-Path "node_modules")) { npm install }
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Frontend'; npm run dev"
Write-Host "已在新窗口启动。访问 http://localhost:5173" -ForegroundColor Green
