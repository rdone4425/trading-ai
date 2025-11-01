"""
风险管理计算工具

功能：
1. 计算止损价格（基于 ATR）
2. 计算止盈价格（基于风险回报比）
3. 计算建议杠杆（基于风险和仓位）
4. 计算仓位大小
"""
from typing import Dict, Tuple, Optional
from tradingai.logger import get_logger

logger = get_logger(__name__)


class RiskCalculator:
    """风险管理计算器"""
    
    @staticmethod
    def calculate_stop_loss(
        entry_price: float,
        atr: float,
        atr_multiplier: float = 2.0,
        position: str = "long"
    ) -> float:
        """
        计算止损价格
        
        Args:
            entry_price: 入场价格
            atr: 平均真实波幅
            atr_multiplier: ATR 倍数
            position: 仓位方向（long/short）
        
        Returns:
            止损价格
        """
        stop_distance = atr * atr_multiplier
        
        if position.lower() in ["long", "buy", "做多"]:
            # 多单：止损在下方
            stop_loss = entry_price - stop_distance
        else:
            # 空单：止损在上方
            stop_loss = entry_price + stop_distance
        
        return max(stop_loss, 0)  # 确保不为负数
    
    @staticmethod
    def calculate_take_profit(
        entry_price: float,
        stop_loss: float,
        risk_reward_ratio: float = 2.0,
        position: str = "long"
    ) -> float:
        """
        计算止盈价格
        
        Args:
            entry_price: 入场价格
            stop_loss: 止损价格
            risk_reward_ratio: 风险回报比
            position: 仓位方向（long/short）
        
        Returns:
            止盈价格
        """
        # 计算止损距离
        stop_distance = abs(entry_price - stop_loss)
        
        # 计算止盈距离
        profit_distance = stop_distance * risk_reward_ratio
        
        if position.lower() in ["long", "buy", "做多"]:
            # 多单：止盈在上方
            take_profit = entry_price + profit_distance
        else:
            # 空单：止盈在下方
            take_profit = entry_price - profit_distance
        
        return max(take_profit, 0)  # 确保不为负数
    
    @staticmethod
    def calculate_position_size(
        account_balance: float,
        risk_percent: float,
        entry_price: float,
        stop_loss: float,
        leverage: int = 1
    ) -> float:
        """
        计算仓位大小（单位：币数量）
        
        Args:
            account_balance: 账户余额（USDT）
            risk_percent: 风险百分比（如 1.0 表示 1%）
            entry_price: 入场价格
            stop_loss: 止损价格
            leverage: 杠杆倍数
        
        Returns:
            仓位大小（币数量）
        """
        # 计算风险金额
        risk_amount = account_balance * (risk_percent / 100)
        
        # 计算止损距离（百分比）
        stop_distance_percent = abs(entry_price - stop_loss) / entry_price
        
        if stop_distance_percent == 0:
            logger.warning("止损距离为 0，无法计算仓位")
            return 0
        
        # 计算仓位价值（USDT）
        position_value = risk_amount / stop_distance_percent
        
        # 考虑杠杆，计算实际需要的保证金
        margin_required = position_value / leverage
        
        # 不能超过账户余额
        if margin_required > account_balance:
            logger.warning(f"所需保证金 {margin_required:.2f} 超过账户余额，调整为最大可用")
            margin_required = account_balance
            position_value = margin_required * leverage
        
        # 计算币数量
        position_size = position_value / entry_price
        
        return position_size
    
    @staticmethod
    def calculate_leverage(
        account_balance: float,
        risk_percent: float,
        entry_price: float,
        stop_loss: float,
        max_leverage: int = 10
    ) -> int:
        """
        计算建议杠杆
        
        Args:
            account_balance: 账户余额（USDT）
            risk_percent: 风险百分比
            entry_price: 入场价格
            stop_loss: 止损价格
            max_leverage: 最大杠杆
        
        Returns:
            建议杠杆倍数
        """
        # 计算止损距离（百分比）
        stop_distance_percent = abs(entry_price - stop_loss) / entry_price
        
        if stop_distance_percent == 0:
            return 1
        
        # 根据止损距离和风险百分比计算建议杠杆
        # 公式：杠杆 = 100 / (止损距离% * 100 / 风险%)
        leverage = risk_percent / (stop_distance_percent * 100)
        
        # 限制在 1 到 max_leverage 之间
        leverage = max(1, min(int(leverage), max_leverage))
        
        return leverage
    
    @staticmethod
    def calculate_risk_metrics(
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        account_balance: float,
        risk_percent: float,
        leverage: int = 1
    ) -> Dict[str, float]:
        """
        计算风险指标
        
        Args:
            entry_price: 入场价格
            stop_loss: 止损价格
            take_profit: 止盈价格
            account_balance: 账户余额
            risk_percent: 风险百分比
            leverage: 杠杆倍数
        
        Returns:
            风险指标字典
        """
        # 计算距离（百分比）
        stop_distance_percent = abs(entry_price - stop_loss) / entry_price * 100
        profit_distance_percent = abs(take_profit - entry_price) / entry_price * 100
        
        # 计算风险回报比
        risk_reward = profit_distance_percent / stop_distance_percent if stop_distance_percent > 0 else 0
        
        # 计算仓位大小
        position_size = RiskCalculator.calculate_position_size(
            account_balance, risk_percent, entry_price, stop_loss, leverage
        )
        
        # 计算仓位价值
        position_value = position_size * entry_price
        
        # 计算保证金
        margin = position_value / leverage
        
        # 计算潜在盈亏
        potential_loss = position_size * abs(entry_price - stop_loss)
        potential_profit = position_size * abs(take_profit - entry_price)
        
        return {
            "stop_distance_percent": stop_distance_percent,
            "profit_distance_percent": profit_distance_percent,
            "risk_reward_ratio": risk_reward,
            "position_size": position_size,
            "position_value": position_value,
            "margin_required": margin,
            "potential_loss": potential_loss,
            "potential_profit": potential_profit,
            "loss_percent": (potential_loss / account_balance) * 100,
            "profit_percent": (potential_profit / account_balance) * 100,
        }
    
    @staticmethod
    def format_risk_report(
        symbol: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        leverage: int,
        metrics: Dict[str, float]
    ) -> str:
        """
        格式化风险报告
        
        Returns:
            格式化的风险报告字符串
        """
        report = f"""
╔══════════════════════════════════════════════════════════╗
║  风险管理报告 - {symbol}
╠══════════════════════════════════════════════════════════╣
║  入场价格: {entry_price:.8f} USDT
║  止损价格: {stop_loss:.8f} USDT ({metrics['stop_distance_percent']:.2f}%)
║  止盈价格: {take_profit:.8f} USDT ({metrics['profit_distance_percent']:.2f}%)
║  风险回报比: 1:{metrics['risk_reward_ratio']:.2f}
╠══════════════════════════════════════════════════════════╣
║  杠杆倍数: {leverage}x
║  仓位大小: {metrics['position_size']:.4f} 币
║  仓位价值: {metrics['position_value']:.2f} USDT
║  保证金: {metrics['margin_required']:.2f} USDT
╠══════════════════════════════════════════════════════════╣
║  潜在亏损: {metrics['potential_loss']:.2f} USDT ({metrics['loss_percent']:.2f}%)
║  潜在盈利: {metrics['potential_profit']:.2f} USDT ({metrics['profit_percent']:.2f}%)
╚══════════════════════════════════════════════════════════╝
"""
        return report

