"""
市场数据过滤器
"""
from typing import List, Dict, Optional
from ..logger import get_logger

logger = get_logger("scanner.filters")


class MarketFilters:
    """市场数据过滤器"""
    
    @staticmethod
    def by_volume_24h(market_data: List[Dict], top_n: int = 20) -> List[Dict]:
        """
        按24小时成交量排序
        
        Args:
            market_data: 市场数据列表
            top_n: 返回前N个
        
        Returns:
            排序后的数据
        """
        sorted_data = sorted(
            market_data,
            key=lambda x: float(x.get('volume', 0)),
            reverse=True
        )
        
        result = sorted_data[:top_n]
        logger.info(f"📊 按成交量筛选: 前 {top_n} 个")
        
        return result
    
    @staticmethod
    def by_price_change(market_data: List[Dict], top_n: int = 20, direction: str = "gainers") -> List[Dict]:
        """
        按涨跌幅排序
        
        Args:
            market_data: 市场数据列表
            top_n: 返回前N个
            direction: "gainers"(涨幅榜) 或 "losers"(跌幅榜)
        
        Returns:
            排序后的数据
        """
        sorted_data = sorted(
            market_data,
            key=lambda x: float(x.get('price_change_percent', 0)),
            reverse=(direction == "gainers")
        )
        
        result = sorted_data[:top_n]
        
        if direction == "gainers":
            logger.info(f"📈 涨幅榜: 前 {top_n} 个")
        else:
            logger.info(f"📉 跌幅榜: 前 {top_n} 个")
        
        return result
    
    @staticmethod
    def by_hot_symbols(market_data: List[Dict], top_n: int = 20) -> List[Dict]:
        """
        按热门程度排序（综合成交量和涨跌幅）
        
        Args:
            market_data: 市场数据列表
            top_n: 返回前N个
        
        Returns:
            排序后的数据
        """
        # 计算热度分数：成交量权重70% + 涨跌幅绝对值权重30%
        for item in market_data:
            volume = float(item.get('volume', 0))
            price_change = abs(float(item.get('price_change_percent', 0)))
            
            # 归一化处理
            volume_score = volume / 1e9  # 假设成交量以亿为单位
            change_score = price_change / 100  # 涨跌幅百分比
            
            # 综合分数
            item['hot_score'] = volume_score * 0.7 + change_score * 0.3
        
        sorted_data = sorted(
            market_data,
            key=lambda x: x.get('hot_score', 0),
            reverse=True
        )
        
        result = sorted_data[:top_n]
        logger.info(f"🔥 热门榜: 前 {top_n} 个")
        
        return result
    
    @staticmethod
    def filter_by_volume_threshold(market_data: List[Dict], min_volume: float) -> List[Dict]:
        """
        过滤低成交量交易对
        
        Args:
            market_data: 市场数据列表
            min_volume: 最小成交量
        
        Returns:
            过滤后的数据
        """
        result = [
            item for item in market_data
            if float(item.get('volume', 0)) >= min_volume
        ]
        
        logger.info(f"🔍 成交量过滤: {len(market_data)} -> {len(result)} 个")
        return result
    
    @staticmethod
    def filter_by_price_range(market_data: List[Dict], min_price: float = 0, max_price: float = float('inf')) -> List[Dict]:
        """
        按价格范围过滤
        
        Args:
            market_data: 市场数据列表
            min_price: 最低价格
            max_price: 最高价格
        
        Returns:
            过滤后的数据
        """
        result = [
            item for item in market_data
            if min_price <= float(item.get('price', 0)) <= max_price
        ]
        
        logger.info(f"💰 价格过滤 [{min_price}-{max_price}]: {len(result)} 个")
        return result
    
    @staticmethod
    def get_summary(market_data: List[Dict]) -> Dict:
        """
        获取市场数据摘要
        
        Args:
            market_data: 市场数据列表
        
        Returns:
            摘要信息
        """
        if not market_data:
            return {}
        
        volumes = [float(item.get('volume', 0)) for item in market_data]
        changes = [float(item.get('price_change_percent', 0)) for item in market_data]
        
        summary = {
            "total": len(market_data),
            "avg_volume": sum(volumes) / len(volumes),
            "max_volume": max(volumes),
            "min_volume": min(volumes),
            "avg_change": sum(changes) / len(changes),
            "max_gainer": max(changes),
            "max_loser": min(changes),
            "gainers_count": sum(1 for c in changes if c > 0),
            "losers_count": sum(1 for c in changes if c < 0)
        }
        
        return summary
    
    @staticmethod
    def print_top_list(market_data: List[Dict], title: str = "排行榜", limit: int = 10):
        """
        打印排行榜
        
        Args:
            market_data: 市场数据列表
            title: 标题
            limit: 显示数量
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"  {title}")
        logger.info(f"{'='*60}")
        
        for i, item in enumerate(market_data[:limit], 1):
            symbol = item.get('symbol', 'N/A')
            price = float(item.get('price', 0))
            change = float(item.get('price_change_percent', 0))
            volume = float(item.get('volume', 0))
            
            change_icon = "📈" if change > 0 else "📉"
            
            logger.info(
                f"{i:2d}. {symbol:12s} | "
                f"价格: {price:>10.4f} | "
                f"{change_icon} {change:>6.2f}% | "
                f"量: {volume:>12,.0f}"
            )
        
        logger.info(f"{'='*60}\n")

