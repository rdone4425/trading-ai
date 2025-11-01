"""
市场数据获取器 - 获取24小时行情数据
"""
from typing import List, Dict
from ..exchange.platform.base import BasePlatform
from ..logger import get_logger

logger = get_logger("scanner.market_data")


class MarketDataFetcher:
    """市场数据获取器"""
    
    def __init__(self, platform: BasePlatform):
        self.platform = platform
    
    async def fetch_24h_tickers(self, symbols: List[str]) -> List[Dict]:
        """
        获取24小时行情数据
        
        Args:
            symbols: 交易对列表
        
        Returns:
            行情数据列表
        """
        logger.info(f"获取 {len(symbols)} 个交易对的24小时行情...")
        
        tickers = []
        
        for i, symbol in enumerate(symbols, 1):
            try:
                ticker = await self._fetch_ticker_24h(symbol)
                if ticker:
                    tickers.append(ticker)
                
                # 进度提示
                if i % 10 == 0:
                    logger.info(f"进度: {i}/{len(symbols)}")
            
            except Exception as e:
                logger.debug(f"获取 {symbol} 行情失败: {e}")
                continue
        
        logger.info(f"✅ 成功获取 {len(tickers)} 个交易对的行情")
        return tickers
    
    async def _fetch_ticker_24h(self, symbol: str) -> Dict:
        """
        获取单个交易对的24小时行情
        
        Args:
            symbol: 交易对
        
        Returns:
            行情数据（统一格式）
        """
        # 直接调用平台接口（已经是统一格式）
        return await self.platform.get_ticker_24h(symbol)
    
    async def fetch_all_tickers_24h(self) -> List[Dict]:
        """
        获取所有交易对的24小时行情（一次性获取，更快）
        
        Returns:
            行情数据列表（统一格式）
        """
        logger.info("获取所有交易对的24小时行情...")
        
        # 直接调用平台接口（已经是统一格式）
        tickers = await self.platform.get_all_tickers_24h()
        
        logger.info(f"✅ 获取到 {len(tickers)} 个交易对的行情")
        return tickers

