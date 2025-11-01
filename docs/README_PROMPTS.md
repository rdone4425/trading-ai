# 提示词系统使用文档

## 📖 概述

本项目使用提示词系统（Prompts）来指导 AI 进行不同类型的分析。提示词分为**系统提示词**（定义角色）和**用户提示词**（提供数据）。

## 🎯 工作流程

```
用户调用 MarketAnalyzer
          ↓
    自动初始化 PromptManager
          ↓
  根据方法选择提示词类型
          ↓
┌─────────┬─────────┬─────────┐
│ analysis│ learning│ review  │
└─────────┴─────────┴─────────┘
     ↓          ↓         ↓
  加载对应目录的提示词文件
          ↓
  system.txt + user.txt
          ↓
   填充数据到占位符
          ↓
    发送到 AI 提供商
          ↓
    解析 AI 响应
          ↓
   返回结构化结果
```

## 📁 目录结构

```
prompts/
├── analysis/              # 市场分析
│   ├── system.txt        # 系统：定义分析师角色
│   └── user.txt          # 用户：市场数据模板
│
├── learning/              # 学习辅导
│   ├── system.txt        # 系统：定义导师角色
│   └── user.txt          # 用户：学习主题模板
│
└── review/                # 交易复盘
    ├── system.txt        # 系统：定义复盘师角色
    └── user.txt          # 用户：交易数据模板
```

## 🔧 使用方法

### 1. 市场分析（analysis/）

**自动使用：** `MarketAnalyzer.analyze_market()`

```python
from tradingai.ai import AIProviderFactory
from tradingai.ai.analyzers import MarketAnalyzer

# 创建分析器（自动加载提示词）
provider = AIProviderFactory.create_from_config()
analyzer = MarketAnalyzer(provider)

# 调用时自动使用 prompts/analysis/ 提示词
result = await analyzer.analyze_market(
    symbol="BTCUSDT",
    klines=kline_data,
    indicators=indicator_data,
    timeframe="1h"
)

# 返回结构化数据
print(f"Action: {result['action']}")
print(f"Confidence: {result['confidence']}")
```

**提示词文件：**
- `system.txt`: 定义专业交易分析师角色
- `user.txt`: 包含市场数据占位符：
  - `{symbol}` - 交易对
  - `{current_price}` - 当前价格
  - `{indicators}` - 技术指标
  - ...

**AI 返回格式：** JSON
```json
{
  "symbol": "BTCUSDT",
  "trend": "上升",
  "action": "做多",
  "confidence": 0.75,
  "entry_price": 95234.50,
  "stop_loss": 93500.00,
  "take_profit": 98000.00,
  "support": 94000.00,
  "resistance": 96500.00,
  "risk_reward_ratio": "1:2.5",
  "reason": "详细分析...",
  "warnings": ["风险提示1", "风险提示2"]
}
```

---

### 2. 学习辅导（learning/）

**自动使用：** `MarketAnalyzer.provide_learning()`

```python
# 调用时自动使用 prompts/learning/ 提示词
learning = await analyzer.provide_learning(
    topic="EMA 指标",
    level="初级",
    questions=["EMA和MA有什么区别？"]
)

print(learning)  # 返回教学文本
```

**提示词文件：**
- `system.txt`: 定义交易导师角色
- `user.txt`: 包含学习主题占位符：
  - `{topic}` - 学习主题
  - `{level}` - 学习水平
  - `{questions}` - 具体问题
  - `{goals}` - 学习目标

**AI 返回格式：** 文本
- 概念解释
- 实际应用
- 注意事项
- 进阶建议

---

### 3. 交易复盘（review/）

**自动使用：** `MarketAnalyzer.review_trade()`

```python
# 调用时自动使用 prompts/review/ 提示词
review = await analyzer.review_trade({
    "symbol": "ETHUSDT",
    "direction": "做多",
    "profit_loss": "+500",
    # ... 更多交易数据
})

# 返回结构化评分
print(f"Rating: {review['overall_rating']}")
print(f"Decision: {review['decision_quality']['score']}/10")
```

**提示词文件：**
- `system.txt`: 定义复盘分析师角色
- `user.txt`: 包含交易数据占位符：
  - `{symbol}` - 交易对
  - `{direction}` - 交易方向
  - `{profit_loss}` - 盈亏金额
  - ...

**AI 返回格式：** JSON
```json
{
  "overall_rating": "良好",
  "decision_quality": {"score": 8, "comment": "..."},
  "execution_quality": {"score": 7, "comment": "..."},
  "risk_management": {"score": 9, "comment": "..."},
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["缺点1", "缺点2"],
  "lessons_learned": ["教训1", "教训2"],
  "improvements": ["建议1", "建议2"],
  "summary": "总结..."
}
```

---

## ⚙️ 自定义提示词

### 修改现有提示词

直接编辑 `prompts/` 目录下的 `.txt` 文件：

```bash
# 修改分析师的角色定义
nano prompts/analysis/system.txt

# 修改数据模板
nano prompts/analysis/user.txt
```

### 创建新类型提示词

```bash
# 1. 创建新目录
mkdir prompts/your_new_type/

# 2. 创建提示词文件
# system.txt - 定义角色
# user.txt - 数据模板

# 3. 更新 PromptManager.PROMPT_TYPES
# 在 tradingai/ai/prompts/prompt_manager.py 中添加
```

### 提示词最佳实践

1. **system.txt (系统提示词)**
   - 清晰定义 AI 的角色和能力
   - 说明输出格式要求（JSON/文本）
   - 强调重要原则（如风险管理）
   - 提供输出示例

2. **user.txt (用户提示词)**
   - 使用 `{variable}` 占位符
   - 结构化组织数据
   - 明确指出必填和可选字段
   - 添加格式提醒

3. **JSON 格式要求**
   - 在提示词中强调"只返回 JSON"
   - 提供完整的 JSON 示例
   - 说明数据类型要求
   - 禁止在 JSON 外添加文字

---

## 🧪 测试提示词

### 快速测试

```bash
# 测试市场分析
python test_analyzer.py

# 测试完整功能
python examples/analyzer_example.py
```

### 查看提示词内容

```bash
# 查看系统提示词
cat prompts/analysis/system.txt

# 查看用户模板
cat prompts/analysis/user.txt
```

### 调试模式

在 `.env` 中设置：
```bash
LOG_LEVEL=DEBUG
```

可以看到：
- 加载了哪些提示词
- 填充后的完整消息
- AI 的原始响应

---

## 📊 提示词效果评估

### 指标

1. **JSON 解析成功率**
   - 目标: > 95%
   - 查看日志中的 "JSON 解析失败" 次数

2. **置信度准确性**
   - AI 给出的置信度是否合理
   - 与实际市场表现对比

3. **建议质量**
   - 交易建议是否有逻辑
   - 止损止盈是否合理

### 优化方法

1. **增强格式要求**
   - 在提示词中多次强调 JSON 格式
   - 提供更详细的示例

2. **调整角色定义**
   - 根据 AI 响应调整角色描述
   - 增加或减少能力说明

3. **优化数据模板**
   - 调整占位符的组织方式
   - 添加更多上下文信息

---

## 🔗 相关文档

- [提示词示例](../examples/prompt_example.py)
- [分析器示例](../examples/analyzer_example.py)
- [AI 提供商文档](README_MODELSCOPE.md)
- [主文档](../README.md)

---

**提示词是 AI 的"灵魂"，精心设计的提示词能显著提升 AI 的表现！** 🎯

