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
        self.active_orders: Dict[str, Dict] = {}  # 活跃订单 {symbol: {stop_loss_order_id, take_profit_order_id}}
        
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
            
            # 0. 验证交易对
            if not symbol or not isinstance(symbol, str):
                return {
                    "success": False,
                    "message": f"交易对无效: {symbol}",
                    "orders": {}
                }
            
            # 验证交易对格式（必须包含USDT等）
            if not any(quote in symbol.upper() for quote in ['USDT', 'BUSD', 'USD']):
                return {
                    "success": False,
                    "message": f"交易对格式无效: {symbol}（必须是USDT/BUSD等合约）",
                    "orders": {}
                }
            
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
            
            # 3.1 检查价格是否存在且有效
            if not all([entry_price, stop_loss, take_profit]):
                return {
                    "success": False,
                    "message": "缺少必要的交易参数（入场价、止损价、止盈价）",
                    "orders": {}
                }
            
            # 3.2 转换为浮点数并验证
            try:
                entry_price = float(entry_price)
                stop_loss = float(stop_loss)
                take_profit = float(take_profit)
                leverage = int(leverage)
            except (ValueError, TypeError) as e:
                return {
                    "success": False,
                    "message": f"交易参数类型错误: {e}",
                    "orders": {}
                }
            
            # 3.3 严格验证价格有效性（必须大于0）
            if entry_price <= 0 or stop_loss <= 0 or take_profit <= 0:
                return {
                    "success": False,
                    "message": f"价格无效（必须>0）: 入场={entry_price}, 止损={stop_loss}, 止盈={take_profit}",
                    "orders": {}
                }
            
            # 3.4 验证价格的合理性
            if action == '做多':
                # 做多：止损应该低于入场价，止盈应该高于入场价
                if stop_loss >= entry_price:
                    return {
                        "success": False,
                        "message": f"做多止损价格不合理: 止损({stop_loss}) >= 入场({entry_price})",
                        "orders": {}
                    }
                if take_profit <= entry_price:
                    return {
                        "success": False,
                        "message": f"做多止盈价格不合理: 止盈({take_profit}) <= 入场({entry_price})",
                        "orders": {}
                    }
            elif action == '做空':
                # 做空：止损应该高于入场价，止盈应该低于入场价
                if stop_loss <= entry_price:
                    return {
                        "success": False,
                        "message": f"做空止损价格不合理: 止损({stop_loss}) <= 入场({entry_price})",
                        "orders": {}
                    }
                if take_profit >= entry_price:
                    return {
                        "success": False,
                        "message": f"做空止盈价格不合理: 止盈({take_profit}) >= 入场({entry_price})",
                        "orders": {}
                    }
            
            # 3.5 验证杠杆倍数
            if leverage < 1 or leverage > 125:
                logger.warning(f"杠杆倍数异常: {leverage}，使用默认值: {config.DEFAULT_LEVERAGE}")
                leverage = config.DEFAULT_LEVERAGE
            
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
            if not position_size or position_size <= 0:
                position_size = self._calculate_position_size(
                    entry_price, stop_loss, leverage, account_balance
                )
            else:
                # 如果提供了仓位大小，转换并验证
                try:
                    position_size = float(position_size)
                except (ValueError, TypeError):
                    return {
                        "success": False,
                        "message": f"仓位大小格式错误: {position_size}",
                        "orders": {}
                    }
            
            # 7.1 验证仓位大小
            if position_size <= 0:
                return {
                    "success": False,
                    "message": f"仓位大小无效（必须>0）: {position_size}",
                    "orders": {}
                }
            
            # 7.2 验证仓位不超过最大限制
            position_value = position_size * entry_price
            max_position_value = account_balance * config.MAX_POSITION_SIZE
            if position_value > max_position_value:
                logger.warning(f"⚠️  仓位过大: {position_value:.2f} > 最大允许 {max_position_value:.2f}，自动调整")
                position_size = (max_position_value / entry_price) * 0.99  # 留一点余地
                logger.info(f"调整后仓位: {position_size:.6f}")
            
            # 7.3 验证保证金是否足够
            margin_required = (position_size * entry_price) / leverage
            if margin_required > account_balance * 0.95:  # 留5%缓冲
                return {
                    "success": False,
                    "message": f"保证金不足: 需要{margin_required:.2f} USDT, 可用{account_balance:.2f} USDT",
                    "orders": {}
                }
            
            # 7.4 记录交易详情（用于日志）
            logger.info(f"📊 交易详情:")
            logger.info(f"   交易对: {symbol}")
            logger.info(f"   方向: {action}")
            logger.info(f"   入场价: {entry_price:.8f}")
            logger.info(f"   止损价: {stop_loss:.8f}")
            logger.info(f"   止盈价: {take_profit:.8f}")
            logger.info(f"   仓位: {position_size:.6f} 币")
            logger.info(f"   杠杆: {leverage}x")
            logger.info(f"   保证金: {margin_required:.2f} USDT")
            logger.info(f"   仓位价值: {position_value:.2f} USDT")
            
            # 计算潜在盈亏
            if action == '做多':
                potential_profit = (take_profit - entry_price) * position_size
                potential_loss = (entry_price - stop_loss) * position_size
            else:  # 做空
                potential_profit = (entry_price - take_profit) * position_size
                potential_loss = (stop_loss - entry_price) * position_size
            
            risk_reward = potential_profit / potential_loss if potential_loss > 0 else 0
            logger.info(f"   潜在盈利: +{potential_profit:.2f} USDT")
            logger.info(f"   潜在亏损: -{potential_loss:.2f} USDT")
            logger.info(f"   盈亏比: 1:{risk_reward:.2f}")
            
            # 7.5 最终确认：如果风险过大，拒绝交易
            risk_percent = (potential_loss / account_balance) * 100
            if risk_percent > config.MAX_LOSS_PER_TRADE * 100:
                return {
                    "success": False,
                    "message": f"风险过大: {risk_percent:.2f}% > 最大允许 {config.MAX_LOSS_PER_TRADE*100:.2f}%",
                    "orders": {}
                }
            
            # 8. 最后确认：记录即将执行的交易（用于审计）
            logger.info(f"🚀 准备执行交易:")
            logger.info(f"   即将开仓: {symbol} {action}")
            logger.info(f"   置信度: {confidence:.1%}")
            logger.info(f"   风险: {risk_percent:.2f}% 账户")
            
            # 8.1 执行入场订单（市价单）
            try:
                entry_order = await self.platform.place_futures_order(
                    symbol=symbol,
                    side=order_side,
                    position_side=position_side,
                    quantity=position_size,
                    order_type="MARKET"
                )
            except Exception as e:
                logger.error(f"❌ 入场订单失败: {e}")
                return {
                    "success": False,
                    "message": f"入场订单失败: {str(e)}",
                    "orders": {}
                }
            
            logger.info(f"✅ 入场订单已提交: {symbol} {action} {position_size:.6f} @ 市价 (余额: {account_balance:.2f} USDT)")
            logger.info(f"   订单ID: {entry_order.get('order_id', 'N/A')}")
            
            # 9. 设置止损订单（必须）
            try:
                stop_loss_order = await self._place_stop_loss_order(
                    symbol, position_side, stop_loss
                )
            except Exception as e:
                logger.error(f"❌ 止损订单失败: {e}")
                # 止损订单失败是严重问题，应该立即平仓
                logger.warning(f"⚠️  止损设置失败，出于安全考虑，将平仓")
                try:
                    await self.close_position(symbol, position_side)
                except Exception as close_error:
                    logger.error(f"❌ 紧急平仓也失败: {close_error}")
                return {
                    "success": False,
                    "message": f"止损订单失败: {str(e)}，已尝试平仓",
                    "orders": {"entry": entry_order}
                }
            
            # 10. 设置止盈订单（必须）
            try:
                take_profit_order = await self._place_take_profit_order(
                    symbol, position_side, take_profit
                )
            except Exception as e:
                logger.error(f"❌ 止盈订单失败: {e}")
                # 止盈失败不那么严重，但也要记录
                logger.warning(f"⚠️  止盈设置失败，持仓仍有止损保护")
                take_profit_order = {"error": str(e)}
            
            # 11. 记录持仓和订单（在执行成功后立即记录，防止重复开单）
            await self._update_active_position(symbol, position_side, entry_order)
            
            # 保存止盈止损订单ID（用于平仓时取消）
            stop_loss_order_id = stop_loss_order.get('order_id') if isinstance(stop_loss_order, dict) else None
            take_profit_order_id = take_profit_order.get('order_id') if isinstance(take_profit_order, dict) else None
            
            self.active_orders[symbol] = {
                "stop_loss_order_id": stop_loss_order_id,
                "take_profit_order_id": take_profit_order_id,
                "position_side": position_side,
                "updated_at": datetime.now().isoformat()
            }
            
            logger.info(f"📝 已记录持仓: {symbol} {position_side} 到本地缓存")
            if stop_loss_order_id:
                logger.debug(f"   止损订单ID: {stop_loss_order_id}")
            if take_profit_order_id:
                logger.debug(f"   止盈订单ID: {take_profit_order_id}")
            
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
            error_str = str(e)
            # 如果已经是逐仓模式（-4046），不需要警告
            if "-4046" in error_str or "No need to change" in error_str:
                logger.debug(f"ℹ️ {symbol} 已经是逐仓模式")
            else:
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
        平仓（会自动取消止盈止损订单）
        
        Args:
            symbol: 交易对
            position_side: 持仓方向（None表示平掉所有方向的持仓）
        
        Returns:
            平仓结果
        """
        try:
            positions = await self.platform.get_position(symbol)
            
            results = []
            cancelled_orders = []
            
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
            
            # 取消止盈止损订单（必须在平仓后进行）
            if symbol in self.active_orders:
                order_info = self.active_orders[symbol]
                stop_loss_order_id = order_info.get('stop_loss_order_id')
                take_profit_order_id = order_info.get('take_profit_order_id')
                
                # 尝试取消止损订单
                if stop_loss_order_id:
                    try:
                        await self.platform.cancel_order(symbol, stop_loss_order_id)
                        cancelled_orders.append(f"止损订单({stop_loss_order_id})")
                        logger.info(f"✅ 已取消止损订单: {symbol} #{stop_loss_order_id}")
                    except Exception as e:
                        logger.warning(f"⚠️  取消止损订单失败: {symbol} #{stop_loss_order_id}, {e}")
                        # 订单可能已经触发或不存在，继续执行
                
                # 尝试取消止盈订单
                if take_profit_order_id:
                    try:
                        await self.platform.cancel_order(symbol, take_profit_order_id)
                        cancelled_orders.append(f"止盈订单({take_profit_order_id})")
                        logger.info(f"✅ 已取消止盈订单: {symbol} #{take_profit_order_id}")
                    except Exception as e:
                        logger.warning(f"⚠️  取消止盈订单失败: {symbol} #{take_profit_order_id}, {e}")
                        # 订单可能已经触发或不存在，继续执行
                
                # 如果订单ID记录不完整，取消该交易对的所有订单（保险措施）
                if not stop_loss_order_id and not take_profit_order_id:
                    try:
                        await self.platform.cancel_all_orders(symbol)
                        logger.info(f"✅ 已取消 {symbol} 的所有挂单（保险措施）")
                        cancelled_orders.append("所有挂单（保险措施）")
                    except Exception as e:
                        logger.warning(f"⚠️  取消所有订单失败: {symbol}, {e}")
                
                # 清除订单记录
                del self.active_orders[symbol]
                logger.debug(f"🗑️  已清除订单记录: {symbol}")
            
            # 清除活跃持仓记录（平仓后可以重新开单）
            if symbol in self.active_positions:
                del self.active_positions[symbol]
                logger.info(f"🗑️  已清除持仓缓存: {symbol}，现在可以重新开仓")
            
            message = f"已平仓: {symbol}"
            if cancelled_orders:
                message += f"，已取消: {', '.join(cancelled_orders)}"
            
            return {
                "success": True,
                "message": message,
                "orders": results,
                "cancelled_orders": cancelled_orders
            }
        
        except Exception as e:
            logger.error(f"平仓失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"平仓失败: {str(e)}",
                "orders": []
            }

