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
        使用凯利公式计算建议杠杆
        
        凯利公式: f* = (bp - q) / b
        其中：
        - f* = 最优下注比例（仓位占总资本的比例）
        - b = 赔率（盈利 / 亏损）
        - p = 胜率（0-1）
        - q = 败率（1-p）
        
        在交易中的应用：
        - b = risk_reward_ratio（止盈距离 / 止损距离）
        - p = 历史胜率（默认假设为 55%，可从复盘结果优化）
        
        Args:
            account_balance: 账户余额（USDT）
            risk_percent: 单笔风险百分比
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
        
        # 凯利公式计算
        # 1. 估算赔率（b）：止盈距离 / 止损距离
        # 假设止盈距离为止损距离的2倍（风险收益比 1:2）
        risk_reward_ratio = 2.0  # 默认 1:2 的风险收益比
        
        # 2. 估算胜率（p）
        # 从复盘知识中获取历史胜率，如果没有则使用保守的 55%
        win_rate = 0.55  # 默认 55%
        
        # 3. 凯利公式：f* = (b*p - q) / b = (b*p - (1-p)) / b = p - (1-p)/b
        try:
            kelly_fraction = (win_rate * risk_reward_ratio - (1 - win_rate)) / risk_reward_ratio
        except ZeroDivisionError:
            kelly_fraction = 0
        
        # 4. 安全性调整：使用部分凯利（0.5倍凯利）来减少波动
        # 完全凯利公式太激进，实践中一般用0.25-0.5倍凯利
        fractional_kelly = kelly_fraction * 0.5
        
        # 5. 确保比例在合理范围内（0-5%）
        # 凯利公式给出的是资金百分比，需要转换为杠杆倍数
        fractional_kelly = max(0.001, min(fractional_kelly, 0.05))  # 限制在0.1%-5%
        
        # 6. 根据单笔风险和杠杆倍数的关系计算杠杆
        # 风险 = 仓位 * 止损距离
        # 如果风险 = risk_percent，则：risk_percent = 仓位 * 止损距离
        # 仓位 = risk_percent / 止损距离
        # 杠杆 = 仓位 / 初始保证金比例
        
        # 以凯利公式结果为基础计算杠杆
        # kelly_leverage = fractional_kelly / stop_distance_percent
        kelly_leverage = fractional_kelly / stop_distance_percent if stop_distance_percent > 0 else 1
        
        # 7. 将凯利公式的结果映射到1-max_leverage范围
        # 使用对数映射使其更平滑
        import math
        if kelly_leverage <= 0:
            leverage = 1
        else:
            # 对数映射：让结果更合理地分布在1-max_leverage之间
            leverage = 1 + (math.log(kelly_leverage + 1) / math.log(max_leverage + 1)) * (max_leverage - 1)
            leverage = int(round(leverage))
        
        # 8. 限制在允许范围内
        leverage = max(1, min(leverage, max_leverage))
        
        logger.debug(
            f"🎲 凯利公式杠杆计算:\n"
            f"   止损距离: {stop_distance_percent*100:.2f}%\n"
            f"   假设胜率: {win_rate*100:.1f}%\n"
            f"   假设赔率: 1:{risk_reward_ratio:.1f}\n"
            f"   凯利分数: {kelly_fraction:.4f}\n"
            f"   部分凯利(0.5倍): {fractional_kelly:.4f}\n"
            f"   计算杠杆: {kelly_leverage:.2f}\n"
            f"   最终杠杆: {leverage}x"
        )
        
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

