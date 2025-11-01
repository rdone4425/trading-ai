# Docker 部署指南

## 快速开始

### 1. 构建镜像

```bash
docker build -t trading-ai .
```

### 2. 运行容器

```bash
# 使用 Docker 直接运行
docker run -d \
  --name trading-ai \
  -v $(pwd)/.env:/app/.env:ro \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  trading-ai

# 或使用 docker-compose
docker-compose up -d
```

### 3. 查看日志

```bash
# Docker
docker logs -f trading-ai

# docker-compose
docker-compose logs -f
```

### 4. 停止容器

```bash
# Docker
docker stop trading-ai
docker rm trading-ai

# docker-compose
docker-compose down
```

## 环境变量配置

在运行容器前，请确保已创建 `.env` 文件：

```bash
cp env.example .env
# 编辑 .env 文件，填入你的配置
```

## 数据持久化

容器会挂载以下目录到宿主机：
- `./data` - 分析结果数据
- `./logs` - 日志文件
- `./.env` - 环境变量配置（只读）

## 注意事项

1. **首次运行**：确保已创建 `.env` 文件并配置了必要的 API 密钥
2. **TA-Lib**：如果需要使用 TA-Lib，需要在 Dockerfile 中取消相关注释并重新构建
3. **资源限制**：建议为容器分配足够的 CPU 和内存资源
4. **时区**：容器默认使用 UTC 时区，代码中已转换为上海时区

## 开发模式

如果需要开发或调试：

```bash
# 交互式运行
docker run -it --rm \
  -v $(pwd):/app \
  -v $(pwd)/.env:/app/.env:ro \
  trading-ai python main.py

# 进入容器
docker exec -it trading-ai bash
```

