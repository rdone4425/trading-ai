# Trading AI - GitHub 上传脚本
# 自动初始化 Git 仓库并准备上传到 GitHub

param(
    [Parameter(Mandatory=$false)]
    [string]$RepositoryUrl = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 准备上传 Trading AI 到 GitHub..." -ForegroundColor Cyan
Write-Host ""

# 进入项目目录
$projectPath = $PSScriptRoot
if (-not $projectPath) {
    $projectPath = Get-Location
}
Set-Location $projectPath

# 1. 检查并初始化 Git
Write-Host "📦 检查 Git 仓库..." -ForegroundColor Yellow
if (-not (Test-Path ".git")) {
    Write-Host "   初始化 Git 仓库..." -ForegroundColor Gray
    git init
} else {
    Write-Host "   Git 仓库已存在" -ForegroundColor Green
}

# 2. 检查 .gitignore
if (-not (Test-Path ".gitignore")) {
    Write-Host "⚠️  警告: .gitignore 文件不存在" -ForegroundColor Yellow
}

# 3. 添加所有文件
Write-Host ""
Write-Host "📝 添加文件到 Git..." -ForegroundColor Yellow
git add .

# 检查状态
$status = git status --short
if ($status) {
    Write-Host "   以下文件将被提交:" -ForegroundColor Gray
    git status --short | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
} else {
    Write-Host "   ✅ 没有需要提交的更改" -ForegroundColor Green
}

# 4. 提交更改
Write-Host ""
Write-Host "💾 提交更改..." -ForegroundColor Yellow
try {
    git commit -m "Initial commit: Trading AI - Intelligent cryptocurrency trading system with Docker support

Features:
- Multi-exchange support (Binance)
- Market scanning (hot, volume, gainers, losers, custom symbols)
- Technical indicators (MA, EMA, RSI, MACD, BBANDS, KDJ, ATR)
- AI-powered market analysis (DeepSeek, ModelScope, OpenAI)
- Automated trading with risk management
- Auto-learning and trade review
- Docker containerization"
    Write-Host "   ✅ 提交成功" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  提交失败或没有更改: $_" -ForegroundColor Yellow
}

# 5. 设置分支
Write-Host ""
Write-Host "🌿 设置主分支..." -ForegroundColor Yellow
git branch -M main

# 6. 处理远程仓库
Write-Host ""
if ($RepositoryUrl) {
    Write-Host "🔗 配置远程仓库: $RepositoryUrl" -ForegroundColor Yellow
    
    # 检查是否已有远程仓库
    $existingRemote = git remote get-url origin 2>$null
    if ($existingRemote) {
        Write-Host "   删除现有远程仓库: $existingRemote" -ForegroundColor Gray
        git remote remove origin
    }
    
    git remote add origin $RepositoryUrl
    Write-Host "   ✅ 远程仓库已配置" -ForegroundColor Green
    
    # 7. 推送（根据参数决定是否强制）
    Write-Host ""
    Write-Host "📤 准备推送到 GitHub..." -ForegroundColor Yellow
    Write-Host ""
    
    if ($Force) {
        Write-Host "⚠️  警告: 将强制推送，这会删除远程仓库的所有文件！" -ForegroundColor Red
        Write-Host ""
        $confirm = Read-Host "确认继续？(yes/no)"
        if ($confirm -eq "yes" -or $confirm -eq "y") {
            Write-Host "🚀 强制推送到 GitHub..." -ForegroundColor Yellow
            git push -f origin main
            Write-Host "✅ 上传完成！" -ForegroundColor Green
        } else {
            Write-Host "❌ 已取消" -ForegroundColor Yellow
        }
    } else {
        Write-Host "🚀 推送到 GitHub..." -ForegroundColor Yellow
        Write-Host "   如果是新仓库，请使用: git push -u origin main" -ForegroundColor Gray
        Write-Host "   如果要清空现有仓库，请使用: git push -f origin main" -ForegroundColor Gray
        Write-Host ""
        Write-Host "   或者重新运行脚本并添加 -Force 参数:" -ForegroundColor Gray
        Write-Host "   .\upload_to_github.ps1 -RepositoryUrl '$RepositoryUrl' -Force" -ForegroundColor Cyan
    }
} else {
    Write-Host "📋 下一步操作:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. 在 GitHub 上创建仓库（或使用现有仓库）" -ForegroundColor White
    Write-Host ""
    Write-Host "2. 运行以下命令设置远程仓库并推送:" -ForegroundColor White
    Write-Host ""
    Write-Host "   git remote add origin https://github.com/你的用户名/仓库名.git" -ForegroundColor Cyan
    Write-Host "   git push -f origin main  # 清空现有仓库" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   或使用此脚本:" -ForegroundColor White
    Write-Host ""
    Write-Host "   .\upload_to_github.ps1 -RepositoryUrl 'https://github.com/你的用户名/仓库名.git' -Force" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host ""
Write-Host "📖 详细说明请查看: GITHUB.md" -ForegroundColor Gray

