"""
交易执行器模块 - 独立于具体交易平台，基于平台抽象接口工作
"""
from .trader import Trader

__all__ = ['Trader']

