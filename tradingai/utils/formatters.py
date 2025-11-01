"""
智能格式化工具
"""
from typing import Union


def smart_format(value: Union[float, int], precision: int = None) -> str:
    """
    智能格式化数值，自动选择最佳显示格式
    
    Args:
        value: 要格式化的数值
        precision: 可选的固定精度
    
    Returns:
        格式化后的字符串
    
    Examples:
        >>> smart_format(0)
        '0'
        >>> smart_format(1234567)
        '1.23e+06'
        >>> smart_format(42500.5)
        '42,500.50'
        >>> smart_format(0.00002233)
        '0.00002233'
        >>> smart_format(0.00000001)
        '1.00000000e-08'
    """
    if value == 0:
        return "0"
    
    abs_value = abs(value)
    
    # 如果指定了精度，直接使用
    if precision is not None:
        return f"{value:.{precision}f}"
    
    # 超大值：使用科学计数法
    if abs_value >= 1e6:
        return f"{value:.2e}"
    
    # 大值：使用千分位分隔符
    elif abs_value >= 1000:
        return f"{value:,.2f}"
    
    # 中等值：2-4位小数
    elif abs_value >= 1:
        return f"{value:.4f}"
    
    # 小值：保持8位小数精度
    elif abs_value >= 0.0001:
        return f"{value:.8f}"
    
    # 极小值：科学计数法
    else:
        return f"{value:.8e}"


def format_price(price: Union[float, int]) -> str:
    """
    格式化价格
    
    Args:
        price: 价格
    
    Returns:
        格式化后的价格字符串
    """
    return smart_format(price)


def format_percentage(value: Union[float, int], with_sign: bool = True) -> str:
    """
    格式化百分比
    
    Args:
        value: 百分比值（如 5.5 表示 5.5%）
        with_sign: 是否显示正负号
    
    Returns:
        格式化后的百分比字符串
    
    Examples:
        >>> format_percentage(5.5)
        '+5.50%'
        >>> format_percentage(-3.2)
        '-3.20%'
        >>> format_percentage(5.5, with_sign=False)
        '5.50%'
    """
    if with_sign:
        sign = '+' if value >= 0 else ''
        return f"{sign}{value:.2f}%"
    else:
        return f"{value:.2f}%"


def format_volume(volume: Union[float, int]) -> str:
    """
    格式化成交量，使用K、M、B等单位
    
    Args:
        volume: 成交量
    
    Returns:
        格式化后的成交量字符串
    
    Examples:
        >>> format_volume(1234)
        '1.23K'
        >>> format_volume(1234567)
        '1.23M'
        >>> format_volume(1234567890)
        '1.23B'
    """
    if volume == 0:
        return "0"
    
    abs_volume = abs(volume)
    
    if abs_volume >= 1e9:
        return f"{volume / 1e9:.2f}B"
    elif abs_volume >= 1e6:
        return f"{volume / 1e6:.2f}M"
    elif abs_volume >= 1e3:
        return f"{volume / 1e3:.2f}K"
    else:
        return f"{volume:.2f}"


def format_dict(data: dict, indent: int = 0) -> str:
    """
    智能格式化字典，自动处理数值显示
    
    Args:
        data: 要格式化的字典
        indent: 缩进级别
    
    Returns:
        格式化后的字符串
    """
    lines = []
    prefix = "  " * indent
    
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(format_dict(value, indent + 1))
        elif isinstance(value, (int, float)):
            formatted_value = smart_format(value)
            lines.append(f"{prefix}{key}: {formatted_value}")
        else:
            lines.append(f"{prefix}{key}: {value}")
    
    return '\n'.join(lines)

