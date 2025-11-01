"""
配置辅助工具 - 处理注释配置项
"""
import os
from typing import Optional, Any


def get_config(key: str, default: Any = None, required: bool = False) -> Optional[Any]:
    """
    获取配置项，如果配置项被注释或未设置，返回 None 或默认值
    
    Args:
        key: 配置项名称
        default: 默认值（当配置项未设置时使用）
        required: 是否必需（如果为True且未配置，抛出异常）
    
    Returns:
        配置值或默认值
    """
    value = os.getenv(key)
    
    # 如果配置项未设置或为空
    if value is None or value.strip() == "":
        if required:
            raise ValueError(f"配置项 {key} 是必需的，但未设置")
        return default
    
    return value


def get_bool_config(key: str, default: bool = False) -> bool:
    """
    获取布尔类型配置
    
    Args:
        key: 配置项名称
        default: 默认值
    
    Returns:
        布尔值
    """
    value = get_config(key)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def get_int_config(key: str, default: int = 0) -> int:
    """
    获取整数类型配置
    
    Args:
        key: 配置项名称
        default: 默认值
    
    Returns:
        整数值
    """
    value = get_config(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_float_config(key: str, default: float = 0.0) -> float:
    """
    获取浮点数类型配置
    
    Args:
        key: 配置项名称
        default: 默认值
    
    Returns:
        浮点数值
    """
    value = get_config(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def get_list_config(key: str, default: list = None, separator: str = ",") -> list:
    """
    获取列表类型配置（逗号分隔）
    
    Args:
        key: 配置项名称
        default: 默认值
        separator: 分隔符
    
    Returns:
        列表
    """
    if default is None:
        default = []
    
    value = get_config(key)
    if value is None or value.strip() == "":
        return default
    
    # 分割并去除空白
    items = [item.strip() for item in value.split(separator) if item.strip()]
    return items if items else default


def is_config_enabled(key: str) -> bool:
    """
    检查配置项是否启用（未注释且值不为空）
    
    Args:
        key: 配置项名称
    
    Returns:
        是否启用
    """
    value = os.getenv(key)
    return value is not None and value.strip() != ""


def config_exists(key: str) -> bool:
    """
    检查配置项是否存在（未被注释）
    
    Args:
        key: 配置项名称
    
    Returns:
        是否存在
    """
    return os.getenv(key) is not None

