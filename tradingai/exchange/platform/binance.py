"""
币安交易平台
"""
from typing import List, Dict, Optional
from .base import BasePlatform
from ..client.binance import BinanceClient
from ...logger import get_logger
from ... import config

logger = get_logger("exchange.platform.binance")


class BinancePlatform(BasePlatform):
    """币安交易平台"""
    
    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = None):
        self.api_key = api_key
        self.api_secret = api_secret
        # 如果没有显式指定testnet，从config中读取
        if testnet is None:
            self.testnet = config.TESTNET
        else:
            self.testnet = testnet
        self.client: Optional[BinanceClient] = None
    
    async def connect(self):
        """连接币安"""
        self.client = BinanceClient(self.api_key, self.api_secret, self.testnet)
        await self.client.__aenter__()
        
        proxy_info = f" (代理: {self.client.proxy})" if self.client.proxy else ""
        network_name = '币安测试网' if self.testnet else '币安主网'
        logger.info(f"✅ 已连接到 {network_name}{proxy_info}")
        logger.debug(f"   网络环境: {config.TRADING_ENVIRONMENT}")
        logger.debug(f"   API端点: {self.client.base_url}")
    
    async def disconnect(self):
        """断开连接"""
        if self.client:
            await self.client.__aexit__(None, None, None)
            logger.info("✅ 已断开连接")
    
    async def get_symbols(self) -> List[str]:
        """获取交易对"""
        if not self.client:
            raise RuntimeError("未连接到交易所")
        return await self.client.get_symbols()
    
    async def get_klines(self, symbol: str, interval: str, limit: int, include_current: bool = False) -> List[Dict]:
        """获取K线"""
        if not self.client:
            raise RuntimeError("未连接到交易所")
        return await self.client.get_klines(symbol, interval, limit, include_current)
    
    async def get_balance(self) -> float:
        """获取余额"""
        if not self.client:
            raise RuntimeError("未连接到交易所")
        balance = await self.client.get_balance()
        return balance if balance else 0.0
    
    async def place_order(self, symbol: str, side: str, quantity: float, price: float = None) -> Optional[Dict]:
        """下单"""
        if not self.client:
            raise RuntimeError("未连接到交易所")
        return await self.client.place_order(symbol, side, quantity, price)
    
    async def get_ticker_24h(self, symbol: str) -> Optional[Dict]:
        """获取单个交易对的24小时行情"""
        if not self.client:
            raise RuntimeError("未连接到交易所")
        # Client 已经返回统一格式，直接透传
        return await self.client.get_ticker_24h(symbol)
    
    async def get_all_tickers_24h(self) -> List[Dict]:
        """获取所有交易对的24小时行情"""
        if not self.client:
            raise RuntimeError("未连接到交易所")
        # Client 已经返回统一格式，直接透传
        return await self.client.get_all_tickers_24h()
    
    async def get_closed_trades(
        self,
        symbol: Optional[str] = None,
        limit: int = 50,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Dict]:
        """获取已平仓的交易历史"""
        if not self.client:
            raise RuntimeError("未连接到交易所")
        return await self.client.get_closed_trades(symbol, limit, start_time, end_time)
    
    # ==================== 交易相关接口实现 ====================
    
    async def set_leverage(self, symbol: str, leverage: int) -> Dict:
        """设置杠杆倍数"""
        if not self.client:
            raise RuntimeError("未连接到交易所")
        return await self.client.set_leverage(symbol, leverage)
    
    async def set_margin_type(self, symbol: str, margin_type: str = "ISOLATED") -> Dict:
        """设置保证金模式"""
        if not self.client:
            raise RuntimeError("未连接到交易所")
        return await self.client.set_margin_type(symbol, margin_type)
    
    async def place_futures_order(
        self,
        symbol: str,
        side: str,
        position_side: str,
        quantity: float,
        price: float = None,
        order_type: str = "MARKET",
        stop_price: float = None,
        close_position: bool = False
    ) -> Dict:
        """期货下单（支持止损止盈）"""
        if not self.client:
            raise RuntimeError("未连接到交易所")
        return await self.client.place_futures_order(
            symbol, side, position_side, quantity, price,
            order_type, stop_price, close_position
        )
    
    async def get_position(self, symbol: str = None) -> List[Dict]:
        """查询持仓"""
        if not self.client:
            raise RuntimeError("未连接到交易所")
        return await self.client.get_position(symbol)
    
    async def cancel_order(self, symbol: str, order_id: int = None) -> Dict:
        """撤销订单"""
        if not self.client:
            raise RuntimeError("未连接到交易所")
        return await self.client.cancel_order(symbol, order_id)
    
    async def cancel_all_orders(self, symbol: str) -> Dict:
        """撤销指定交易对的所有订单"""
        if not self.client:
            raise RuntimeError("未连接到交易所")
        return await self.client.cancel_all_orders(symbol)

