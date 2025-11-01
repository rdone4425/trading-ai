"""
AI 提供商基类 - 只负责与 AI API 通信
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class BaseAIProvider(ABC):
    """
    AI 提供商基类
    
    职责：只负责与 AI API 的通信，不包含具体的业务逻辑
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        初始化 AI 提供商
        
        Args:
            api_key: API 密钥
            **kwargs: 其他配置参数（model, base_url 等）
        """
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        发送对话请求
        
        Args:
            messages: 消息列表 [{"role": "system/user/assistant", "content": "..."}]
            model: 模型名称
            temperature: 温度参数（0-1），控制随机性
            max_tokens: 最大token数
            **kwargs: 其他参数
        
        Returns:
            AI 响应内容
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        获取提供商名称
        
        Returns:
            提供商名称
        """
        pass
    
    async def close(self):
        """关闭连接（如果需要）"""
        pass

