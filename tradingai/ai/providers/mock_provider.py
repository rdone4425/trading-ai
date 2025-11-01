"""
Mock AI 提供商 - 用于测试

只负责模拟与 AI API 的通信，不包含业务逻辑
"""
import random
from typing import Dict, List, Optional
from ..base import BaseAIProvider
from ...logger import get_logger

logger = get_logger("ai.mock")


class MockProvider(BaseAIProvider):
    """Mock AI 提供商（测试用）"""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key, **kwargs)
        logger.info("初始化 Mock AI 提供商（测试模式）")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        模拟对话
        
        Returns:
            模拟的响应
        """
        logger.debug(f"Mock Chat: {len(messages)} 条消息")
        
        # 从消息中提取用户内容
        user_content = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_content = msg.get("content", "")
                break
        
        # 根据内容返回不同的响应
        if "JSON" in user_content or "json" in user_content:
            # 如果请求 JSON 格式，返回 JSON
            return '''
{
    "signal": "buy",
    "confidence": 0.75,
    "reason": "Mock分析：技术指标显示上涨趋势",
    "target_price": 100.0,
    "stop_loss": 95.0
}
'''
        else:
            # 普通文本响应
            responses = [
                "基于当前技术指标分析，市场呈现震荡上行趋势。建议适当持仓观望。",
                "价格在关键支撑位获得支撑，建议关注突破信号后再决定进场时机。",
                "成交量放大，可能即将突破重要阻力位，可以考虑轻仓跟进。",
                "技术指标显示超买，建议谨慎追高，等待回调后再寻找机会。",
                "当前处于盘整阶段，等待方向选择，暂不建议重仓操作。",
            ]
            return random.choice(responses)
    
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return "Mock AI Provider"
