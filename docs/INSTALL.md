# 安装说明

## 1. Python 环境
```bash
python --version  # 需要 Python 3.8+
```

## 2. 安装依赖

### Windows 用户

**TA-Lib 安装（重要）**

由于 TA-Lib 需要 C 语言依赖，Windows 用户需要：

**方法1: 使用预编译包（推荐）**
```bash
# 从这里下载对应的 whl 文件：
# https://github.com/cgohlke/talib-build/releases
# 例如：TA_Lib-0.4.28-cp311-cp311-win_amd64.whl

pip install TA_Lib-0.4.28-cp311-cp311-win_amd64.whl
```

**方法2: 使用 conda**
```bash
conda install -c conda-forge ta-lib
```

**安装其他依赖**
```bash
pip install -r requirements.txt
```

### Linux/Mac 用户

```bash
# 安装 TA-Lib C 库
# Ubuntu/Debian
sudo apt-get install ta-lib

# macOS
brew install ta-lib

# 安装 Python 依赖
pip install -r requirements.txt
```

## 3. 配置环境变量

复制 `env.example` 为 `.env` 并填写配置：
```bash
cp env.example .env
```

编辑 `.env` 文件，填写 API Key 等信息。

## 4. 运行

```bash
python main.py
```

## 常见问题

### Q: TA-Lib 安装失败？
A: Windows 用户请使用预编译包（方法1），从 GitHub releases 下载对应 Python 版本的 whl 文件。

### Q: 如何不安装 TA-Lib？
A: 技术指标功能是可选的。如果不需要技术分析，可以不安装 TA-Lib，只移除 requirements.txt 中的 `TA-Lib` 行即可。程序会自动检测并跳过技术指标功能。

### Q: 代理设置？
A: 在 `.env` 中设置：
```
USE_PROXY=true
PROXY_HOST=127.0.0.1
PROXY_PORT=7890
```


