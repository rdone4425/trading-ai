"""
币安客户端
"""
import asyncio
import aiohttp
import hmac
import hashlib
import time
from typing import List, Dict, Optional
from datetime import datetime
from ...proxy import ProxyFactory
from ...logger import get_logger

logger = get_logger(__name__)


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
        
        # 时间偏移（用于校准本地时间与币安服务器时间）
        self.time_offset = 0  # 毫秒
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        # 初始化时验证API密钥
        await self._validate_api_key()
        # 初始化时获取服务器时间以校准时间偏移（必须在验证前或后都要做）
        await self._sync_server_time()
        logger.info(f"✅ 币安客户端初始化完成")
        logger.info(f"   网络: {'🧪 Testnet' if self.testnet else '🚀 Mainnet'}")
        logger.info(f"   时间偏移: {self.time_offset}ms")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _sync_server_time(self):
        """与币安服务器同步时间，解决时间戳不匹配问题"""
        try:
            url = f"{self.base_url}/fapi/v1/time"
            async with self.session.get(url, proxy=self.proxy, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    server_time = data.get("serverTime", 0)
                    local_time = int(time.time() * 1000)
                    self.time_offset = server_time - local_time
                    logger.debug(f"✅ 服务器时间同步完成: 偏移 {self.time_offset}ms")
                    return True
                else:
                    logger.warning(f"⚠️ 无法获取服务器时间: HTTP {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ 时间同步失败: {e}")
            return False
    
    def _sign(self, query_string: str) -> str:
        """生成签名"""
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def _request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """发送请求"""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        params = params or {}
        headers = {"X-MBX-APIKEY": self.api_key}
        url = f"{self.base_url}{endpoint}"
        
        if signed:
            # 使用经过校准的时间戳（关键！）
            current_timestamp = int(time.time() * 1000) + self.time_offset
            params["timestamp"] = current_timestamp
            
            # 添加recvWindow参数（给服务器处理请求的容差时间）
            # 默认5000ms（5秒）
            if "recvWindow" not in params:
                params["recvWindow"] = 5000
            
            # 重要：按照币安要求生成查询字符串
            # 1. 参数必须按字母顺序排序
            # 2. 参数值必须是字符串
            # 3. 使用&连接
            sorted_params = []
            for key in sorted(params.keys()):
                value = params[key]
                # 将所有值转换为字符串
                if isinstance(value, bool):
                    value_str = str(value).lower()
                else:
                    value_str = str(value)
                sorted_params.append(f"{key}={value_str}")
            
            query_string = "&".join(sorted_params)
            
            # 2. 生成HMAC-SHA256签名
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            params["signature"] = signature
            
            # 详细诊断日志
            logger.debug(f"📤 签名请求:")
            logger.debug(f"   端点: {method} {endpoint}")
            logger.debug(f"   时间戳: {current_timestamp} (本地时间+{self.time_offset}ms偏移)")
            logger.debug(f"   API密钥长度: {len(self.api_key)} 字符")
            logger.debug(f"   API密钥有效: {self.api_key is not None and len(self.api_key) > 0}")
            logger.debug(f"   参数: {len(params)-1}个 (不含signature)")
            if logger.isEnabledFor(10):  # DEBUG级别
                logger.debug(f"   查询字符串(签名前): {query_string[:150]}...")
                logger.debug(f"   生成的签名: {signature[:20]}...")
                # 验证参数中没有None值
                for k, v in params.items():
                    if v is None:
                        logger.warning(f"⚠️  参数 {k} 的值为 None!")
        
        try:
            # 使用params作为查询参数
            async with self.session.request(
                method, url, 
                params=params, 
                headers=headers, 
                proxy=self.proxy, 
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                response_text = await resp.text()
                
                if resp.status != 200:
                    error_msg = f"API Error {resp.status}: {response_text}"
                    logger.error(f"❌ {error_msg}")
                    
                    # 签名错误的特殊处理
                    if resp.status == 400 and "Signature" in response_text:
                        logger.warning(f"⚠️ 检测到签名错误")
                        logger.warning(f"   时间偏移: {self.time_offset}ms")
                        logger.warning(f"   当前时间戳: {params.get('timestamp', 'N/A')}")
                        logger.warning(f"   💡 建议: 检查API密钥和密钥是否匹配")
                        logger.warning(f"   💡 建议: 检查系统时间是否准确")
                        # 注意：不要在这里重新同步，因为初始化时已经同步过了
                        # 重新同步会导致每个请求都重新同步，效率很低
                    
                    raise Exception(error_msg)
                
                try:
                    return await resp.json()
                except Exception as e:
                    logger.error(f"❌ 响应JSON解析失败: {e}")
                    logger.debug(f"   原始响应: {response_text[:200]}")
                    raise Exception(f"无法解析API响应: {e}")
                    
        except asyncio.TimeoutError:
            raise Exception("请求超时 - API无响应")
        except aiohttp.ClientError as e:
            raise Exception(f"网络错误: {e}")
    
    async def get_symbols(self, limit: int = 0) -> List[str]:
        """
        获取永续合约交易对列表
        
        Args:
            limit: 返回数量限制，0表示不限制（返回所有符合条件的交易对）
        
        Returns:
            永续合约交易对列表（仅USDT计价，状态为TRADING）
        """
        data = await self._request("GET", "/fapi/v1/exchangeInfo")
        symbols = []
        for item in data.get("symbols", []):
            symbol = item.get("symbol", "")
            status = item.get("status", "")
            contract_type = item.get("contractType", "")
            
            # 严格筛选：必须是永续合约、TRADING状态、USDT计价
            if (symbol.endswith("USDT") and 
                status == "TRADING" and
                contract_type == "PERPETUAL"):
                symbols.append(symbol)
        
        # 如果limit > 0，则限制返回数量
        if limit > 0:
            return symbols[:limit]
        return symbols
    
    async def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100, include_current: bool = False, start_time: int = None, end_time: int = None) -> List[Dict]:
        """
        获取K线数据（支持批量获取超过1000根）
        
        Args:
            symbol: 交易对
            interval: K线周期
            limit: 需要获取的K线数量（如果>1000会自动分批获取）
            include_current: 是否包含当前进行中的K线
            start_time: 开始时间（毫秒时间戳，可选）
            end_time: 结束时间（毫秒时间戳，可选）
        
        Returns:
            K线数据列表（按时间正序排列）
        """
        # 币安API单次最多返回1000根K线
        MAX_PER_REQUEST = 1000
        
        all_klines = []
        remaining = limit
        current_end_time = end_time or int(time.time() * 1000)
        
        # 如果limit > 1000，需要分批获取
        while remaining > 0:
            # 本次请求的数量
            request_limit = min(remaining, MAX_PER_REQUEST)
            
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": request_limit
            }
            
            # 如果指定了结束时间，添加endTime参数
            if current_end_time:
                params["endTime"] = current_end_time
            
            try:
                data = await self._request("GET", "/fapi/v1/klines", params)
                
                if not data:
                    break
                
                current_time = int(time.time() * 1000)
                batch_klines = []
                
                for k in data:
                    close_time = int(k[6])  # 收盘时间
                    is_closed = close_time < current_time
                    
                    kline = {
                        "timestamp": datetime.fromtimestamp(k[0] / 1000),
                        "open": float(k[1]),
                        "high": float(k[2]),
                        "low": float(k[3]),
                        "close": float(k[4]),
                        "volume": float(k[7]),
                        "is_closed": is_closed
                    }
                    batch_klines.append(kline)
                
                # 将这批数据添加到总列表（逆序添加，因为API返回的是从新到旧）
                all_klines = batch_klines + all_klines
                
                # 如果返回的数据少于请求的数量，说明没有更多历史数据了
                if len(data) < request_limit:
                    break
                
                # 更新下一次请求的结束时间（使用最早的那根K线的开盘时间-1）
                if batch_klines:
                    earliest_timestamp = batch_klines[0]["timestamp"]
                    current_end_time = int(earliest_timestamp.timestamp() * 1000) - 1
                
                remaining -= len(data)
                
                # 避免过于频繁的请求
                if remaining > 0:
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"获取K线数据失败 {symbol}: {e}")
                break
        
        # 如果不需要当前K线，只返回已完成的
        if not include_current and all_klines:
            all_klines = [k for k in all_klines if k['is_closed']]
        
        # 限制返回数量
        return all_klines[:limit] if limit else all_klines
    
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
        """
        获取所有永续合约交易对的24小时行情（统一格式）
        
        注意：只返回永续合约（PERPETUAL），不包括季度合约等其他类型
        """
        # 先获取所有永续合约交易对列表
        perpetual_symbols = await self.get_symbols(limit=0)  # limit=0表示获取所有
        perpetual_set = set(perpetual_symbols)
        
        # 获取所有交易对24小时行情
        data = await self._request("GET", "/fapi/v1/ticker/24hr")
        
        # 只保留永续合约（USDT计价，且在perpetual_symbols列表中）
        tickers = []
        for item in data:
            symbol = item["symbol"]
            # 双重验证：既是USDT计价，又在永续合约列表中
            if symbol.endswith("USDT") and symbol in perpetual_set:
                tickers.append({
                    "symbol": symbol,
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

    async def _validate_api_key(self):
        """验证API密钥是否有效"""
        if not self.api_key or not self.api_secret:
            logger.error(f"❌ API密钥或密钥为空!")
            logger.error(f"   API密钥: {'✅ 已设置' if self.api_key else '❌ 未设置'}")
            logger.error(f"   API密钥: {'✅ 已设置' if self.api_secret else '❌ 未设置'}")
            logger.error(f"   请检查环境变量: BINANCE_API_KEY 和 BINANCE_API_SECRET")
            return
        
        # 检查长度
        if len(self.api_key) < 30:
            logger.error(f"❌ API密钥长度过短: {len(self.api_key)} 字符 (应该 > 30)")
            logger.error(f"   这可能不是真正的Binance API密钥")
            return
        
        if len(self.api_secret) < 30:
            logger.error(f"❌ API密钥长度过短: {len(self.api_secret)} 字符 (应该 > 30)")
            logger.error(f"   这可能不是真正的Binance API密钥")
            return
        
        logger.info(f"✅ API密钥格式检查通过")
        logger.info(f"   API密钥: {self.api_key[:8]}...{self.api_key[-8:]} ({len(self.api_key)} 字符)")
        logger.info(f"   API密钥: {self.api_secret[:8]}...{self.api_secret[-8:]} ({len(self.api_secret)} 字符)")
        logger.info(f"   网络环境: {'🧪 Testnet' if self.testnet else '🚀 Mainnet'}")
        
        # 尝试获取账户信息来验证密钥是否真正有效
        try:
            await self._validate_api_with_account_info()
        except Exception as e:
            logger.warning(f"⚠️ 无法验证API密钥: {e}")
    
    async def _validate_api_with_account_info(self):
        """通过获取账户信息来验证API密钥的有效性"""
        try:
            params = {
                "timestamp": int(time.time() * 1000) + self.time_offset
            }
            params["recvWindow"] = 5000
            
            sorted_params = []
            for key in sorted(params.keys()):
                value = params[key]
                if isinstance(value, bool):
                    value_str = str(value).lower()
                else:
                    value_str = str(value)
                sorted_params.append(f"{key}={value_str}")
            
            query_string = "&".join(sorted_params)
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            params["signature"] = signature
            
            headers = {"X-MBX-APIKEY": self.api_key}
            # 使用期货账户信息端点（支持两个网络）
            url = f"{self.base_url}/fapi/v1/account"
            
            logger.debug(f"🔍 验证API密钥...")
            logger.debug(f"   URL: {url}")
            logger.debug(f"   网络: {'Testnet' if self.testnet else 'Mainnet'}")
            
            async with self.session.get(url, params=params, headers=headers, proxy=self.proxy, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    logger.info(f"✅ API密钥验证成功！")
                elif resp.status == 401:
                    logger.error(f"❌ API认证失败（401）- API密钥或密钥无效")
                    logger.error(f"   检查: BINANCE_API_KEY 和 BINANCE_API_SECRET 是否正确")
                elif resp.status == 400:
                    text = await resp.text()
                    if "Signature" in text:
                        logger.error(f"❌ 签名验证失败 - 检查密钥是否匹配")
                    logger.error(f"   响应: {text[:200]}")
                elif resp.status == 404:
                    logger.error(f"❌ 端点不存在（404）")
                    logger.error(f"   可能原因：")
                    logger.error(f"   1. 网络设置错误（用了testnet密钥但在mainnet，反之亦然）")
                    logger.error(f"   2. 代理或网络连接问题")
                    logger.error(f"   URL: {url}")
                else:
                    text = await resp.text()
                    logger.warning(f"⚠️ API验证返回 {resp.status}: {text[:200]}")
        except Exception as e:
            logger.debug(f"验证API时出错: {e}")

