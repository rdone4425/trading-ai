"""
指标配置解析器
支持灵活的指标参数配置
"""
import os
from typing import Dict, List, Any, Optional
from ..logger import get_logger

logger = get_logger("indicators.config_parser")


class IndicatorConfigParser:
    """
    指标配置解析器
    
    配置格式示例（环境变量）：
        INDICATOR_ema=20,120
        INDICATOR_atr=14
        INDICATOR_ma=20,30,60
        INDICATOR_rsi=14
        INDICATOR_macd=12,26,9
    
    配置格式示例（字符串）：
        ema=20,120
        atr=14
        ma=20,30,60
        rsi=14
        macd=12,26,9
    
    解析后：
        {
            "ema": [20, 120],
            "atr": [14],
            "ma": [20, 30, 60],
            "rsi": [14],
            "macd": [12, 26, 9]
        }
    """
    
    # 支持的指标及其参数名称
    SUPPORTED_INDICATORS = {
        "ma": ["period"],
        "ema": ["period"],
        "rsi": ["period"],
        "macd": ["fastperiod", "slowperiod", "signalperiod"],
        "bbands": ["period", "nbdevup", "nbdevdn"],
        "kdj": ["fastk_period", "slowk_period", "slowd_period"],
        "atr": ["period"],
        "adx": ["period"],
        "cci": ["period"],
        "willr": ["period"],
        "obv": [],
        "stoch": ["fastk_period", "slowk_period", "slowd_period"]
    }
    
    @staticmethod
    def parse_from_string(config_string: str) -> Dict[str, List]:
        """
        从字符串解析配置
        
        Args:
            config_string: 配置字符串，格式如 "ema=20,120;ma=20,30"
        
        Returns:
            解析后的配置字典 {indicator_name: [params]}
        """
        if not config_string or not config_string.strip():
            return {}
        
        result = {}
        
        # 支持分号或换行分隔
        lines = config_string.replace(';', '\n').strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            try:
                # 解析单行配置
                parsed = IndicatorConfigParser._parse_line(line)
                if parsed:
                    indicator_name, params = parsed
                    result[indicator_name] = params
                    
            except Exception as e:
                logger.warning(f"解析配置失败: {line} - {e}")
                continue
        
        logger.info(f"✅ 解析完成，共 {len(result)} 个指标")
        return result
    
    @staticmethod
    def _parse_line(line: str) -> Optional[tuple]:
        """
        解析单行配置
        
        Args:
            line: 配置行，格式如 "ema=20,120"
        
        Returns:
            (indicator_name, params)
        """
        if '=' not in line:
            return None
        
        key, value = line.split('=', 1)
        indicator_name = key.strip().lower()
        value = value.strip()
        
        # 验证指标名称
        if indicator_name not in IndicatorConfigParser.SUPPORTED_INDICATORS:
            logger.warning(f"不支持的指标: {indicator_name}")
            return None
        
        # 解析参数
        params = []
        if value:
            for v in value.split(','):
                v = v.strip()
                if v:
                    try:
                        # 尝试转换为数字
                        if '.' in v:
                            params.append(float(v))
                        else:
                            params.append(int(v))
                    except ValueError:
                        logger.warning(f"参数格式错误: {v}")
                        continue
        
        return indicator_name, params
    
    @staticmethod
    def parse_from_env(prefix: str = "INDICATOR") -> Dict[str, List]:
        """
        从环境变量解析配置
        
        📌 注意：只解析未被注释的配置项
               如果某个 INDICATOR_ 配置在 .env 中被注释（以 # 开头），
               则不会被解析和计算
        
        Args:
            prefix: 环境变量前缀，如 "INDICATOR"
        
        Returns:
            解析后的配置字典 {indicator_name: [params]}
        
        Example:
            环境变量:
                INDICATOR_ema=20,50,120       ✓ 启用
                INDICATOR_rsi=14              ✓ 启用
                # INDICATOR_macd=12,26,9      ✗ 注释，跳过
            
            返回:
            
            结果:
                {"ema": [20, 50, 120], "rsi": [14]}
        """
        import os
        
        result = {}
        
        # 查找所有匹配的环境变量
        for key, value in os.environ.items():
            if key.startswith(prefix + '_'):
                # 跳过空值或被注释的配置
                if not value or not value.strip():
                    logger.debug(f"跳过空配置: {key}")
                    continue
                
                # 去掉前缀，如 INDICATOR_ema -> ema
                indicator_name = key[len(prefix) + 1:].lower()
                
                try:
                    parsed = IndicatorConfigParser._parse_line(f"{indicator_name}={value}")
                    if parsed:
                        ind_name, params = parsed
                        result[ind_name] = params
                        
                except Exception as e:
                    logger.warning(f"解析环境变量失败: {key} - {e}")
                    continue
        
        logger.info(f"✅ 从环境变量加载 {len(result)} 个指标配置")
        return result
    
    @staticmethod
    def get_indicator_params(config: Dict[str, List], 
                            indicator_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定指标的参数字典
        
        Args:
            config: 配置字典
            indicator_name: 指标名称
        
        Returns:
            参数字典，如 {"period": 20}
        """
        if indicator_name not in config:
            return None
        
        params_list = config[indicator_name]
        param_names = IndicatorConfigParser.SUPPORTED_INDICATORS.get(indicator_name, [])
        
        if not param_names:
            return {}
        
        # 将参数列表转换为字典
        params_dict = {}
        for i, param_name in enumerate(param_names):
            if i < len(params_list):
                params_dict[param_name] = params_list[i]
        
        return params_dict
    
    @staticmethod
    def get_all_indicators(config: Dict[str, List]) -> List[str]:
        """
        获取所有指标名称
        
        Args:
            config: 配置字典
        
        Returns:
            指标名称列表
        """
        return list(config.keys())
    
    @staticmethod
    def validate_config(config: Dict[str, List]) -> List[str]:
        """
        验证配置
        
        Args:
            config: 配置字典
        
        Returns:
            错误信息列表
        """
        errors = []
        
        for indicator_name, params in config.items():
            # 检查指标是否支持
            if indicator_name not in IndicatorConfigParser.SUPPORTED_INDICATORS:
                errors.append(f"不支持的指标: {indicator_name}")
                continue
            
            # 检查参数数量
            expected_params = IndicatorConfigParser.SUPPORTED_INDICATORS[indicator_name]
            if len(params) < len(expected_params):
                errors.append(
                    f"{indicator_name}: 参数不足，需要 {len(expected_params)} 个，提供了 {len(params)} 个"
                )
            
            # 检查参数值
            for param in params:
                if not isinstance(param, (int, float)) or param <= 0:
                    errors.append(f"{indicator_name}: 参数必须为正数")
                    break
        
        return errors
    
    @staticmethod
    def to_string(config: Dict[str, List]) -> str:
        """
        将配置字典转换为字符串
        
        Args:
            config: 配置字典
        
        Returns:
            配置字符串
        """
        lines = []
        for indicator_name in sorted(config.keys()):
            params = config[indicator_name]
            params_str = ','.join(str(p) for p in params)
            lines.append(f"{indicator_name}={params_str}")
        
        return '\n'.join(lines)

