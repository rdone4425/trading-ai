# Trading AI 文档索引

欢迎使用 Trading AI！本目录包含所有相关文档。

## 📚 文档列表

### 基础配置

- **[安装指南](INSTALL.md)** - 环境配置和安装步骤

### 核心功能

- **[自动扫描](README_AUTO_SCAN.md)** - 自动循环扫描和定时任务
- **[AI 并发分析](README_CONCURRENT.md)** ⭐ **NEW** - 并发分析功能，大幅提升速度
- **[AI 提供商集成](README_MODELSCOPE.md)** - ModelScope 等 AI 服务接入
- **[提示词系统](README_PROMPTS.md)** - AI 提示词管理和自定义

### 高级主题

- **交易标准系统** - 建立交易标准，按标准执行（见 `README_PROMPTS.md`）

## 🚀 快速开始

1. 安装依赖：参考 [INSTALL.md](INSTALL.md)
2. 配置环境变量：复制 `env.example` 到 `.env`
3. 运行主程序：`python main.py`

## 🎯 核心特性

### 1. 市场扫描
- ✅ 多种扫描模式（热门/成交量/涨跌幅）
- ✅ 自定义交易对列表
- ✅ 自动循环扫描

### 2. 技术指标
- ✅ EMA、RSI、MACD、BBANDS、KDJ、ATR
- ✅ 动态配置指标参数
- ✅ 金叉死叉检测

### 3. AI 分析
- ✅ 多 AI 提供商支持（OpenAI、DeepSeek、ModelScope等）
- ✅ **并发分析**，速度提升2-4x ⭐
- ✅ 交易标准系统化分析
- ✅ JSON 结构化输出

### 4. 数据管理
- ✅ 自动保存分析结果
- ✅ 按日期分类存储
- ✅ 日志自动清理

## 📖 详细功能说明

### 并发分析 ⭐ NEW

使用 `MarketAnalyzer.analyze_batch()` 同时分析多个交易对，大幅提升速度：

```python
from tradingai.ai.analyzers import MarketAnalyzer

analyzer = MarketAnalyzer(provider, indicator_engine=indicator_engine)
results = await analyzer.analyze_batch(data, timeframe='1h', concurrent=True)
```

**性能对比：**
- 串行分析：10个交易对 ≈ 100秒
- 并发分析(3)：10个交易对 ≈ 40秒（**2.5x 速度提升**）

配置并发数量：
```bash
MAX_CONCURRENT_ANALYSIS=3
```

详见 [README_CONCURRENT.md](README_CONCURRENT.md)

### 交易标准系统

AI 采用系统化交易方法：

1. **制定标准**：根据市场环境选择策略
2. **对照检查**：检查数据是否符合标准
3. **执行决策**：符合标准才交易，不符合则观望

示例输出：

```json
{
  "trading_standard": "采用趋势跟随策略。判断条件：1. EMA7>EMA25>EMA99；2. RSI>50；3. 成交量放大",
  "action": "做多",
  "confidence": 0.75,
  "reason": "当前市场完全符合趋势跟随标准：EMA多头排列，RSI为65显示动量强劲..."
}
```

## 🛠 配置文件

- `.env` - 环境变量配置
- `prompts/prompts.json` - AI 提示词配置
- `tradingai/config.py` - 系统配置

## 📝 日志文件

日志位置：`logs/trading-ai-YYYYMMDD.log`

自动清理：保留最近3小时的日志内容

## 💾 数据文件

分析结果：`data/YYYY-MM-DD/analysis_HHMMSS.json`

按日期自动分类存储

## 🔧 开发指南

### 添加新的 AI 提供商

1. 在 `tradingai/ai/providers/` 创建新文件
2. 继承 `BaseAIProvider` 类
3. 实现 `chat()` 方法
4. 在 `AIProviderFactory` 注册

### 自定义提示词

编辑 `prompts/prompts.json`：

```json
{
  "analysis": {
    "system": "你的系统提示词...",
    "user": "你的用户提示词..."
  }
}
```

### 添加新的技术指标

1. 在 `tradingai/indicators/calculator.py` 添加计算方法
2. 在 `tradingai/indicators/config_parser.py` 添加配置支持
3. 在 `.env` 中添加配置项

## 🐛 故障排除

常见问题和解决方案：

1. **AI 不返回 JSON**
   - 检查提示词配置
   - 尝试不同的 AI 模型
   - 查看日志获取详细错误

2. **分析速度慢**
   - 启用并发分析
   - 增加 `MAX_CONCURRENT_ANALYSIS`
   - 减少 `KLINE_LIMIT`

3. **API 限流**
   - 降低并发数量
   - 增加扫描间隔
   - 检查 API 配额

## 📞 获取帮助

- 查看日志文件：`logs/`
- 检查配置文件：`.env`
- 阅读详细文档：本目录下的各个 README

## 🎓 学习路径

1. **入门**：[INSTALL.md](INSTALL.md) → [README_AUTO_SCAN.md](README_AUTO_SCAN.md)
2. **进阶**：[README_CONCURRENT.md](README_CONCURRENT.md) → [README_PROMPTS.md](README_PROMPTS.md)
3. **定制**：[README_MODELSCOPE.md](README_MODELSCOPE.md) → 开发自定义功能

## 📊 系统架构

```
Trading AI
├── 市场扫描器 (MarketScanner)
│   ├── 交易所平台 (BinancePlatform)
│   └── 交易对筛选
├── 指标引擎 (IndicatorEngine)
│   ├── 技术指标计算
│   └── 信号检测
└── AI 模块 (ai/)
    ├── 提供商 (providers/)
    │   ├── DeepSeekProvider
    │   └── ModelScopeProvider
    ├── 提示词 (prompts/)
    │   └── PromptManager
    └── 分析器 (analyzers/)
        └── MarketAnalyzer      # 单个分析 + 并发分析 ⭐
```

## 🔄 更新日志

- **2025-11-01**: 添加 AI 并发分析功能
- **2025-11-01**: 完善交易标准系统
- **2025-11-01**: 优化提示词管理

---

**提示**：建议从 [README_CONCURRENT.md](README_CONCURRENT.md) 开始，了解如何大幅提升分析速度！
