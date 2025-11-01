# GitHub 上传指南

## 📋 前提条件

1. 已安装 Git
2. 已创建 GitHub 仓库（或准备创建）
3. 已配置 Git 用户信息

## 🚀 上传步骤

### 方法一：清理现有仓库并重新上传（推荐）

如果你已经有一个 GitHub 仓库，需要清空所有文件后重新上传：

```bash
# 1. 进入项目目录
cd trading-ai

# 2. 初始化 Git（如果还没有）
git init

# 3. 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/你的用户名/仓库名.git

# 如果远程仓库已存在，先删除再添加
# git remote remove origin
# git remote add origin https://github.com/你的用户名/仓库名.git

# 4. 添加所有文件
git add .

# 5. 提交
git commit -m "Initial commit: Trading AI system with Docker support"

# 6. 如果是清空现有仓库，强制推送（⚠️ 会删除远程所有文件）
git branch -M main
git push -f origin main

# 或者推送到新分支
# git push -f origin main:main --force
```

### 方法二：使用孤儿分支（完全清空历史）

如果你想完全清空 Git 历史记录：

```bash
# 1. 创建孤儿分支
git checkout --orphan new-main

# 2. 添加所有文件
git add .

# 3. 提交
git commit -m "Initial commit: Trading AI system"

# 4. 删除旧的 main 分支
git branch -D main

# 5. 重命名当前分支为 main
git branch -m main

# 6. 强制推送（清空远程仓库）
git push -f origin main
```

### 方法三：创建新仓库

如果你要创建一个全新的仓库：

```bash
# 1. 在 GitHub 上创建新仓库（空仓库）

# 2. 在项目目录中执行
cd trading-ai
git init
git add .
git commit -m "Initial commit: Trading AI system with Docker support"
git branch -M main
git remote add origin https://github.com/你的用户名/仓库名.git
git push -u origin main
```

## 📝 重要文件说明

以下文件会被提交到 GitHub：
- ✅ 所有源代码（`tradingai/`）
- ✅ 配置文件（`config.py`, `env.example`）
- ✅ 文档（`docs/`, `README.md`）
- ✅ Docker 配置（`Dockerfile`, `docker-compose.yml`, `.dockerignore`）
- ✅ 依赖文件（`requirements.txt`）
- ✅ 示例代码（`examples/`）
- ✅ 提示词配置（`prompts/`）

以下文件**不会**被提交（已在 `.gitignore` 中）：
- ❌ `.env`（环境变量，包含敏感信息）
- ❌ `data/`（分析结果数据）
- ❌ `logs/`（日志文件）
- ❌ `test_*.py`（测试文件）
- ❌ `__pycache__/`（Python 缓存）

## ⚠️ 安全注意事项

1. **不要提交 `.env` 文件**：包含 API 密钥等敏感信息
2. **检查敏感信息**：确保没有硬编码的密钥或密码
3. **使用 `.env.example`**：作为配置模板提供给其他用户

## 🔄 后续更新

```bash
# 添加更改
git add .

# 提交
git commit -m "描述你的更改"

# 推送
git push origin main
```

## 📦 Docker 部署

上传到 GitHub 后，可以在任何支持 Docker 的环境中使用：

```bash
# 克隆仓库
git clone https://github.com/你的用户名/仓库名.git
cd 仓库名

# 构建镜像
docker build -t trading-ai .

# 运行容器
docker-compose up -d
```

详见：[DOCKER.md](./DOCKER.md)

