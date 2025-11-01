"""
AI 提供商工厂
"""
from typing import Optional
from .base import BaseAIProvider
from ..logger import get_logger

logger = get_logger("ai.factory")


class AIProviderFactory:
    """AI 提供商工厂"""
    
    # 支持的提供商
    PROVIDERS = {
        "deepseek": "tradingai.ai.providers.deepseek_provider.DeepSeekProvider",
        "modelscope": "tradingai.ai.providers.modelscope_provider.ModelScopeProvider",
        "openai": "tradingai.ai.providers.openai_provider.OpenAIProvider",
        "claude": "tradingai.ai.providers.claude_provider.ClaudeProvider",
        "gemini": "tradingai.ai.providers.gemini_provider.GeminiProvider",
        "local": "tradingai.ai.providers.local_provider.LocalProvider",
        "mock": "tradingai.ai.providers.mock_provider.MockProvider",
    }
    
    @classmethod
    def create(
        cls,
        provider_name: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> BaseAIProvider:
        """
        创建 AI 提供商实例
        
        Args:
            provider_name: 提供商名称（openai/claude/gemini/local/mock）
            api_key: API 密钥
            **kwargs: 其他配置参数
        
        Returns:
            AI 提供商实例
        
        Raises:
            ValueError: 不支持的提供商
        
        Example:
            # 使用 OpenAI
            provider = AIProviderFactory.create("openai", api_key="sk-xxx")
            
            # 使用 Mock（测试用）
            provider = AIProviderFactory.create("mock")
        """
        provider_name = provider_name.lower()
        
        if provider_name not in cls.PROVIDERS:
            raise ValueError(
                f"不支持的 AI 提供商: {provider_name}。"
                f"支持的提供商: {', '.join(cls.PROVIDERS.keys())}"
            )
        
        # 动态导入提供商类
        provider_path = cls.PROVIDERS[provider_name]
        module_path, class_name = provider_path.rsplit(".", 1)
        
        try:
            module = __import__(module_path, fromlist=[class_name])
            provider_class = getattr(module, class_name)
            
            # 创建实例
            provider = provider_class(api_key=api_key, **kwargs)
            
            logger.info(f"✅ 创建 AI 提供商: {provider.get_provider_name()}")
            return provider
        
        except ImportError as e:
            logger.error(f"导入 AI 提供商失败: {provider_name} - {e}")
            raise
        except Exception as e:
            logger.error(f"创建 AI 提供商失败: {provider_name} - {e}")
            raise
    
    @classmethod
    def create_from_config(cls) -> BaseAIProvider:
        """
        从配置创建 AI 提供商
        
        Returns:
            AI 提供商实例
        
        Example:
            # 从 .env 配置创建
            provider = AIProviderFactory.create_from_config()
        """
        from .. import config
        
        provider_name = config.AI_PROVIDER
        api_key = config.AI_API_KEY
        model = config.AI_MODEL
        
        # 清理配置值（移除注释和空白）
        def clean_value(value: str) -> str:
            """清理配置值，移除注释"""
            if not value:
                return ""
            # 移除行内注释
            if "#" in value:
                value = value.split("#")[0]
            return value.strip()
        
        provider_name = clean_value(provider_name) or "mock"
        api_key = clean_value(api_key)
        model = clean_value(model)
        
        # 构建配置参数
        kwargs = {}
        if model:
            kwargs["model"] = model
        
        logger.info(f"从配置创建 AI 提供商: {provider_name}")
        return cls.create(provider_name, api_key=api_key, **kwargs)
    
    @classmethod
    def list_providers(cls) -> list:
        """
        列出所有支持的提供商
        
        Returns:
            提供商列表
        """
        return list(cls.PROVIDERS.keys())

