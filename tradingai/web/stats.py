"""
交易统计模块
计算胜率、盈亏比、收益等统计数据
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class TradingStats:
    """交易统计计算器"""
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化统计计算器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.analysis_dir = self.data_dir / "analysis"
        self.trades_file = self.data_dir / "trades.json"
        
    def get_recent_analysis(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取最近的分析结果
        
        Args:
            limit: 返回数量限制
            
        Returns:
            分析结果列表
        """
        results = []
        
        if not self.analysis_dir.exists():
            return results
            
        # 获取所有分析文件
        for date_dir in sorted(self.analysis_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
                
            for file in sorted(date_dir.glob("*.json"), reverse=True):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        results.append(data)
                        
                    if len(results) >= limit:
                        return results
                except Exception as e:
                    logger.warning(f"读取分析文件失败 {file}: {e}")
                    
        return results
    
    def load_trades(self) -> List[Dict[str, Any]]:
        """
        加载交易记录
        
        Returns:
            交易记录列表
        """
        if not self.trades_file.exists():
            return []
            
        try:
            with open(self.trades_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载交易记录失败: {e}")
            return []
    
    def save_trade(self, trade: Dict[str, Any]):
        """
        保存交易记录
        
        Args:
            trade: 交易记录
        """
        trades = self.load_trades()
        trades.append(trade)
        
        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.trades_file, 'w', encoding='utf-8') as f:
                json.dump(trades, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存交易记录失败: {e}")
    
    def calculate_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        计算交易统计数据
        
        Args:
            days: 统计天数
            
        Returns:
            统计数据字典
        """
        trades = self.load_trades()
        
        # 过滤指定天数内的交易
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_trades = [
            t for t in trades 
            if datetime.fromisoformat(t.get('timestamp', '2000-01-01')) > cutoff_date
        ]
        
        total_trades = len(recent_trades)
        if total_trades == 0:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_profit': 0.0,
                'total_loss': 0.0,
                'profit_loss_ratio': 0.0,
                'avg_profit': 0.0,
                'avg_loss': 0.0,
                'net_profit': 0.0,
                'roi': 0.0
            }
        
        # 分类交易
        winning_trades = [t for t in recent_trades if t.get('profit', 0) > 0]
        losing_trades = [t for t in recent_trades if t.get('profit', 0) < 0]
        
        # 计算盈利和亏损
        total_profit = sum(t.get('profit', 0) for t in winning_trades)
        total_loss = abs(sum(t.get('profit', 0) for t in losing_trades))
        
        # 计算胜率
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        
        # 计算盈亏比
        avg_profit = total_profit / len(winning_trades) if winning_trades else 0
        avg_loss = total_loss / len(losing_trades) if losing_trades else 0
        profit_loss_ratio = avg_profit / avg_loss if avg_loss > 0 else 0
        
        # 净利润
        net_profit = total_profit - total_loss
        
        # ROI（假设初始资金1000 USDT）
        initial_capital = 1000
        roi = (net_profit / initial_capital * 100) if initial_capital > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': round(win_rate, 2),
            'total_profit': round(total_profit, 2),
            'total_loss': round(total_loss, 2),
            'profit_loss_ratio': round(profit_loss_ratio, 2),
            'avg_profit': round(avg_profit, 2),
            'avg_loss': round(avg_loss, 2),
            'net_profit': round(net_profit, 2),
            'roi': round(roi, 2),
            'period_days': days
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        获取仪表板数据
        
        Returns:
            仪表板数据
        """
        return {
            'recent_analysis': self.get_recent_analysis(limit=20),
            'stats_7d': self.calculate_stats(days=7),
            'stats_30d': self.calculate_stats(days=30),
            'all_trades': self.load_trades()[-50:]  # 最近50条交易
        }

