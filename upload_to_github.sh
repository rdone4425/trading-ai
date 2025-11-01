#!/bin/bash
# GitHub 上传脚本

set -e

echo "🚀 开始准备上传到 GitHub..."

# 检查是否已初始化 Git
if [ ! -d .git ]; then
    echo "📦 初始化 Git 仓库..."
    git init
fi

# 添加所有文件
echo "📝 添加文件..."
git add .

# 检查是否有未提交的更改
if git diff --staged --quiet; then
    echo "⚠️  没有需要提交的更改"
    exit 0
fi

# 提交
echo "💾 提交更改..."
git commit -m "Initial commit: Trading AI system with Docker support"

# 提示用户配置远程仓库
echo ""
echo "⚠️  请按以下步骤操作："
echo "1. 在 GitHub 上创建新仓库（或使用现有仓库）"
echo "2. 运行以下命令设置远程仓库："
echo ""
echo "   git remote add origin https://github.com/你的用户名/仓库名.git"
echo ""
echo "3. 如果是清空现有仓库，运行："
echo ""
echo "   git branch -M main"
echo "   git push -f origin main"
echo ""
echo "4. 如果是新仓库，运行："
echo ""
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "📖 详细说明请查看: GITHUB.md"

