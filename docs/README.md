# 📚 Trading AI 文档中心

欢迎来到 Trading AI 的完整文档！这里提供了系统的所有使用说明和技术文档。

## 🚀 快速导航

### 新手入门
- 📖 **[项目主页](../README.md)** - 项目概述和快速开始
- 🔧 **[安装指南](INSTALL.md)** - 详细的安装步骤和依赖配置
- 💰 **[交易功能](../TRADING.md)** - 完整的交易功能使用指南
- 🐳 **[Docker部署](../DOCKER.md)** - 容器化部署指南

### 功能使用
- 🔄 **[自动扫描](AUTO_SCAN.md)** - 自动循环扫描和K线对齐
- 🚀 **[并发分析](CONCURRENT.md)** - 提升分析速度的并发配置
- 📊 **[数据流程](DATA_FLOW.md)** - 数据处理流程和结构说明
- 🎯 **[提示词管理](PROMPTS.md)** - AI提示词配置和管理

### 高级配置
- 🤖 **[ModelScope集成](MODELSCOPE.md)** - 使用阿里云ModelScope
- 🎨 **[示例代码](../examples/README.md)** - 各种功能的示例代码
- 💬 **[提示词库](../prompts/README.md)** - 内置提示词说明

## 📁 项目结构

```
trading-ai/
├── README.md                 # 项目主页
├── TRADING.md               # 交易功能完整指南
├── DOCKER.md                # Docker部署指南
├── install.sh               # 一键安装脚本
├── main.py                  # 主程序入口
├── requirements.txt         # Python依赖
├── env.example             # 配置文件模板
│
├── docs/                   # 📚 文档目录
│   ├── README.md          # 文档索引（本文件）
│   ├── INSTALL.md         # 安装指南
│   ├── AUTO_SCAN.md       # 自动扫描功能
│   ├── CONCURRENT.md      # 并发分析配置
│   ├── DATA_FLOW.md       # 数据流程说明
│   ├── PROMPTS.md         # 提示词管理
│   └── MODELSCOPE.md      # ModelScope集成
│
├── examples/              # 💡 示例代码
│   ├── README.md         # 示例说明
│   ├── ai_example.py     # AI 分析示例
│   ├── indicator_example.py  # 指标计算示例
│   └── auto_scan_example.py  # 自动扫描示例
│
├── prompts/              # 🎯 提示词库
│   ├── README.md        # 提示词说明
│   └── prompts.json     # 提示词配置
│
└── tradingai/           # 🔧 核心代码
    ├── scanner/         # 市场扫描
    ├── indicators/      # 技术指标
    ├── ai/             # AI 分析
    ├── trader/         # 交易执行
    ├── exchange/       # 交易所接口
    └── logger/         # 日志系统
```

## 🎯 按场景查找文档

### 我想安装和配置系统
1. 📖 阅读 [项目主页](../README.md) 了解系统概述
2. 🔧 按照 [安装指南](INSTALL.md) 安装依赖
3. ⚙️ 配置 `.env` 文件（参考 `env.example`）
4. ▶️ 运行 `python main.py` 开始使用

### 我想使用交易功能
1. 💰 阅读 [交易功能指南](../TRADING.md)
2. ⚠️ 先在**观察模式**测试（无需API）
3. 🧪 在**测试网**验证策略（虚拟资金）
4. 💵 谨慎开启**实盘交易**（真实资金）

### 我想自动化运行
1. 🔄 启用 [自动扫描功能](AUTO_SCAN.md)
2. ⏰ 配置K线周期对齐
3. 🐳 可选：使用 [Docker部署](../DOCKER.md)
4. 📊 监控日志和分析结果

### 我想提升性能
1. 🚀 配置 [并发分析](CONCURRENT.md)
2. ⚙️ 调整 `MAX_CONCURRENT_ANALYSIS` 参数
3. 💾 启用结果缓存
4. 📈 监控系统资源使用

### 我想自定义AI分析
1. 🎯 了解 [提示词管理](PROMPTS.md)
2. 💬 编辑 `prompts/prompts.json`
3. 📝 查看 [数据流程](DATA_FLOW.md) 了解数据结构
4. 🔧 重启系统应用更改

### 我想扩展功能
1. 🎨 查看 [示例代码](../examples/README.md)
2. 📊 了解 [数据流程](DATA_FLOW.md)
3. 🔌 研究核心模块代码
4. 🛠️ 基于示例开发新功能

## ⚙️ 配置文件说明

### `.env` - 主配置文件
```bash
# 交易环境
TRADING_ENVIRONMENT=observe  # observe/testnet/mainnet

# API配置
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret

# AI配置
AI_PROVIDER=deepseek
AI_API_KEY=your_ai_key

# 扫描配置
TIMEFRAME=15m
AUTO_SCAN=true
```

详细配置说明请参考 `env.example` 文件。

## 🔧 常见问题

### Q: 如何选择AI提供商？
A: 编辑 `.env` 中的 `AI_PROVIDER`：
- `mock` - 模拟AI（测试用）
- `deepseek` - DeepSeek（推荐）
- `modelscope` - 阿里云（需配置，见 [MODELSCOPE.md](MODELSCOPE.md)）

### Q: 如何提升分析速度？
A: 参考 [并发分析文档](CONCURRENT.md)：
- 增加 `MAX_CONCURRENT_ANALYSIS` (推荐 3-5)
- 使用更快的AI提供商
- 减少扫描的交易对数量

### Q: 如何安全地测试交易功能？
A: 按顺序测试：
1. **观察模式** (`TRADING_ENVIRONMENT=observe`) - 无需API
2. **测试网** (`TRADING_ENVIRONMENT=testnet`) - 虚拟资金
3. **实盘** (`TRADING_ENVIRONMENT=mainnet`) - 真实资金（⚠️谨慎）

详见 [交易功能文档](../TRADING.md)。

### Q: 如何部署到服务器？
A: 推荐使用Docker：
1. 查看 [Docker部署文档](../DOCKER.md)
2. 使用 `install.sh` 脚本自动安装
3. 配置自动重启和监控

### Q: 日志文件太多了怎么办？
A: 系统自动清理：
- 保留最近3小时的日志
- 分析结果保留最近2天
- 可在代码中调整保留天数

## 🆘 获取帮助

- 📖 **文档**: 查看本文档中心的相关页面
- 💬 **Issues**: 在 [GitHub Issues](https://github.com/rdone4425/trading-ai/issues) 提问
- 🐛 **Bug报告**: 提供详细的错误日志和复现步骤
- 💡 **功能建议**: 欢迎在 Issues 中提出

## 📝 贡献文档

发现文档错误或需要改进？欢迎：
1. Fork 项目
2. 修改文档
3. 提交 Pull Request

## 🔗 快速链接

| 链接 | 说明 |
|------|------|
| [项目主页](../README.md) | 快速开始和系统概述 |
| [交易指南](../TRADING.md) | 完整的交易功能说明 |
| [Docker部署](../DOCKER.md) | 容器化部署 |
| [安装指南](INSTALL.md) | 依赖安装步骤 |
| [示例代码](../examples/README.md) | 功能示例 |

---

**提示**: 建议新用户按照以下顺序阅读文档：
1. [项目主页](../README.md) → 2. [安装指南](INSTALL.md) → 3. [自动扫描](AUTO_SCAN.md) → 4. [交易指南](../TRADING.md)
