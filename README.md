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

查看 **[docs 目录](./docs/)** 获取详细文档：

| 文档 | 说明 |
|------|------|
| 📖 [文档索引](./docs/README.md) | 完整文档导航和项目结构 |
| 🔧 [安装说明](./docs/INSTALL.md) | 依赖安装和TA-Lib配置指南 |
| 🔄 [自动扫描](./docs/AUTO_SCAN.md) | 自动循环扫描功能使用手册 |
| 🎯 [示例代码](./examples/README.md) | 示例代码说明 |

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 1. 构建镜像
docker build -t trading-ai .

# 2. 配置环境变量
cp env.example .env
# 编辑 .env 文件

# 3. 运行容器
docker-compose up -d

# 4. 查看日志
docker-compose logs -f
```

详细说明：[DOCKER.md](./DOCKER.md)

### 方式二：本地安装

#### 1. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装TA-Lib（可选，用于技术指标）
# Windows: 下载whl文件安装
# Linux/Mac: 见 docs/INSTALL.md
```

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
├── main.py                    # 🎬 主程序
├── requirements.txt           # 📦 依赖列表
├── env.example                # ⚙️ 配置模板
├── Dockerfile                 # 🐳 Docker 配置
├── docker-compose.yml         # 🐳 Docker Compose 配置
├── DOCKER.md                  # 🐳 Docker 部署指南
├── GITHUB.md                  # 📤 GitHub 上传指南
└── README.md                  # 📋 本文件
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
A: 在 `.env` 中设置：
```env
USE_PROXY=true
PROXY_HOST=127.0.0.1
PROXY_PORT=7890
```

### Q: 如何调整扫描频率？
A: 修改 `TIMEFRAME` 参数，支持 1m, 5m, 15m, 30m, 1h, 4h 等

### Q: 如何停止自动扫描？
A: 按 `Ctrl+C` 即可优雅退出

### Q: 日志文件太大怎么办？
A: 程序会自动清理超过指定时间的日志内容，默认保留3小时

更多问题请参考：[docs/AUTO_SCAN.md](./docs/AUTO_SCAN.md)

## 📝 许可证

MIT License

---

**开始你的智能交易之旅！** 🚀

有问题？查看 [完整文档](./docs/) 或提交 Issue。
