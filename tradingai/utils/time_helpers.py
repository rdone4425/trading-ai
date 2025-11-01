"""
时间处理工具
"""
from datetime import datetime, timezone, timedelta
from typing import Union, Optional
import re


# 定义时区
UTC = timezone.utc
SHANGHAI = timezone(timedelta(hours=8))  # 东八区


# K线周期单位到秒的映射
TIMEFRAME_SECONDS = {
    'm': 60,          # 分钟
    'h': 3600,        # 小时
    'd': 86400,       # 天
    'w': 604800,      # 周
    'M': 2592000,     # 月（按30天计算）
}


def utc_to_shanghai(dt: Union[datetime, int, float, str]) -> datetime:
    """
    将UTC时间转换为上海时区
    
    Args:
        dt: UTC时间，支持多种格式：
            - datetime对象
            - Unix时间戳（秒）
            - Unix时间戳（毫秒）
            - ISO格式字符串
    
    Returns:
        上海时区的datetime对象
    
    Examples:
        >>> from datetime import datetime
        >>> utc_time = datetime(2024, 11, 1, 12, 0, 0, tzinfo=UTC)
        >>> shanghai_time = utc_to_shanghai(utc_time)
        >>> print(shanghai_time)
        2024-11-01 20:00:00+08:00
        
        >>> timestamp = 1698840000
        >>> shanghai_time = utc_to_shanghai(timestamp)
    """
    # 如果是datetime对象
    if isinstance(dt, datetime):
        # 如果没有时区信息，假设是UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        # 转换到上海时区
        return dt.astimezone(SHANGHAI)
    
    # 如果是时间戳（秒或毫秒）
    elif isinstance(dt, (int, float)):
        # 判断是秒还是毫秒
        if dt > 1e10:  # 毫秒时间戳
            dt = dt / 1000
        utc_time = datetime.fromtimestamp(dt, tz=UTC)
        return utc_time.astimezone(SHANGHAI)
    
    # 如果是字符串
    elif isinstance(dt, str):
        try:
            # 尝试解析ISO格式
            utc_time = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            if utc_time.tzinfo is None:
                utc_time = utc_time.replace(tzinfo=UTC)
            return utc_time.astimezone(SHANGHAI)
        except ValueError:
            raise ValueError(f"无法解析时间字符串: {dt}")
    
    else:
        raise TypeError(f"不支持的时间类型: {type(dt)}")


def shanghai_to_utc(dt: Union[datetime, int, float]) -> datetime:
    """
    将上海时区时间转换为UTC
    
    Args:
        dt: 上海时区时间
    
    Returns:
        UTC时间的datetime对象
    """
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=SHANGHAI)
        return dt.astimezone(UTC)
    
    elif isinstance(dt, (int, float)):
        if dt > 1e10:
            dt = dt / 1000
        shanghai_time = datetime.fromtimestamp(dt, tz=SHANGHAI)
        return shanghai_time.astimezone(UTC)
    
    else:
        raise TypeError(f"不支持的时间类型: {type(dt)}")


def now_shanghai() -> datetime:
    """
    获取当前上海时区时间
    
    Returns:
        当前上海时区的datetime对象
    """
    return datetime.now(tz=SHANGHAI)


def now_utc() -> datetime:
    """
    获取当前UTC时间
    
    Returns:
        当前UTC时间的datetime对象
    """
    return datetime.now(tz=UTC)


def format_time(dt: datetime, format_type: str = "default") -> str:
    """
    格式化时间显示
    
    Args:
        dt: datetime对象
        format_type: 格式类型
            - "default": 2024-11-01 20:00:00
            - "date": 2024-11-01
            - "time": 20:00:00
            - "datetime": 2024-11-01 20:00:00
            - "full": 2024年11月01日 20:00:00
            - "short": 11-01 20:00
            - "iso": 2024-11-01T20:00:00+08:00
    
    Returns:
        格式化后的时间字符串
    """
    if format_type == "date":
        return dt.strftime("%Y-%m-%d")
    
    elif format_type == "time":
        return dt.strftime("%H:%M:%S")
    
    elif format_type == "datetime" or format_type == "default":
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    elif format_type == "full":
        return dt.strftime("%Y年%m月%d日 %H:%M:%S")
    
    elif format_type == "short":
        return dt.strftime("%m-%d %H:%M")
    
    elif format_type == "iso":
        return dt.isoformat()
    
    else:
        return dt.strftime("%Y-%m-%d %H:%M:%S")


