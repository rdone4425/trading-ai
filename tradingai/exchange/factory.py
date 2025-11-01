"""
平台工厂
"""
from .platform.base import BasePlatform
from .platform.binance import BinancePlatform
from .. import config


class PlatformFactory:
    """交易平台工厂"""
    
    @staticmethod
    def create(platform_name: str = "binance", **kwargs) -> BasePlatform:
        """
        创建交易平台
        
        Args:
            platform_name: 平台名称 (binance, okx等)
            **kwargs: 额外参数
        
        Returns:
            交易平台实例
        """
        if platform_name.lower() == "binance":
            return BinancePlatform(
                api_key=kwargs.get('api_key', config.BINANCE_API_KEY),
                api_secret=kwargs.get('api_secret', config.BINANCE_API_SECRET),
                testnet=kwargs.get('testnet', config.TESTNET)
            )
        else:
            raise ValueError(f"不支持的交易平台: {platform_name}")
    
    @staticmethod
    def create_from_config() -> BasePlatform:
        """从配置创建平台"""
        return PlatformFactory.create(
            platform_name=config.EXCHANGE_NAME,
            api_key=config.BINANCE_API_KEY,
            api_secret=config.BINANCE_API_SECRET,
            testnet=config.TESTNET
        )

