# Trading AI - Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 安装 TA-Lib（可选，如果系统不支持则使用纯 Python 实现）
# RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
#     && tar -xzf ta-lib-0.4.0-src.tar.gz \
#     && cd ta-lib/ && ./configure --prefix=/usr && make && make install \
#     && cd .. && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p /app/data /app/logs

# 设置执行权限
RUN chmod +x main.py

# 暴露Web监控页面端口
EXPOSE 8080

# 默认命令
CMD ["python", "main.py"]