def time_ago(dt: datetime) -> str:
    """
    计算时间距离现在多久（相对时间）
    
    Args:
        dt: datetime对象
    
    Returns:
        相对时间字符串，如 "3分钟前"、"2小时前"
    
    Examples:
        >>> past_time = datetime.now(SHANGHAI) - timedelta(minutes=5)
        >>> print(time_ago(past_time))
        5分钟前
    """
    # 确保有时区信息
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=SHANGHAI)
    
    now = datetime.now(tz=dt.tzinfo)
    delta = now - dt
    
    seconds = delta.total_seconds()
    
    if seconds < 0:
        return "未来"
    
    elif seconds < 60:
        return f"{int(seconds)}秒前"
    
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes}分钟前"
    
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours}小时前"
    
    elif seconds < 2592000:  # 30天
        days = int(seconds / 86400)
        return f"{days}天前"
    
    else:
        return format_time(dt, "date")


def timestamp_to_shanghai(timestamp: Union[int, float], milliseconds: bool = None) -> datetime:
    """
    时间戳转上海时区
    
    Args:
        timestamp: Unix时间戳
        milliseconds: 是否为毫秒时间戳（None=自动检测）
    
    Returns:
        上海时区的datetime对象
    """
    if milliseconds is None:
        # 自动检测：大于10位数字认为是毫秒
        milliseconds = timestamp > 1e10
    
    if milliseconds:
        timestamp = timestamp / 1000
    
    utc_time = datetime.fromtimestamp(timestamp, tz=UTC)
    return utc_time.astimezone(SHANGHAI)


