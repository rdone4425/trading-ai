# 数据流说明：扫描器 → AI分析器

本文档详细说明扫描器（MarketScanner）如何获取、计算并传递数据给AI分析器（MarketAnalyzer）。

## 数据流程概览

```
1. 扫描器扫描市场 → 获取交易对列表
2. 扫描器获取K线数据 → 从交易所API获取
3. 扫描器计算技术指标 → 基于K线数据计算
4. 扫描器传递数据给AI分析器 → klines + indicators
5. AI分析器格式化数据 → 准备提示词
6. AI分析器调用AI → 基于格式化数据进行分析
```

## 1. K线数据结构

扫描器获取的K线数据格式：

```python
klines: List[Dict] = [
    {
        'time': datetime,      # 时间戳（datetime对象）
        'open': float,          # 开盘价
        'high': float,          # 最高价
        'low': float,           # 最低价
        'close': float,         # 收盘价
        'volume': float,        # 成交量
        # ... 其他字段（根据交易所API）
    },
    # ... 更多K线
]
```

**特点：**
- 列表格式，每个元素是一条K线
- 每条K线是字典，包含 `time/open/high/low/close/volume` 等字段
- 数量由配置中的 `LOOKBACK` 决定（默认200根）

## 2. 指标数据结构

扫描器计算的指标数据格式：

```python
indicators: Dict[str, Any] = {
    # 简单指标（数组格式）
    'ema_20': np.ndarray([...]),      # EMA(20)的数组，长度与K线相同
    'ema_50': np.ndarray([...]),      # EMA(50)的数组
    'ma_120': np.ndarray([...]),      # MA(120)的数组
    'rsi': np.ndarray([...]),         # RSI指标的数组
    'atr': np.ndarray([...]),          # ATR指标的数组
    
    # 复合指标（字典格式）
    'macd': {
        'macd': np.ndarray([...]),         # MACD线
        'macd_signal': np.ndarray([...]),  # 信号线
        'macd_hist': np.ndarray([...]),    # 柱状图
    },
    
    'bbands': {
        'bb_upper': np.ndarray([...]),     # 上轨
        'bb_middle': np.ndarray([...]),    # 中轨
        'bb_lower': np.ndarray([...]),     # 下轨
    },
    
    'kdj': {
        'kdj_k': np.ndarray([...]),        # K值
        'kdj_d': np.ndarray([...]),        # D值
        'kdj_j': np.ndarray([...]),        # J值
    },
    
    # ... 更多指标（根据配置）
}
```

**特点：**
- 字典格式，键为指标名称
- 简单指标的值是NumPy数组，长度与K线数组相同
- 复合指标（如MACD、布林带）的值是字典，包含多个子数组
- 数组中的每个元素对应一条K线的指标值
- 最后一个元素（`array[-1]`）是最新的指标值

## 3. 传递给AI分析器

扫描器调用 `analyzer.analyze_market()` 时传递的参数：

```python
analysis = await self.analyzer.analyze_market(
    symbol="BTCUSDT",           # 交易对名称
    klines=[...],               # 扫描器获取的K线数据（List[Dict]）
    indicators={...},           # 扫描器计算的指标数据（Dict[str, Any]）
    timeframe="1h"              # 时间周期
)
```

## 4. AI分析器处理流程

### 4.1 数据验证

AI分析器首先验证接收到的数据：

```python
# 验证K线数据
if not klines:
    logger.warning("无K线数据，无法分析")
    return None

# 验证指标数据有效性
valid_indicators = self._validate_indicators(indicators)
# 检查每个指标是否有有效值（非None、非NaN）
```

### 4.2 数据格式化

AI分析器将原始数据格式化为文本，用于填充提示词模板：

```python
market_data = {
    "symbol": "BTCUSDT",                    # 交易对
    "current_price": "67,890.50",          # 当前价格（格式化）
    "change_24h": "+2.34%",                 # 24h涨跌幅
    "volume_24h": "1,234.56 BTC",          # 24h成交量
    "timeframe": "1h",                     # 时间周期
    "indicators": """                      # 格式化的指标文本
        - ema_20: 67,500.00
        - ema_50: 67,200.00
        - rsi: 65.23
        - macd_macd: 123.45
        - macd_signal: 120.00
        ...
    """,
    "high": "68,000.00",                   # 最高价
    "low": "67,500.00",                    # 最低价
    "open": "67,800.00",                   # 开盘价
    "close": "67,890.50",                  # 收盘价
    "review_insights": "...",              # 复盘经验和优化策略（如果有）
}
```

### 4.3 构建AI提示词

使用 `PromptManager` 构建完整的AI消息：

```python
messages = [
    {
        "role": "system",
        "content": "你是专业的加密货币交易分析师..."
    },
    {
        "role": "user",
        "content": """
        请分析以下市场数据：
        
        交易对: {symbol}
        当前价格: {current_price}
        24h涨跌幅: {change_24h}
        时间周期: {timeframe}
        
        技术指标:
        {indicators}
        
        {review_insights}
        
        请基于以上数据进行分析...
        """
    }
]
```

### 4.4 调用AI并解析结果

AI返回JSON格式的分析结果，包含：
- `action`: 操作建议（买入/卖出/观望）
- `confidence`: 置信度（0-1）
- `trend`: 趋势（上涨/下跌/震荡）
- `entry_price`: 建议入场价格
- `stop_loss`: 止损价格
- `take_profit`: 止盈价格
- `leverage`: 建议杠杆
- `reason`: 分析原因
- `trading_standard`: 交易标准
- 等等...

## 5. 数据有效性检查

### 5.1 指标有效性验证

系统会检查每个指标是否有有效值：

