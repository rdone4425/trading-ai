"""
市场扫描器 - 统一的市场数据扫描和筛选入口
"""
from typing import List, Dict, Optional, Callable
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from ..exchange import PlatformFactory
from ..exchange.platform.base import BasePlatform
from .symbol_parser import SymbolParser
from .. import config
from ..logger import get_logger
from ..utils import (
    align_to_timeframe,
    get_kline_range,
    is_kline_closed,
    time_until_next_kline,
    format_time,
    now_shanghai
)

logger = get_logger("scanner.market")


class MarketScanner:
    """市场扫描器"""
    
    def __init__(
        self,
        exchange_name: Optional[str] = None,
        timeframe: Optional[str] = None,
        lookback: Optional[int] = None,
        scan_limit: Optional[int] = None,
        hot_top_n: Optional[int] = None,
        volume_24h_top_n: Optional[int] = None,
        gainers_top_n: Optional[int] = None,
        losers_top_n: Optional[int] = None,
        default_quote: Optional[str] = None,
        min_volume: Optional[float] = None,
        min_change: Optional[float] = None,
        max_change: Optional[float] = None,
        kline_type: Optional[str] = None,
        analyzer = None,
        indicator_engine = None
    ):
        """
        初始化扫描器
        
        Args:
            exchange_name: 交易所名称（默认从配置读取）
            timeframe: K线周期（默认从配置读取）
            lookback: K线数量（默认从配置读取）
            scan_limit: 扫描交易对数量（默认从配置读取）
            hot_top_n: 热门榜默认数量
            volume_24h_top_n: 成交量榜默认数量
            gainers_top_n: 涨幅榜默认数量
            losers_top_n: 跌幅榜默认数量
            default_quote: 默认报价货币
            min_volume: 最小成交量过滤
            min_change: 最小涨跌幅过滤（%）
            max_change: 最大涨跌幅过滤（%）
            kline_type: K线类型 closed(已完成) 或 open(进行中)
        """
        # 基础配置
        self.exchange_name = exchange_name or config.EXCHANGE_NAME
        self.timeframe = timeframe or config.TIMEFRAME
        self.lookback = lookback or config.LOOKBACK
        self.scan_limit = scan_limit or config.SCAN_TOP_N
        
        # K线类型配置
        self.kline_type = (kline_type or config.KLINE_TYPE).lower()
        if self.kline_type not in ['closed', 'open']:
            self.kline_type = 'closed'
        
        # 排行榜配置（统一使用SCAN_TOP_N）
        self.hot_top_n = hot_top_n or config.SCAN_TOP_N
        self.volume_24h_top_n = volume_24h_top_n or config.SCAN_TOP_N
        self.gainers_top_n = gainers_top_n or config.SCAN_TOP_N
        self.losers_top_n = losers_top_n or config.SCAN_TOP_N
        
        # 筛选配置
        self.default_quote = default_quote or config.DEFAULT_QUOTE
        self.min_volume = min_volume if min_volume is not None else 0
        self.min_change = min_change if min_change is not None else -100
        self.max_change = max_change if max_change is not None else 100
        
        # 运行时变量
        self.platform: Optional[BasePlatform] = None
        self.symbols: List[str] = []
        self.tickers: Dict[str, Dict] = {}  # 交易对的行情数据
        
        # AI 分析相关
        self.analyzer = analyzer
        self.indicator_engine = indicator_engine
        self.analysis_results: List[Dict] = []  # 存储 AI 分析结果
        
        if self.analyzer:
            logger.info("✅ 已集成 AI 分析器")
        if self.indicator_engine:
            logger.info("✅ 已集成技术指标引擎")
        
        # 自动扫描相关
        self._auto_scan_task: Optional[asyncio.Task] = None
        self._scan_callback: Optional[Callable] = None
        self._is_scanning: bool = False
    
    async def connect(self):
        """连接到交易所"""
        logger.info(f"连接到 {self.exchange_name}...")
        
        # 使用工厂创建平台
        self.platform = PlatformFactory.create_from_config()
        
        await self.platform.connect()
        logger.info("✅ 连接成功")
    
    async def disconnect(self):
        """断开连接"""
        if self.platform:
            await self.platform.disconnect()
            logger.info("✅ 已断开连接")
    
    async def analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """
        分析单个交易对（扫描器获取数据 → 计算指标 → 传递给AI分析）
        
        数据流程：
        1. 扫描器从交易所获取K线数据
        2. 扫描器使用指标引擎计算技术指标
        3. 扫描器将K线和指标传递给AI分析器
        4. AI基于扫描器传递的数据进行分析
        
        Args:
            symbol: 交易对
        
        Returns:
            AI 分析结果，如果失败返回 None
        """
        try:
            # 1. 扫描器获取 K 线数据（从交易所）
            klines = await self.get_klines(symbol)
            if not klines:
                logger.warning(f"⚠️  {symbol} 扫描器未获取到K线数据")
                return None
            
            logger.debug(f"📊 扫描器获取 {symbol} K线: {len(klines)} 根")
            
            # 显示K线数据结构示例（第一条和最后一条）
            if klines:
                logger.debug(f"   K线数据结构示例（第一条）:")
                first_kline = klines[0]
                logger.debug(f"     时间: {first_kline.get('time', 'N/A')}, "
                           f"开: {first_kline.get('open', 'N/A')}, "
                           f"高: {first_kline.get('high', 'N/A')}, "
                           f"低: {first_kline.get('low', 'N/A')}, "
                           f"收: {first_kline.get('close', 'N/A')}, "
                           f"量: {first_kline.get('volume', 'N/A')}")
                if len(klines) > 1:
                    last_kline = klines[-1]
                    logger.debug(f"   K线数据结构示例（最后一条）:")
                    logger.debug(f"     时间: {last_kline.get('time', 'N/A')}, "
                               f"开: {last_kline.get('open', 'N/A')}, "
                               f"高: {last_kline.get('high', 'N/A')}, "
                               f"低: {last_kline.get('low', 'N/A')}, "
                               f"收: {last_kline.get('close', 'N/A')}, "
                               f"量: {last_kline.get('volume', 'N/A')}")
            
            # 2. 扫描器计算技术指标（基于获取的K线）
            if not self.indicator_engine:
                logger.warning(f"⚠️  未配置技术指标引擎，无法为 {symbol} 计算指标")
                return None
            
            indicators = self.indicator_engine.calculate_all(klines)
            if not indicators:
                logger.warning(f"⚠️  {symbol} 指标计算失败")
                return None
            
            logger.debug(f"📈 扫描器计算 {symbol} 指标: {len(indicators)} 个")
            
            # 显示指标数据结构详情
            logger.debug(f"   指标数据详情:")
            try:
                import numpy as np
                HAS_NUMPY = True
            except ImportError:
                HAS_NUMPY = False
            
            for ind_name, ind_value in indicators.items():
                if HAS_NUMPY and isinstance(ind_value, np.ndarray):
                    if len(ind_value) > 0:
                        nan_count = np.sum(np.isnan(ind_value))
                        valid_count = len(ind_value) - nan_count
                        if valid_count > 0:
                            # 获取最后一个非NaN值
                            valid_mask = ~np.isnan(ind_value)
                            valid_indices = np.where(valid_mask)[0]
                            last_valid = float(ind_value[valid_indices[-1]])
                            logger.debug(f"     {ind_name}: numpy数组[{len(ind_value)}], 有效值: {valid_count}, NaN: {nan_count}, 最新有效值: {last_valid}")
                        else:
                            logger.debug(f"     {ind_name}: numpy数组[{len(ind_value)}], 全部为NaN")
                    else:
                        logger.debug(f"     {ind_name}: 空numpy数组")
                elif isinstance(ind_value, (list, tuple)):
                    if len(ind_value) > 0:
                        last_val = ind_value[-1]
                        valid_count = sum(1 for v in ind_value if v is not None and str(v) != 'nan')
                        logger.debug(f"     {ind_name}: 列表[{len(ind_value)}], 有效值: {valid_count}, 最新值: {last_val}")
                    else:
                        logger.debug(f"     {ind_name}: 空列表")
                elif isinstance(ind_value, dict):
                    logger.debug(f"     {ind_name}: 复合指标 {list(ind_value.keys())}")
                    for sub_name, sub_value in ind_value.items():
                        if HAS_NUMPY and isinstance(sub_value, np.ndarray):
                            if len(sub_value) > 0:
                                valid_mask = ~np.isnan(sub_value)
                                valid_count = np.sum(valid_mask)
                                if valid_count > 0:
                                    valid_indices = np.where(valid_mask)[0]
                                    last_valid = float(sub_value[valid_indices[-1]])
                                    logger.debug(f"       {sub_name}: numpy数组[{len(sub_value)}], 最新有效值: {last_valid}")
                                else:
                                    logger.debug(f"       {sub_name}: numpy数组，全部为NaN")
                        elif isinstance(sub_value, (list, tuple)) and len(sub_value) > 0:
                            logger.debug(f"       {sub_name}: 列表[{len(sub_value)}], 最新值: {sub_value[-1]}")
                        else:
                            logger.debug(f"       {sub_name}: {sub_value}")
                else:
                    logger.debug(f"     {ind_name}: {ind_value}")
            
            # 3. 扫描器将数据和指标传递给AI分析器
            if not self.analyzer:
                logger.warning(f"⚠️  未配置 AI 分析器，无法分析 {symbol}")
                return None
            
            logger.debug(f"🤖 传递数据给AI分析器: {symbol}")
            logger.debug(f"   - K线数据: {len(klines)} 根（字典格式，包含time/open/high/low/close/volume）")
            logger.debug(f"   - 技术指标: {list(indicators.keys())}（字典格式，值为数组或复合字典）")
            logger.debug(f"   - 时间周期: {self.timeframe}")
            
            # AI分析器基于扫描器传递的数据和指标进行分析
            analysis = await self.analyzer.analyze_market(
                symbol=symbol,
                klines=klines,      # 扫描器获取的K线数据
                indicators=indicators,  # 扫描器计算的指标数据
                timeframe=self.timeframe
            )
            
            if analysis:
                logger.debug(f"✅ AI分析完成: {symbol}")
            
            return analysis
        
        except Exception as e:
            logger.error(f"❌ 分析 {symbol} 失败: {e}", exc_info=True)
            return None
    
    async def scan_and_analyze(self, concurrent: bool = True) -> List[Dict]:
        """
        扫描市场并自动进行 AI 分析
        
        数据流程：
        1. 扫描器扫描市场，获取交易对列表
        2. 扫描器为每个交易对获取K线数据（从交易所）
        3. 扫描器计算技术指标（基于K线）
        4. 扫描器将K线和指标传递给AI分析器
        5. AI基于扫描器传递的数据和指标进行分析
        
        Args:
            concurrent: 是否使用并发分析（默认 True，可大幅提升速度）
        
        Returns:
            分析结果列表
        """
        try:
            # 1. 扫描交易对
            symbols = await self.scan_symbols()
            logger.info(f"✅ 扫描到 {len(symbols)} 个交易对")
            
            if not self.analyzer or not self.indicator_engine:
                logger.warning("⚠️  未配置 AI 分析器或指标引擎，仅返回交易对列表")
                return []
            
            # 2. 分析交易对（并发或串行）
            self.analysis_results = []
            
            if concurrent and len(symbols) > 1:
                # 并发分析（推荐）
                logger.info(f"🚀 开始并发分析（最大并发: {config.MAX_CONCURRENT_ANALYSIS}）")
                await self._analyze_concurrent(symbols)
            else:
                # 串行分析
                logger.info("📊 开始串行分析")
                await self._analyze_sequential(symbols)
            
            logger.info(f"\n✅ 完成分析: {len(self.analysis_results)}/{len(symbols)}")
            
            # 保存分析结果（如果启用）
            if config.SAVE_ANALYSIS_RESULTS and self.analysis_results:
                self.save_analysis_results()
            
            return self.analysis_results
        
        except Exception as e:
            logger.error(f"❌ 扫描分析失败: {e}")
            return []
    
    async def _analyze_sequential(self, symbols: List[str]):
        """串行分析交易对（逐个分析）"""
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"进度: {i}/{len(symbols)} - {symbol}")
            result = await self.analyze_symbol(symbol)
            if result:
                self.analysis_results.append(result)
                logger.info(f"  ✅ {result['action']} (置信度: {result['confidence']:.1%})")
    
    async def _analyze_concurrent(self, symbols: List[str]):
        """并发分析交易对（同时分析多个，速度更快）"""
        import asyncio
        from tradingai import config
        
        # 使用信号量限制并发数量
        semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_ANALYSIS)
        
        async def analyze_with_semaphore(symbol: str, index: int):
            """带信号量控制的分析函数"""
            async with semaphore:
                logger.info(f"🔄 开始分析 ({index}/{len(symbols)}): {symbol}")
                try:
                    result = await self.analyze_symbol(symbol)
                    if result:
                        logger.info(
                            f"✅ 完成分析 ({index}/{len(symbols)}): {symbol} - "
                            f"{result['action']} (置信度: {result['confidence']:.1%})"
                        )
                        return result
                    else:
                        logger.warning(f"⚠️  分析失败 ({index}/{len(symbols)}): {symbol}")
                        return None
                except Exception as e:
                    logger.error(f"❌ 分析出错 ({index}/{len(symbols)}): {symbol} - {e}")
                    return None
        
        # 创建所有任务
        tasks = [
            analyze_with_semaphore(symbol, i)
            for i, symbol in enumerate(symbols, 1)
        ]
        
        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 收集成功的结果
        for result in results:
            if result and not isinstance(result, Exception):
                self.analysis_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"❌ 任务异常: {result}")
    
    def cleanup_old_analysis_results(self, retention_days: int = 2, cleanup_interval_days: int = 1) -> int:
        """
        每N天清理一次，保留最近M天的分析结果，删除更早的目录和文件
        
        Args:
            retention_days: 保留天数，默认2天（保留今天、昨天）
            cleanup_interval_days: 清理间隔天数，默认1天（每天执行一次清理）
        
        Returns:
            清理的文件数量
        """
        try:
            # 获取项目根目录
            project_root = Path(__file__).parent.parent.parent
            base_dir = project_root / config.ANALYSIS_RESULTS_DIR
            
            if not base_dir.exists():
                return 0
            
            # 获取当前日期（上海时区）
            now = now_shanghai()
            today = now.date()
            
            # 检查上次清理时间（记录在隐藏文件中）
            last_cleanup_file = base_dir / '.last_cleanup'
            should_cleanup = False
            
            if last_cleanup_file.exists():
                try:
                    last_cleanup_str = last_cleanup_file.read_text(encoding='utf-8').strip()
                    last_cleanup_date = datetime.strptime(last_cleanup_str, '%Y-%m-%d').date()
                    days_since_cleanup = (today - last_cleanup_date).days
                    # 如果距离上次清理已经过了至少N天，则执行清理
                    if days_since_cleanup >= cleanup_interval_days:
                        should_cleanup = True
                except Exception as e:
                    logger.warning(f"读取上次清理时间失败: {e}，将执行清理")
                    should_cleanup = True
            else:
                # 首次运行，执行清理
                should_cleanup = True
            
            if not should_cleanup:
                return 0  # 未到清理时间
            
            # 计算需要删除的日期（超过保留天数的日期）
            # 保留：今天、昨天、前天（共3天），删除第4天及更早的
            cutoff_date = today - timedelta(days=retention_days)
            
            deleted_count = 0
            deleted_dirs = []
            
            # 遍历所有日期目录
            for date_dir in base_dir.iterdir():
                if not date_dir.is_dir():
                    continue
                
                # 检查日期目录名是否为有效的日期格式（YYYY-MM-DD）
                try:
                    dir_date = datetime.strptime(date_dir.name, '%Y-%m-%d').date()
                    
                    # 如果目录日期早于截止日期，删除该目录
                    if dir_date < cutoff_date:
                        dir_deleted = 0
                        
                        # 删除目录中的所有文件
                        for file_path in date_dir.glob('analysis_*.json'):
                            try:
                                file_path.unlink()
                                deleted_count += 1
                                dir_deleted += 1
                            except Exception as e:
                                logger.warning(f"删除文件失败 {file_path}: {e}")
                                continue
                        
                        # 删除目录中的所有剩余文件（如果有非分析文件，也一起删除）
                        try:
                            remaining_items = list(date_dir.iterdir())
                            for item in remaining_items:
                                try:
                                    if item.is_file():
                                        item.unlink()
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        
                        # 删除目录
                        try:
                            date_dir.rmdir()
                            deleted_dirs.append(date_dir.name)
                            logger.debug(f"🗑️  已删除分析目录: {date_dir.name}")
                        except Exception:
                            pass  # 目录不为空，可能还有子目录
                    
                except ValueError:
                    # 不是有效的日期目录（YYYY-MM-DD格式），跳过
                    continue
            
            # 更新上次清理时间
            try:
                last_cleanup_file.write_text(today.strftime('%Y-%m-%d'), encoding='utf-8')
            except Exception as e:
                logger.warning(f"更新清理时间失败: {e}")
            
            if deleted_count > 0 or deleted_dirs:
                logger.info(
                    f"🗑️  清理完成：删除了 {len(deleted_dirs)} 个目录，共 {deleted_count} 个分析结果文件"
                    f"（保留最近 {retention_days} 天的数据）"
                )
                if deleted_dirs:
                    logger.debug(f"   已删除目录: {', '.join(sorted(deleted_dirs))}")
            
            return deleted_count
        
        except Exception as e:
            logger.error(f"❌ 清理分析结果文件失败: {e}", exc_info=True)
            return 0
    
    def save_analysis_results(self, filename: Optional[str] = None) -> Optional[str]:
        """
        保存分析结果到 JSON 文件（按日期分类）
        
        Args:
            filename: 自定义文件名（可选），默认使用时间戳
        
        Returns:
            保存的文件路径，失败返回 None
        """
        try:
            if not self.analysis_results:
                logger.warning("没有分析结果可保存")
                return None
            
            # 在保存前清理旧文件（每天清理一次，只保留最近2天的数据）
            self.cleanup_old_analysis_results(retention_days=2, cleanup_interval_days=1)
            
            # 获取当前时间（上海时区）
            now = now_shanghai()
            
            # 获取项目根目录（相对于当前文件向上3级）
            project_root = Path(__file__).parent.parent.parent
            
            # 创建按日期分类的目录结构：trading-ai/data/2025-11-01/
            date_dir = project_root / config.ANALYSIS_RESULTS_DIR / now.strftime('%Y-%m-%d')
            date_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名（只用时间，不含日期）
            if not filename:
                filename = f"analysis_{now.strftime('%H%M%S')}.json"
            
            filepath = date_dir / filename
            
            # 构建保存数据
            save_data = {
                "scan_time": now_shanghai().isoformat(),
                "exchange": self.exchange_name,
                "timeframe": self.timeframe,
                "kline_type": self.kline_type,
                "total_symbols": len(self.symbols),
                "analyzed_count": len(self.analysis_results),
                "summary": self.get_analysis_summary(),
                "results": self.analysis_results
            }
            
            # 保存为 JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 分析结果已保存: {filepath}")
            return str(filepath)
        
        except Exception as e:
            logger.error(f"❌ 保存分析结果失败: {e}", exc_info=True)
            return None
    
    def get_analysis_summary(self) -> Dict:
        """
        获取分析结果汇总
        
        Returns:
            汇总统计
        """
        if not self.analysis_results:
            return {}
        
        # 统计各种建议
        actions = {}
        for result in self.analysis_results:
            action = result.get('action', '未知')
            actions[action] = actions.get(action, 0) + 1
        
        # 获取高置信度的建议
        threshold = config.AI_CONFIDENCE_THRESHOLD
        high_confidence = [
            r for r in self.analysis_results 
            if r.get('confidence', 0) >= threshold
        ]
        
        # 按置信度排序
        sorted_results = sorted(
            self.analysis_results, 
            key=lambda x: x.get('confidence', 0), 
            reverse=True
        )
        
        # top_results 只保存关键字段（避免与 results 重复）
        top_results_simplified = []
        for r in sorted_results[:5]:
            top_results_simplified.append({
                'symbol': r.get('symbol'),
                'action': r.get('action'),
                'confidence': r.get('confidence'),
                'trend': r.get('trend'),
                'entry_price': r.get('entry_price'),
                'stop_loss': r.get('stop_loss'),
                'take_profit': r.get('take_profit')
            })
        
        return {
            'total': len(self.analysis_results),
            'actions': actions,
            'high_confidence_count': len(high_confidence),
            'high_confidence_results': high_confidence,
            'top_results': top_results_simplified,  # 只保存关键字段，完整数据在 results 中
            'threshold': threshold
        }
    
    async def scan_symbols(self) -> List[str]:
        """
        扫描交易对
        
        Returns:
            交易对列表
        """
        if not self.platform:
            raise RuntimeError("未连接到交易所，请先调用 connect()")
        
        # 优先使用自定义交易对
        if config.CUSTOM_SYMBOLS_RAW:
            # 解析并标准化交易对
            custom_list = SymbolParser.parse_custom_symbols(
                config.CUSTOM_SYMBOLS_RAW,
                self.exchange_name
            )
            
            # 如果解析失败（可能是单个货币），尝试智能搜索
            if custom_list:
                # 验证交易对是否有效
                valid_symbols = []
                all_exchange_symbols = await self.platform.get_symbols()
                
                for symbol in custom_list:
                    # 如果已经是完整交易对，直接使用
                    if symbol in all_exchange_symbols:
                        valid_symbols.append(symbol)
                    else:
                        # 尝试智能搜索（可能是单个货币）
                        searched = SymbolParser.smart_search(symbol, all_exchange_symbols, self.default_quote)
                        if searched:
                            valid_symbols.extend(searched)
                
                if valid_symbols:
                    # 去重
                    self.symbols = list(dict.fromkeys(valid_symbols))
                    
                    # 获取价格信息
                    all_tickers = await self.platform.get_all_tickers_24h()
                    self.tickers = {t["symbol"]: t for t in all_tickers if t["symbol"] in self.symbols}
                    
                    logger.info(f"✅ 使用自定义交易对: {len(self.symbols)} 个")
                    logger.info(f"   交易对: {', '.join(self.symbols[:10])}")
                    return self.symbols
        
        # 否则使用扫描类型
        logger.info("正在根据扫描类型获取交易对...")
        scan_types = [t.strip().lower() for t in config.SCAN_TYPES.split(",") if t.strip()]
        
        all_tickers = []
        for scan_type in scan_types:
            if scan_type == "hot":
                tickers = await self.get_hot_symbols(top_n=config.SCAN_TOP_N)
                all_tickers.extend(tickers)
            elif scan_type == "volume":
                tickers = await self.get_top_volume(top_n=config.SCAN_TOP_N)
                all_tickers.extend(tickers)
            elif scan_type == "gainers":
                tickers = await self.get_top_gainers(top_n=config.SCAN_TOP_N)
                all_tickers.extend(tickers)
            elif scan_type == "losers":
                tickers = await self.get_top_losers(top_n=config.SCAN_TOP_N)
                all_tickers.extend(tickers)
        
        # 去重（保持顺序，使用symbol作为key）
        unique_tickers = {}
        for ticker in all_tickers:
            symbol = ticker["symbol"]
            if symbol not in unique_tickers:
                unique_tickers[symbol] = ticker
        
        # 限制为统一数量
        limited_tickers = list(unique_tickers.values())[:config.SCAN_TOP_N]
        
        # 保存交易对列表和行情数据
        self.symbols = [t["symbol"] for t in limited_tickers]
        self.tickers = {t["symbol"]: t for t in limited_tickers}
        
        logger.info(f"✅ 找到 {len(self.symbols)} 个交易对")
        return self.symbols
    
    async def get_klines(self, symbol: str, kline_type: Optional[str] = None) -> List[Dict]:
        """
        获取单个交易对的K线
        
        Args:
            symbol: 交易对
            kline_type: K线类型 closed(已完成) 或 open(进行中)，默认使用配置
        
        Returns:
            K线数据列表
        """
        if not self.platform:
            raise RuntimeError("未连接到交易所")
        
        kline_type = kline_type or self.kline_type
        
        klines = await self.platform.get_klines(
            symbol=symbol,
            interval=self.timeframe,
            limit=self.lookback,
            include_current=kline_type == 'open'  # 进行中的K线需要包含当前
        )
        
        logger.debug(f"{symbol}: 获取到 {len(klines)} 根K线 ({kline_type})")
        return klines
    
    async def scan_all_klines(self) -> Dict[str, List[Dict]]:
        """
        扫描所有交易对的K线
        
        Returns:
            {symbol: [klines]} 字典
        """
        if not self.symbols:
            await self.scan_symbols()
        
        logger.info(f"开始扫描 {len(self.symbols)} 个交易对的K线...")
        
        all_klines = {}
        for i, symbol in enumerate(self.symbols, 1):
            try:
                klines = await self.get_klines(symbol)
                all_klines[symbol] = klines
                
                if i % 10 == 0:  # 每10个打印一次进度
                    logger.info(f"进度: {i}/{len(self.symbols)}")
            
            except Exception as e:
                logger.error(f"获取 {symbol} K线失败: {e}")
                continue
        
        logger.info(f"✅ 扫描完成，成功获取 {len(all_klines)} 个交易对的数据")
        return all_klines
    
    async def scan_with_filter(
        self,
        min_volume: Optional[float] = None,
        max_symbols: Optional[int] = None
    ) -> Dict[str, List[Dict]]:
        """
        带过滤条件的扫描
        
        Args:
            min_volume: 最小成交量
            max_symbols: 最大交易对数量
        
        Returns:
            过滤后的K线数据
        """
        all_klines = await self.scan_all_klines()
        
        # 过滤低成交量
        if min_volume:
            filtered = {}
            for symbol, klines in all_klines.items():
                if klines:
                    latest_volume = klines[-1].get('volume', 0)
                    if latest_volume >= min_volume:
                        filtered[symbol] = klines
            
            logger.info(f"过滤后剩余 {len(filtered)} 个交易对")
            all_klines = filtered
        
        # 限制数量
        if max_symbols and len(all_klines) > max_symbols:
            all_klines = dict(list(all_klines.items())[:max_symbols])
            logger.info(f"限制数量为 {max_symbols} 个")
        
        return all_klines
    
    async def get_market_summary(self) -> Dict:
        """
        获取市场摘要
        
        Returns:
            市场统计信息
        """
        if not self.symbols:
            await self.scan_symbols()
        
        summary = {
            "exchange": self.exchange_name,
            "total_symbols": len(self.symbols),
            "timeframe": self.timeframe,
            "lookback": self.lookback,
            "symbols": self.symbols[:10],  # 前10个示例
            "tickers": [self.tickers.get(s, {}) for s in self.symbols[:10]]  # 带价格信息
        }
        
        return summary
    
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """
        获取单个交易对的行情数据
        
        Args:
            symbol: 交易对
        
        Returns:
            行情数据（价格、涨跌幅、成交量等）
        """
        return self.tickers.get(symbol)
    
    def get_all_tickers(self) -> Dict[str, Dict]:
        """
        获取所有交易对的行情数据
        
        Returns:
            所有交易对的行情字典
        """
        return self.tickers
    
    async def start_auto_scan(
        self,
        callback: Optional[Callable] = None,
        align_to_kline: bool = True,
        wait_for_close: bool = True
    ):
        """
        启动自动扫描
        
        Args:
            callback: 每次扫描完成后的回调函数，接收参数 (symbols, tickers)
            align_to_kline: 是否对准K线周期开始扫描
            wait_for_close: 是否等待K线完成（仅在 kline_type='closed' 时有效）
        """
        if self._is_scanning:
            logger.warning("自动扫描已在运行中")
            return
        
        if not self.platform:
            raise RuntimeError("请先调用 connect() 连接到交易所")
        
        self._scan_callback = callback
        self._is_scanning = True
        
        logger.info("🔄 启动自动扫描")
        logger.info(f"   周期: {self.timeframe}")
        logger.info(f"   K线类型: {self.kline_type} ({'已完成' if self.kline_type == 'closed' else '进行中'})")
        logger.info(f"   对准K线: {'是' if align_to_kline else '否'}")
        
        # 创建并启动扫描任务
        self._auto_scan_task = asyncio.create_task(
            self._auto_scan_loop(align_to_kline, wait_for_close)
        )
    
    async def stop_auto_scan(self):
        """停止自动扫描"""
        if not self._is_scanning:
            logger.warning("自动扫描未运行")
            return
        
        logger.info("⏹️  停止自动扫描")
        self._is_scanning = False
        
        if self._auto_scan_task:
            self._auto_scan_task.cancel()
            try:
                await self._auto_scan_task
            except asyncio.CancelledError:
                pass
            self._auto_scan_task = None
    
    async def _auto_scan_loop(self, align_to_kline: bool, wait_for_close: bool):
        """
        自动扫描循环
        
        Args:
            align_to_kline: 是否对准K线周期
            wait_for_close: 是否等待K线完成
        """
        try:
            # 循环扫描
            while self._is_scanning:
                try:
                    # 记录扫描时间
                    scan_time = now_shanghai()
                    logger.info("="*60)
                    logger.info(f"📊 开始扫描 - {format_time(scan_time)}")
                    
                    # 执行扫描
                    symbols = await self.scan_symbols()
                    
                    # 调用回调函数（传入 scanner 实例）
                    if self._scan_callback:
                        try:
                            # 检查回调函数是否是协程函数
                            if asyncio.iscoroutinefunction(self._scan_callback):
                                await self._scan_callback(self, symbols, self.tickers)
                            else:
                                # 同步回调函数，直接调用
                                result = self._scan_callback(self, symbols, self.tickers)
                                # 如果返回的是协程对象，需要await
                                if asyncio.iscoroutine(result):
                                    await result
                        except Exception as e:
                            logger.error(f"回调函数执行失败: {e}", exc_info=True)
                    
                    logger.info(f"✅ 扫描完成 - 找到 {len(symbols)} 个交易对")
                    
                    # 等待下一根K线（如果启用了K线对准）
                    if align_to_kline:
                        await self._wait_for_next_kline(wait_for_close=wait_for_close and self.kline_type == 'closed')
                    else:
                        # 不对准K线，只是简单等待一段时间
                        logger.info("⏰ 等待 60 秒后进行下次扫描...")
                        await asyncio.sleep(60)
                
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"扫描失败: {e}", exc_info=True)
                    # 发生错误时等待一段时间再重试
                    logger.info("等待 30 秒后重试...")
                    await asyncio.sleep(30)
        
        except asyncio.CancelledError:
            logger.info("自动扫描已取消")
        finally:
            self._is_scanning = False
    
    async def _wait_for_next_kline(self, wait_for_close: bool = True):
        """
        等待下一根K线
        
        Args:
            wait_for_close: 是否等待K线完成（True=等待完成，False=等待开始）
        """
        now = now_shanghai()
        
        # 计算等待时间（timedelta对象）
        time_delta = time_until_next_kline(self.timeframe, now)
        wait_seconds = time_delta.total_seconds()
        
        if wait_for_close:
            # 等待当前K线完成
            target_time = now + time_delta
            action = "完成"
        else:
            # 已经对准了，等待下一根K线开始
            target_time = now + time_delta
            action = "开始"
        
        if wait_seconds > 0:
            logger.info(f"⏰ 等待 {wait_seconds:.0f} 秒，直到下一根 {self.timeframe} K线{action}...")
            logger.info(f"   当前时间: {format_time(now)}")
            logger.info(f"   目标时间: {format_time(target_time)}")
            
            # 分段等待，每10秒显示一次进度
            remaining = wait_seconds
            while remaining > 0 and self._is_scanning:
                wait = min(10, remaining)
                await asyncio.sleep(wait)
                remaining -= wait
                if remaining > 0 and remaining % 30 == 0:  # 每30秒提醒一次
                    logger.info(f"   剩余等待时间: {remaining:.0f} 秒")
        
        logger.info(f"🎯 K线已{action}")
    
    @property
    def is_scanning(self) -> bool:
        """是否正在自动扫描"""
        return self._is_scanning
    
    async def get_hot_symbols(self, top_n: Optional[int] = None, quote: Optional[str] = None) -> List[Dict]:
        """
        获取热门交易对（综合成交量和涨跌幅）
        
        Args:
            top_n: 返回前N个（默认使用配置的 hot_top_n）
            quote: 报价货币筛选（默认使用配置的 default_quote）
        
        Returns:
            热门交易对列表
        """
        top_n = top_n or self.hot_top_n
        quote = quote or self.default_quote
        if not self.platform:
            raise RuntimeError("未连接到交易所")
        
        # 获取所有24小时行情
        tickers = await self.platform.get_all_tickers_24h()
        
        # 过滤报价货币
        if quote:
            tickers = [t for t in tickers if SymbolParser.get_quote(t["symbol"]) == quote.upper()]
        
        # 计算热度分数并排序
        for ticker in tickers:
            volume = ticker.get('volume', 0)
            price_change = abs(ticker.get('price_change_percent', 0))
            volume_score = volume / 1e9 if volume > 0 else 0
            change_score = price_change / 100
            ticker['hot_score'] = volume_score * 0.7 + change_score * 0.3
        
        sorted_tickers = sorted(tickers, key=lambda x: x.get('hot_score', 0), reverse=True)
        return sorted_tickers[:top_n]
    
    async def get_top_gainers(self, top_n: Optional[int] = None, quote: Optional[str] = None) -> List[Dict]:
        """
        获取涨幅榜
        
        Args:
            top_n: 返回前N个（默认使用配置的 gainers_top_n）
            quote: 报价货币筛选（默认使用配置的 default_quote）
        
        Returns:
            涨幅榜列表
        """
        top_n = top_n or self.gainers_top_n
        quote = quote or self.default_quote
        if not self.platform:
            raise RuntimeError("未连接到交易所")
        
        tickers = await self.platform.get_all_tickers_24h()
        
        # 过滤报价货币
        if quote:
            tickers = [t for t in tickers if SymbolParser.get_quote(t["symbol"]) == quote.upper()]
        
        # 按涨幅排序
        sorted_tickers = sorted(tickers, key=lambda x: x.get('price_change_percent', 0), reverse=True)
        return sorted_tickers[:top_n]
    
    async def get_top_losers(self, top_n: Optional[int] = None, quote: Optional[str] = None) -> List[Dict]:
        """
        获取跌幅榜
        
        Args:
            top_n: 返回前N个（默认使用配置的 losers_top_n）
            quote: 报价货币筛选（默认使用配置的 default_quote）
        
        Returns:
            跌幅榜列表
        """
        top_n = top_n or self.losers_top_n
        quote = quote or self.default_quote
        if not self.platform:
            raise RuntimeError("未连接到交易所")
        
        tickers = await self.platform.get_all_tickers_24h()
        
        # 过滤报价货币
        if quote:
            tickers = [t for t in tickers if SymbolParser.get_quote(t["symbol"]) == quote.upper()]
        
        # 按跌幅排序
        sorted_tickers = sorted(tickers, key=lambda x: x.get('price_change_percent', 0), reverse=False)
        return sorted_tickers[:top_n]
    
    async def get_top_volume(self, top_n: Optional[int] = None, quote: Optional[str] = None) -> List[Dict]:
        """
        获取成交量排行
        
        Args:
            top_n: 返回前N个（默认使用配置的 volume_24h_top_n）
            quote: 报价货币筛选（默认使用配置的 default_quote）
        
        Returns:
            成交量排行列表
        """
        top_n = top_n or self.volume_24h_top_n
        quote = quote or self.default_quote
        if not self.platform:
            raise RuntimeError("未连接到交易所")
        
        tickers = await self.platform.get_all_tickers_24h()
        
        # 过滤报价货币
        if quote:
            tickers = [t for t in tickers if SymbolParser.get_quote(t["symbol"]) == quote.upper()]
        
        # 按成交量排序
        sorted_tickers = sorted(tickers, key=lambda x: x.get('volume', 0), reverse=True)
        return sorted_tickers[:top_n]
    
    async def custom_scan(
        self,
        quote: Optional[str] = None,
        min_volume: Optional[float] = None,
        min_price: float = 0,
        max_price: float = float('inf'),
        min_change: Optional[float] = None,
        max_change: Optional[float] = None,
        bases: List[str] = None
    ) -> List[Dict]:
        """
        自定义筛选交易对
        
        Args:
            quote: 报价货币（默认使用配置的 default_quote）
            min_volume: 最小成交量（默认使用配置的 min_volume）
            min_price: 最低价格
            max_price: 最高价格
            min_change: 最小涨跌幅（%，默认使用配置的 min_change）
            max_change: 最大涨跌幅（%，默认使用配置的 max_change）
            bases: 指定基础货币列表
        
        Returns:
            符合条件的交易对列表
        
        Example:
            >>> # 查找涨幅 > 5%，成交量 > 1000万的USDT交易对
            >>> results = await scanner.custom_scan(
            ...     min_volume=10000000,
            ...     min_change=5
            ... )
        """
        if not self.platform:
            raise RuntimeError("未连接到交易所")
        
        # 使用配置的默认值
        quote = quote or self.default_quote
        min_volume = min_volume if min_volume is not None else self.min_volume
        min_change = min_change if min_change is not None else self.min_change
        max_change = max_change if max_change is not None else self.max_change
        
        tickers = await self.platform.get_all_tickers_24h()
        
        results = []
        for ticker in tickers:
            symbol = ticker["symbol"]
            
            # 解析交易对
            parsed = SymbolParser.parse(symbol)
            if not parsed:
                continue
            
            # 报价货币过滤
            if quote and parsed["quote"] != quote.upper():
                continue
            
            # 基础货币过滤
            if bases:
                bases_upper = [b.upper() for b in bases]
                if parsed["base"] not in bases_upper:
                    continue
            
            # 成交量过滤
            if ticker.get('volume', 0) < min_volume:
                continue
            
            # 价格过滤
            price = ticker.get('price', 0)
            if price < min_price or price > max_price:
                continue
            
            # 涨跌幅过滤
            change = ticker.get('price_change_percent', 0)
            if change < min_change or change > max_change:
                continue
            
            results.append(ticker)
        
        logger.info(f"自定义筛选: 找到 {len(results)} 个符合条件的交易对")
        return results
    
    async def search_symbol(self, input_str: str) -> List[str]:
        """
        智能搜索交易对
        
        Args:
            input_str: 输入（如 "btc" 或 "BTCUSDT"）
        
        Returns:
            匹配的交易对列表
        
        Example:
            >>> # 输入 btc，自动找到 BTCUSDT
            >>> symbols = await scanner.search_symbol("btc")
            ["BTCUSDT", "BTCBUSD", ...]
        """
        if not self.platform:
            raise RuntimeError("未连接到交易所")
        
        return await SymbolParser.search_from_exchange(input_str, self.platform)


async def create_scanner_from_config() -> MarketScanner:
    """
    从配置创建扫描器（便捷函数）
    
    Returns:
        配置好的扫描器实例
    """
    scanner = MarketScanner()
    await scanner.connect()
    return scanner

