# AI 模块架构说明

## 📁 目录结构

```
tradingai/ai/
├── __init__.py              # 模块导出
├── providers/               # 🔌 AI 提供商（通信层）
│   ├── __init__.py
│   ├── base.py             # 提供商基类
│   ├── factory.py          # 提供商工厂
│   ├── mock_provider.py    # Mock 提供商（测试用）
│   └── deepseek_provider.py  # DeepSeek 提供商
├── analyzers/               # 🎯 分析器（业务层）
│   ├── __init__.py
│   └── market_analyzer.py  # 市场分析器
└── prompts/                 # 📝 提示词（模板层）
    └── __init__.py
```

## 🏗️ 架构设计

### 三层分离架构

```
┌─────────────────────────────────────────────────┐
│  analyzers/ (业务层)                             │
│  - 市场分析                                       │
│  - 信号生成                                       │
│  - 风险评估                                       │
└──────────────────┬──────────────────────────────┘
                   │ 调用
┌──────────────────▼──────────────────────────────┐
│  providers/ (通信层)                             │
│  - OpenAI/DeepSeek                               │
│  - Claude                                        │
│  - 本地模型                                      │
└──────────────────┬──────────────────────────────┘
                   │ 使用
┌──────────────────▼──────────────────────────────┐
│  prompts/ (模板层)                               │
│  - 提示词模板                                     │
│  - 角色设定                                       │
│  - 格式要求                                       │
└─────────────────────────────────────────────────┘
```

## 📦 各层职责

### 1. providers/ - AI 提供商（通信层）

**职责：**只负责与 AI API 的通信

**不包含：**
- ❌ 业务逻辑（市场分析等）
- ❌ 提示词构建
- ❌ 结果解析

**只包含：**
- ✅ API 连接
- ✅ 消息发送
- ✅ 响应接收

**示例：**
```python
# 提供商只负责通信
provider = AIProviderFactory.create("deepseek", api_key="xxx")
response = await provider.chat(messages=[...])
```

### 2. analyzers/ - 分析器（业务层）

**职责：**使用 AI 提供商完成具体业务

**包含：**
- ✅ 市场数据分析
- ✅ 交易信号生成
- ✅ 风险评估
- ✅ 结果解析

**示例：**
```python
# 分析器负责业务逻辑
analyzer = MarketAnalyzer(provider)
result = await analyzer.analyze_market(symbol, klines, indicators)
# result = {"signal": "buy", "confidence": 0.8, ...}
```

### 3. prompts/ - 提示词（模板层）

**职责：**管理各种场景的提示词模板

**包含：**
- ✅ 系统角色设定
- ✅ 输入格式要求
- ✅ 输出格式规范
- ✅ 示例和说明

## 🔄 使用流程

```python
# 1. 创建提供商（通信层）
provider = AIProviderFactory.create_from_config()

# 2. 创建分析器（业务层）
analyzer = MarketAnalyzer(provider)

# 3. 执行分析
result = await analyzer.analyze_market(
    symbol="BTCUSDT",
    klines=klines_data,
    indicators=indicators_data
)

# 4. 使用结果
if result["signal"] == "buy":
    print(f"买入信号，置信度：{result['confidence']:.2%}")
```

## ✨ 优势

1. **职责清晰**
   - 提供商专注通信
   - 分析器专注业务
   - 提示词独立管理

2. **易于扩展**
   - 添加新提供商：只需实现 `BaseAIProvider`
   - 添加新分析功能：创建新的分析器类
   - 修改提示词：只需修改模板

3. **易于测试**
   - 可以独立测试每一层
   - Mock 提供商用于测试
   - 业务逻辑与通信解耦

4. **易于维护**
   - 修改 AI API 不影响业务逻辑
   - 修改业务逻辑不影响通信层
   - 目录结构清晰明了

## 🚀 添加新提供商

```python
# tradingai/ai/providers/deepseek_provider.py
from .base import BaseAIProvider

class DeepSeekProvider(BaseAIProvider):
    async def chat(self, messages, **kwargs):
        # 只负责与 DeepSeek API 通信
        ...
    
    def get_provider_name(self):
        return "DeepSeek"
```

## 🎯 添加新分析器

```python
# tradingai/ai/analyzers/risk_analyzer.py
from ..providers.base import BaseAIProvider

class RiskAnalyzer:
    def __init__(self, provider: BaseAIProvider):
        self.provider = provider
    
    async def assess_risk(self, ...):
        # 使用提供商进行风险评估
        ...
```

## 📝 注意事项

1. **提供商不应包含业务逻辑**
   - ❌ 不要在提供商中分析市场
   - ✅ 只负责发送和接收消息

2. **分析器应该可复用**
   - ✅ 可以使用任何提供商
   - ✅ 业务逻辑独立于具体 AI

3. **保持层次分明**
   - ✅ providers/ 只导入基础库
   - ✅ analyzers/ 可以导入 providers/
   - ✅ prompts/ 独立于其他层


