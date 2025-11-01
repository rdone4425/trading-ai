"""
日志系统
"""
import logging
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional
import os

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 全局变量：记录是否已经清理过日志
_logs_cleaned = False


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    # 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(
    name: str = "tradingai",
    level: str = "INFO",
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    设置日志器
    
    Args:
        name: 日志器名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径
        console: 是否输出到控制台
    
    Returns:
        配置好的日志器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 清除已有的处理器
    logger.handlers.clear()
    
    # 日志格式
    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 控制台处理器（彩色）
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = ColoredFormatter(log_format, date_format)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def cleanup_old_logs(log_dir: Path, max_hours: int = 3):
    """
    清理日志文件中超过指定时间的内容
    
    Args:
        log_dir: 日志目录
        max_hours: 保留的最大小时数
    """
    if not log_dir.exists():
        return
    
    from datetime import datetime, timedelta
    import re
    
    # 计算截止时间
    cutoff_time = datetime.now() - timedelta(hours=max_hours)
    
    # 日志时间格式：2025-11-01 14:05:40
    log_time_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')
    
    cleaned_files = 0
    total_lines_removed = 0
    
    try:
        # 遍历日志目录
        for file_path in log_dir.glob("*.log"):
            if not file_path.is_file():
                continue
            
            try:
                # 读取日志文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                if not lines:
                    continue
                
                # 过滤保留最近的日志行
                kept_lines = []
                current_log_time = None
                lines_removed = 0
                
                for line in lines:
                    # 尝试匹配时间戳
                    match = log_time_pattern.match(line)
                    if match:
                        try:
                            log_time = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                            current_log_time = log_time
                        except ValueError:
                            pass
                    
                    # 如果当前行属于最近的日志条目，保留它
                    if current_log_time and current_log_time >= cutoff_time:
                        kept_lines.append(line)
                    else:
                        lines_removed += 1
                
                # 如果有内容被删除，重写文件
                if lines_removed > 0:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(kept_lines)
                    
                    cleaned_files += 1
                    total_lines_removed += lines_removed
            
            except Exception as e:
                print(f"清理日志文件失败 {file_path}: {e}")
        
        if cleaned_files > 0:
            print(f"清理了 {cleaned_files} 个日志文件，删除了 {total_lines_removed} 行旧日志（保留最近 {max_hours} 小时）")
    
    except Exception as e:
        print(f"清理日志文件时出错: {e}")


def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    获取日志器（快捷方式）
    
    Args:
        name: 模块名称
        log_file: 日志文件路径（可选）
    
    Returns:
        日志器实例
    """
    global _logs_cleaned
    from ..config import LOG_LEVEL, LOG_DIR
    
    # 首次调用时清理旧日志
    if not _logs_cleaned:
        log_dir = PROJECT_ROOT / LOG_DIR
        log_retention_hours = int(os.getenv("LOG_RETENTION_HOURS", "3"))
        cleanup_old_logs(log_dir, log_retention_hours)
        _logs_cleaned = True
    
    # 默认日志文件
    if log_file is None:
        today = datetime.now().strftime('%Y%m%d')
        log_file = str(PROJECT_ROOT / LOG_DIR / f"trading_{today}.log")
    
    return setup_logger(
        name=f"tradingai.{name}",
        level=LOG_LEVEL,
        log_file=log_file,
        console=True
    )

