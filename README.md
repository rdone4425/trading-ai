# 🤖 Trading AI - 智能交易系统

> 功能强大、模块化的加密货币智能交易系统

## ✨ 主要特性

- 🔄 **多交易所支持** - 当前支持币安（Binance），架构支持扩展更多交易所
- 📊 **智能市场扫描** - 热门币种、成交量、涨跌幅、自定义交易对监控
- 🎯 **技术指标分析** - MA/EMA/RSI/MACD/BBANDS/KDJ/ATR 等主流指标
- 🔄 **自动循环扫描** - 根据K线周期智能对准，自动化监控市场
- ⏰ **时间管理** - UTC/上海时区转换，K线时间对齐
- 📝 **智能日志** - 自动清理旧日志，保持系统整洁
- 🔐 **安全可靠** - API密钥安全管理，支持代理访问

## 📚 完整文档

> **[📖 查看文档中心](./docs/README.md)** - 完整的使用指南和API文档

### 核心文档
| 文档 | 说明 |
|------|------|
| 💰 **[交易功能](./docs/TRADING.md)** | 自动交易完整指南（观察/测试网/实盘） |
| 🐳 **[Docker部署](./docs/DOCKER.md)** | 容器化部署和自动化安装 |
| 🔧 **[安装指南](./docs/INSTALL.md)** | 依赖安装和环境配置 |
| 🔄 **[自动扫描](./docs/AUTO_SCAN.md)** | 循环扫描和K线对齐 |
| 🚀 **[并发分析](./docs/CONCURRENT.md)** | 提升分析速度配置 |
| 📊 **[数据流程](./docs/DATA_FLOW.md)** | 数据结构和处理流程 |

## 🚀 快速开始

### 方式一：一键安装脚本（最简单推荐）

**使用方式：**

1. **如果你已经有 `install.sh` 脚本**（在项目目录中）：
   ```bash
   ./install.sh
   ```

2. **首次安装，一条命令完成**：
   ```bash
   git clone https://github.com/rdone4425/trading-ai.git && cd trading-ai && chmod +x install.sh && ./install.sh
   ```

3. **在任意目录运行脚本，它会引导下载**：
   ```bash
   curl -fsSL https://raw.githubusercontent.com/rdone4425/trading-ai/main/install.sh -o install.sh
   chmod +x install.sh
   ./install.sh
   ```

> 💡 **提示**：如果当前目录不是项目目录，脚本会自动提示下载项目。

**脚本功能菜单：**

运行 `./install.sh` 后，会进入交互式菜单，支持以下操作：

| 选项 | 功能 | 说明 |
|------|------|------|
| **U** | 下载/更新项目 | 智能检测：项目不存在则下载，存在则从 GitHub 更新并自动重新构建启动 |
| **1** | 安装 Docker 和 Docker Compose | 自动检测系统并安装缺失的 Docker/Docker Compose 组件 |
| **2** | 配置环境变量 | 交互式配置 `.env` 文件 |
| **3** | 构建 Docker 镜像 | 构建项目 Docker 镜像 |
| **4** | 启动服务 | 启动 Trading AI 服务 |
| **5** | 停止服务 | 停止运行中的服务 |
| **6** | 重启服务 | 重启 Trading AI 服务 |
| **7** | 查看日志 | 实时查看运行日志 |
| **8** | 查看状态 | 查看容器运行状态 |
| **C** | 清理/卸载 | 清理容器、镜像和数据 |
| **0** | 退出 | 退出管理菜单 |

**脚本特性：**
- ✅ **智能下载/更新**：一个选项搞定所有操作，自动检测项目是否存在（不存在则下载，存在则更新）
- ✅ **一键更新**：从 GitHub 更新代码后自动重新构建并启动服务
- ✅ **智能检测**：自动检测 Docker/Docker Compose 安装状态
- ✅ **版本提示**：菜单中显示代码是否有新版本可用
- ✅ **支持多系统**：支持 Ubuntu/Debian/CentOS/RHEL/Fedora
- ✅ **彩色输出**：实时显示系统状态，操作提示清晰

### 方式二：Docker 手动部署

如果不想使用安装脚本，可以手动部署：

```bash
# 1. 配置环境变量
cp env.example .env
# 编辑 .env 文件，填入你的配置

# 2. 构建镜像
docker build -t trading-ai .
# 或使用 docker-compose
docker-compose build

# 3. 运行容器
docker-compose up -d

# 4. 查看日志
docker-compose logs -f trading-ai
```

**常用命令：**
```bash
# 查看状态
docker-compose ps

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看实时日志
docker-compose logs -f

# 进入容器
docker-compose exec trading-ai bash
```

