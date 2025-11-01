"""
ModelScope AI 提供商

使用 OpenAI SDK 与 ModelScope API 通信
需要安装: pip install openai
"""
from typing import Dict, List, Optional
from ..base import BaseAIProvider
from ...logger import get_logger

logger = get_logger("ai.modelscope")


class ModelScopeProvider(BaseAIProvider):
    """
    ModelScope AI 提供商
    
    ModelScope 使用 OpenAI 兼容的 API
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        初始化 ModelScope 提供商
        
        Args:
            api_key: ModelScope Token
            **kwargs: 其他配置
                - model: 模型 ID（默认: ZhipuAI/GLM-4.6）
        """
        super().__init__(api_key, **kwargs)
        
        # 导入 OpenAI SDK
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "需要安装 OpenAI SDK 才能使用 ModelScope: pip install openai"
            )
        
        # 配置
        self.model = kwargs.get("model", "ZhipuAI/GLM-4.6")
        self.base_url = "https://api-inference.modelscope.cn/v1"  # 固定的 API 地址
        
        # 创建客户端
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.base_url
        )
        
        logger.info(f"初始化 ModelScope 提供商 (模型: {self.model}, URL: {self.base_url})")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        发送对话请求到 ModelScope
        
        Args:
            messages: 消息列表
            model: 模型 ID（可选，默认使用初始化时的模型）
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
        
        Returns:
            AI 响应内容
        """
        model = model or self.model
        
        try:
            logger.debug(f"调用 ModelScope API (model={model}, messages={len(messages)})")
            
            # 构建请求参数
            request_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": False,
            }
            
            # 添加 max_tokens（如果提供）
            if max_tokens:
                request_params["max_tokens"] = max_tokens
            
            # 添加其他参数
            for key in ["top_p", "frequency_penalty", "presence_penalty"]:
                if key in kwargs:
                    request_params[key] = kwargs[key]
            
            # 调用 API
            response = self.client.chat.completions.create(**request_params)
            
            # 提取响应内容
            content = response.choices[0].message.content
            
            logger.debug(f"ModelScope 响应: {len(content)} 字符")
            return content
        
        except Exception as e:
            logger.error(f"ModelScope API 调用失败: {e}")
            raise
    
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return f"ModelScope ({self.model})"
    
    async def close(self):
        """关闭连接"""
        if hasattr(self.client, 'close'):
            self.client.close()
        logger.debug("ModelScope 客户端已关闭")

