# AI 并发分析功能

## 概述

`MarketAnalyzer` 内置并发分析功能，允许同时分析多个交易对，大幅提升分析速度。

**关键优势**：分析 10 个交易对，从 100 秒降至 40 秒（**2.5x 速度提升**）

## 功能特点

### 1. 智能并发控制

- 使用 `asyncio.Semaphore` 限制并发数量
- 避免 API 过载
- 自动处理异常，确保稳定性

### 2. 性能提升

**示例场景：分析 10 个交易对**

| 模式 | 耗时 | 说明 |
|------|------|------|
| 串行分析 | ~100 秒 | 逐个分析，每个10秒 |
| 并发分析(3) | ~40 秒 | 同时分析3个，速度提升2.5x |
| 并发分析(5) | ~25 秒 | 同时分析5个，速度提升4x |

### 3. 使用方法

```python
from tradingai.ai.analyzers import MarketAnalyzer
from tradingai.indicators import IndicatorEngine
from tradingai.ai import AIProviderFactory

# 1. 初始化
ai_provider = AIProviderFactory.create_from_config()
indicator_engine = IndicatorEngine()

analyzer = MarketAnalyzer(
    provider=ai_provider,
    indicator_engine=indicator_engine,  # 批量分析必需
    max_concurrent=3  # 可选，默认使用配置
)

# 2. 准备数据
data = [
    {'symbol': 'BTCUSDT', 'klines': btc_klines},
    {'symbol': 'ETHUSDT', 'klines': eth_klines},
    {'symbol': 'BNBUSDT', 'klines': bnb_klines},
]

# 3. 并发分析（推荐）
results = await analyzer.analyze_batch(data, timeframe='1h', concurrent=True)

# 4. 串行分析（对比）
results = await analyzer.analyze_batch(data, timeframe='1h', concurrent=False)
```

#### 配置并发数量

在 `.env` 文件中配置：

```bash
# 同时分析多少个交易对
# 建议: 1-5，值越大速度越快但对API有一定压力
MAX_CONCURRENT_ANALYSIS=3
```

## 核心组件

### MarketAnalyzer.analyze_batch()

**位置**: `tradingai/ai/analyzers/market_analyzer.py`

**主要方法**:
- `analyze_market()` - 分析单个交易对
- `analyze_batch()` - 批量分析多个交易对（支持并发）
- `provide_learning()` - 学习辅导
- `review_trade()` - 交易复盘

## 工作原理

### 1. 串行分析（传统方式）

```
交易对1 → 分析1 ──→ 交易对2 → 分析2 ──→ 交易对3 → 分析3
(10秒)         (10秒)         (10秒)
总耗时: 30秒
```

### 2. 并发分析（新方式，MAX_CONCURRENT_ANALYSIS=3）

```
交易对1 ──→ 分析1 ┐
交易对2 ──→ 分析2 ├─→ 同时进行
交易对3 ──→ 分析3 ┘
(10秒)

交易对4 ──→ 分析4 ┐
交易对5 ──→ 分析5 ├─→ 接着进行
...              ┘

总耗时: ~15秒（速度提升2x）
```

## 实现细节

### 核心代码

```python
class MarketAnalyzer:
    """市场分析器（内置并发功能）"""
    
    async def analyze_batch(self, data, timeframe, concurrent=True):
        """批量分析多个交易对"""
        if concurrent and len(data) > 1:
            return await self._analyze_concurrent(data, timeframe)
        else:
            return await self._analyze_sequential(data, timeframe)
    
    async def _analyze_concurrent(self, data, timeframe):
        """并发分析实现"""
        # 1. 创建信号量限制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # 2. 为每个交易对创建分析任务
        async def analyze_with_semaphore(item, index):
            async with semaphore:  # 获取许可
                # 计算指标 + AI 分析
                indicators = self.indicator_engine.calculate_all(item['klines'])
                return await self.analyze_market(
                    symbol=item['symbol'],
                    klines=item['klines'],
                    indicators=indicators,
                    timeframe=timeframe
                )
        
        # 3. 并发执行所有任务
        tasks = [analyze_with_semaphore(d, i) for i, d in enumerate(data, 1)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 4. 收集成功的结果
        return [r for r in results if r and not isinstance(r, Exception)]
```

### 错误处理

- 单个交易对分析失败不影响其他交易对
- 自动捕获异常，记录错误日志
- 使用 `return_exceptions=True` 确保所有任务完成

## 配置建议

### API 限制考虑

不同 AI 提供商有不同的并发限制：

| 提供商 | 建议并发数 | 说明 |
|--------|----------|------|
| OpenAI | 3-5 | RPM 限制较高 |
| DeepSeek | 3 | 默认配置 |
| ModelScope | 2-3 | 免费额度有限 |
| Mock | 10+ | 无限制 |

### 性能调优

```bash
# 保守配置（稳定优先）
MAX_CONCURRENT_ANALYSIS=2

# 平衡配置（推荐）
MAX_CONCURRENT_ANALYSIS=3

# 激进配置（速度优先，需要高级 API 账号）
MAX_CONCURRENT_ANALYSIS=5
```

## 日志示例

### 并发分析日志

```
✅ 扫描到 5 个交易对
🚀 开始并发分析（最大并发: 3）
🔄 开始分析 (1/5): BTCUSDT
🔄 开始分析 (2/5): ETHUSDT
🔄 开始分析 (3/5): BNBUSDT
✅ 完成分析 (1/5): BTCUSDT - 做多 (置信度: 75.0%)
🔄 开始分析 (4/5): XRPUSDT
✅ 完成分析 (2/5): ETHUSDT - 观望 (置信度: 50.0%)
🔄 开始分析 (5/5): ADAUSDT
✅ 完成分析 (3/5): BNBUSDT - 做空 (置信度: 65.0%)
✅ 完成分析 (4/5): XRPUSDT - 观望 (置信度: 55.0%)
✅ 完成分析 (5/5): ADAUSDT - 做多 (置信度: 70.0%)

✅ 完成分析: 5/5
```

### 串行分析日志

```
✅ 扫描到 5 个交易对
📊 开始串行分析
进度: 1/5 - BTCUSDT
  ✅ 做多 (置信度: 75.0%)
进度: 2/5 - ETHUSDT
  ✅ 观望 (置信度: 50.0%)
...

✅ 完成分析: 5/5
```

## 注意事项

1. **API 配额**：并发会更快消耗 API 配额
2. **错误率**：并发数过高可能导致 API 限流
3. **内存使用**：并发数越高，内存占用越大
4. **网络稳定性**：网络不稳定时建议降低并发数

## 相关配置

```bash
# .env 配置示例
MAX_CONCURRENT_ANALYSIS=3    # 并发分析数量
AI_PROVIDER=deepseek         # AI 提供商
AI_MODEL=deepseek-chat       # AI 模型
CUSTOM_SYMBOLS=btc,eth,bnb   # 自定义交易对
```

## 性能监控

系统会自动记录：
- 每个交易对的分析耗时
- 并发执行的实际情况
- 异常和错误信息

建议通过日志文件监控性能：

```bash
# 查看最近的分析日志
tail -f logs/trading-ai-*.log
```

## 相关文件

- 配置文件: `tradingai/config.py` (MAX_CONCURRENT_ANALYSIS)
- 实现代码: `tradingai/scanner/market_scanner.py`
  - `_analyze_concurrent()` - 并发分析实现
  - `_analyze_sequential()` - 串行分析实现
- 环境变量示例: `env.example`