def shanghai_to_timestamp(dt: datetime, milliseconds: bool = False) -> Union[int, float]:
    """
    上海时区时间转时间戳
    
    Args:
        dt: datetime对象
        milliseconds: 是否返回毫秒时间戳
    
    Returns:
        Unix时间戳
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=SHANGHAI)
    
    timestamp = dt.timestamp()
    
    if milliseconds:
        return int(timestamp * 1000)
    else:
        return int(timestamp)


def parse_timeframe(timeframe: str) -> int:
    """
    解析时间周期字符串，返回秒数
    
    Args:
        timeframe: 时间周期字符串，如 "1m", "5m", "1h", "1d"
    
    Returns:
        周期对应的秒数
    
    Examples:
        >>> parse_timeframe("1m")
        60
        >>> parse_timeframe("1h")
        3600
        >>> parse_timeframe("1d")
        86400
    """
    match = re.match(r'(\d+)([mhdwM])', timeframe)
    if not match:
        raise ValueError(f"无效的时间周期格式: {timeframe}")
    
    value, unit = match.groups()
    value = int(value)
    
    if unit not in TIMEFRAME_SECONDS:
        raise ValueError(f"不支持的时间单位: {unit}")
    
    return value * TIMEFRAME_SECONDS[unit]


def align_to_timeframe(dt: Union[datetime, int, float], 
                       timeframe: str, 
                       direction: str = "floor") -> datetime:
    """
    将时间对准到K线周期
    
    Args:
        dt: 要对准的时间（datetime对象或时间戳）
        timeframe: K线周期，如 "1m", "5m", "15m", "1h", "4h", "1d"
        direction: 对准方向
            - "floor": 向下对准（默认）
            - "ceil": 向上对准
            - "round": 四舍五入
    
    Returns:
        对准后的datetime对象（带上海时区）
    
    Examples:
        >>> dt = datetime(2024, 11, 1, 13, 25, 30, tzinfo=SHANGHAI)
        >>> align_to_timeframe(dt, "1h", "floor")
        datetime(2024, 11, 1, 13, 0, 0, tzinfo=SHANGHAI)
        
        >>> align_to_timeframe(dt, "15m", "floor")
        datetime(2024, 11, 1, 13, 15, 0, tzinfo=SHANGHAI)
        
        >>> align_to_timeframe(dt, "1d", "floor")
        datetime(2024, 11, 1, 0, 0, 0, tzinfo=SHANGHAI)
    """
    # 转换为datetime对象
    if isinstance(dt, (int, float)):
        dt = timestamp_to_shanghai(dt)
    elif isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=SHANGHAI)
        else:
            dt = dt.astimezone(SHANGHAI)
    
    # 解析周期
    period_seconds = parse_timeframe(timeframe)
    
    # 转换为时间戳进行对准
    timestamp = dt.timestamp()
    
    # 对准到周期
    if direction == "floor":
        aligned_timestamp = (timestamp // period_seconds) * period_seconds
    elif direction == "ceil":
        aligned_timestamp = ((timestamp + period_seconds - 1) // period_seconds) * period_seconds
    elif direction == "round":
        aligned_timestamp = round(timestamp / period_seconds) * period_seconds
    else:
        raise ValueError(f"不支持的对准方向: {direction}")
    
    # 转换回datetime
    aligned_dt = datetime.fromtimestamp(aligned_timestamp, tz=SHANGHAI)
    
    return aligned_dt


def get_next_kline_time(dt: Union[datetime, int, float], 
                        timeframe: str) -> datetime:
    """
    获取下一根K线的开始时间
    
    Args:
        dt: 当前时间
        timeframe: K线周期
    
    Returns:
        下一根K线的开始时间
    
    Examples:
        >>> dt = datetime(2024, 11, 1, 13, 0, 0, tzinfo=SHANGHAI)
        >>> get_next_kline_time(dt, "1h")
        datetime(2024, 11, 1, 14, 0, 0, tzinfo=SHANGHAI)
    """
    current_aligned = align_to_timeframe(dt, timeframe, "floor")
    period_seconds = parse_timeframe(timeframe)
    next_time = current_aligned + timedelta(seconds=period_seconds)
    return next_time


def get_kline_range(dt: Union[datetime, int, float], 
                    timeframe: str) -> tuple[datetime, datetime]:
    """
    获取指定时间所在K线的时间范围
    
    Args:
        dt: 时间
        timeframe: K线周期
    
    Returns:
        (开始时间, 结束时间) 元组
    
    Examples:
        >>> dt = datetime(2024, 11, 1, 13, 25, 30, tzinfo=SHANGHAI)
        >>> start, end = get_kline_range(dt, "1h")
        >>> print(start, end)
        2024-11-01 13:00:00+08:00 2024-11-01 14:00:00+08:00
    """
    start_time = align_to_timeframe(dt, timeframe, "floor")
    end_time = get_next_kline_time(start_time, timeframe)
    return start_time, end_time


def is_kline_closed(dt: Union[datetime, int, float], 
                    timeframe: str,
                    check_time: Optional[Union[datetime, int, float]] = None) -> bool:
    """
    判断K线是否已经完成
    
    Args:
        dt: K线的时间
        timeframe: K线周期
        check_time: 检查时间（默认为当前时间）
    
    Returns:
        True: K线已完成, False: K线进行中
    
    Examples:
        >>> kline_time = datetime(2024, 11, 1, 13, 0, 0, tzinfo=SHANGHAI)
        >>> current_time = datetime(2024, 11, 1, 14, 5, 0, tzinfo=SHANGHAI)
        >>> is_kline_closed(kline_time, "1h", current_time)
        True
    """
    if check_time is None:
        check_time = now_shanghai()
    
    _, end_time = get_kline_range(dt, timeframe)
    
    # 转换check_time为datetime
    if isinstance(check_time, (int, float)):
        check_time = timestamp_to_shanghai(check_time)
    elif isinstance(check_time, datetime):
        if check_time.tzinfo is None:
            check_time = check_time.replace(tzinfo=SHANGHAI)
        else:
            check_time = check_time.astimezone(SHANGHAI)
    
    return check_time >= end_time


def time_until_next_kline(timeframe: str, 
                          current_time: Optional[Union[datetime, int, float]] = None) -> timedelta:
    """
    计算距离下一根K线还有多久
    
    Args:
        timeframe: K线周期
        current_time: 当前时间（默认为现在）
    
    Returns:
        时间间隔
    
    Examples:
        >>> time_until_next_kline("1h")
        timedelta(seconds=1245)  # 20分钟45秒
    """
    if current_time is None:
        current_time = now_shanghai()
    elif isinstance(current_time, (int, float)):
        current_time = timestamp_to_shanghai(current_time)
    elif isinstance(current_time, datetime):
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=SHANGHAI)
        else:
            current_time = current_time.astimezone(SHANGHAI)
    
    next_kline = get_next_kline_time(current_time, timeframe)
    return next_kline - current_time

