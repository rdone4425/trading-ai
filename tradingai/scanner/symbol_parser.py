"""
交易对解析工具 - 通用于所有交易所
"""
from typing import Dict, Optional, List, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from ..exchange.platform.base import BasePlatform


class SymbolParser:
    """交易对解析器"""
    
    # 常见的报价货币
    QUOTE_CURRENCIES = [
        'USDT', 'USDC', 'BUSD', 'USD', 'TUSD',  # 稳定币
        'BTC', 'ETH', 'BNB',                      # 主流币
        'EUR', 'GBP', 'JPY', 'CNY'                # 法币
    ]
    
    # 交易对分隔符（不同交易所）
    SEPARATORS = ['/', '-', '_', '']
    
    @classmethod
    def parse(cls, symbol: str, exchange: str = "binance") -> Optional[Dict]:
        """
        解析交易对
        
        Args:
            symbol: 交易对符号，如 "BTCUSDT", "BTC/USDT", "BTC-USDT"
            exchange: 交易所名称
        
        Returns:
            解析结果字典：
            {
                "symbol": "BTCUSDT",         # 原始符号
                "base": "BTC",               # 基础货币
                "quote": "USDT",             # 报价货币
                "formatted": "BTC/USDT",     # 格式化显示
                "exchange": "binance"        # 交易所
            }
        """
        if not symbol:
            return None
        
        original_symbol = symbol
        symbol = symbol.upper().strip()
        
        # 尝试不同的解析方法
        result = cls._parse_with_separator(symbol)
        
        if not result:
            result = cls._parse_without_separator(symbol)
        
        if result:
            result["symbol"] = original_symbol  # 保留原始符号
            result["formatted"] = f"{result['base']}/{result['quote']}"
            result["exchange"] = exchange.lower()
            return result
        
        return None
    
    
    @classmethod
    def _parse_with_separator(cls, symbol: str) -> Optional[Dict]:
        """解析带分隔符的交易对"""
        for sep in ['/', '-', '_']:
            if sep in symbol:
                parts = symbol.split(sep)
                if len(parts) == 2:
                    base, quote = parts
                    return {"base": base, "quote": quote}
        return None
    
    @classmethod
    def _parse_without_separator(cls, symbol: str) -> Optional[Dict]:
        """解析无分隔符的交易对（如 BTCUSDT）"""
        # 尝试匹配常见的报价货币
        for quote in cls.QUOTE_CURRENCIES:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                if base:  # 确保基础货币不为空
                    return {"base": base, "quote": quote}
        
        return None
    
    @classmethod
    def normalize(cls, symbol: str, format_type: str = "binance") -> str:
        """
        标准化交易对格式
        
        Args:
            symbol: 原始交易对
            format_type: 目标格式类型
                - "binance": BTCUSDT
                - "standard": BTC/USDT
                - "okx": BTC-USDT
                - "hyphen": BTC-USDT
                - "underscore": BTC_USDT
        
        Returns:
            标准化后的交易对
        """
        parsed = cls.parse(symbol)
        if not parsed:
            return symbol
        
        base = parsed["base"]
        quote = parsed["quote"]
        
        formats = {
            "binance": f"{base}{quote}",
            "standard": f"{base}/{quote}",
            "okx": f"{base}-{quote}",
            "hyphen": f"{base}-{quote}",
            "underscore": f"{base}_{quote}",
        }
        
        return formats.get(format_type, f"{base}/{quote}")
    
    @classmethod
    def get_base(cls, symbol: str) -> Optional[str]:
        """获取基础货币"""
        parsed = cls.parse(symbol)
        return parsed["base"] if parsed else None
    
    @classmethod
    def get_quote(cls, symbol: str) -> Optional[str]:
        """获取报价货币"""
        parsed = cls.parse(symbol)
        return parsed["quote"] if parsed else None
    
    @classmethod
    def is_usdt_pair(cls, symbol: str) -> bool:
        """判断是否为USDT交易对"""
        quote = cls.get_quote(symbol)
        return quote in ['USDT', 'USDC', 'BUSD']
    
    @classmethod
    def is_btc_pair(cls, symbol: str) -> bool:
        """判断是否为BTC交易对"""
        return cls.get_quote(symbol) == 'BTC'
    
    @classmethod
    def filter_by_quote(cls, symbols: List[str], quote_currency: str = "USDT") -> List[str]:
        """
        按报价货币过滤交易对
        
        Args:
            symbols: 交易对列表
            quote_currency: 报价货币
        
        Returns:
            过滤后的交易对列表
        """
        quote_currency = quote_currency.upper()
        return [s for s in symbols if cls.get_quote(s) == quote_currency]
    
    @classmethod
    def group_by_base(cls, symbols: List[str]) -> Dict[str, List[str]]:
        """
        按基础货币分组
        
        Args:
            symbols: 交易对列表
        
        Returns:
            {基础货币: [交易对列表]}
        """
        groups = {}
        for symbol in symbols:
            base = cls.get_base(symbol)
            if base:
                if base not in groups:
                    groups[base] = []
                groups[base].append(symbol)
        return groups
    
    @classmethod
    def group_by_quote(cls, symbols: List[str]) -> Dict[str, List[str]]:
        """
        按报价货币分组
        
        Args:
            symbols: 交易对列表
        
        Returns:
            {报价货币: [交易对列表]}
        """
        groups = {}
        for symbol in symbols:
            quote = cls.get_quote(symbol)
            if quote:
                if quote not in groups:
                    groups[quote] = []
                groups[quote].append(symbol)
        return groups
    
    @classmethod
    def convert_exchange_format(cls, symbol: str, from_exchange: str, to_exchange: str) -> str:
        """
        转换不同交易所的格式
        
        Args:
            symbol: 原始交易对
            from_exchange: 源交易所
            to_exchange: 目标交易所
        
        Returns:
            转换后的交易对
        """
        # 先解析
        parsed = cls.parse(symbol, from_exchange)
        if not parsed:
            return symbol
        
        # 根据目标交易所格式化
        exchange_formats = {
            "binance": "binance",
            "okx": "hyphen",
            "bybit": "binance",
            "huobi": "binance",
            "kraken": "standard"
        }
        
        format_type = exchange_formats.get(to_exchange.lower(), "standard")
        return cls.normalize(symbol, format_type)
    
    @classmethod
    def validate(cls, symbol: str) -> bool:
        """
        验证交易对格式是否有效
        
        Args:
            symbol: 交易对
        
        Returns:
            是否有效
        """
        parsed = cls.parse(symbol)
        return parsed is not None
    
    @classmethod
    def batch_parse(cls, symbols: List[str], exchange: str = "binance") -> List[Dict]:
        """
        批量解析交易对
        
        Args:
            symbols: 交易对列表
            exchange: 交易所名称
        
        Returns:
            解析结果列表
        """
        results = []
        for symbol in symbols:
            parsed = cls.parse(symbol, exchange)
            if parsed:
                results.append(parsed)
        return results
    
    @classmethod
    def get_stats(cls, symbols: List[str]) -> Dict:
        """
        获取交易对统计信息
        
        Args:
            symbols: 交易对列表
        
        Returns:
            统计信息
        """
        by_quote = cls.group_by_quote(symbols)
        by_base = cls.group_by_base(symbols)
        
        return {
            "total": len(symbols),
            "unique_bases": len(by_base),
            "unique_quotes": len(by_quote),
            "quote_distribution": {k: len(v) for k, v in by_quote.items()},
            "top_bases": sorted(by_base.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        }
    
    @classmethod
    def is_single_currency(cls, input_str: str) -> bool:
        """
        判断输入是否为单个货币（不是交易对）
        
        Args:
            input_str: 输入字符串
        
        Returns:
            是否为单个货币
        """
        return cls.parse(input_str) is None
    
    @classmethod
    def search_by_currency(cls, currency: str, symbols: List[str], position: str = "both") -> List[str]:
        """
        搜索包含指定货币的交易对
        
        Args:
            currency: 货币代码，如 "BTC", "btc"
            symbols: 交易对列表
            position: 搜索位置
                - "base": 只搜索基础货币
                - "quote": 只搜索报价货币
                - "both": 搜索两者（默认）
        
        Returns:
            匹配的交易对列表
        
        Example:
            >>> symbols = ["BTCUSDT", "ETHBTC", "ETHUSDT"]
            >>> SymbolParser.search_by_currency("btc", symbols)
            ["BTCUSDT", "ETHBTC"]
        """
        currency = currency.upper().strip()
        results = []
        
        for symbol in symbols:
            parsed = cls.parse(symbol)
            if not parsed:
                continue
            
            if position in ["base", "both"]:
                if parsed["base"] == currency:
                    results.append(symbol)
                    continue
            
            if position in ["quote", "both"]:
                if parsed["quote"] == currency:
                    results.append(symbol)
        
        return results
    
    @classmethod
    def smart_search(cls, input_str: str, symbols: List[str], default_quote: str = "USDT") -> List[str]:
        """
        智能搜索：如果是单个货币，自动补全为交易对
        
        Args:
            input_str: 输入字符串，如 "btc" 或 "BTCUSDT"
            symbols: 交易对列表
            default_quote: 默认报价货币
        
        Returns:
            匹配的交易对列表
        
        Example:
            >>> SymbolParser.smart_search("btc", symbols)
            ["BTCUSDT"]  # 如果只输入 btc，自动找 BTCUSDT
            
            >>> SymbolParser.smart_search("BTCUSDT", symbols)
            ["BTCUSDT"]  # 如果输入完整交易对，直接返回
        """
        input_str = input_str.upper().strip()
        
        # 先尝试作为完整交易对解析
        if cls.validate(input_str):
            # 是完整交易对，直接查找
            return [s for s in symbols if cls.normalize(s, "binance") == cls.normalize(input_str, "binance")]
        
        # 不是完整交易对，当作货币代码搜索
        # 优先返回与默认报价货币的配对
        matches = cls.search_by_currency(input_str, symbols)
        
        if not matches:
            return []
        
        # 优先返回默认报价货币的交易对
        priority_matches = []
        other_matches = []
        
        for symbol in matches:
            parsed = cls.parse(symbol)
            if parsed:
                if parsed["quote"] == default_quote and parsed["base"] == input_str:
                    priority_matches.append(symbol)
                else:
                    other_matches.append(symbol)
        
        return priority_matches + other_matches
    
    @classmethod
    def suggest_pairs(cls, currency: str, available_quotes: List[str] = None) -> List[str]:
        """
        为单个货币建议可能的交易对
        
        Args:
            currency: 货币代码
            available_quotes: 可用的报价货币列表（None则使用默认）
        
        Returns:
            建议的交易对列表
        
        Example:
            >>> SymbolParser.suggest_pairs("BTC")
            ["BTCUSDT", "BTCBUSD", "BTCUSDC"]
        """
        currency = currency.upper().strip()
        
        if available_quotes is None:
            available_quotes = ['USDT', 'USDC', 'BUSD', 'BTC', 'ETH']
        
        suggestions = []
        for quote in available_quotes:
            if currency != quote:  # 避免 BTCBTC
                suggestions.append(f"{currency}{quote}")
        
        return suggestions
    
    @classmethod
    async def search_from_exchange(cls, input_str: str, platform: 'BasePlatform', default_quote: str = "USDT") -> List[str]:
        """
        从交易所自动获取交易对并搜索
        
        Args:
            input_str: 输入字符串（可以是 "btc" 或 "BTCUSDT"）
            platform: 交易平台实例
            default_quote: 默认报价货币
        
        Returns:
            匹配的交易对列表
        
        Example:
            >>> platform = PlatformFactory.create_from_config()
            >>> await platform.connect()
            >>> results = await SymbolParser.search_from_exchange("btc", platform)
            ["BTCUSDT", "BTCBUSD", ...]
        """
        # 从交易所获取所有交易对
        symbols = await platform.get_symbols()
        
        # 使用智能搜索
        return cls.smart_search(input_str, symbols, default_quote)
    
    @classmethod
    async def get_exchange_symbols(cls, platform: 'BasePlatform', filter_quote: str = None) -> List[Dict]:
        """
        从交易所获取所有交易对并解析
        
        Args:
            platform: 交易平台实例
            filter_quote: 可选，只返回特定报价货币的交易对
        
        Returns:
            解析后的交易对列表
        
        Example:
            >>> symbols = await SymbolParser.get_exchange_symbols(platform, "USDT")
            [{"symbol": "BTCUSDT", "base": "BTC", "quote": "USDT", ...}, ...]
        """
        # 获取所有交易对
        symbols = await platform.get_symbols()
        
        # 批量解析
        parsed_symbols = cls.batch_parse(symbols)
        
        # 可选过滤
        if filter_quote:
            filter_quote = filter_quote.upper()
            parsed_symbols = [s for s in parsed_symbols if s["quote"] == filter_quote]
        
        return parsed_symbols
    
    @classmethod
    def parse_custom_symbols(cls, custom_symbols_str: str, exchange: str = "binance") -> List[str]:
        """
        解析自定义交易对字符串，返回标准化的交易对列表
        
        Args:
            custom_symbols_str: 逗号分隔的交易对字符串，如 "BTCUSDT,ETHUSDT" 或 "btc,eth"
            exchange: 交易所名称
        
        Returns:
            标准化后的交易对列表
        
        Example:
            >>> SymbolParser.parse_custom_symbols("BTCUSDT,ETHUSDT")
            ["BTCUSDT", "ETHUSDT"]
            
            >>> SymbolParser.parse_custom_symbols("btc,eth")  # 需要平台才能智能搜索
            []
        """
        if not custom_symbols_str or not custom_symbols_str.strip():
            return []
        
        symbols = []
        for symbol_str in custom_symbols_str.split(","):
            symbol_str = symbol_str.strip()
            if not symbol_str:
                continue
            
            # 尝试解析
            parsed = cls.parse(symbol_str, exchange)
            if parsed:
                # 标准化为交易所格式
                normalized = cls.normalize(symbol_str, exchange)
                symbols.append(normalized)
            else:
                # 如果解析失败，保留原始值（可能是单个货币）
                symbols.append(symbol_str.upper())
        
        return symbols