详细说明：[DOCKER.md](./DOCKER.md)

### 方式三：本地安装（不使用 Docker）

适合开发者或想要直接运行 Python 代码的用户：

#### 1. 安装依赖

**Python 环境要求：**
- Python 3.8 或更高版本
- pip 包管理器

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 TA-Lib（可选，用于技术指标加速）
# Windows: 下载对应的 whl 文件安装
#   pip install TA_Lib-0.4.24-cp38-cp38-win_amd64.whl
# Linux/Mac: 需要先编译安装 TA-Lib 库
#   详见 docs/INSTALL.md
```

> 💡 **提示**：如果不安装 TA-Lib，系统会自动使用纯 Python 实现（NumPy/Pandas），功能相同但速度稍慢。

详细安装说明：[docs/INSTALL.md](./docs/INSTALL.md)

### 2. 配置环境

```bash
# 复制配置模板
cp env.example .env

# 编辑 .env 文件，配置你的参数
```

**最小配置：**
```env
# 交易所
EXCHANGE_NAME=binance
TRADING_ENVIRONMENT=observe    # observe=观察模式（无需API密钥）

# K线配置
TIMEFRAME=15m                  # K线周期
LOOKBACK=100                   # K线数量
KLINE_TYPE=closed              # closed=已完成，open=进行中

# 扫描配置
AUTO_SCAN=false                # true=自动循环，false=单次扫描
SCAN_TYPES=hot,volume,gainers,losers
SCAN_TOP_N=20                  # 扫描数量
```

### 3. 运行程序

**单次扫描（默认）：**
```bash
python main.py
```

**自动循环扫描：**
```bash
# 方法1: 修改 .env 文件
# 设置 AUTO_SCAN=true
python main.py

# 方法2: 临时启用（PowerShell）
$env:AUTO_SCAN="true"; python main.py

# 方法3: 临时启用（Linux/Mac）
AUTO_SCAN=true python main.py
```

详细使用说明：[docs/AUTO_SCAN.md](./docs/AUTO_SCAN.md)

## 📂 项目结构

```
trading-ai/
├── docs/                      # 📚 完整文档
│   ├── README.md             # 文档索引
│   ├── INSTALL.md            # 安装指南
│   └── AUTO_SCAN.md          # 自动扫描说明
├── examples/                  # 🎯 示例代码
│   ├── indicator_example.py  # 指标计算示例
│   ├── time_example.py       # 时间转换示例
│   ├── auto_scan_example.py  # 自动扫描示例
│   └── custom_scan_example.py# 自定义扫描示例
├── tradingai/                 # 💼 核心代码
│   ├── config.py             # 配置管理
│   ├── exchange/             # 交易所接口
│   ├── scanner/              # 市场扫描器
│   ├── indicators/           # 技术指标
│   ├── logger/               # 日志系统
│   ├── utils/                # 工具函数
│   └── proxy/                # 代理管理
├── logs/                      # 📝 日志文件
├── data/                      # 💾 数据文件（分析结果、上下文）
├── main.py                    # 🎬 主程序入口
├── install.sh                 # 🚀 一键安装脚本（推荐）
├── requirements.txt           # 📦 Python 依赖列表
├── env.example                # ⚙️ 环境变量配置模板
├── Dockerfile                 # 🐳 Docker 镜像配置
├── docker-compose.yml         # 🐳 Docker Compose 配置
├── DOCKER.md                  # 🐳 Docker 部署详细指南
├── GITHUB.md                  # 📤 GitHub 上传指南
└── README.md                  # 📋 本文件（项目说明）
```

## 🎯 使用示例

### 示例1：监控热门币种（5分钟K线）
```bash
# .env 配置
TIMEFRAME=5m
AUTO_SCAN=true
SCAN_TYPES=hot,volume
SCAN_TOP_N=10

# 运行
python main.py
```

### 示例2：监控特定币种（15分钟K线）
```bash
# .env 配置
TIMEFRAME=15m
AUTO_SCAN=true
CUSTOM_SYMBOLS=btc,eth,bnb,sol,xrp

