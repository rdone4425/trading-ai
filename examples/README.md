# 使用示例

## 指标计算示例

### 运行示例
```bash
python examples/indicator_example.py
```

### 配置方法

#### 方法1: 代码中配置
```python
from tradingai.indicators import IndicatorEngine

# 配置字符串
config_str = """
1_ema=20,120
1_ma=20,30,60
1_rsi=14
2_macd=12,26,9
"""

engine = IndicatorEngine(config_str)
indicators = engine.calculate_group(klines, "1")
```

#### 方法2: 环境变量配置
在 `.env` 文件中：
```bash
INDICATOR_CONFIG=1_ema=20,120;1_ma=20,30;1_rsi=14;2_macd=12,26,9
```

代码中：
```python
from tradingai import config
from tradingai.indicators import IndicatorEngine

engine = IndicatorEngine()
engine.load_config(config.INDICATOR_CONFIG_RAW)
```

### 配置格式说明

**环境变量格式**: `INDICATOR_指标名=参数1,参数2,...`

**代码字符串格式**: `指标名=参数1,参数2,...`

**示例**:

环境变量配置（.env）:
```bash
INDICATOR_ema=7,20,120      # 计算 EMA(7), EMA(20), EMA(120)
INDICATOR_ma=20,30,60       # 计算 MA(20), MA(30), MA(60)
INDICATOR_rsi=14            # 计算 RSI(14)
INDICATOR_atr=14            # 计算 ATR(14)
INDICATOR_macd=12,26,9      # 计算 MACD(12,26,9)
```

代码字符串配置:
```python
config_str = """
ema=7,20,120
ma=20,30,60
rsi=14
macd=12,26,9
"""
```

### 支持的指标

| 指标名 | 参数说明 | 示例 |
|--------|---------|------|
| `ma` | 周期 | `1_ma=20,30,60` |
| `ema` | 周期 | `1_ema=12,26` |
| `rsi` | 周期 | `1_rsi=14` |
| `macd` | 快线,慢线,信号线 | `1_macd=12,26,9` |
| `bbands` | 周期,上轨倍数,下轨倍数 | `1_bbands=20,2,2` |
| `kdj` | FastK,SlowK,SlowD | `1_kdj=9,3,3` |
| `atr` | 周期 | `1_atr=14` |

### 使用场景

**场景1: 多策略回测**
```python
# 策略1: 短期指标
strategy1_config = "ema=5,10;rsi=7"

# 策略2: 长期指标
strategy2_config = "ema=20,60;rsi=14"

# 策略3: 综合指标
strategy3_config = "macd=12,26,9;bbands=20,2,2"
```

**场景2: EMA 交叉策略**
```python
# 检测 EMA(7) 和 EMA(20) 的交叉
cross_info = engine.detect_ema_cross(klines, 7, 20)

if cross_info['latest_cross'] == 'golden':
    print("🟢 金叉信号 - 做多")
elif cross_info['latest_cross'] == 'death':
    print("🔴 死叉信号 - 做空")

# 查看当前位置
if cross_info['current_position'] == 'above':
    print("快线在慢线上方")
```

**场景3: 动态调参**
```python
# 测试不同参数组合
for fast in [5, 7, 10]:
    for slow in [20, 30, 60]:
        cross_info = engine.detect_ema_cross(klines, fast, slow)
        print(f"EMA({fast}) vs EMA({slow}): {cross_info['latest_cross']}")
```

**场景4: 实时监控**
```python
# 获取最新指标值用于实时判断
latest = engine.get_latest_values(klines)
if latest['rsi'] < 30:
    print("超卖")
elif latest['rsi'] > 70:
    print("超买")
```

