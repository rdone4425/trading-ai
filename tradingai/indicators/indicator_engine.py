"""
指标计算引擎
整合配置解析和指标计算
"""
from typing import Dict, List, Optional, Any
import numpy as np
from .calculator import IndicatorCalculator
from .config_parser import IndicatorConfigParser
from ..logger import get_logger

logger = get_logger("indicators.engine")


class IndicatorEngine:
    """
    指标计算引擎
    整合配置解析和批量指标计算
    """
    
    def __init__(self, config_string: Optional[str] = None):
        """
        初始化引擎
        
        Args:
            config_string: 配置字符串，如 "ema=20,120;ma=20,30"
        """
        self.calculator = IndicatorCalculator()
        self.config = {}
        
        if config_string:
            self.load_config(config_string)
    
    def load_config(self, config_string: str):
        """
        加载配置
        
        Args:
            config_string: 配置字符串
        """
        self.config = IndicatorConfigParser.parse_from_string(config_string)
        
        # 验证配置
        errors = IndicatorConfigParser.validate_config(self.config)
        if errors:
            logger.warning(f"配置验证发现问题: {errors}")
        
        logger.info(f"✅ 加载配置: {len(self.config)} 个指标")
    
    def load_from_env(self, prefix: str = "INDICATOR"):
        """
        从环境变量加载配置
        
        Args:
            prefix: 环境变量前缀
        """
        self.config = IndicatorConfigParser.parse_from_env(prefix)
        logger.info(f"✅ 从环境变量加载配置: {len(self.config)} 个指标")
    
    def calculate_all(self, klines: List[Dict]) -> Dict[str, Any]:
        """
        计算所有配置的指标
        
        Args:
            klines: K线数据
        
        Returns:
            指标结果字典
        """
        result = {}
        
        for indicator_name, params in self.config.items():
            try:
                # 根据指标名称调用对应的计算方法
                if indicator_name == "ma":
                    for period in params:
                        values = self.calculator.calculate_ma(klines, period)
                        if values is not None:
                            result[f"ma_{period}"] = values
                
                elif indicator_name == "ema":
                    for period in params:
                        values = self.calculator.calculate_ema(klines, period)
                        if values is not None:
                            result[f"ema_{period}"] = values
                
                elif indicator_name == "rsi":
                    period = params[0] if params else 14
                    values = self.calculator.calculate_rsi(klines, period)
                    if values is not None:
                        result["rsi"] = values
                
                elif indicator_name == "macd":
                    fast = params[0] if len(params) > 0 else 12
                    slow = params[1] if len(params) > 1 else 26
                    signal = params[2] if len(params) > 2 else 9
                    macd_result = self.calculator.calculate_macd(
                        klines, fast, slow, signal
                    )
                    if macd_result is not None:
                        macd, signal_line, hist = macd_result
                        result["macd"] = macd
                        result["macd_signal"] = signal_line
                        result["macd_hist"] = hist
                
                elif indicator_name == "bbands":
                    period = params[0] if len(params) > 0 else 20
                    nbdevup = params[1] if len(params) > 1 else 2
                    nbdevdn = params[2] if len(params) > 2 else 2
                    bbands_result = self.calculator.calculate_bollinger_bands(
                        klines, period, nbdevup, nbdevdn
                    )
                    if bbands_result is not None:
                        upper, middle, lower = bbands_result
                        result["bb_upper"] = upper
                        result["bb_middle"] = middle
                        result["bb_lower"] = lower
                
                elif indicator_name == "kdj":
                    fastk = params[0] if len(params) > 0 else 9
                    slowk = params[1] if len(params) > 1 else 3
                    slowd = params[2] if len(params) > 2 else 3
                    kdj_result = self.calculator.calculate_kdj(klines, fastk, slowk, slowd)
                    if kdj_result is not None:
                        k, d, j = kdj_result
                        result["kdj_k"] = k
                        result["kdj_d"] = d
                        result["kdj_j"] = j
                
                elif indicator_name == "atr":
                    period = params[0] if params else 14
                    values = self.calculator.calculate_atr(klines, period)
                    if values is not None:
                        result["atr"] = values
                
                else:
                    logger.warning(f"不支持的指标: {indicator_name}")
            
            except Exception as e:
                logger.error(f"计算指标 {indicator_name} 失败: {e}")
                continue
        
        logger.info(f"✅ 计算了 {len(result)} 个指标")
        return result
    
    def get_latest_values(self, klines: List[Dict], format_output: bool = False) -> Dict[str, any]:
        """
        获取最新指标值
        
        Args:
            klines: K线数据
            format_output: 是否格式化输出为字符串
        
        Returns:
            最新指标值字典（float 或格式化字符串）
        """
        indicators = self.calculate_all(klines)
        
        latest = {}
        for key, values in indicators.items():
            if values is not None and len(values) > 0:
                # 获取最后一个非 NaN 值
                valid_values = values[~np.isnan(values)]
                if len(valid_values) > 0:
                    value = float(valid_values[-1])
                    if format_output:
                        from ..utils import smart_format
                        latest[key] = smart_format(value)
                    else:
                        latest[key] = value
        
        return latest
    
    def get_indicators(self) -> List[str]:
        """
        获取所有配置的指标
        
        Returns:
            指标列表
        """
        return list(self.config.keys())
    
    def get_indicator_config(self, indicator_name: str) -> Optional[List]:
        """
        获取指标的配置参数
        
        Args:
            indicator_name: 指标名称
        
        Returns:
            参数列表
        """
        return self.config.get(indicator_name)
    
    def summary(self) -> str:
        """
        获取配置摘要
        
        Returns:
            配置摘要字符串
        """
        lines = []
        lines.append(f"指标引擎配置:")
        lines.append(f"  总指标数: {len(self.config)}")
        
        for indicator_name, params in self.config.items():
            params_str = ', '.join(str(p) for p in params)
            lines.append(f"    - {indicator_name.upper()}: {params_str}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def detect_cross(fast_line: np.ndarray, slow_line: np.ndarray) -> Dict:
        """
        检测两条线的交叉
        
        Args:
            fast_line: 快线数据
            slow_line: 慢线数据
        
        Returns:
            交叉信息 {
                "latest_cross": "golden" | "death" | None,  # 最新交叉类型
                "cross_index": int,  # 交叉位置索引
                "golden_crosses": List[int],  # 所有金叉位置
                "death_crosses": List[int]  # 所有死叉位置
            }
        """
        # 移除 NaN 值
        valid_idx = ~(np.isnan(fast_line) | np.isnan(slow_line))
        fast_valid = fast_line[valid_idx]
        slow_valid = slow_line[valid_idx]
        
        if len(fast_valid) < 2:
            return {
                "latest_cross": None,
                "cross_index": -1,
                "golden_crosses": [],
                "death_crosses": []
            }
        
        # 计算差值
        diff = fast_valid - slow_valid
        
        # 检测交叉点（符号变化）
        golden_crosses = []  # 金叉：快线上穿慢线
        death_crosses = []   # 死叉：快线下穿慢线
        
        for i in range(1, len(diff)):
            if diff[i-1] < 0 and diff[i] > 0:
                # 金叉
                golden_crosses.append(i)
            elif diff[i-1] > 0 and diff[i] < 0:
                # 死叉
                death_crosses.append(i)
        
        # 确定最新的交叉
        latest_cross = None
        cross_index = -1
        
        if golden_crosses or death_crosses:
            last_golden = golden_crosses[-1] if golden_crosses else -1
            last_death = death_crosses[-1] if death_crosses else -1
            
            if last_golden > last_death:
                latest_cross = "golden"
                cross_index = last_golden
            else:
                latest_cross = "death"
                cross_index = last_death
        
        return {
            "latest_cross": latest_cross,
            "cross_index": cross_index,
            "golden_crosses": golden_crosses,
            "death_crosses": death_crosses,
            "current_position": "above" if diff[-1] > 0 else "below"  # 当前快线位置
        }
    
    def detect_ema_cross(self, klines: List[Dict], fast_period: int, slow_period: int) -> Dict:
        """
        检测 EMA 交叉
        
        Args:
            klines: K线数据
            fast_period: 快线周期
            slow_period: 慢线周期
        
        Returns:
            交叉信息
        """
        fast_ema = self.calculator.calculate_ema(klines, fast_period)
        slow_ema = self.calculator.calculate_ema(klines, slow_period)
        
        if fast_ema is None or slow_ema is None:
            logger.error(f"计算 EMA({fast_period}) 和 EMA({slow_period}) 失败")
            return {}
        
        cross_info = self.detect_cross(fast_ema, slow_ema)
        cross_info["fast_period"] = fast_period
        cross_info["slow_period"] = slow_period
        cross_info["fast_value"] = float(fast_ema[~np.isnan(fast_ema)][-1]) if len(fast_ema[~np.isnan(fast_ema)]) > 0 else None
        cross_info["slow_value"] = float(slow_ema[~np.isnan(slow_ema)][-1]) if len(slow_ema[~np.isnan(slow_ema)]) > 0 else None
        
        return cross_info
    
    def detect_ma_cross(self, klines: List[Dict], fast_period: int, slow_period: int) -> Dict:
        """
        检测 MA 交叉
        
        Args:
            klines: K线数据
            fast_period: 快线周期
            slow_period: 慢线周期
        
        Returns:
            交叉信息
        """
        fast_ma = self.calculator.calculate_ma(klines, fast_period)
        slow_ma = self.calculator.calculate_ma(klines, slow_period)
        
        if fast_ma is None or slow_ma is None:
            logger.error(f"计算 MA({fast_period}) 和 MA({slow_period}) 失败")
            return {}
        
        cross_info = self.detect_cross(fast_ma, slow_ma)
        cross_info["fast_period"] = fast_period
        cross_info["slow_period"] = slow_period
        cross_info["fast_value"] = float(fast_ma[~np.isnan(fast_ma)][-1]) if len(fast_ma[~np.isnan(fast_ma)]) > 0 else None
        cross_info["slow_value"] = float(slow_ma[~np.isnan(slow_ma)][-1]) if len(slow_ma[~np.isnan(slow_ma)]) > 0 else None
        
        return cross_info
