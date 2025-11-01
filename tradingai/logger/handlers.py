"""
自定义日志处理器
"""
import logging
from pathlib import Path
from datetime import datetime

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent


class RotatingFileHandler(logging.FileHandler):
    """按日期轮转的文件处理器"""
    
    def __init__(self, log_dir: str = None, prefix: str = "trading"):
        if log_dir is None:
            log_dir = str(PROJECT_ROOT / "logs")
        self.log_dir = Path(log_dir)
        self.prefix = prefix
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前日志文件
        self.current_date = datetime.now().strftime('%Y%m%d')
        log_file = self.log_dir / f"{prefix}_{self.current_date}.log"
        
        super().__init__(log_file, encoding='utf-8')
    
    def emit(self, record):
        """输出日志记录"""
        # 检查日期是否变化
        today = datetime.now().strftime('%Y%m%d')
        if today != self.current_date:
            # 关闭旧文件
            self.close()
            
            # 打开新文件
            self.current_date = today
            log_file = self.log_dir / f"{self.prefix}_{self.current_date}.log"
            self.baseFilename = str(log_file)
            self.stream = self._open()
        
        super().emit(record)


class TradeLogger:
    """交易专用日志器"""
    
    def __init__(self, log_file: str = None):
        if log_file is None:
            log_file = str(PROJECT_ROOT / "logs" / "trades.log")
        
        self.logger = logging.getLogger("tradingai.trades")
        self.logger.setLevel(logging.INFO)
        
        # 确保目录存在
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # 文件处理器
        handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            '%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_signal(self, symbol: str, signal: str, price: float, confidence: float):
        """记录交易信号"""
        self.logger.info(
            f"SIGNAL | {symbol} | {signal} | Price: {price:.4f} | Confidence: {confidence:.2%}"
        )
    
    def log_order(self, symbol: str, side: str, quantity: float, price: float, order_id: str):
        """记录订单"""
        self.logger.info(
            f"ORDER | {symbol} | {side} | Qty: {quantity:.4f} | Price: {price:.4f} | ID: {order_id}"
        )
    
    def log_fill(self, symbol: str, side: str, quantity: float, price: float, pnl: float = 0):
        """记录成交"""
        self.logger.info(
            f"FILL | {symbol} | {side} | Qty: {quantity:.4f} | Price: {price:.4f} | PnL: {pnl:.2f}"
        )
    
    def log_error(self, symbol: str, error: str):
        """记录错误"""
        self.logger.error(f"ERROR | {symbol} | {error}")

