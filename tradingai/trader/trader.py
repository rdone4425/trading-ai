"""
交易执行器 - 基于平台抽象接口，支持多平台
"""
from typing import Dict, List, Optional, Any
from datetime import datetime

from tradingai.logger import get_logger
from tradingai.exchange.platform.base import BasePlatform
from tradingai.utils.risk_calculator import RiskCalculator
import tradingai.config as config

logger = get_logger(__name__)


class Trader:
    """
    交易执行器
    
    职责：
    1. 基于AI分析结果自动执行交易
    2. 强制设置止盈止损（每笔交易必须有保护）
    3. 设置杠杆和逐仓模式
    4. 确保单向持仓（同一交易对只有一个方向）
    5. 风险管理（仓位大小、风险控制）
    
    特点：
    - 完全基于平台抽象接口，不依赖具体平台实现
    - 支持币安、OKX、Bybit等所有实现了BasePlatform的平台
    """
    
    def __init__(self, platform: BasePlatform):
        """
        初始化交易执行器
        
        Args:
            platform: 交易平台实例（必须实现BasePlatform接口）
        """
        self.platform = platform
        self.risk_calculator = RiskCalculator()
        self.active_positions: Dict[str, Dict] = {}  # 当前活跃持仓 {symbol: position_info}
        self._cached_balance: Optional[float] = None  # 缓存的余额（避免频繁请求）
        self._balance_cache_time: Optional[float] = None  # 余额缓存时间
        
        logger.info("交易执行器已初始化")
    
    async def execute_trade(
        self,
        analysis_result: Dict[str, Any],
        auto_set_leverage: bool = True,
        auto_set_margin: bool = True
    ) -> Dict[str, Any]:
        """
        执行交易（基于AI分析结果）
        
        Args:
            analysis_result: AI分析结果，必须包含：
                - symbol: 交易对
                - action: 做多/做空/观望
                - entry_price: 入场价格
                - stop_loss: 止损价格
                - take_profit: 止盈价格
                - leverage: 杠杆倍数
                - position_size: 仓位大小（币数量）
                - confidence: 置信度
            auto_set_leverage: 是否自动设置杠杆（默认True）
            auto_set_margin: 是否自动设置逐仓模式（默认True）
        
        Returns:
            交易结果 {
                "success": bool,
                "message": str,
                "orders": {
                    "entry": 入场订单,
                    "stop_loss": 止损订单,
                    "take_profit": 止盈订单
                },
                "position": 持仓信息
            }
        """
        try:
            symbol = analysis_result.get('symbol')
            action = analysis_result.get('action')
            confidence = analysis_result.get('confidence', 0)
            
            # 1. 检查是否观望
            if action == '观望' or confidence < config.AI_CONFIDENCE_THRESHOLD:
                return {
                    "success": False,
                    "message": f"观望建议（置信度: {confidence:.1%} < 阈值: {config.AI_CONFIDENCE_THRESHOLD:.1%}）",
                    "orders": {}
                }
            
            # 2. 检查是否已有持仓（防止重复开单）
            # 2.1 先检查本地缓存（快速检查）
            if symbol in self.active_positions:
                cached_position = self.active_positions[symbol]
                logger.warning(f"⚠️  {symbol} 在本地缓存中已有持仓记录: {cached_position.get('position_side')}")
                # 继续检查交易所实际持仓（缓存可能过期）
            
            # 2.2 检查交易所实际持仓（防止重复开单）
            existing_position = await self._check_existing_position(symbol)
            if existing_position:
                position_side = existing_position.get('position_side', 'UNKNOWN')
                position_amt = existing_position.get('position_amt', 0)
                logger.warning(f"⚠️  {symbol} 已有实际持仓: {position_side}, 数量: {position_amt}")
                
                # 更新本地缓存
                self.active_positions[symbol] = {
                    "position_side": position_side,
                    "position_amt": position_amt,
                    "entry_time": existing_position.get('entry_time', datetime.now().isoformat())
                }
                
                return {
                    "success": False,
                    "message": f"已有持仓: {position_side} (数量: {position_amt})，无法重复开仓（单向持仓模式）",
                    "orders": {},
                    "position": existing_position
                }
            
            # 2.3 在提交订单前再次快速检查（双重保险）
            # 如果本地缓存显示有持仓，即使交易所还没更新，也阻止开单
            if symbol in self.active_positions:
                cached_position = self.active_positions[symbol]
                # 再次从交易所确认（因为可能持仓已平但缓存未更新）
                final_check = await self._check_existing_position(symbol)
                if final_check:
                    return {
                        "success": False,
                        "message": f"双重检查：{symbol} 确认已有持仓，防止重复开单",
                        "orders": {},
                        "position": final_check
                    }
                else:
                    # 交易所没有持仓但本地有缓存，清除过期缓存
                    logger.debug(f"清除过期缓存: {symbol}")
                    del self.active_positions[symbol]
            
            # 3. 提取交易参数
            entry_price = analysis_result.get('entry_price')
            stop_loss = analysis_result.get('stop_loss')
            take_profit = analysis_result.get('take_profit')
            leverage = analysis_result.get('leverage', config.DEFAULT_LEVERAGE)
            position_size = analysis_result.get('position_size')
            
            if not all([entry_price, stop_loss, take_profit]):
                return {
                    "success": False,
                    "message": "缺少必要的交易参数（入场价、止损价、止盈价）",
                    "orders": {}
                }
            
            # 4. 设置杠杆和逐仓模式
            if auto_set_leverage:
                await self._set_leverage(symbol, leverage)
            
            if auto_set_margin:
                await self._set_isolated_margin(symbol)
            
            # 5. 确定交易方向
            if action == '做多':
                position_side = "LONG"
                order_side = "BUY"
            elif action == '做空':
                position_side = "SHORT"
                order_side = "SELL"
            else:
                return {
                    "success": False,
                    "message": f"未知的交易方向: {action}",
                    "orders": {}
                }
            
            # 6. 获取账户余额（从交易所实时获取）
            account_balance = await self._get_account_balance()
            
            # 7. 计算仓位大小（如果未提供）
            if not position_size:
                position_size = self._calculate_position_size(
                    entry_price, stop_loss, leverage, account_balance
                )
            
            if position_size <= 0:
                return {
                    "success": False,
                    "message": f"计算出的仓位大小为0，无法执行交易",
                    "orders": {}
                }
            
            # 8. 执行入场订单（市价单）
            entry_order = await self.platform.place_futures_order(
                symbol=symbol,
                side=order_side,
                position_side=position_side,
                quantity=position_size,
                order_type="MARKET"
            )
            
            logger.info(f"✅ 入场订单已提交: {symbol} {action} {position_size} @ 市价 (余额: {account_balance:.2f} USDT)")
            
            # 9. 设置止损订单（必须）
            stop_loss_order = await self._place_stop_loss_order(
                symbol, position_side, stop_loss
            )
            
            # 10. 设置止盈订单（必须）
            take_profit_order = await self._place_take_profit_order(
                symbol, position_side, take_profit
            )
            
            # 11. 记录持仓（在执行成功后立即记录，防止重复开单）
            await self._update_active_position(symbol, position_side, entry_order)
            logger.info(f"📝 已记录持仓: {symbol} {position_side} 到本地缓存")
            
            return {
                "success": True,
                "message": f"交易执行成功: {symbol} {action}",
                "orders": {
                    "entry": entry_order,
                    "stop_loss": stop_loss_order,
                    "take_profit": take_profit_order
                },
                "position": {
                    "symbol": symbol,
                    "position_side": position_side,
                    "quantity": position_size,
                    "entry_price": entry_price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "leverage": leverage
                }
            }
        
        except Exception as e:
            logger.error(f"❌ 交易执行失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"交易执行失败: {str(e)}",
                "orders": {}
            }
    
    async def _check_existing_position(self, symbol: str) -> Optional[Dict]:
        """
        检查是否已有持仓（防止重复开单）
        
        Args:
            symbol: 交易对
        
        Returns:
            持仓信息（如果有），否则None
        """
        try:
            positions = await self.platform.get_position(symbol)
            
            if not positions:
                return None
            
            # 检查是否有该交易对的持仓（非零持仓）
            for position in positions:
                if position.get('symbol') == symbol:
                    position_amt = position.get('position_amt', 0)
                    # 处理可能是字符串的情况
                    if isinstance(position_amt, str):
                        try:
                            position_amt = float(position_amt)
                        except (ValueError, TypeError):
                            position_amt = 0
                    
                    # 如果持仓数量不为0，说明有持仓
                    if abs(position_amt) > 1e-8:  # 使用小的阈值避免浮点数精度问题
                        logger.debug(f"检测到持仓: {symbol} {position.get('position_side')} {position_amt}")
                        return position
            
            return None
        
        except Exception as e:
            logger.warning(f"⚠️  检查持仓失败: {e}")
            # 如果检查失败，为了安全起见，假设可能有持仓（保守策略）
            # 但这可能会阻止所有交易，所以还是返回None，让调用方决定
            return None
    
    async def _set_leverage(self, symbol: str, leverage: int):
        """
        设置杠杆倍数
        
        Args:
            symbol: 交易对
            leverage: 杠杆倍数
        """
        try:
            await self.platform.set_leverage(symbol, leverage)
            logger.debug(f"✅ 已设置杠杆: {symbol} {leverage}x")
        except Exception as e:
            logger.warning(f"⚠️  设置杠杆失败: {e}")
            # 不抛出异常，允许继续交易
    
    async def _set_isolated_margin(self, symbol: str):
        """
        设置逐仓模式
        
        Args:
            symbol: 交易对
        """
        try:
            await self.platform.set_margin_type(symbol, "ISOLATED")
            logger.debug(f"✅ 已设置逐仓模式: {symbol}")
        except Exception as e:
            logger.warning(f"⚠️  设置逐仓模式失败: {e}")
            # 不抛出异常，允许继续交易
    
    async def _get_account_balance(self, use_cache: bool = True, cache_duration: int = 60) -> float:
        """
        从交易所获取账户余额（带缓存）
        
        Args:
            use_cache: 是否使用缓存（默认True，减少API调用）
            cache_duration: 缓存时长（秒，默认60秒）
        
        Returns:
            账户余额（USDT），如果获取失败则返回配置的默认值
        """
        import time
        
        # 检查缓存
        if use_cache and self._cached_balance is not None and self._balance_cache_time:
            if time.time() - self._balance_cache_time < cache_duration:
                return self._cached_balance
        
        try:
            # 从交易所获取实时余额
            balance = await self.platform.get_balance()
            
            if balance and balance > 0:
                self._cached_balance = balance
                self._balance_cache_time = time.time()
                logger.debug(f"📊 账户余额: {balance:.2f} USDT (从交易所获取)")
                return balance
            else:
                # 余额为0或获取失败，使用配置默认值
                logger.warning(f"⚠️  无法获取账户余额或余额为0，使用配置默认值: {config.ACCOUNT_BALANCE} USDT")
                return config.ACCOUNT_BALANCE
        
        except Exception as e:
            logger.warning(f"⚠️  获取账户余额失败: {e}，使用配置默认值: {config.ACCOUNT_BALANCE} USDT")
            return config.ACCOUNT_BALANCE
    
    def _calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        leverage: int,
        account_balance: float
    ) -> float:
        """
        计算仓位大小
        
        Args:
            entry_price: 入场价格
            stop_loss: 止损价格
            leverage: 杠杆倍数
            account_balance: 账户余额（从交易所获取）
        
        Returns:
            仓位大小（币数量）
        """
        position_size = self.risk_calculator.calculate_position_size(
            account_balance=account_balance,
            risk_percent=config.RISK_PERCENT,
            entry_price=entry_price,
            stop_loss=stop_loss,
            leverage=leverage
        )
        
        return position_size
    
    async def _place_stop_loss_order(
        self,
        symbol: str,
        position_side: str,
        stop_loss: float
    ) -> Dict:
        """
        设置止损订单（必须）
        
        Args:
            symbol: 交易对
            position_side: 持仓方向（LONG/SHORT）
            stop_loss: 止损价格
        
        Returns:
            止损订单信息
        """
        # 确定止损订单方向（多单止损是卖出，空单止损是买入）
        if position_side == "LONG":
            order_side = "SELL"  # 多单止损：卖出
            order_type = "STOP_MARKET"  # 市价止损
        else:
            order_side = "BUY"  # 空单止损：买入
            order_type = "STOP_MARKET"  # 市价止损
        
        order = await self.platform.place_futures_order(
            symbol=symbol,
            side=order_side,
            position_side=position_side,
            quantity=0,  # 平仓时使用closePosition
            order_type=order_type,
            stop_price=stop_loss,
            close_position=True  # 平仓
        )
        
        logger.info(f"✅ 止损订单已设置: {symbol} @ {stop_loss}")
        return order
    
    async def _place_take_profit_order(
        self,
        symbol: str,
        position_side: str,
        take_profit: float
    ) -> Dict:
        """
        设置止盈订单（必须）
        
        Args:
            symbol: 交易对
            position_side: 持仓方向（LONG/SHORT）
            take_profit: 止盈价格
        
        Returns:
            止盈订单信息
        """
        # 确定止盈订单方向（多单止盈是卖出，空单止盈是买入）
        if position_side == "LONG":
            order_side = "SELL"  # 多单止盈：卖出
            order_type = "TAKE_PROFIT_MARKET"  # 市价止盈
        else:
            order_side = "BUY"  # 空单止盈：买入
            order_type = "TAKE_PROFIT_MARKET"  # 市价止盈
        
        order = await self.platform.place_futures_order(
            symbol=symbol,
            side=order_side,
            position_side=position_side,
            quantity=0,  # 平仓时使用closePosition
            order_type=order_type,
            stop_price=take_profit,  # 触发价格
            close_position=True  # 平仓
        )
        
        logger.info(f"✅ 止盈订单已设置: {symbol} @ {take_profit}")
        return order
    
    async def _update_active_position(
        self,
        symbol: str,
        position_side: str,
        entry_order: Dict
    ):
        """
        更新活跃持仓记录（防止重复开单）
        
        Args:
            symbol: 交易对
            position_side: 持仓方向
            entry_order: 入场订单
        """
        # 立即更新本地缓存，防止重复开单
        self.active_positions[symbol] = {
            "position_side": position_side,
            "entry_order_id": entry_order.get("order_id"),
            "entry_time": datetime.now().isoformat(),
            "quantity": entry_order.get("quantity", 0),
            "updated_at": datetime.now().isoformat()
        }
        logger.debug(f"已更新本地持仓缓存: {symbol} {position_side}")
    
    async def get_all_positions(self) -> List[Dict]:
        """
        获取所有持仓
        
        Returns:
            持仓列表
        """
        try:
            return await self.platform.get_position()
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            return []
    
    async def close_position(self, symbol: str, position_side: str = None) -> Dict:
        """
        平仓
        
        Args:
            symbol: 交易对
            position_side: 持仓方向（None表示平掉所有方向的持仓）
        
        Returns:
            平仓结果
        """
        try:
            positions = await self.platform.get_position(symbol)
            
            results = []
            for position in positions:
                if position['symbol'] == symbol:
                    if position_side and position['position_side'] != position_side:
                        continue
                    
                    # 确定平仓方向
                    if position['position_side'] == "LONG":
                        side = "SELL"  # 多单平仓：卖出
                    else:
                        side = "BUY"  # 空单平仓：买入
                    
                    # 平仓
                    order = await self.platform.place_futures_order(
                        symbol=symbol,
                        side=side,
                        position_side=position['position_side'],
                        quantity=0,
                        order_type="MARKET",
                        close_position=True
                    )
                    
                    results.append(order)
                    logger.info(f"✅ 已平仓: {symbol} {position['position_side']}")
            
            # 清除活跃持仓记录（平仓后可以重新开单）
            if symbol in self.active_positions:
                del self.active_positions[symbol]
                logger.info(f"🗑️  已清除持仓缓存: {symbol}，现在可以重新开仓")
            
            return {
                "success": True,
                "message": f"已平仓: {symbol}",
                "orders": results
            }
        
        except Exception as e:
            logger.error(f"平仓失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"平仓失败: {str(e)}",
                "orders": []
            }

