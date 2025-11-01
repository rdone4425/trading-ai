"""
技术指标计算器
支持 TA-Lib 和纯 Python 实现
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False

from ..logger import get_logger

logger = get_logger("indicators")


class IndicatorCalculator:
    """技术指标计算器"""
    
    def __init__(self):
        if not TALIB_AVAILABLE:
            logger.info("ℹ️  TA-Lib 未安装，使用纯 Python 实现")
            logger.info("   安装 TA-Lib 可获得更好的性能")
    
    @staticmethod
    def is_available() -> bool:
        """检查计算器是否可用（总是返回 True）"""
        return True  # 现在总是可用，因为有纯 Python 后备
    
    @staticmethod
    def using_talib() -> bool:
        """检查是否使用 TA-Lib"""
        return TALIB_AVAILABLE
    
    @staticmethod
    def klines_to_dataframe(klines: List[Dict]) -> pd.DataFrame:
        """
        将K线数据转换为 DataFrame
        
        Args:
            klines: K线列表
        
        Returns:
            DataFrame
        """
        df = pd.DataFrame(klines)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
        return df
    
    @staticmethod
    def calculate_ma(klines: List[Dict], period: int = 20) -> Optional[np.ndarray]:
        """
        计算移动平均线 (MA)
        
        Args:
            klines: K线数据
            period: 周期
        
        Returns:
            MA 值数组
        """
        close = np.array([k['close'] for k in klines])
        
        if TALIB_AVAILABLE:
            return talib.SMA(close, timeperiod=period)
        else:
            # 纯 Python 实现
            return pd.Series(close).rolling(window=period).mean().values
    
    @staticmethod
    def calculate_ema(klines: List[Dict], period: int = 20) -> Optional[np.ndarray]:
        """
        计算指数移动平均线 (EMA)
        
        Args:
            klines: K线数据
            period: 周期
        
        Returns:
            EMA 值数组
        """
        close = np.array([k['close'] for k in klines])
        
        if TALIB_AVAILABLE:
            return talib.EMA(close, timeperiod=period)
        else:
            # 纯 Python 实现
            return pd.Series(close).ewm(span=period, adjust=False).mean().values
    
    @staticmethod
    def calculate_rsi(klines: List[Dict], period: int = 14) -> Optional[np.ndarray]:
        """
        计算相对强弱指标 (RSI)
        
        Args:
            klines: K线数据
            period: 周期
        
        Returns:
            RSI 值数组
        """
        close = np.array([k['close'] for k in klines])
        
        if TALIB_AVAILABLE:
            return talib.RSI(close, timeperiod=period)
        else:
            # 纯 Python 实现
            delta = pd.Series(close).diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.values
    
    @staticmethod
    def calculate_macd(klines: List[Dict], 
                      fastperiod: int = 12, 
                      slowperiod: int = 26, 
                      signalperiod: int = 9) -> Optional[tuple]:
        """
        计算 MACD 指标
        
        Args:
            klines: K线数据
            fastperiod: 快线周期
            slowperiod: 慢线周期
            signalperiod: 信号线周期
        
        Returns:
            (macd, signal, hist) 元组
        """
        close = np.array([k['close'] for k in klines])
        
        if TALIB_AVAILABLE:
            macd, signal, hist = talib.MACD(close, 
                                            fastperiod=fastperiod, 
                                            slowperiod=slowperiod, 
                                            signalperiod=signalperiod)
            return macd, signal, hist
        else:
            # 纯 Python 实现
            close_series = pd.Series(close)
            ema_fast = close_series.ewm(span=fastperiod, adjust=False).mean()
            ema_slow = close_series.ewm(span=slowperiod, adjust=False).mean()
            macd = ema_fast - ema_slow
            signal = macd.ewm(span=signalperiod, adjust=False).mean()
            hist = macd - signal
            return macd.values, signal.values, hist.values
    
    @staticmethod
    def calculate_bollinger_bands(klines: List[Dict], 
                                  period: int = 20, 
                                  nbdevup: int = 2, 
                                  nbdevdn: int = 2) -> Optional[tuple]:
        """
        计算布林带 (Bollinger Bands)
        
        Args:
            klines: K线数据
            period: 周期
            nbdevup: 上轨标准差倍数
            nbdevdn: 下轨标准差倍数
        
        Returns:
            (upper, middle, lower) 元组
        """
        close = np.array([k['close'] for k in klines])
        
        if TALIB_AVAILABLE:
            upper, middle, lower = talib.BBANDS(close, 
                                               timeperiod=period, 
                                               nbdevup=nbdevup, 
                                               nbdevdn=nbdevdn)
            return upper, middle, lower
        else:
            # 纯 Python 实现
            close_series = pd.Series(close)
            middle = close_series.rolling(window=period).mean()
            std = close_series.rolling(window=period).std()
            upper = middle + (std * nbdevup)
            lower = middle - (std * nbdevdn)
            return upper.values, middle.values, lower.values
    
    @staticmethod
    def calculate_kdj(klines: List[Dict], 
                     fastk_period: int = 9, 
                     slowk_period: int = 3, 
                     slowd_period: int = 3) -> Optional[tuple]:
        """
        计算 KDJ 指标
        
        Args:
            klines: K线数据
            fastk_period: FastK 周期
            slowk_period: SlowK 周期
            slowd_period: SlowD 周期
        
        Returns:
            (k, d, j) 元组
        """
        high = np.array([k['high'] for k in klines])
        low = np.array([k['low'] for k in klines])
        close = np.array([k['close'] for k in klines])
        
        if TALIB_AVAILABLE:
            k, d = talib.STOCH(high, low, close, 
                              fastk_period=fastk_period, 
                              slowk_period=slowk_period, 
                              slowd_period=slowd_period)
            j = 3 * k - 2 * d
            return k, d, j
        else:
            # 纯 Python 实现
            high_series = pd.Series(high)
            low_series = pd.Series(low)
            close_series = pd.Series(close)
            
            # RSV (Raw Stochastic Value)
            lowest_low = low_series.rolling(window=fastk_period).min()
            highest_high = high_series.rolling(window=fastk_period).max()
            rsv = (close_series - lowest_low) / (highest_high - lowest_low) * 100
            
            # K值 (SlowK)
            k = rsv.ewm(alpha=1/slowk_period, adjust=False).mean()
            
            # D值 (SlowD)
            d = k.ewm(alpha=1/slowd_period, adjust=False).mean()
            
            # J值
            j = 3 * k - 2 * d
            
            return k.values, d.values, j.values
    
    @staticmethod
    def calculate_atr(klines: List[Dict], period: int = 14) -> Optional[np.ndarray]:
        """
        计算平均真实波幅 (ATR)
        
        Args:
            klines: K线数据
            period: 周期
        
        Returns:
            ATR 值数组
        """
        high = np.array([k['high'] for k in klines])
        low = np.array([k['low'] for k in klines])
        close = np.array([k['close'] for k in klines])
        
        if TALIB_AVAILABLE:
            return talib.ATR(high, low, close, timeperiod=period)
        else:
            # 纯 Python 实现
            high_series = pd.Series(high)
            low_series = pd.Series(low)
            close_series = pd.Series(close)
            
            tr1 = high_series - low_series
            tr2 = abs(high_series - close_series.shift())
            tr3 = abs(low_series - close_series.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()
            return atr.values
    
    @staticmethod
    def calculate_all(klines: List[Dict]) -> Dict:
        """
        计算所有常用指标
        
        Args:
            klines: K线数据
        
        Returns:
            包含所有指标的字典
        """
        if not TALIB_AVAILABLE:
            logger.error("TA-Lib 未安装")
            return {}
        
        if len(klines) < 50:
            logger.warning(f"K线数量不足 ({len(klines)})，建议至少50根")
        
        indicators = {}
        
        try:
            # 移动平均线
            indicators['ma5'] = IndicatorCalculator.calculate_ma(klines, 5)
            indicators['ma10'] = IndicatorCalculator.calculate_ma(klines, 10)
            indicators['ma20'] = IndicatorCalculator.calculate_ma(klines, 20)
            indicators['ma60'] = IndicatorCalculator.calculate_ma(klines, 60)
            
            # EMA
            indicators['ema12'] = IndicatorCalculator.calculate_ema(klines, 12)
            indicators['ema26'] = IndicatorCalculator.calculate_ema(klines, 26)
            
            # RSI
            indicators['rsi'] = IndicatorCalculator.calculate_rsi(klines, 14)
            
            # MACD
            macd, signal, hist = IndicatorCalculator.calculate_macd(klines)
            indicators['macd'] = macd
            indicators['macd_signal'] = signal
            indicators['macd_hist'] = hist
            
            # 布林带
            upper, middle, lower = IndicatorCalculator.calculate_bollinger_bands(klines)
            indicators['bb_upper'] = upper
            indicators['bb_middle'] = middle
            indicators['bb_lower'] = lower
            
            # KDJ
            k, d, j = IndicatorCalculator.calculate_kdj(klines)
            indicators['kdj_k'] = k
            indicators['kdj_d'] = d
            indicators['kdj_j'] = j
            
            # ATR
            indicators['atr'] = IndicatorCalculator.calculate_atr(klines)
            
            logger.info(f"✅ 计算完成 {len(indicators)} 个指标")
            
        except Exception as e:
            logger.error(f"计算指标失败: {e}")
        
        return indicators
    
    @staticmethod
    def get_latest_values(klines: List[Dict]) -> Dict:
        """
        获取最新的指标值（用于实时判断）
        
        Args:
            klines: K线数据
        
        Returns:
            最新指标值字典
        """
        if not TALIB_AVAILABLE:
            return {}
        
        indicators = IndicatorCalculator.calculate_all(klines)
        
        latest = {}
        for key, values in indicators.items():
            if values is not None and len(values) > 0:
                # 获取最后一个非 NaN 值
                valid_values = values[~np.isnan(values)]
                if len(valid_values) > 0:
                    latest[key] = float(valid_values[-1])
        
        return latest