# 运行
python main.py
```

### 示例3：技术指标分析
```bash
# 运行指标示例（包含MA/EMA/RSI/MACD等）
python examples/indicator_example.py
```

### 示例4：自定义策略扫描
```bash
# 运行自定义扫描（包含EMA交叉、RSI超买超卖检测）
python examples/custom_scan_example.py
```

## ⚙️ 核心配置

### 交易所配置
```env
EXCHANGE_NAME=binance              # 交易所名称
TRADING_ENVIRONMENT=observe        # observe/testnet/mainnet
BINANCE_API_KEY=your_key          # API密钥（observe模式不需要）
BINANCE_API_SECRET=your_secret    # API密钥（observe模式不需要）
```

### K线配置
```env
TIMEFRAME=15m                      # 1m,5m,15m,30m,1h,4h,1d等
LOOKBACK=100                       # 获取K线数量
KLINE_TYPE=closed                  # closed=已完成, open=进行中
```

### 扫描配置
```env
AUTO_SCAN=false                    # 自动循环扫描开关
SCAN_TYPES=hot,volume,gainers,losers  # 扫描类型
SCAN_TOP_N=20                      # 每种类型取前N个
CUSTOM_SYMBOLS=                    # 自定义交易对（优先级高）
```

### 指标配置
```env
INDICATOR_ema=7,20,120            # EMA周期配置
INDICATOR_rsi=14                   # RSI周期
INDICATOR_atr=14                   # ATR周期
```

### 日志配置
```env
LOG_LEVEL=INFO                     # 日志级别
LOG_DIR=logs                       # 日志目录
LOG_RETENTION_HOURS=3              # 保留最近N小时的日志
```

## 🔧 技术指标

支持的技术指标：

- **MA** - 移动平均线
- **EMA** - 指数移动平均线
- **RSI** - 相对强弱指数
- **MACD** - 平滑异同移动平均线
- **BBANDS** - 布林带
- **KDJ** - 随机指标
- **ATR** - 平均真实波幅

指标支持纯Python实现（NumPy/Pandas），也支持TA-Lib加速计算。

## 📊 市场扫描

支持的扫描类型：

- **hot** - 热门币种（综合成交量和涨跌幅）
- **volume** - 24小时成交量排行
- **gainers** - 涨幅榜
- **losers** - 跌幅榜
- **custom** - 自定义交易对列表

## 💡 常见问题

### Q: 如何启用代理？
**A:** 在 `.env` 文件中设置：
```env
USE_PROXY=true
PROXY_HOST=127.0.0.1
PROXY_PORT=7890
```

### Q: 如何调整扫描频率？
**A:** 修改 `.env` 中的 `TIMEFRAME` 参数，支持：
- 分钟：`1m`, `3m`, `5m`, `15m`, `30m`
- 小时：`1h`, `2h`, `4h`, `6h`, `8h`, `12h`
- 天：`1d`, `3d`, `1w`, `1M`

### Q: 如何停止自动扫描？
**A:** 按 `Ctrl+C` 即可优雅退出。如果使用 Docker，运行 `docker-compose stop`

### Q: 日志文件太大怎么办？
**A:** 程序会自动清理超过指定时间的日志内容，默认保留 3 小时。可以在 `.env` 中调整 `LOG_RETENTION_HOURS`

### Q: Docker 安装失败怎么办？
**A:** 
- 检查网络连接
- 确保有 sudo 权限
- 查看详细错误信息：`./install.sh` 菜单选项 [1]
- 手动安装：参考 [Docker 官方文档](https://docs.docker.com/get-docker/)

### Q: 如何更新项目？
**A:** 有两种方式：

**方式一：使用安装脚本（推荐）**
```bash
./install.sh
# 选择菜单选项 [U] 下载/更新项目
```
脚本会自动：
1. 检测项目是否存在（不存在则下载，存在则更新）
2. 如有更新，拉取最新代码
3. 询问是否重新构建并启动服务
4. 完成更新并重启服务

**方式二：手动更新**
```bash
# 使用 Git 拉取最新代码
git pull origin main

# 如果使用 Docker，重新构建镜像并启动
docker-compose build
docker-compose up -d
```

### Q: 观察模式需要 API 密钥吗？
**A:** 观察模式（`TRADING_ENVIRONMENT=observe`）不需要 API 密钥，可以安全测试所有功能（除了实际交易）

### Q: 如何查看实时日志？
**A:** 
- 使用安装脚本：菜单选项 [8]
- 手动：`docker-compose logs -f trading-ai`
- 本地运行：日志保存在 `logs/` 目录

### Q: 配置文件在哪里？
**A:** 配置文件是 `.env`，位于项目根目录。首次使用可以通过 `./install.sh` 菜单选项 [3] 进行配置

更多问题请参考：[docs/AUTO_SCAN.md](./docs/AUTO_SCAN.md) 或提交 [GitHub Issue](https://github.com/rdone4425/trading-ai/issues)

## 📝 许可证

MIT License

---

**开始你的智能交易之旅！** 🚀

有问题？查看 [完整文档](./docs/) 或提交 Issue。
