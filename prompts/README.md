# 交易 AI 提示词库

本目录使用 **JSON 格式** 管理所有 AI 提示词。

## 📁 文件结构

```
prompts/
├── prompts.json    # 所有提示词的JSON配置文件
└── README.md       # 本文件
```

## 📝 prompts.json 格式

```json
{
  "提示词类型": {
    "name": "名称",
    "description": "描述",
    "system": "系统提示词（定义AI角色）",
    "user": "用户提示词模板（包含占位符）",
    "output_format": "json/text",
    "temperature": 0.3,
    "max_tokens": 2000
  }
}
```

## 🎯 支持的提示词类型

### 1. analysis - 市场分析
- **角色**: 专业交易分析师
- **输出**: JSON 格式
- **配置**: `temperature=0.3`, `max_tokens=2000`
- **用途**: 实时市场分析，给出交易建议

### 2. learning - 学习辅导
- **角色**: 交易导师
- **输出**: 文本格式
- **配置**: `temperature=0.7`, `max_tokens=3000`
- **用途**: 交易知识教学和指导

### 3. review - 交易复盘
- **角色**: 复盘分析师
- **输出**: JSON 格式
- **配置**: `temperature=0.5`, `max_tokens=3000`
- **用途**: 历史交易复盘和改进建议

## 🔧 使用方法

### Python 代码中使用

```python
from tradingai.ai.prompts import PromptManager

# 初始化（自动加载 prompts.json）
pm = PromptManager()

# 获取系统提示词
system = pm.get_system_prompt("analysis")

# 获取用户模板
user = pm.get_user_template("analysis")

# 获取配置
config = pm.get_prompt_config("analysis")
# {'temperature': 0.3, 'max_tokens': 2000, 'output_format': 'json'}

# 格式化用户提示词
user_prompt = pm.format_user_prompt("analysis", {
    "symbol": "BTCUSDT",
    "current_price": "95000",
    # ... 更多数据
})

# 获取完整消息
messages = pm.get_full_prompt("analysis", market_data)
```

### MarketAnalyzer 中使用

MarketAnalyzer 会自动加载和使用提示词：

```python
from tradingai.ai import AIProviderFactory
from tradingai.ai.analyzers import MarketAnalyzer

provider = AIProviderFactory.create_from_config()
analyzer = MarketAnalyzer(provider)

# 自动使用 analysis 提示词
result = await analyzer.analyze_market(symbol, klines, indicators)

# 自动使用 learning 提示词
learning = await analyzer.provide_learning(topic, level)

# 自动使用 review 提示词
review = await analyzer.review_trade(trade_data)
```

## ✏️ 修改提示词

直接编辑 `prompts.json` 文件：

```bash
# 使用任何文本编辑器
code prompts.json
# 或
notepad prompts.json
```

修改后自动生效（有缓存机制，或调用 `pm.reload_prompt()` 强制重新加载）。

## 🎨 添加新类型提示词

在 `prompts.json` 中添加新的键：

```json
{
  "新类型": {
    "name": "新类型名称",
    "description": "描述",
    "system": "系统提示词...",
    "user": "用户模板...",
    "output_format": "json",
    "temperature": 0.7,
    "max_tokens": 2000
  }
}
```

然后在 `PromptManager.PROMPT_TYPES` 中添加该类型。

## 📋 占位符说明

用户提示词模板中使用 `{variable}` 格式的占位符：

### analysis 占位符
- `{symbol}` - 交易对
- `{current_price}` - 当前价格
- `{change_24h}` - 24小时涨跌幅
- `{volume_24h}` - 24小时成交量
- `{timeframe}` - 时间周期
- `{indicators}` - 技术指标
- `{high}`, `{low}`, `{open}`, `{close}` - K线数据

### learning 占位符
- `{topic}` - 学习主题
- `{level}` - 学习水平
- `{questions}` - 具体问题
- `{goals}` - 学习目标

### review 占位符
- `{symbol}` - 交易对
- `{direction}` - 交易方向
- `{entry_price}`, `{exit_price}` - 价格
- `{profit_loss}` - 盈亏
- `{reasoning}` - 交易依据
- ... 更多字段

## 🔍 JSON vs 文本文件

### 为什么使用 JSON？

✅ **优点**:
- 所有提示词集中管理
- 包含配置参数（temperature, max_tokens等）
- 易于版本控制
- 结构化，便于程序读取
- 支持多语言

❌ **旧的文本文件格式**:
- 文件分散（system.txt + user.txt）
- 配置分离
- 难以维护

### 向后兼容

PromptManager 同时支持两种格式：
- 优先使用 `prompts.json`
- 如果不存在，降级到 `.txt` 文件
- 可以通过 `use_json=False` 参数强制使用文本格式

## 🚀 最佳实践

1. **修改前备份**
   ```bash
   cp prompts.json prompts.json.backup
   ```

2. **验证 JSON 格式**
   ```bash
   python -m json.tool prompts.json
   ```

3. **测试修改效果**
   ```bash
   python test_analyzer.py
   ```

4. **使用版本控制**
   ```bash
   git add prompts.json
   git commit -m "优化提示词"
   ```

## 📚 相关文档

- [完整使用指南](../docs/README_PROMPTS.md)
- [MarketAnalyzer 文档](../tradingai/ai/analyzers/README.md)
- [示例代码](../examples/analyzer_example.py)

---

**提示词是 AI 的"灵魂"，精心设计的提示词能显著提升 AI 的表现！** 🎯
