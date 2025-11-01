"""
市场分析器 - 使用 AI 分析市场数据

支持三种分析模式：
1. 市场分析 (analysis) - 实时市场分析和交易建议
2. 学习辅导 (learning) - 交易知识学习和指导
3. 交易复盘 (review) - 历史交易复盘和总结
4. 批量分析 (analyze_batch) - 支持串行/并发分析多个交易对
"""
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from tradingai.logger import get_logger
import tradingai.config as config
from tradingai.utils.risk_calculator import RiskCalculator
from tradingai.utils.formatters import (
    smart_format, format_price, format_percentage, format_volume
)
from tradingai.ai.base import BaseAIProvider
from tradingai.ai.prompts.prompt_manager import PromptManager
from tradingai.ai.context_manager import ContextManager

logger = get_logger("ai.analyzer")


class MarketAnalyzer:
    """
    市场分析器
    
    职责：使用 AI 提供商分析市场数据，提供交易建议、学习辅导和交易复盘
    
    功能：
    1. 市场分析 - analyze_market()
    2. 学习辅导 - provide_learning()
    3. 交易复盘 - review_trade()
    """
    
    def __init__(
        self,
        provider: BaseAIProvider,
        prompt_manager: Optional[PromptManager] = None,
        indicator_engine: Optional[Any] = None,
        max_concurrent: Optional[int] = None,
        enable_risk_calculation: bool = True,
        platform: Optional[Any] = None
    ):
        """
        初始化市场分析器
        
        Args:
            provider: AI 提供商
            prompt_manager: 提示词管理器（可选，默认创建新实例）
            indicator_engine: 技术指标引擎（可选，用于批量分析）
            max_concurrent: 最大并发数（可选，默认使用配置）
            enable_risk_calculation: 是否启用风险计算（默认 True）
            platform: 交易平台实例（可选，用于获取实际账户余额）
        """
        # 核心组件
        self.provider: BaseAIProvider = provider
        self.prompt_manager: PromptManager = prompt_manager or PromptManager()
        self.indicator_engine: Optional[Any] = indicator_engine
        self.max_concurrent: int = max_concurrent or config.MAX_CONCURRENT_ANALYSIS
        self.enable_risk_calculation: bool = enable_risk_calculation
        self.risk_calculator: Optional[RiskCalculator] = RiskCalculator() if enable_risk_calculation else None
        self.platform: Optional[Any] = platform  # 交易平台实例（用于获取实际余额）
        
        # 账户余额缓存
        self._cached_balance: Optional[float] = None  # 缓存的余额
        self._balance_cache_time: Optional[float] = None  # 余额缓存时间（时间戳）
        
        # 复盘知识库：存储复盘结果，用于改进后续分析
        self.review_knowledge: List[Dict[str, Any]] = []  # 存储复盘结果
        
        # 策略优化库：存储优化后的交易策略
        self.optimized_strategies: List[Dict[str, Any]] = []  # 存储优化后的策略
        
        # 学习结果库：存储学习结果
        self.learning_results: List[Dict[str, Any]] = []  # 存储学习结果
        
        # 上下文管理器：持久化存储复盘知识和优化策略
        self.context_manager: ContextManager = ContextManager()
        
        # 从上下文加载历史数据（异步，延迟加载）
        # 注意：__init__ 不能是异步，所以在首次使用时会自动加载
        self._context_loaded = False
        
        logger.info(f"初始化市场分析器: {provider.get_provider_name()}")
        if enable_risk_calculation:
            # 如果有平台实例，会在首次使用时获取实际余额
            balance_info = "从交易所实时获取" if platform else f"{config.ACCOUNT_BALANCE} USDT (配置值)"
            logger.info(f"✅ 风险管理已启用（账户余额: {balance_info}, 风险: {config.RISK_PERCENT}%）")
    
    async def analyze_market(
        self,
        symbol: str,
        klines: List[Dict],
        indicators: Dict[str, Any],
        timeframe: str = "1h",
        **kwargs
    ) -> Dict[str, Any]:
        """
        分析市场数据并给出交易建议
        
        Args:
            symbol: 交易对
            klines: K线数据
            indicators: 技术指标数据
            timeframe: 时间周期
            **kwargs: 其他参数
                - temperature: AI 温度参数（默认 0.3，更保守）
                - max_tokens: 最大 token 数
        
        Returns:
            分析结果 {
                "symbol": "交易对",
                "trend": "上升/下降/震荡",
                "action": "做多/做空/观望",
                "confidence": 0.0-1.0,
                "entry_price": 入场价格,
                "stop_loss": 止损价格,
                "take_profit": 止盈价格,
                "support": 支撑位,
                "resistance": 阻力位,
                "risk_reward_ratio": 风险回报比,
                "reason": "分析原因",
                "warnings": ["风险提示"],
                "provider": "AI提供商",
                "analyzed_at": "分析时间"
            }
        
        Example:
            analyzer = MarketAnalyzer(provider)
            result = await analyzer.analyze_market("BTCUSDT", klines, indicators)
            print(f"建议: {result['action']}, 置信度: {result['confidence']}")
        """
        try:
            # 验证输入数据
            if not klines:
                logger.warning(f"⚠️  {symbol} 无K线数据，无法分析")
                return None
            
            # 延迟加载上下文（首次使用时）
            if not self._context_loaded:
                await self._load_context()
                self._context_loaded = True
            
            # 验证指标数据有效性
            logger.debug(f"🔍 验证指标数据: {symbol}")
            logger.debug(f"  指标字典键: {list(indicators.keys()) if indicators else 'None'}")
            if indicators:
                for name, value in list(indicators.items())[:3]:  # 只显示前3个
                    value_type = type(value).__name__
                    if hasattr(value, '__len__'):
                        length = len(value)
                        logger.debug(f"  {name}: 类型={value_type}, 长度={length}")
                        if length > 0:
                            try:
                                import numpy as np
                                if isinstance(value, np.ndarray):
                                    nan_count = np.sum(np.isnan(value))
                                    valid_count = length - nan_count
                                    logger.debug(f"    有效值: {valid_count}/{length}, NaN: {nan_count}")
                                    if valid_count > 0:
                                        logger.debug(f"    最新值: {value[-1]}")
                            except:
                                logger.debug(f"    无法检查numpy数组")
                    else:
                        logger.debug(f"  {name}: 类型={value_type}, 值={value}")
            
            valid_indicators = self._validate_indicators(indicators)
            logger.debug(f"✅ 验证结果: {valid_indicators}/{len(indicators) if indicators else 0} 个有效指标")
            
            if valid_indicators == 0:
                logger.warning(f"⚠️  {symbol} 无有效技术指标数据，无法进行可靠分析")
                # 仍然进行分析，但会在提示词中明确告知指标数据不足
                # 让AI知道是基于有限数据做出的判断
            elif valid_indicators < len(indicators):
                logger.warning(f"⚠️  {symbol} 部分技术指标无效（有效: {valid_indicators}/{len(indicators)}）")
            
            logger.debug(f"📊 AI分析器接收数据验证: {symbol}")
            logger.debug(f"  - K线数量: {len(klines)} 根")
            logger.debug(f"  - K线数据结构: 字典列表，每条包含 time/open/high/low/close/volume")
            if klines:
                logger.debug(f"  - 最新K线: 时间={klines[-1].get('time', 'N/A')}, "
                           f"价格={klines[-1].get('close', 'N/A')}")
            logger.debug(f"  - 指标总数: {len(indicators)} 个")
            logger.debug(f"  - 有效指标数: {valid_indicators} 个")
            logger.debug(f"  - 指标列表: {list(indicators.keys())}")
            
            # 1. 准备数据（使用扫描器传递的K线和指标）
            market_data = self._prepare_analysis_data(
                symbol, klines, indicators, timeframe
            )
            
            logger.debug(f"📋 格式化后的市场数据（传递给AI）:")
            logger.debug(f"  - 交易对: {market_data.get('symbol', 'N/A')}")
            logger.debug(f"  - 当前价格: {market_data.get('current_price', 'N/A')}")
            logger.debug(f"  - 24h涨跌幅: {market_data.get('change_24h', 'N/A')}")
            logger.debug(f"  - 24h成交量: {market_data.get('volume_24h', 'N/A')}")
            logger.debug(f"  - 时间周期: {market_data.get('timeframe', 'N/A')}")
            logger.debug(f"  - 技术指标: {'已格式化（见下方详情）' if market_data.get('indicators') else '无数据'}")
            
            # 2. 添加复盘知识和优化策略（如果存在）
            review_insights_text = self._format_review_insights()
            if review_insights_text:
                # 优先显示优化策略，然后显示复盘经验
                market_data['review_insights'] = f"\n**复盘经验和优化策略（请严格按照执行）：**\n{review_insights_text}"
                logger.debug(f"  - 复盘经验: 已添加（{len(review_insights_text)} 字符）")
            else:
                market_data['review_insights'] = ""
                logger.debug(f"  - 复盘经验: 无")
            
            # 3. 使用提示词管理器构建消息（包含扫描器传递的数据和指标）
            messages = self.prompt_manager.get_full_prompt("analysis", market_data)
            logger.debug(f"📨 构建的AI消息: {len(messages)} 条")
            if messages:
                logger.debug(f"  - 系统提示: {len(messages[0].get('content', ''))} 字符")
                if len(messages) > 1:
                    user_prompt_preview = messages[1].get('content', '')[:200]
                    logger.debug(f"  - 用户提示预览: {user_prompt_preview}...")
            
            # 4. 调用 AI（基于扫描器传递的数据和指标进行分析）
            logger.info(f"🤖 使用 {self.provider.get_provider_name()} 分析 {symbol}（基于扫描数据和指标）")
            logger.debug(f"  发送消息数: {len(messages)}")
            
            response = await self.provider.chat(
                messages=messages,
                temperature=kwargs.get("temperature", 0.3),  # 更保守的温度
                max_tokens=kwargs.get("max_tokens", 2000)
            )
            
            # 打印原始响应（用于调试）
            logger.debug(f"AI 原始响应: {response[:200]}...")
            
            # 5. 解析响应
            result = self._parse_analysis_response(response, symbol, klines)
            
            # 6. 风险管理计算（如果启用，基于扫描器传递的指标）
            if self.enable_risk_calculation and result['action'] != "观望":
                result = await self._enhance_with_risk_management(result, indicators)
            
            result["provider"] = self.provider.get_provider_name()
            result["analyzed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            logger.info(
                f"✅ 分析完成: {symbol} - {result.get('action', 'N/A')} "
                f"(置信度: {result.get('confidence', 0):.1%})"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"❌ 市场分析失败: {symbol} - {e}", exc_info=True)
            raise
    
    async def provide_learning(
        self,
        topic: str,
        level: str = "初级",
        questions: Optional[List[str]] = None,
        goals: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        提供交易学习辅导
        
        Args:
            topic: 学习主题（如"EMA指标使用"）
            level: 学习水平（新手/初级/中级/高级）
            questions: 具体问题列表
            goals: 学习目标
            **kwargs: 其他参数
        
        Returns:
            学习内容文本
        
        Example:
            learning = await analyzer.provide_learning(
                topic="EMA指标",
                level="初级",
                questions=["EMA和MA有什么区别？", "如何使用EMA交叉？"]
            )
        """
        try:
            # 准备学习数据
            learning_data = {
                "topic": topic,
                "level": level,
                "questions": "\n".join(questions) if questions else "无",
                "goals": goals or "掌握该主题的基本概念和应用"
            }
            
            # 使用提示词管理器
            messages = self.prompt_manager.get_full_prompt("learning", learning_data)
            
            logger.info(f"📚 提供学习辅导: {topic} (水平: {level})")
            response = await self.provider.chat(
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 3000)
            )
            
            logger.info(f"✅ 学习内容生成完成")
            
            # 返回结构化学习结果（供上下文保存）
            learning_result = {
                "topic": topic,
                "level": level,
                "content": response,
                "questions": questions or [],
                "goals": goals or "掌握该主题的基本概念和应用",
                "learned_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "provider": self.provider.get_provider_name()
            }
            
            return learning_result
        
        except Exception as e:
            logger.error(f"❌ 学习辅导失败: {e}", exc_info=True)
            raise
    
    async def review_trade(
        self,
        trade_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        复盘交易并提供改进建议
        
        Args:
            trade_data: 交易数据 {
                "symbol": 交易对,
                "direction": "做多/做空",
                "trade_time": 交易时间,
                "duration": 持仓时长,
                "entry_price": 入场价格,
                "exit_price": 出场价格,
                "stop_loss": 止损价格,
                "take_profit": 止盈价格,
                "profit_loss": 盈亏金额,
                "profit_loss_percentage": 盈亏比例,
                "risk_reward_ratio": 风险回报比,
                "reasoning": 交易依据,
                "entry_market_state": 入场时市场状态,
                "exit_market_state": 出场时市场状态,
                "indicators": 技术指标情况,
                "entry_mindset": 入场心态,
                "holding_process": 持仓过程,
                "exit_reason": 出场原因
            }
            **kwargs: 其他参数
        
        Returns:
            复盘结果 {
                "overall_rating": "优秀/良好/一般/较差",
                "decision_quality": {"score": 8, "comment": "..."},
                "execution_quality": {"score": 7, "comment": "..."},
                "risk_management": {"score": 9, "comment": "..."},
                "strengths": ["优点1", "优点2"],
                "weaknesses": ["缺点1", "缺点2"],
                "lessons_learned": ["教训1", "教训2"],
                "improvements": ["改进建议1", "改进建议2"],
                "summary": "总体复盘总结"
            }
        
        Example:
            review = await analyzer.review_trade({
                "symbol": "BTCUSDT",
                "direction": "做多",
                "profit_loss": "+500.00",
                # ... 更多数据
            })
        """
        try:
            # 格式化交易数据
            formatted_data = self._format_trade_data(trade_data)
            
            # 使用提示词管理器
            messages = self.prompt_manager.get_full_prompt("review", formatted_data)
            
            logger.info(
                f"🔍 复盘交易: {trade_data.get('symbol')} "
                f"{trade_data.get('direction')} "
                f"({trade_data.get('profit_loss_percentage', 'N/A')}%)"
            )
            
            response = await self.provider.chat(
                messages=messages,
                temperature=kwargs.get("temperature", 0.5),
                max_tokens=kwargs.get("max_tokens", 3000)
            )
            
            # 解析复盘结果
            result = self._parse_review_response(response, trade_data)
            result["reviewed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result["provider"] = self.provider.get_provider_name()
            
            logger.info(f"✅ 复盘完成: 总体评价 {result.get('overall_rating', 'N/A')}")
            return result
        
        except Exception as e:
            logger.error(f"❌ 交易复盘失败: {e}", exc_info=True)
            raise
    
    def _prepare_analysis_data(
        self,
        symbol: str,
        klines: List[Dict],
        indicators: Dict[str, Any],
        timeframe: str
    ) -> Dict[str, str]:
        """
        准备市场分析数据（用于提示词模板）
        
        Args:
            symbol: 交易对
            klines: K线数据
            indicators: 技术指标数据
            timeframe: 时间周期
        
        Returns:
            格式化的数据字典（用于填充提示词模板）
        """
        if not klines:
            return {
                "symbol": symbol,
                "current_price": "N/A",
                "change_24h": "N/A",
                "volume_24h": "N/A",
                "timeframe": timeframe,
                "indicators": "无数据",
                "high": "N/A",
                "low": "N/A",
                "open": "N/A",
                "close": "N/A"
            }
        
        # 获取最新 K 线
        latest = klines[-1]
        
        # 计算24h涨跌幅（或最近涨跌幅）
        if len(klines) > 1:
            prev_close = klines[-2].get('close', latest.get('close', 0))
            current_close = latest.get('close', 0)
            change_pct = ((current_close - prev_close) / prev_close * 100) if prev_close else 0
        else:
            change_pct = 0
        
        # 格式化技术指标
        indicators_text = self._format_indicators(indicators)
        
        return {
            "symbol": symbol,
            "current_price": format_price(latest.get('close', 0)),
            "change_24h": format_percentage(change_pct / 100),
            "volume_24h": format_volume(latest.get('volume', 0)),
            "timeframe": timeframe,
            "indicators": indicators_text,
            "high": format_price(latest.get('high', 0)),
            "low": format_price(latest.get('low', 0)),
            "open": format_price(latest.get('open', 0)),
            "close": format_price(latest.get('close', 0))
        }
    
    def _validate_indicators(self, indicators: Dict[str, Any]) -> int:
        """
        验证指标数据有效性，返回有效指标数量
        
        Args:
            indicators: 指标数据字典
        
        Returns:
            有效指标数量
        """
        if not indicators:
            return 0
        
        try:
            import numpy as np
            HAS_NUMPY = True
        except ImportError:
            HAS_NUMPY = False
        
        def has_valid_data(data):
            """检查数据是否包含有效值"""
            if data is None:
                return False
            
            # 处理numpy数组
            if HAS_NUMPY and isinstance(data, np.ndarray):
                if len(data) == 0:
                    return False
                # 检查数组中是否有非NaN值
                valid_mask = ~np.isnan(data)
                return np.any(valid_mask)
            
            # 处理普通列表或元组
            if isinstance(data, (list, tuple)):
                if len(data) == 0:
                    return False
                # 检查列表中是否有有效值
                for v in data:
                    if v is None:
                        continue
                    if HAS_NUMPY:
                        if isinstance(v, (float, np.floating)):
                            if not np.isnan(v):
                                return True
                        elif isinstance(v, np.ndarray):
                            if len(v) > 0 and np.any(~np.isnan(v)):
                                return True
                        else:
                            # 其他类型，尝试转换为float检查
                            try:
                                fv = float(v)
                                if not np.isnan(fv):
                                    return True
                            except (ValueError, TypeError):
                                pass
                    else:
                        # 没有numpy，使用字符串检查
                        if str(v) != 'nan' and v is not None:
                            return True
                return False
            
            # 处理字典（复合指标）
            if isinstance(data, dict):
                # 检查子指标是否有有效值
                for sub_value in data.values():
                    if has_valid_data(sub_value):
                        return True
                return False
            
            # 处理单个数值
            if isinstance(data, (int, float)):
                if HAS_NUMPY:
                    return not np.isnan(data)
                else:
                    return str(data) != 'nan' and data is not None
            
            # 其他类型，尝试检查
            return data is not None
        
        valid_count = 0
        for name, value in indicators.items():
            if has_valid_data(value):
                valid_count += 1
        
        return valid_count
    
    def _format_indicators(self, indicators: Dict[str, Any]) -> str:
        """
        格式化技术指标为文本
        
        Args:
            indicators: 技术指标数据
        
        Returns:
            格式化的指标文本
        """
        if not indicators:
            return "⚠️ 系统检测：无技术指标数据（指标计算可能失败或未配置）"
        
        try:
            import numpy as np
            HAS_NUMPY = True
        except ImportError:
            HAS_NUMPY = False
        
        lines = []
        valid_count = 0
        
        def get_last_valid_value(data):
            """获取最后一个有效值"""
            if HAS_NUMPY and isinstance(data, np.ndarray):
                if len(data) == 0:
                    return None
                # 获取最后一个非NaN值
                valid_mask = ~np.isnan(data)
                if np.any(valid_mask):
                    valid_indices = np.where(valid_mask)[0]
                    return float(data[valid_indices[-1]])
                return None
            elif isinstance(data, (list, tuple)):
                if len(data) == 0:
                    return None
                # 从后往前找第一个有效值
                for i in range(len(data) - 1, -1, -1):
                    v = data[i]
                    if v is not None:
                        if HAS_NUMPY:
                            if isinstance(v, (float, np.floating)):
                                if not np.isnan(v):
                                    return float(v)
                            elif isinstance(v, np.ndarray):
                                continue  # 跳过数组中的数组
                        if str(v) != 'nan':
                            try:
                                return float(v)
                            except (ValueError, TypeError):
                                pass
                return None
            elif isinstance(data, (int, float)):
                if HAS_NUMPY:
                    if not np.isnan(data):
                        return float(data)
                elif str(data) != 'nan':
                    return float(data)
                return None
            return None
        
        for name, values in sorted(indicators.items()):
            is_valid = False
            
            # 处理numpy数组（最常见的情况）
            if HAS_NUMPY and isinstance(values, np.ndarray):
                if len(values) > 0:
                    last_value = get_last_valid_value(values)
                    if last_value is not None:
                        formatted_value = smart_format(last_value)
                        lines.append(f"- {name}: {formatted_value}")
                        is_valid = True
            # 处理普通列表或元组
            elif isinstance(values, (list, tuple)) and len(values) > 0:
                last_value = get_last_valid_value(values)
                if last_value is not None:
                    formatted_value = smart_format(last_value)
                    lines.append(f"- {name}: {formatted_value}")
                    is_valid = True
            # 处理单个数值
            elif isinstance(values, (int, float)):
                if HAS_NUMPY:
                    if not np.isnan(values):
                        formatted_value = smart_format(values)
                        lines.append(f"- {name}: {formatted_value}")
                        is_valid = True
                elif str(values) != 'nan':
                    formatted_value = smart_format(values)
                    lines.append(f"- {name}: {formatted_value}")
                    is_valid = True
            # 处理字典（复合指标，如MACD）
            elif isinstance(values, dict):
                has_valid_sub = False
                for sub_name, sub_value in values.items():
                    last_value = get_last_valid_value(sub_value)
                    if last_value is not None:
                        formatted_value = smart_format(last_value)
                        lines.append(f"- {name}_{sub_name}: {formatted_value}")
                        has_valid_sub = True
                is_valid = has_valid_sub
            
            if is_valid:
                valid_count += 1
        
        if valid_count == 0:
            return "⚠️ 系统检测：所有技术指标数据无效（可能因K线数据不足导致指标计算失败）"
        
        if valid_count < len(indicators):
            return f"⚠️ 系统检测：部分指标无效（有效: {valid_count}/{len(indicators)}）\n" + "\n".join(lines)
        
        return "\n".join(lines) if lines else "⚠️ 系统检测：无有效指标数据"
    
    def _format_review_insights(self) -> str:
        """
        格式化复盘知识、优化策略和学习结果为文本，供分析时参考
        
        Returns:
            格式化的复盘知识、优化策略和学习结果文本
        """
        lines = []
        
        # 0. 格式化学习结果（理论知识基础，优先显示）
        if self.learning_results:
            # 提取关键学习点
            key_learnings = []
            for learning in self.learning_results[-3:]:  # 最近3次学习
                topic = learning.get('topic', '')
                content = learning.get('content', '')
                # 提取学习内容的前200字作为关键点
                if isinstance(content, str) and len(content) > 50:
                    # 尝试提取核心要点（前几句话）
                    key_point = content[:200].replace('\n', ' ').strip()
                    if key_point:
                        key_learnings.append({
                            'topic': topic,
                            'summary': key_point
                        })
            
            if key_learnings:
                lines.append("📖 历史学习知识（理论指导）：")
                for learning in key_learnings[:2]:  # 最多2条
                    lines.append(f"  【{learning['topic']}】")
                    lines.append(f"  {learning['summary']}...")
                lines.append("")
        
        # 1. 格式化复盘知识
        if self.review_knowledge:
            all_lessons = []
            all_improvements = []
            all_weaknesses = []
            
            for review in self.review_knowledge[-5:]:  # 只取最近5次复盘
                lessons = review.get('lessons_learned', [])
                improvements = review.get('improvements', [])
                weaknesses = review.get('weaknesses', [])
                
                all_lessons.extend(lessons if isinstance(lessons, list) else [])
                all_improvements.extend(improvements if isinstance(improvements, list) else [])
                all_weaknesses.extend(weaknesses if isinstance(weaknesses, list) else [])
            
            if all_lessons:
                unique_lessons = list(set(all_lessons))[:5]  # 最多5条
                lines.append("📚 历史复盘经验教训：")
                for lesson in unique_lessons:
                    lines.append(f"  - {lesson}")
                lines.append("")
            
            if all_improvements:
                unique_improvements = list(set(all_improvements))[:5]  # 最多5条
                lines.append("💡 改进建议（应用于当前分析）：")
                for improvement in unique_improvements:
                    lines.append(f"  - {improvement}")
                lines.append("")
            
            if all_weaknesses:
                unique_weaknesses = list(set(all_weaknesses))[:3]  # 最多3条
                lines.append("⚠️  需要避免的问题：")
                for weakness in unique_weaknesses:
                    lines.append(f"  - {weakness}")
                lines.append("")
        
        # 2. 格式化优化后的策略（优先显示）
        if self.optimized_strategies:
            lines.append("🎯 优化后的交易策略（请严格按照执行）：")
            for i, strategy in enumerate(self.optimized_strategies[-3:], 1):  # 最近3条策略
                strategy_name = strategy.get('strategy_name', f'策略{i}')
                strategy_rules = strategy.get('rules', [])
                conditions = strategy.get('entry_conditions', [])
                exit_rules = strategy.get('exit_rules', [])
                
                lines.append(f"\n  【{strategy_name}】")
                
                if strategy_rules:
                    lines.append("  核心规则：")
                    for rule in strategy_rules[:3]:  # 最多3条
                        lines.append(f"    • {rule}")
                
                if conditions:
                    lines.append("  入场条件：")
                    for condition in conditions[:3]:  # 最多3条
                        lines.append(f"    ✓ {condition}")
                
                if exit_rules:
                    lines.append("  出场规则：")
                    for rule in exit_rules[:2]:  # 最多2条
                        lines.append(f"    → {rule}")
            
            lines.append("")
        
        return "\n".join(lines) if lines else ""
    
    async def _load_context(self):
        """从上下文加载历史数据（异步）"""
        try:
            context = await self.context_manager.load_all_context()
            
            # 加载复盘知识
            if context.get("review_knowledge"):
                self.review_knowledge = context["review_knowledge"]
                logger.info(f"📚 已加载复盘知识: {len(self.review_knowledge)} 条")
            
            # 加载优化策略
            if context.get("optimized_strategies"):
                self.optimized_strategies = context["optimized_strategies"]
                logger.info(f"🎯 已加载优化策略: {len(self.optimized_strategies)} 条")
            
            # 加载学习结果
            if context.get("learning_results"):
                self.learning_results = context["learning_results"]
                logger.info(f"📖 已加载学习结果: {len(self.learning_results)} 条")
        
        except Exception as e:
            logger.warning(f"⚠️  加载上下文失败: {e}")
    
    async def _save_context(self):
        """保存当前上下文到文件（异步）"""
        try:
            await self.context_manager.save_all_context(
                review_knowledge=self.review_knowledge,
                optimized_strategies=self.optimized_strategies,
                learning_results=self.learning_results
            )
        except Exception as e:
            logger.warning(f"⚠️  保存上下文失败: {e}")
    
    async def add_review_knowledge(self, review_result: Dict[str, Any]):
        """
        添加复盘结果到知识库，并自动优化策略（异步）
        
        Args:
            review_result: 复盘结果（从 review_trade 返回）
        """
        if review_result:
            self.review_knowledge.append(review_result)
            # 只保留最近20次复盘结果，避免过多
            if len(self.review_knowledge) > 20:
                self.review_knowledge = self.review_knowledge[-20:]
            
            logger.debug(f"✅ 已添加复盘知识（共 {len(self.review_knowledge)} 条）")
            
            # 保存到上下文
            await self._save_context()
            
            # 自动优化策略（基于复盘结果）
            await self._optimize_strategy_from_review(review_result)
    
    async def _optimize_strategy_from_review(self, review_result: Dict[str, Any]):
        """
        基于复盘结果优化交易策略
        
        Args:
            review_result: 复盘结果
        """
        try:
            improvements = review_result.get('improvements', [])
            lessons = review_result.get('lessons_learned', [])
            weaknesses = review_result.get('weaknesses', [])
            
            if not improvements and not lessons:
                return
            
            # 从复盘结果中提取策略优化点
            optimization_points = []
            
            # 从改进建议中提取策略规则
            for improvement in improvements:
                if isinstance(improvement, str) and len(improvement) > 10:
                    optimization_points.append({
                        'type': 'improvement',
                        'content': improvement
                    })
            
            # 从经验教训中提取策略规则
            for lesson in lessons:
                if isinstance(lesson, str) and len(lesson) > 10:
                    optimization_points.append({
                        'type': 'lesson',
                        'content': lesson
                    })
            
            # 从缺点中提取需要避免的规则
            for weakness in weaknesses:
                if isinstance(weakness, str) and len(weakness) > 10:
                    optimization_points.append({
                        'type': 'avoid',
                        'content': f"避免: {weakness}"
                    })
            
            if not optimization_points:
                return
            
            # 生成优化后的策略
            optimized_strategy = self._generate_optimized_strategy(optimization_points)
            
            if optimized_strategy:
                self.optimized_strategies.append(optimized_strategy)
                # 只保留最近10条优化策略
                if len(self.optimized_strategies) > 10:
                    self.optimized_strategies = self.optimized_strategies[-10:]
                
                logger.info(f"✅ 已生成优化策略: {optimized_strategy.get('strategy_name', '未命名')}")
                logger.debug(f"策略规则数: {len(optimized_strategy.get('rules', []))}")
                
                # 保存到上下文
                await self._save_context()
        
        except Exception as e:
            logger.warning(f"⚠️  策略优化失败: {e}")
    
    def _generate_optimized_strategy(self, optimization_points: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        根据优化点生成优化后的策略
        
        Args:
            optimization_points: 优化点列表
        
        Returns:
            优化后的策略字典
        """
        from datetime import datetime
        
        # 分析优化点，生成策略规则
        rules = []
        entry_conditions = []
        exit_rules = []
        
        for point in optimization_points[:5]:  # 最多5个优化点
            content = point.get('content', '')
            point_type = point.get('type', '')
            
            if point_type == 'improvement':
                # 改进建议 → 策略规则
                if any(keyword in content.lower() for keyword in ['止损', 'stop', '风险']):
                    rules.append(content)
                elif any(keyword in content.lower() for keyword in ['入场', 'entry', '买入', '卖出']):
                    entry_conditions.append(content)
                elif any(keyword in content.lower() for keyword in ['出场', 'exit', '止盈']):
                    exit_rules.append(content)
                else:
                    rules.append(content)
            
            elif point_type == 'lesson':
                # 经验教训 → 策略规则
                rules.append(content)
            
            elif point_type == 'avoid':
                # 避免的问题 → 负面规则
                rules.append(content)
        
        if not rules and not entry_conditions:
            return None
        
        # 生成策略名称
        strategy_name = f"优化策略_{datetime.now().strftime('%m%d_%H%M')}"
        
        return {
            'strategy_name': strategy_name,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'based_on_reviews': len(optimization_points),
            'rules': rules[:5],  # 最多5条规则
            'entry_conditions': entry_conditions[:3],  # 最多3个入场条件
            'exit_rules': exit_rules[:3],  # 最多3个出场规则
            'optimization_points': optimization_points  # 保留原始优化点
        }
    
    async def add_optimized_strategy(self, strategy: Dict[str, Any]):
        """
        手动添加优化后的策略（异步）
        
        Args:
            strategy: 策略字典，包含：
                - strategy_name: 策略名称
                - rules: 策略规则列表
                - entry_conditions: 入场条件列表
                - exit_rules: 出场规则列表
        """
        if strategy:
            self.optimized_strategies.append(strategy)
            if len(self.optimized_strategies) > 10:
                self.optimized_strategies = self.optimized_strategies[-10:]
            
            logger.info(f"✅ 已添加优化策略: {strategy.get('strategy_name', '未命名')}")
            
            # 保存到上下文
            await self._save_context()
    
    async def clear_optimized_strategies(self):
        """清空优化策略库（异步）"""
        self.optimized_strategies.clear()
        logger.info("已清空优化策略库")
        
        # 保存到上下文
        await self._save_context()
    
    def get_optimized_strategies(self) -> List[Dict[str, Any]]:
        """获取所有优化后的策略"""
        return self.optimized_strategies.copy()
    
    async def add_learning_result(self, learning_result: Dict[str, Any]):
        """
        添加学习结果到知识库（异步）
        
        Args:
            learning_result: 学习结果（从 provide_learning 返回）
        """
        if learning_result:
            self.learning_results.append(learning_result)
            # 只保留最近20次学习结果，避免过多
            if len(self.learning_results) > 20:
                self.learning_results = self.learning_results[-20:]
            
            logger.debug(f"✅ 已添加学习结果（共 {len(self.learning_results)} 条）")
            
            # 保存到上下文
            await self._save_context()
    
    def get_learning_results(self) -> List[Dict[str, Any]]:
        """获取所有学习结果"""
        return self.learning_results.copy()
    
    async def clear_review_knowledge(self):
        """清空复盘知识库（异步）"""
        self.review_knowledge.clear()
        logger.info("已清空复盘知识库")
        
        # 保存到上下文
        await self._save_context()
    
    def get_review_knowledge_count(self) -> int:
        """获取复盘知识库中的记录数"""
        return len(self.review_knowledge)
    
    def _format_trade_data(self, trade_data: Dict[str, Any]) -> Dict[str, str]:
        """
        格式化交易数据（用于复盘提示词）
        
        Args:
            trade_data: 交易数据
        
        Returns:
            格式化的数据字典
        """
        # 确保所有必需字段都有值
        formatted = {}
        for key in [
            "symbol", "direction", "trade_time", "duration",
            "entry_price", "exit_price", "stop_loss", "take_profit",
            "profit_loss", "profit_loss_percentage", "risk_reward_ratio",
            "reasoning", "entry_market_state", "exit_market_state",
            "indicators", "entry_mindset", "holding_process", "exit_reason"
        ]:
            formatted[key] = str(trade_data.get(key, "未提供"))
        
        return formatted
    
    def _parse_analysis_response(
        self,
        response: str,
        symbol: str,
        klines: List[Dict]
    ) -> Dict[str, Any]:
        """
        解析 AI 分析响应为结构化数据
        
        Args:
            response: AI 响应文本
            symbol: 交易对
            klines: K线数据（用于获取当前价格）
        
        Returns:
            解析后的分析结果
        """
        current_price = klines[-1].get('close', 0) if klines else 0
        
        # 尝试解析 JSON 格式
        try:
            if '{' in response and '}' in response:
                # 提取 JSON（可能在代码块中）
                json_str = response
                
                # 如果在代码块中，提取出来
                if '```json' in response:
                    start = response.find('```json') + 7
                    end = response.find('```', start)
                    if end > start:
                        json_str = response[start:end].strip()
                elif '```' in response:
                    start = response.find('```') + 3
                    end = response.find('```', start)
                    if end > start:
                        json_str = response[start:end].strip()
                else:
                    # 直接提取 JSON 部分
                    start = response.find('{')
                    end = response.rfind('}') + 1
                    json_str = response[start:end]
                
                data = json.loads(json_str)
                
                # 提取所有字段
                result = {
                    "symbol": data.get("symbol", symbol),
                    "trend": data.get("trend", "未知"),
                    "action": data.get("action", "观望"),
                    "confidence": float(data.get("confidence", 0.5)),
                    "entry_price": float(data.get("entry_price", current_price)),
                    "stop_loss": float(data.get("stop_loss", current_price * 0.95)),
                    "take_profit": float(data.get("take_profit", current_price * 1.05)),
                    "support": float(data.get("support", current_price * 0.97)),
                    "resistance": float(data.get("resistance", current_price * 1.03)),
                    "risk_reward_ratio": data.get("risk_reward_ratio", "N/A"),
                    "trading_standard": data.get("trading_standard", "未提供"),
                    "reason": data.get("reason", ""),
                    "warnings": data.get("warnings", [])
                }
                
                logger.debug(f"✅ 成功解析 JSON 响应")
                return result
        
        except json.JSONDecodeError as e:
            logger.debug(f"JSON 解析失败: {e}，使用文本解析")
        except Exception as e:
            logger.warning(f"解析响应时出错: {e}，使用文本解析")
        
        # 文本解析（降级处理）
        logger.debug("使用文本解析模式")
        response_lower = response.lower()
        
        # 判断行动
        if any(word in response_lower for word in ["买入", "buy", "做多", "long"]):
            action = "做多"
        elif any(word in response_lower for word in ["卖出", "sell", "做空", "short"]):
            action = "做空"
        else:
            action = "观望"
        
        # 提取置信度
        confidence = 0.5
        if any(word in response_lower for word in ["强烈", "高度", "very", "strong"]):
            confidence = 0.8
        elif any(word in response_lower for word in ["谨慎", "低", "weak"]):
            confidence = 0.3
        
        return {
            "symbol": symbol,
            "trend": "未知",
            "action": action,
            "confidence": confidence,
            "entry_price": current_price,
            "stop_loss": current_price * (0.97 if action == "做多" else 1.03),
            "take_profit": current_price * (1.05 if action == "做多" else 0.95),
            "support": current_price * 0.97,
            "resistance": current_price * 1.03,
            "risk_reward_ratio": "N/A",
            "reason": response,
            "warnings": ["AI 响应未使用 JSON 格式，解析可能不准确"],
            "trading_standard": "未提供"
        }
    
    async def _enhance_with_risk_management(
        self,
        result: Dict[str, Any],
        indicators: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用风险管理工具优化分析结果
        
        Args:
            result: 原始分析结果
            indicators: 技术指标（需要包含 ATR）
        
        Returns:
            增强后的分析结果
        """
        try:
            entry_price = result['entry_price']
            action = result['action']
            position = "long" if action in ["做多", "买入", "buy", "long"] else "short"
            
            # 1. 获取 ATR（如果有）
            atr = None
            if indicators:
                # 尝试从不同的 ATR 键中获取
                for key in ["ATR", "atr", "ATR_14", "atr_14"]:
                    if key in indicators:
                        atr_value = indicators[key]
                        if isinstance(atr_value, (list, tuple)) and len(atr_value) > 0:
                            atr = atr_value[-1]
                        elif isinstance(atr_value, (int, float)):
                            atr = atr_value
                        break
            
            # 如果没有 ATR，使用价格的百分比估算
            if atr is None or atr == 0:
                atr = entry_price * 0.02  # 假设 ATR 为价格的 2%
                logger.debug(f"未找到 ATR 指标，使用估算值: {atr}")
            
            # 2. 重新计算止损（基于 ATR）
            calculated_stop_loss = self.risk_calculator.calculate_stop_loss(
                entry_price=entry_price,
                atr=atr,
                atr_multiplier=config.ATR_MULTIPLIER,
                position=position
            )
            
            # 3. 重新计算止盈（基于风险回报比）
            calculated_take_profit = self.risk_calculator.calculate_take_profit(
                entry_price=entry_price,
                stop_loss=calculated_stop_loss,
                risk_reward_ratio=config.RISK_REWARD_RATIO,
                position=position
            )
            
            # 4. 获取账户余额（优先从交易所获取，失败则使用配置值）
            account_balance = await self._get_account_balance()
            
            # 5. 计算建议杠杆
            suggested_leverage = self.risk_calculator.calculate_leverage(
                account_balance=account_balance,
                risk_percent=config.RISK_PERCENT,
                entry_price=entry_price,
                stop_loss=calculated_stop_loss,
                max_leverage=config.MAX_LEVERAGE
            )
            
            # 6. 计算风险指标
            risk_metrics = self.risk_calculator.calculate_risk_metrics(
                entry_price=entry_price,
                stop_loss=calculated_stop_loss,
                take_profit=calculated_take_profit,
                account_balance=account_balance,
                risk_percent=config.RISK_PERCENT,
                leverage=suggested_leverage
            )
            
            # 6. 更新结果
            result['stop_loss'] = calculated_stop_loss
            result['take_profit'] = calculated_take_profit
            result['leverage'] = suggested_leverage
            result['position_size'] = risk_metrics['position_size']
            result['position_value'] = risk_metrics['position_value']
            result['margin_required'] = risk_metrics['margin_required']
            result['potential_loss'] = risk_metrics['potential_loss']
            result['potential_profit'] = risk_metrics['potential_profit']
            result['risk_reward_ratio'] = f"1:{risk_metrics['risk_reward_ratio']:.2f}"
            
            # 添加风险管理警告
            if 'warnings' not in result:
                result['warnings'] = []
            
            result['warnings'].insert(0, f"建议杠杆: {suggested_leverage}x")
            result['warnings'].insert(1, f"仓位大小: {risk_metrics['position_size']:.4f} 币")
            result['warnings'].insert(2, f"保证金: {risk_metrics['margin_required']:.2f} USDT")
            
            logger.debug(f"✅ 风险管理计算完成: 杠杆 {suggested_leverage}x, 仓位 {risk_metrics['position_size']:.4f}")
            
        except Exception as e:
            logger.error(f"❌ 风险管理计算失败: {e}", exc_info=True)
        
        return result
    
    async def _get_account_balance(self, use_cache: bool = True, cache_duration: int = 60) -> float:
        """
        获取账户余额（优先从交易所获取，失败则使用配置值）
        
        Args:
            use_cache: 是否使用缓存（默认True，减少API调用）
            cache_duration: 缓存时长（秒，默认60秒）
        
        Returns:
            账户余额（USDT）
        """
        import time
        
        # 检查缓存
        if use_cache and self._cached_balance is not None and self._balance_cache_time:
            if time.time() - self._balance_cache_time < cache_duration:
                return self._cached_balance
        
        # 如果有平台实例，尝试从交易所获取
        if self.platform:
            try:
                balance = await self.platform.get_balance()
                if balance and balance > 0:
                    self._cached_balance = balance
                    self._balance_cache_time = time.time()
                    logger.debug(f"📊 账户余额: {balance:.2f} USDT (从交易所获取)")
                    return balance
            except Exception as e:
                logger.debug(f"⚠️  获取账户余额失败，使用配置默认值: {e}")
        
        # 回退到配置默认值
        return config.ACCOUNT_BALANCE
    
    def _parse_review_response(
        self,
        response: str,
        trade_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析 AI 复盘响应
        
        Args:
            response: AI 响应文本
            trade_data: 原始交易数据
        
        Returns:
            解析后的复盘结果
        """
        # 尝试解析 JSON
        try:
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                data = json.loads(json_str)
                
                logger.debug(f"✅ 成功解析复盘 JSON 响应")
                return data
        
        except Exception as e:
            logger.debug(f"JSON 解析失败: {e}，返回文本格式")
        
        # 降级处理：返回文本内容
        return {
            "overall_rating": "未评分",
            "decision_quality": {"score": 0, "comment": "无法解析"},
            "execution_quality": {"score": 0, "comment": "无法解析"},
            "risk_management": {"score": 0, "comment": "无法解析"},
            "strengths": [],
            "weaknesses": [],
            "lessons_learned": [],
            "improvements": [],
            "summary": response
        }
    
    async def analyze_batch(
        self,
        data: List[Dict[str, Any]],
        timeframe: str,
        concurrent: bool = True
    ) -> List[Dict[str, Any]]:
        """
        批量分析多个交易对（支持串行/并发）
        
        Args:
            data: 数据列表，每项包含：
                - symbol: 交易对
                - klines: K线数据（必需，扫描器获取）
                - indicators: 技术指标（可选，如果未提供则自动计算）
            timeframe: 时间周期
            concurrent: 是否使用并发（默认 True，推荐）
        
        Returns:
            分析结果列表
        
        Note:
            AI分析完全基于扫描器传递的K线和指标数据
        """
        if not data:
            logger.warning("⚠️  没有数据需要分析")
            return []
        
        if not self.indicator_engine:
            logger.error("❌ 批量分析需要 indicator_engine，请在初始化时传入")
            return []
        
        logger.info(f"📊 准备分析 {len(data)} 个交易对（基于扫描器传递的数据）")
        
        if concurrent and len(data) > 1:
            # 并发分析（推荐）
            return await self._analyze_concurrent(data, timeframe)
        else:
            # 串行分析（仅当只有1个交易对或关闭并发时）
            return await self._analyze_sequential(data, timeframe)
    
    async def _analyze_sequential(
        self,
        data: List[Dict[str, Any]],
        timeframe: str
    ) -> List[Dict[str, Any]]:
        """串行分析（逐个分析，基于扫描器传递的数据）"""
        logger.info("📊 串行分析模式")
        results = []
        
        for i, item in enumerate(data, 1):
            symbol = item['symbol']
            klines = item['klines']  # 扫描器传递的K线
            
            logger.info(f"进度: {i}/{len(data)} - {symbol}")
            
            # 获取或计算指标（优先使用扫描器传递的指标）
            if 'indicators' in item and item['indicators']:
                indicators = item['indicators']  # 使用扫描器传递的指标
                logger.debug(f"  使用扫描器传递的指标: {list(indicators.keys())}")
            else:
                # 如果没有传递指标，则计算（这种情况不应该发生，因为扫描器应该已经计算了）
                if not self.indicator_engine:
                    logger.error(f"❌ 无指标引擎且数据中无指标，跳过 {symbol}")
                    continue
                indicators = self.indicator_engine.calculate_all(klines)
                logger.debug(f"  重新计算指标: {list(indicators.keys())}")
            
            # AI 分析（基于扫描器传递的K线和指标）
            result = await self.analyze_market(
                symbol=symbol,
                klines=klines,      # 扫描器传递的K线
                indicators=indicators,  # 扫描器传递的指标
                timeframe=timeframe
            )
            
            if result:
                results.append(result)
                logger.info(
                    f"  ✅ {result['action']} "
                    f"(置信度: {result['confidence']:.1%})"
                )
        
        return results
    
    async def _analyze_concurrent(
        self,
        data: List[Dict[str, Any]],
        timeframe: str
    ) -> List[Dict[str, Any]]:
        """并发分析（同时分析多个，基于扫描器传递的数据）"""
        logger.info(f"🚀 开始并发分析（最大并发: {self.max_concurrent}）")
        
        # 使用信号量限制并发数量
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def analyze_with_semaphore(item: Dict, index: int):
            """带信号量控制的分析任务"""
            symbol = item['symbol']
            klines = item['klines']  # 扫描器传递的K线
            
            async with semaphore:  # 获取信号量许可
                try:
                    logger.info(f"[{index}/{len(data)}] 开始分析 {symbol}")
                    
                    # 获取或计算指标（优先使用扫描器传递的指标）
                    if 'indicators' in item and item['indicators']:
                        indicators = item['indicators']  # 使用扫描器传递的指标
                        logger.debug(f"  [{index}/{len(data)}] 使用扫描器传递的指标: {list(indicators.keys())}")
                    else:
                        # 如果没有传递指标，则计算（不应该发生）
                        if not self.indicator_engine:
                            logger.error(f"❌ 无指标引擎且数据中无指标，跳过 {symbol}")
                            return None
                        indicators = self.indicator_engine.calculate_all(klines)
                        logger.debug(f"  [{index}/{len(data)}] 重新计算指标: {list(indicators.keys())}")
                    
                    # AI 分析（基于扫描器传递的K线和指标）
                    result = await self.analyze_market(
                        symbol=symbol,
                        klines=klines,      # 扫描器传递的K线
                        indicators=indicators,  # 扫描器传递的指标
                        timeframe=timeframe
                    )
                    
                    if result:
                        logger.info(
                            f"  ✅ [{index}/{len(data)}] {symbol}: {result['action']} "
                            f"(置信度: {result['confidence']:.1%})"
                        )
                        return result
                    else:
                        logger.warning(f"  ⚠️  [{index}/{len(data)}] {symbol} 未返回分析结果")
                        return None
                
                except Exception as e:
                    logger.error(f"  ❌ [{index}/{len(data)}] {symbol} 分析失败: {e}")
                    return None
        
        # 创建并发任务
        tasks = [
            analyze_with_semaphore(item, i)
            for i, item in enumerate(data, 1)
        ]
        
        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 收集成功的结果
        valid_results = [
            r for r in results
            if r and not isinstance(r, Exception)
        ]
        
        logger.info(f"✅ 并发分析完成: {len(valid_results)}/{len(data)} 成功")
        return valid_results
    
    async def close(self):
        """关闭分析器（释放资源）"""
        if hasattr(self.provider, 'close'):
            await self.provider.close()
        logger.debug("市场分析器已关闭")

