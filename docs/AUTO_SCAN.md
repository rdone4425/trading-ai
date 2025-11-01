# 自动扫描功能使用说明

## 功能概述

Trading AI 支持两种扫描模式：
1. **单次扫描**：运行一次后退出（默认）
2. **自动循环扫描**：根据K线周期自动循环扫描

## 启用自动循环扫描

### 方法1：修改 .env 配置文件

在 `.env` 文件中设置：

```bash
AUTO_SCAN=true
```

然后运行：

```bash
python main.py
```

### 方法2：临时启用（仅本次运行）

**Windows PowerShell:**
```powershell
$env:AUTO_SCAN="true"; python main.py
```

**Windows CMD:**
```cmd
set AUTO_SCAN=true && python main.py
```

**Linux/Mac:**
```bash
AUTO_SCAN=true python main.py
```

## 工作原理

### 单次扫描模式 (AUTO_SCAN=false)
```
启动 → 连接交易所 → 扫描一次 → 显示结果 → 退出
```

### 自动循环扫描模式 (AUTO_SCAN=true)
```
启动 → 连接交易所 → 扫描 → 等待K线完成 → 扫描 → ...（循环）
```

**自动扫描特性：**
- ✅ 启动时立即执行第一次扫描
- ✅ 自动对准K线周期（根据 `TIMEFRAME` 配置）
- ✅ 等待K线完成后再进行下次扫描（根据 `KLINE_TYPE` 配置）
- ✅ 实时显示扫描进度和等待时间
- ✅ 按 `Ctrl+C` 优雅退出

## 配置说明

### TIMEFRAME（K线周期）
决定扫描的时间间隔：

```bash
TIMEFRAME=1m    # 每1分钟扫描一次
TIMEFRAME=5m    # 每5分钟扫描一次
TIMEFRAME=15m   # 每15分钟扫描一次
TIMEFRAME=1h    # 每1小时扫描一次
TIMEFRAME=4h    # 每4小时扫描一次
```

### KLINE_TYPE（K线类型）
决定扫描时机：

```bash
KLINE_TYPE=closed  # 等待K线完成后扫描（推荐）
KLINE_TYPE=open    # K线进行中也扫描（实时性更强）
```

### 扫描方式

#### 自定义交易对
```bash
CUSTOM_SYMBOLS=btc,eth,xrp  # 只扫描指定的交易对
```

#### 自动扫描
```bash
CUSTOM_SYMBOLS=             # 留空，使用SCAN_TYPES自动扫描
SCAN_TYPES=hot,volume,gainers,losers
SCAN_TOP_N=20               # 每种类型取前20个，合并去重
```

## 示例配置

### 短线交易配置（1分钟K线）
```bash
TIMEFRAME=1m
KLINE_TYPE=closed
AUTO_SCAN=true
SCAN_TYPES=volume,gainers
SCAN_TOP_N=10
```

### 中线交易配置（15分钟K线）
```bash
TIMEFRAME=15m
KLINE_TYPE=closed
AUTO_SCAN=true
SCAN_TYPES=hot,volume,gainers,losers
SCAN_TOP_N=20
```

### 长线交易配置（1小时K线）
```bash
TIMEFRAME=1h
KLINE_TYPE=closed
AUTO_SCAN=true
CUSTOM_SYMBOLS=btc,eth,bnb,sol
```

## 运行示例

### 示例1：自动扫描热门币种
```bash
# 配置 .env
TIMEFRAME=15m
AUTO_SCAN=true
SCAN_TYPES=hot,volume
SCAN_TOP_N=10

# 运行
python main.py
```

**输出：**
```
============================================================
🤖 Trading AI 启动
============================================================

⚙️  配置:
   交易所: binance
   周期: 15m
   K线类型: closed (已完成)
   扫描模式: hot,volume
   数量: 10

🔄 启动自动扫描
   周期: 15m
   K线类型: closed (已完成)
   对准K线: 是

============================================================
📊 开始扫描 - 2025-11-01 14:15:00
============================================================
找到 10 个交易对

💰 价格信息（前5个）:
   BTCUSDT        68,234.50 (  +2.45%) 量:    1.23B
   ETHUSDT         3,456.78 (  +1.89%) 量:    856.43M
   ...

✅ 扫描完成 - 找到 10 个交易对

⏰ 等待 895 秒，直到下一根 15m K线完成...
   当前时间: 2025-11-01 14:15:05
   目标时间: 2025-11-01 14:30:00

... (等待中)

🎯 K线已完成

============================================================
📊 开始扫描 - 2025-11-01 14:30:00
============================================================
...
```

### 示例2：单次快速扫描
```bash
# 临时禁用自动扫描
$env:AUTO_SCAN="false"; python main.py
```

## 停止扫描

在自动扫描过程中，按 `Ctrl+C` 即可优雅退出：

```
^C
⏹️  收到中断信号，停止扫描...
✅ 已停止
```

## 进阶示例

### 使用专用的自动扫描示例
```bash
python examples/auto_scan_example.py
```

### 使用自定义回调的扫描示例
```bash
python examples/custom_scan_example.py
```

这两个示例提供了更多的自定义功能和演示。

## 常见问题

### Q: 如何调整扫描频率？
A: 修改 `TIMEFRAME` 配置，支持：1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d 等

### Q: 扫描是精确对准K线时间吗？
A: 是的，程序会自动计算并等待到K线完成的精确时刻才开始扫描

### Q: 可以在扫描时计算指标吗？
A: 可以！参考 `examples/custom_scan_example.py`，在回调函数中添加指标计算逻辑

### Q: 如何避免API限流？
A: 
1. 适当增加 `TIMEFRAME` 周期（如15m或1h）
2. 减少 `SCAN_TOP_N` 数量
3. 使用 `CUSTOM_SYMBOLS` 只监控关注的币种

## 总结

- **默认**：单次扫描后退出
- **启用自动扫描**：设置 `AUTO_SCAN=true`
- **扫描频率**：由 `TIMEFRAME` 决定
- **扫描时机**：由 `KLINE_TYPE` 决定
- **优雅退出**：`Ctrl+C`

享受自动化交易扫描！🚀

