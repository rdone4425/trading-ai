# 交易功能使用指南

## 概述

Trading AI 现已集成自动交易功能，可以基于 AI 分析结果自动执行交易。系统支持三种运行模式：

1. **观察模式 (observe)**: 仅分析，不执行交易
2. **测试网模式 (testnet)**: 在币安测试网执行交易
3. **实盘模式 (mainnet)**: 在币安实盘执行交易 ⚠️

## 核心功能

### 1. 交易执行器 (Trader)

位置：`tradingai/trader/trader.py`

**主要功能**：
- ✅ 基于 AI 分析结果自动执行交易
- ✅ 强制设置止损止盈（每笔交易必须有保护）
- ✅ 自动设置杠杆和逐仓模式
- ✅ 单向持仓控制（同一交易对只有一个方向持仓）
- ✅ 防止重复开单（三重检查机制）
- ✅ 风险管理（仓位大小、风险控制）

**关键特性**：
- 完全基于平台抽象接口，不依赖具体平台实现
- 支持币安、OKX、Bybit 等所有实现了 BasePlatform 的平台
- 智能缓存机制，减少 API 调用

### 2. 自动交易流程

```
扫描市场 → AI 分析 → 高置信度建议 → 自动执行交易
```

系统会自动执行以下步骤：

1. **扫描市场**：获取符合条件的交易对
2. **AI 分析**：分析技术指标，生成交易建议
3. **筛选建议**：仅处理高置信度建议（可配置阈值）
4. **执行交易**：
   - 检查现有持仓（防止重复）
   - 设置杠杆和逐仓模式
   - 提交入场订单（市价单）
   - 设置止损订单（必须）
   - 设置止盈订单（必须）
   - 记录持仓信息

## 配置说明

### 1. 基础配置 (.env)

```bash
# ============= 交易环境 =============
# observe: 观察模式（不执行交易）
# testnet: 测试网模式（使用测试资金）
# mainnet: 实盘模式（真实资金，⚠️ 谨慎！）
TRADING_ENVIRONMENT=observe

# ============= API 配置 =============
# 币安 API（如果是 testnet 或 mainnet 模式，必须配置）
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here

# ============= 风险管理配置 =============
# 默认杠杆倍数
DEFAULT_LEVERAGE=10

# 最大持仓数
MAX_POSITIONS=5

# 单笔交易最大仓位（账户余额的百分比）
MAX_POSITION_SIZE=0.2

# 单笔交易最大亏损（账户余额的百分比）
MAX_LOSS_PER_TRADE=0.02

# 风险百分比（每笔交易愿意承受的风险）
RISK_PERCENT=0.01

# ============= AI 分析配置 =============
# AI 置信度阈值（只执行高于此阈值的交易）
AI_CONFIDENCE_THRESHOLD=0.6

# 账户余额（如果无法从交易所获取，使用此默认值）
ACCOUNT_BALANCE=10000.0
```

### 2. 模式切换

#### 观察模式（默认，安全）
```bash
TRADING_ENVIRONMENT=observe
```
- 不需要配置 API Key
- 仅进行分析，不执行交易
- 适合测试和学习

#### 测试网模式
```bash
TRADING_ENVIRONMENT=testnet
BINANCE_API_KEY=<testnet_api_key>
BINANCE_API_SECRET=<testnet_api_secret>
```
- 使用币安测试网
- 测试资金，无风险
- 验证交易逻辑
- 测试网注册：https://testnet.binancefuture.com/

#### 实盘模式 ⚠️
```bash
TRADING_ENVIRONMENT=mainnet
BINANCE_API_KEY=<real_api_key>
BINANCE_API_SECRET=<real_api_secret>
```
- ⚠️ 使用真实资金
- ⚠️ 务必充分测试后再启用
- ⚠️ 建议先在测试网验证策略

## 使用方法

### 1. 快速测试

运行测试脚本，验证交易功能是否正常：

```bash
python test_trading.py
```

测试内容：
- ✅ 平台连接
- ✅ 账户余额获取
- ✅ 持仓查询
- ✅ 持仓检查
- ℹ️ 交易执行（安全模式，默认跳过）

### 2. 运行主程序

#### 单次扫描分析
```bash
python main.py
```

系统会：
1. 扫描市场
2. 进行 AI 分析
3. 显示高置信度建议
4. **如果是 testnet/mainnet 模式，自动执行交易**

#### 自动循环扫描
```bash
# 在 .env 中设置
AUTO_SCAN=true
SCAN_INTERVAL=60  # 扫描间隔（秒）
```

然后运行：
```bash
python main.py
```

系统会每隔一段时间自动扫描、分析并执行交易。

## 交易逻辑详解

### 1. 防重复机制

系统采用**三重检查机制**防止重复开单：

1. **本地缓存检查**：快速检查内存中的持仓记录
2. **交易所实际持仓检查**：查询交易所当前持仓
3. **下单前再次确认**：提交订单前的最后一次检查

### 2. 风险管理

系统自动计算并控制风险：

