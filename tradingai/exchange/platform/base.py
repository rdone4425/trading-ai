"""
交易平台基类
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BasePlatform(ABC):
    """交易平台基类"""
    
    @abstractmethod
    async def connect(self):
        """连接交易所"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    async def get_symbols(self) -> List[str]:
        """获取交易对"""
        pass
    
    @abstractmethod
    async def get_klines(self, symbol: str, interval: str, limit: int, include_current: bool = False) -> List[Dict]:
        """
        获取K线
        
        Args:
            symbol: 交易对
            interval: K线周期
            limit: K线数量
            include_current: 是否包含当前进行中的K线（False=仅已完成，True=包含进行中）
        
        Returns:
            K线数据列表
        """
        pass
    
    @abstractmethod
    async def get_balance(self) -> float:
        """获取余额"""
        pass
    
    @abstractmethod
    async def place_order(self, symbol: str, side: str, quantity: float, price: float = None) -> Optional[Dict]:
        """下单"""
        pass
    
    @abstractmethod
    async def get_ticker_24h(self, symbol: str) -> Optional[Dict]:
        """
        获取单个交易对的24小时行情
        
        Args:
            symbol: 交易对
        
        Returns:
            24小时行情数据
        """
        pass
    
    @abstractmethod
    async def get_all_tickers_24h(self) -> List[Dict]:
        """
        获取所有交易对的24小时行情
        
        Returns:
            所有交易对的24小时行情列表
        """
        pass
    
    @abstractmethod
    async def get_closed_trades(
        self,
        symbol: Optional[str] = None,
        limit: int = 50,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Dict]:
        """
        获取已平仓的交易历史（默认最近1天）
        
        Args:
            symbol: 交易对（None 表示所有交易对）
            limit: 返回数量限制（最大1000）
            start_time: 开始时间（毫秒时间戳，None则使用默认最近1天）
            end_time: 结束时间（毫秒时间戳，None则使用当前时间）
        
        Returns:
            已平仓交易列表，每个交易包含：
            {
                "symbol": "交易对",
                "direction": "做多/做空",
                "trade_time": "交易时间",
                "duration": "持仓时长",
                "entry_price": 入场价格,
                "exit_price": 出场价格,
                "stop_loss": 止损价格,
                "take_profit": 止盈价格,
                "profit_loss": 盈亏金额,
                "profit_loss_percentage": 盈亏比例,
                "risk_reward_ratio": 风险回报比,
                "quantity": 数量,
                "fee": 手续费,
                ...
            }
        
        Note:
            - 如果不指定 start_time 和 end_time，默认获取最近1天的交易
        """
        pass
    
    # ==================== 交易相关接口（期货合约） ====================
    
    @abstractmethod
    async def set_leverage(self, symbol: str, leverage: int) -> Dict:
        """
        设置杠杆倍数
        
        Args:
            symbol: 交易对
            leverage: 杠杆倍数（1-125）
        
        Returns:
            设置结果
        """
        pass
    
    @abstractmethod
    async def set_margin_type(self, symbol: str, margin_type: str = "ISOLATED") -> Dict:
        """
        设置保证金模式
        
        Args:
            symbol: 交易对
            margin_type: 保证金类型（ISOLATED=逐仓, CROSSED=全仓）
        
        Returns:
            设置结果
        """
        pass
    
    @abstractmethod
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
        """
        期货下单（支持止损止盈）
        
        Args:
            symbol: 交易对
            side: 方向（BUY/SELL）
            position_side: 持仓方向（LONG/SHORT）
            quantity: 数量
            price: 限价（限价单必填）
            order_type: 订单类型（MARKET/LIMIT/STOP/TAKE_PROFIT/STOP_MARKET/TAKE_PROFIT_MARKET）
            stop_price: 触发价格（止损止盈订单必填）
            close_position: 是否平仓（true时忽略quantity）
        
        Returns:
            订单信息
        """
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str = None) -> List[Dict]:
        """
        查询持仓
        
        Args:
            symbol: 交易对（None表示查询所有持仓）
        
        Returns:
            持仓列表
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, symbol: str, order_id: int = None) -> Dict:
        """
        撤销订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID（None表示撤销该交易对的所有订单）
        
        Returns:
            撤销结果
        """
        pass
    
    @abstractmethod
    async def cancel_all_orders(self, symbol: str) -> Dict:
        """
        撤销指定交易对的所有订单
        
        Args:
            symbol: 交易对
        
        Returns:
            撤销结果
        """
        pass