```python
def _validate_indicators(indicators: Dict[str, Any]) -> int:
    """验证指标数据有效性，返回有效指标数量"""
    valid_count = 0
    for name, value in indicators.items():
        if isinstance(value, (list, tuple, np.ndarray)):
            # 检查数组中是否有有效值（非None、非NaN）
            if len(value) > 0:
                valid_values = [v for v in value if v is not None and str(v) != 'nan']
                if len(valid_values) > 0:
                    valid_count += 1
        elif isinstance(value, dict):
            # 复合指标：检查子指标是否有有效值
            has_valid = False
            for sub_value in value.values():
                if isinstance(sub_value, (list, tuple, np.ndarray)) and len(sub_value) > 0:
                    valid_sub = [v for v in sub_value if v is not None and str(v) != 'nan']
                    if len(valid_sub) > 0:
                        has_valid = True
                        break
            if has_valid:
                valid_count += 1
    return valid_count
```

### 5.2 警告信息

如果指标数据不足，系统会在日志中输出警告：

- `⚠️ {symbol} 无技术指标数据，无法分析` - 完全没有指标数据
- `⚠️ {symbol} 无有效技术指标数据，无法进行可靠分析` - 所有指标都无效
- `⚠️ {symbol} 部分技术指标无效（有效: X/Y）` - 部分指标无效

格式化后的指标文本也会包含警告：

```
⚠️ 系统检测：无技术指标数据（指标计算可能失败或未配置）
```

或

```
⚠️ 系统检测：所有技术指标数据无效（可能因K线数据不足导致指标计算失败）
```

## 6. 调试和查看数据流

### 6.1 启用DEBUG日志

设置日志级别为DEBUG：

```python
import logging
logging.getLogger("tradingai").setLevel(logging.DEBUG)
```

### 6.2 运行测试脚本

运行 `examples/data_flow_test.py`：

```bash
cd trading-ai
python examples/data_flow_test.py
```

该脚本会：
1. 创建扫描器和AI分析器
2. 扫描一个交易对
3. 详细输出每个步骤的数据结构
4. 保存完整的分析结果到JSON文件

### 6.3 日志输出示例

启用DEBUG日志后，你会看到类似以下输出：

```
📊 扫描器获取 BTCUSDT K线: 200 根
   K线数据结构示例（第一条）:
     时间: 2025-01-01 00:00:00, 开: 67000.0, 高: 67500.0, 低: 66800.0, 收: 67300.0, 量: 1234.56
   K线数据结构示例（最后一条）:
     时间: 2025-01-08 23:00:00, 开: 67800.0, 高: 68000.0, 低: 67700.0, 收: 67890.5, 量: 2345.67

📈 扫描器计算 BTCUSDT 指标: 5 个
   指标数据详情:
     ema_20: 数组[200], 有效值: 181, 最新值: 67500.0
     ema_50: 数组[200], 有效值: 151, 最新值: 67200.0
     rsi: 数组[200], 有效值: 187, 最新值: 65.23
     macd: 复合指标 ['macd', 'macd_signal', 'macd_hist']
       macd: 数组[200], 最新值: 123.45
       macd_signal: 数组[200], 最新值: 120.00
       macd_hist: 数组[200], 最新值: 3.45

🤖 传递数据给AI分析器: BTCUSDT
   - K线数据: 200 根（字典格式，包含time/open/high/low/close/volume）
   - 技术指标: ['ema_20', 'ema_50', 'rsi', 'macd']（字典格式，值为数组或复合字典）
   - 时间周期: 1h

📊 AI分析器接收数据验证: BTCUSDT
  - K线数量: 200 根
  - K线数据结构: 字典列表，每条包含 time/open/high/low/close/volume
  - 最新K线: 时间=2025-01-08 23:00:00, 价格=67890.5
  - 指标总数: 5 个
  - 有效指标数: 5 个
  - 指标列表: ['ema_20', 'ema_50', 'rsi', 'macd', 'atr']

📋 格式化后的市场数据（传递给AI）:
  - 交易对: BTCUSDT
  - 当前价格: 67,890.50
  - 24h涨跌幅: +2.34%
  - 24h成交量: 2,345.67 BTC
  - 时间周期: 1h
  - 技术指标: 已格式化（见下方详情）
  - 复盘经验: 无

📨 构建的AI消息: 2 条
  - 系统提示: 1234 字符
  - 用户提示预览: 请分析以下市场数据：交易对: BTCUSDT 当前价格: 67,890.50 ...
```

## 7. 常见问题

### Q: 为什么指标数组长度与K线数量相同，但有效值数量不同？

A: 因为指标计算需要一定数量的历史数据。例如：
- EMA(20) 需要至少20根K线才能计算出第一个有效值
- RSI(14) 需要至少14根K线
- MACD(12,26,9) 需要至少26根K线

所以前面的K线对应的指标值可能是NaN，只有后面的指标值才是有效的。

### Q: 如何知道某个指标是否有效？

A: 系统会自动检查，并在日志中输出：
- 有效指标数量
- 无效指标的警告信息

你也可以在格式化后的指标文本中看到：
- 如果所有指标都无效，会显示 `⚠️ 系统检测：所有技术指标数据无效`
- 如果部分指标无效，会显示 `⚠️ 系统检测：部分指标无效（有效: X/Y）`

### Q: 指标数据不足时，AI还能分析吗？

A: 可以，但会在提示词中明确告知AI指标数据不足，让AI知道是基于有限数据做出的判断。AI的分析结果会包含相应的警告信息。

### Q: 如何确认扫描器正确传递了数据？

A: 
1. 启用DEBUG日志（见上文）
2. 查看日志中的 `📊 扫描器获取` 和 `📈 扫描器计算` 部分
3. 查看日志中的 `📊 AI分析器接收数据验证` 部分
4. 运行 `examples/data_flow_test.py` 测试脚本

