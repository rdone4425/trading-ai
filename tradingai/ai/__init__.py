"""
AI 分析模块

结构：
- base.py & factory.py  - 基类和工厂
- providers/            - 具体提供商实现（通信层）
- analyzers/            - 分析器（业务层）
- prompts/              - 提示词（模板层）
"""
from .base import BaseAIProvider
from .factory import AIProviderFactory
from .analyzers import MarketAnalyzer

__all__ = [
    "BaseAIProvider",
    "AIProviderFactory",
    "MarketAnalyzer",
]

