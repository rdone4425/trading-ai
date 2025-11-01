"""
币安客户端
"""
import aiohttp
import hmac
import hashlib
import time
from typing import List, Dict, Optional
from datetime import datetime
from ...proxy import ProxyFactory


class BinanceClient:
    """币安期货 API 客户端"""
    
    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # 直接在这里获取代理
        self.proxy = ProxyFactory.create_from_config()
        
        self.base_url = (
            "https://testnet.binancefuture.com" 
            if testnet else "https://fapi.binance.com"
        )
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _sign(self, query_string: str) -> str:
        """生成签名"""
        return hmac.new(
            self.api_secret.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()
    
    async def _request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """发送请求"""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        params = params or {}
        headers = {"X-MBX-APIKEY": self.api_key}
        url = f"{self.base_url}{endpoint}"
        
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            params["signature"] = self._sign(query_string)
        
        try:
            async with self.session.request(method, url, params=params, headers=headers, proxy=self.proxy) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    raise Exception(f"API Error {resp.status}: {error}")
                return await resp.json()
        except aiohttp.ClientError as e:
            raise Exception(f"网络错误: {e}")
    
    async def get_symbols(self, limit: int = 50) -> List[str]:
        """获取交易对列表"""
        data = await self._request("GET", "/fapi/v1/exchangeInfo")
        symbols = []
        for item in data.get("symbols", []):
            if (item["symbol"].endswith("USDT") and 
                item["status"] == "TRADING" and
                item.get("contractType") == "PERPETUAL"):
                symbols.append(item["symbol"])
        return symbols[:limit]
    
    async def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100, include_current: bool = False) -> List[Dict]:
        """获取K线数据"""
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        
        data = await self._request("GET", "/fapi/v1/klines", params)
        
        klines = []
        current_time = int(time.time() * 1000)
        
        for i, k in enumerate(data):
            close_time = int(k[6])  # 收盘时间
            # 判断K线是否完成：收盘时间 < 当前时间
            is_closed = close_time < current_time
            
            klines.append({
                "timestamp": datetime.fromtimestamp(k[0] / 1000),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[7]),
                "is_closed": is_closed
            })
        
        # 如果不需要当前K线，只返回已完成的
        if not include_current and klines:
            # 通常最后一根是当前K线，保留已完成的K线
            klines = [k for k in klines if k['is_closed']]
        
        return klines
    
    async def get_balance(self) -> Optional[float]:
        """获取账户余额"""
        data = await self._request("GET", "/fapi/v2/account", {}, signed=True)
        return float(data.get("availableBalance", 0))
    
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
            symbol: 交易对（None 表示所有交易对，但API需要指定）
            limit: 返回数量限制（最大1000）
            start_time: 开始时间（毫秒时间戳，None则使用默认最近1天）
            end_time: 结束时间（毫秒时间戳，None则使用当前时间）
        
        Returns:
            已完成的交易列表
        
        Note:
            - 如果不指定 start_time 和 end_time，默认获取最近1天的交易
        """
        params = {}
        
        if symbol:
            params["symbol"] = symbol
        
        if limit:
            params["limit"] = min(limit, 1000)  # Binance最大1000
        
        if start_time:
            params["startTime"] = start_time
        
        if end_time:
            params["endTime"] = end_time
        
        # 如果没有指定时间范围，默认最近1天
        if not start_time and not end_time:
            current_time = int(time.time() * 1000)
            one_day_ago = current_time - (24 * 60 * 60 * 1000)  # 24小时前
            params["startTime"] = one_day_ago
            params["endTime"] = current_time
        
        # 获取账户交易历史（已完成的订单对应的交易）
        # 使用 /fapi/v2/account/trades 获取账户交易历史
        try:
            trades = await self._request("GET", "/fapi/v2/account/trades", params, signed=True)
            
            # 转换为标准格式
            closed_trades = []
            for trade in trades:
                # Binance返回格式：{
                #   "symbol": "BTCUSDT",
                #   "id": 12345,
                #   "orderId": 67890,
                #   "price": "95000.00",
                #   "qty": "0.01",
                #   "quoteQty": "950.00",
                #   "commission": "0.95",
                #   "commissionAsset": "USDT",
                #   "time": 1699000000000,
                #   "isBuyer": true,
                #   "isMaker": false,
                #   "positionSide": "LONG"
                # }
                
                # 需要将买入和卖出配对，计算出完整的交易
                closed_trades.append({
                    "symbol": trade.get("symbol", ""),
                    "trade_id": trade.get("id", 0),
                    "order_id": trade.get("orderId", 0),
                    "price": float(trade.get("price", 0)),
                    "quantity": float(trade.get("qty", 0)),
                    "quote_quantity": float(trade.get("quoteQty", 0)),
                    "fee": float(trade.get("commission", 0)),
                    "fee_asset": trade.get("commissionAsset", ""),
                    "timestamp": int(trade.get("time", 0)),
                    "is_buyer": trade.get("isBuyer", False),
                    "is_maker": trade.get("isMaker", False),
                    "position_side": trade.get("positionSide", "BOTH"),
                    "raw_data": trade  # 保留原始数据
                })
            
            # 按时间排序（最新的在前）
            closed_trades.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return closed_trades[:limit]
            
        except Exception as e:
            # 静默失败，返回空列表（可能是API权限问题或没有交易历史）
            # 不打印错误信息，直接跳过
            return []
    
    async def place_order(self, symbol: str, side: str, quantity: float, price: float = None) -> Optional[Dict]:
        """下单"""
        params = {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT" if price else "MARKET",
            "quantity": quantity
        }
        
        if price:
            params["price"] = price
            params["timeInForce"] = "GTC"
        
        data = await self._request("POST", "/fapi/v1/order", params, signed=True)
        
        return {
            "order_id": data["orderId"],
            "symbol": data["symbol"],
            "side": data["side"],
            "quantity": float(data["origQty"]),
            "price": float(data.get("price", 0)),
            "status": data["status"]
        }
    
    async def get_ticker_24h(self, symbol: str) -> Optional[Dict]:
        """获取24小时行情（统一格式）"""
        data = await self._request("GET", "/fapi/v1/ticker/24hr", {"symbol": symbol})
        
        # 统一格式
        return {
            "symbol": data["symbol"],
            "price": float(data["lastPrice"]),
            "price_change": float(data["priceChange"]),
            "price_change_percent": float(data["priceChangePercent"]),
            "volume": float(data["volume"]),
            "quote_volume": float(data["quoteVolume"]),
            "high": float(data["highPrice"]),
            "low": float(data["lowPrice"]),
            "open": float(data["openPrice"]),
            "close": float(data["lastPrice"]),
            "count": int(data["count"])
        }
    
    async def get_all_tickers_24h(self) -> List[Dict]:
        """获取所有交易对24小时行情（统一格式）"""
        data = await self._request("GET", "/fapi/v1/ticker/24hr")
        
        # 只要USDT合约，并统一格式
        tickers = []
        for item in data:
            if item["symbol"].endswith("USDT"):
                tickers.append({
                    "symbol": item["symbol"],
                    "price": float(item["lastPrice"]),
                    "price_change": float(item["priceChange"]),
                    "price_change_percent": float(item["priceChangePercent"]),
                    "volume": float(item["volume"]),
                    "quote_volume": float(item["quoteVolume"]),
                    "high": float(item["highPrice"]),
                    "low": float(item["lowPrice"]),
                    "open": float(item["openPrice"]),
                    "close": float(item["lastPrice"]),
                    "count": int(item["count"])
                })
        
        return tickers
    
    async def set_leverage(self, symbol: str, leverage: int) -> Dict:
        """
        设置杠杆倍数
        
        Args:
            symbol: 交易对
            leverage: 杠杆倍数（1-125）
        
        Returns:
            设置结果
        """
        params = {
            "symbol": symbol,
            "leverage": leverage
        }
        
        data = await self._request("POST", "/fapi/v1/leverage", params, signed=True)
        return data
    
    async def set_margin_type(self, symbol: str, margin_type: str = "ISOLATED") -> Dict:
        """
        设置保证金模式
        
        Args:
            symbol: 交易对
            margin_type: 保证金类型（ISOLATED=逐仓, CROSSED=全仓）
        
        Returns:
            设置结果
        """
        params = {
            "symbol": symbol,
            "marginType": margin_type
        }
        
        data = await self._request("POST", "/fapi/v1/marginType", params, signed=True)
        return data
    
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
        params = {
            "symbol": symbol,
            "side": side,
            "positionSide": position_side,
            "type": order_type
        }
        
        if close_position:
            params["closePosition"] = "true"
        else:
            params["quantity"] = quantity
        
        if order_type in ["LIMIT", "STOP", "TAKE_PROFIT"]:
            if not price:
                raise ValueError(f"限价订单必须指定价格")
            params["price"] = price
            params["timeInForce"] = "GTC"
        
        if order_type in ["STOP", "TAKE_PROFIT", "STOP_MARKET", "TAKE_PROFIT_MARKET"]:
            if not stop_price:
                raise ValueError(f"止损止盈订单必须指定触发价格")
            params["stopPrice"] = stop_price
        
        data = await self._request("POST", "/fapi/v1/order", params, signed=True)
        
        return {
            "order_id": data["orderId"],
            "symbol": data["symbol"],
            "side": data["side"],
            "position_side": data.get("positionSide", position_side),
            "order_type": data["type"],
            "quantity": float(data.get("origQty", 0)),
            "price": float(data.get("price", 0)),
            "stop_price": float(data.get("stopPrice", 0)),
            "status": data["status"],
            "executed_qty": float(data.get("executedQty", 0)),
            "cumulative_quote_qty": float(data.get("cumulativeQuoteQty", 0))
        }
    
    async def get_position(self, symbol: str = None) -> List[Dict]:
        """
        查询持仓
        
        Args:
            symbol: 交易对（None表示查询所有持仓）
        
        Returns:
            持仓列表
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        
        data = await self._request("GET", "/fapi/v2/positionRisk", params, signed=True)
        
        positions = []
        for item in data:
            position_amt = float(item["positionAmt"])
            if position_amt != 0:  # 只返回有持仓的
                positions.append({
                    "symbol": item["symbol"],
                    "position_side": item["positionSide"],  # LONG/SHORT/BOTH
                    "position_amt": position_amt,
                    "entry_price": float(item["entryPrice"]),
                    "unrealized_pnl": float(item["unRealizedProfit"]),
                    "leverage": int(item["leverage"]),
                    "margin_type": item["marginType"],  # isolated/crossed
                    "isolated_margin": float(item.get("isolatedMargin", 0)),
                    "liquidation_price": float(item.get("liquidationPrice", 0)),
                    "mark_price": float(item.get("markPrice", 0)),
                    "percentage": float(item.get("percentage", 0))
                })
        
        return positions
    
    async def cancel_order(self, symbol: str, order_id: int = None) -> Dict:
        """
        撤销订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID（None表示撤销该交易对的所有订单）
        
        Returns:
            撤销结果
        """
        params = {"symbol": symbol}
        if order_id:
            params["orderId"] = order_id
        
        data = await self._request("DELETE", "/fapi/v1/order", params, signed=True)
        return data
    
    async def cancel_all_orders(self, symbol: str) -> Dict:
        """
        撤销指定交易对的所有订单
        
        Args:
            symbol: 交易对
        
        Returns:
            撤销结果
        """
        params = {"symbol": symbol}
        data = await self._request("DELETE", "/fapi/v1/allOpenOrders", params, signed=True)
        return data

