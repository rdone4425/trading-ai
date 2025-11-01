"""
Trading AI - 智能交易系统
"""
__version__ = "1.0.0"

from . import config
from .exchange import PlatformFactory
from .scanner import MarketScanner, SymbolParser
from .logger import get_logger
from .indicators import IndicatorCalculator
from .utils import (
    smart_format,
    format_price,
    format_percentage,
    format_volume,
    utc_to_shanghai,
    shanghai_to_utc,
    now_shanghai,
    format_time,
    time_ago,
    align_to_timeframe,
    get_kline_range,
    get_next_kline_time,
    is_kline_closed,
    time_until_next_kline
)

__all__ = [
    'config',
    'PlatformFactory', 
    'MarketScanner',
    'SymbolParser',
    'get_logger',
    'IndicatorCalculator',
    'smart_format',
    'format_price',
    'format_percentage',
    'format_volume',
    'utc_to_shanghai',
    'shanghai_to_utc',
    'now_shanghai',
    'format_time',
    'time_ago',
    'align_to_timeframe',
    'get_kline_range',
    'get_next_kline_time',
    'is_kline_closed',
    'time_until_next_kline'
]

