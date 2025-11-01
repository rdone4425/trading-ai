"""
代理工厂 - 简单实用
"""
from typing import Optional
from .. import config
from ..logger import get_logger

logger = get_logger("proxy")


class ProxyFactory:
    """代理工厂"""
    
    @staticmethod
    def create_from_config() -> Optional[str]:
        """
        从配置创建代理URL
        
        Returns:
            代理URL字符串，如 "http://127.0.0.1:7890" 或 None（不使用代理）
        """
        # 检查是否启用代理
        if not config.USE_PROXY:
            logger.debug("未启用代理")
            return None
        
        # 构建代理URL
        proxy_url = f"http://{config.PROXY_HOST}:{config.PROXY_PORT}"
        
        logger.info(f"✅ 使用代理: {config.PROXY_HOST}:{config.PROXY_PORT}")
        return proxy_url
    
    @staticmethod
    def create(host: str, port: int) -> str:
        """
        手动创建代理URL
        
        Args:
            host: 代理主机
            port: 代理端口
        
        Returns:
            代理URL字符串
        """
        proxy_url = f"http://{host}:{port}"
        logger.info(f"创建代理: {host}:{port}")
        return proxy_url