```python
# 仓位大小计算
position_size = (account_balance * risk_percent) / (entry_price - stop_loss) * leverage

# 保证金计算
margin_required = (position_size * entry_price) / leverage

# 潜在盈亏
potential_profit = (take_profit - entry_price) * position_size
potential_loss = (entry_price - stop_loss) * position_size
```

### 3. 止损止盈

每笔交易**强制设置**止损和止盈：

- **止损订单**：市价止损 (STOP_MARKET)
- **止盈订单**：市价止盈 (TAKE_PROFIT_MARKET)
- 两者都设置为平仓 (closePosition=True)

### 4. 杠杆和保证金模式

系统自动配置：

- **杠杆**：根据配置或 AI 建议设置
- **保证金模式**：逐仓 (ISOLATED)
- 每个交易对独立管理风险

## 日志和监控

### 1. 日志位置

- **主日志**：`logs/trading_ai.log`
- **交易日志**：`logs/trade.log`
- **分析结果**：`data/analysis_results/YYYYMMDD/`

### 2. 关键日志标识

- `[TRADE]`：交易执行相关
- `[RISK]`：风险管理相关
- `[POSITION]`：持仓管理相关
- `[OK]`：操作成功
- `[WARN]`：警告信息
- `[ERROR]`：错误信息

## 安全建议

### ⚠️ 重要提示

1. **先在观察模式测试**
   - 熟悉系统运行流程
   - 验证 AI 分析质量
   - 了解交易逻辑

2. **再在测试网验证**
   - 使用测试资金模拟真实交易
   - 验证风险管理
   - 确认止损止盈正常工作

3. **最后小资金实盘**
   - 使用少量资金开始
   - 持续监控系统运行
   - 根据表现调整参数

### 🔒 API 安全

1. **限制权限**：
   - 仅授予必要的交易权限
   - 禁用提币权限
   - 启用 IP 白名单

2. **密钥管理**：
   - 不要在代码中硬编码密钥
   - 使用 .env 文件管理
   - 定期更换密钥

3. **监控异常**：
   - 设置告警通知
   - 定期检查交易记录
   - 及时处理异常情况

## 常见问题

### Q1: 为什么交易没有执行？

**可能原因**：
1. 运行在观察模式 (`TRADING_ENVIRONMENT=observe`)
2. AI 置信度低于阈值 (`AI_CONFIDENCE_THRESHOLD`)
3. 该交易对已有持仓（单向持仓限制）
4. 风险管理检查未通过

**解决方法**：
- 检查 `.env` 配置
- 降低置信度阈值（谨慎！）
- 查看日志中的详细原因

### Q2: 如何调整风险参数？

修改 `.env` 中的风险配置：

```bash
# 每笔交易风险（1% 账户）
RISK_PERCENT=0.01

# 单笔最大仓位（20% 账户）
MAX_POSITION_SIZE=0.2

# 单笔最大亏损（2% 账户）
MAX_LOSS_PER_TRADE=0.02
```

### Q3: 如何手动平仓？

系统会在以下情况自动平仓：
- 触发止损
- 触发止盈
- 手动在交易所平仓

如需通过代码平仓：

```python
from tradingai.trader import Trader
from tradingai.exchange.factory import PlatformFactory

platform = PlatformFactory.create(...)
trader = Trader(platform)

# 平仓
await trader.close_position("BTCUSDT", "LONG")
```

### Q4: 测试网和实盘有什么区别？

| 特性 | 测试网 | 实盘 |
|------|--------|------|
| 资金 | 虚拟测试资金 | 真实资金 |
| API | testnet.binancefuture.com | fapi.binance.com |
| 风险 | 无风险 | 有风险 |
| 用途 | 测试和学习 | 真实交易 |

## 高级配置

### 1. 自定义交易策略

在 `main.py` 中可以自定义交易逻辑：

```python
# 过滤高置信度结果
high_conf_results = [
    r for r in analysis_results 
    if r.get('confidence', 0) >= 0.8  # 自定义阈值
    and r.get('action') != '观望'
    and r.get('symbol') in ['BTCUSDT', 'ETHUSDT']  # 限制交易对
]

# 执行交易
for result in high_conf_results:
    trade_result = await trader.execute_trade(result)
```

### 2. 监控和告警

可以集成第三方告警服务：

```python
# 交易成功通知
if trade_result.get('success'):
    send_notification(f"已开仓：{symbol} {action}")

# 止损触发通知
if position_closed_by_stop_loss:
    send_alert(f"止损触发：{symbol}")
```

## 性能优化

1. **缓存机制**：
   - 账户余额缓存（60秒）
   - 持仓信息本地缓存
   - 减少 API 调用

2. **异步处理**：
   - 所有网络请求使用 `asyncio`
   - 并发处理多个交易对
   - 非阻塞文件 I/O

3. **智能重试**：
   - API 请求失败自动重试
   - 指数退避策略
   - 避免触发限流

## 贡献和反馈

如有问题或建议，欢迎：
- 提交 Issue
- 创建 Pull Request
- 联系开发团队

---

**免责声明**：本系统仅供学习和研究使用。使用本系统进行真实交易存在风险，可能导致资金损失。请在充分测试和理解系统的基础上谨慎使用。开发者不对任何损失负责。

