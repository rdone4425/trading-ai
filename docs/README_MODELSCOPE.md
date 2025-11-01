# ModelScope AI 提供商使用指南

ModelScope（魔塔）是一个集成了众多开源模型的 AI 平台，提供 OpenAI 兼容的 API。

## 📋 目录
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [支持的模型](#支持的模型)
- [使用示例](#使用示例)
- [常见问题](#常见问题)

---

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install openai
```

### 2. 获取 ModelScope Token
1. 访问 [ModelScope 官网](https://www.modelscope.cn/)
2. 注册并登录账号
3. 进入 [API Token 管理页面](https://www.modelscope.cn/my/myaccesstoken)
4. 创建或复制你的 Token

### 3. 配置 .env
```bash
# AI 提供商配置
AI_PROVIDER=modelscope
AI_API_KEY=ms-xxxxxxxxxxxxxxxxxxxxxx  # 你的 ModelScope Token
AI_MODEL=ZhipuAI/GLM-4.6              # 可选，默认为 ZhipuAI/GLM-4.6
```

### 4. 运行
```bash
cd trading-ai
python main.py
```

---

## ⚙️ 配置说明

### 必需配置
| 配置项 | 说明 | 示例 |
|--------|------|------|
| `AI_PROVIDER` | 提供商名称 | `modelscope` |
| `AI_API_KEY` | ModelScope Token | `ms-727ef905-...` |

### 可选配置
| 配置项 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `AI_MODEL` | 模型 ID | `ZhipuAI/GLM-4.6` | `Qwen/Qwen2.5-72B-Instruct` |

### API 地址
ModelScope 使用固定的 API 地址，无需配置：
- **Base URL**: `https://api-inference.modelscope.cn/v1`

---

## 🤖 支持的模型

ModelScope 支持众多开源模型，以下是一些推荐的模型：

### 中文对话模型
| 模型 ID | 说明 | 上下文长度 |
|---------|------|-----------|
| `ZhipuAI/GLM-4.6` | 智谱 GLM-4.6（默认） | 128K |
| `Qwen/Qwen2.5-72B-Instruct` | 阿里通义千问 2.5 | 32K |
| `THUDM/chatglm3-6b` | 清华 ChatGLM3 | 8K |

### 其他模型
更多模型请访问 [ModelScope 模型库](https://www.modelscope.cn/models)

---

## 📝 使用示例

### 示例 1：基础使用
```python
from tradingai.ai import AIProviderFactory

# 创建提供商
provider = AIProviderFactory.create(
    provider_name="modelscope",
    api_key="ms-xxxxxxxxxxxxxxxxxxxxxx"
)

# 发送对话
messages = [
    {"role": "system", "content": "你是一个专业的加密货币分析师。"},
    {"role": "user", "content": "分析一下比特币的趋势"}
]

response = await provider.chat(messages)
print(response)
```

### 示例 2：指定模型
```python
# 使用通义千问模型
provider = AIProviderFactory.create(
    provider_name="modelscope",
    api_key="ms-xxxxxxxxxxxxxxxxxxxxxx",
    model="Qwen/Qwen2.5-72B-Instruct"
)
```

### 示例 3：从配置创建
```python
# 从 .env 自动加载配置
provider = AIProviderFactory.create_from_config()
```

### 示例 4：市场分析
```python
from tradingai.ai.analyzers import MarketAnalyzer

# 创建分析器
analyzer = MarketAnalyzer(provider)

# 分析市场
market_data = {
    "symbol": "BTCUSDT",
    "price": 95000,
    "indicators": {...}
}

analysis = await analyzer.analyze(market_data)
print(f"建议: {analysis['action']}")
print(f"置信度: {analysis['confidence']}")
```

---

## 🧪 测试

运行 ModelScope 提供商测试：
```bash
cd trading-ai
python examples/modelscope_example.py
```

测试包括：
1. ✅ 基础对话测试
2. ✅ 市场分析测试
3. ✅ 从配置创建测试

---

## ❓ 常见问题

### Q1: 如何获取 ModelScope Token？
**A**: 访问 [ModelScope Token 管理页面](https://www.modelscope.cn/my/myaccesstoken)，登录后创建新 Token。

### Q2: 支持流式响应吗？
**A**: 当前版本使用非流式模式（`stream=False`）。后续版本可能会支持流式响应。

### Q3: 调用 API 失败怎么办？
**A**: 请检查：
1. Token 是否正确
2. 网络连接是否正常
3. 模型 ID 是否存在
4. 查看日志文件获取详细错误信息

### Q4: 如何切换不同的模型？
**A**: 在 `.env` 中修改 `AI_MODEL` 参数，或在代码中通过 `model` 参数指定：
```python
provider = AIProviderFactory.create(
    provider_name="modelscope",
    api_key="your_token",
    model="Qwen/Qwen2.5-72B-Instruct"
)
```

### Q5: ModelScope 和 DeepSeek 有什么区别？
**A**: 
- **ModelScope**: 模型聚合平台，可以使用多种开源模型，免费额度较高
- **DeepSeek**: 专注于自研模型，推理速度快，价格便宜

根据需求选择：
- 需要尝试多种模型 → ModelScope
- 追求性能和稳定性 → DeepSeek

### Q6: API 有速率限制吗？
**A**: ModelScope 对免费用户有一定的调用频率和额度限制。具体限制请查看 [ModelScope 官方文档](https://www.modelscope.cn/docs)。

---

## 🔗 相关链接

- [ModelScope 官网](https://www.modelscope.cn/)
- [ModelScope API 文档](https://www.modelscope.cn/docs)
- [模型库](https://www.modelscope.cn/models)
- [OpenAI SDK 文档](https://github.com/openai/openai-python)

---

## 📞 技术支持

遇到问题？
1. 查看日志文件：`logs/tradingai_*.log`
2. 查看 [常见问题](#常见问题)
3. 提交 Issue

---

**祝交易愉快！** 🚀

