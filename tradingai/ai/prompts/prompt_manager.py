"""
提示词管理器

负责加载、格式化和管理 AI 提示词
支持两种格式：
1. JSON 文件 (prompts.json) - 推荐
2. 文本文件 (system.txt + user.txt) - 兼容旧版
"""
import json
from pathlib import Path
from typing import Dict, Optional, Any
from ...logger import get_logger

logger = get_logger("ai.prompts")


class PromptManager:
    """提示词管理器"""
    
    # 提示词根目录
    PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "prompts"
    
    # 支持的提示词类型
    PROMPT_TYPES = ["analysis", "learning", "review"]
    
    def __init__(self, prompts_dir: Optional[Path] = None, use_json: bool = True):
        """
        初始化提示词管理器
        
        Args:
            prompts_dir: 自定义提示词目录（可选）
            use_json: 是否使用 JSON 格式（默认 True）
        """
        self.prompts_dir = prompts_dir or self.PROMPTS_DIR
        self.use_json = use_json
        
        # 缓存已加载的提示词
        self._cache: Dict[str, str] = {}
        self._json_prompts: Optional[Dict[str, Any]] = None
        
        # 如果使用 JSON 格式，加载 prompts.json
        if self.use_json:
            self._load_json_prompts()
        
        logger.debug(f"初始化提示词管理器: {self.prompts_dir} (JSON: {use_json})")
    
    def _load_json_prompts(self):
        """加载 JSON 格式的提示词"""
        json_file = self.prompts_dir / "prompts.json"
        
        if not json_file.exists():
            logger.warning(f"JSON 提示词文件不存在: {json_file}，将使用文本格式")
            self.use_json = False
            return
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                self._json_prompts = json.load(f)
            
            logger.info(f"✅ 加载 JSON 提示词: {len(self._json_prompts)} 个类型")
        
        except Exception as e:
            logger.error(f"加载 JSON 提示词失败: {e}")
            self.use_json = False
    
    def get_system_prompt(self, prompt_type: str) -> str:
        """
        获取系统提示词
        
        Args:
            prompt_type: 提示词类型 (analysis/learning/review)
        
        Returns:
            系统提示词内容
        
        Raises:
            ValueError: 不支持的提示词类型
            FileNotFoundError: 提示词文件不存在
        """
        if prompt_type not in self.PROMPT_TYPES:
            raise ValueError(
                f"不支持的提示词类型: {prompt_type}。"
                f"支持的类型: {', '.join(self.PROMPT_TYPES)}"
            )
        
        cache_key = f"{prompt_type}_system"
        
        # 检查缓存
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 从 JSON 加载
        if self.use_json and self._json_prompts:
            if prompt_type in self._json_prompts:
                content = self._json_prompts[prompt_type].get("system", "")
                self._cache[cache_key] = content
                logger.debug(f"从 JSON 加载系统提示词: {prompt_type}")
                return content
        
        # 从文本文件加载（兼容旧版）
        prompt_file = self.prompts_dir / prompt_type / "system.txt"
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"提示词文件不存在: {prompt_file}")
        
        content = prompt_file.read_text(encoding="utf-8")
        
        # 缓存
        self._cache[cache_key] = content
        
        logger.debug(f"从文本文件加载系统提示词: {prompt_type}")
        return content
    
    def get_user_template(self, prompt_type: str) -> str:
        """
        获取用户提示词模板
        
        Args:
            prompt_type: 提示词类型 (analysis/learning/review)
        
        Returns:
            用户提示词模板
        
        Raises:
            ValueError: 不支持的提示词类型
            FileNotFoundError: 提示词文件不存在
        """
        if prompt_type not in self.PROMPT_TYPES:
            raise ValueError(
                f"不支持的提示词类型: {prompt_type}。"
                f"支持的类型: {', '.join(self.PROMPT_TYPES)}"
            )
        
        cache_key = f"{prompt_type}_user"
        
        # 检查缓存
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 从 JSON 加载
        if self.use_json and self._json_prompts:
            if prompt_type in self._json_prompts:
                content = self._json_prompts[prompt_type].get("user", "")
                self._cache[cache_key] = content
                logger.debug(f"从 JSON 加载用户提示词: {prompt_type}")
                return content
        
        # 从文本文件加载（兼容旧版）
        prompt_file = self.prompts_dir / prompt_type / "user.txt"
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"提示词文件不存在: {prompt_file}")
        
        content = prompt_file.read_text(encoding="utf-8")
        
        # 缓存
        self._cache[cache_key] = content
        
        logger.debug(f"从文本文件加载用户提示词: {prompt_type}")
        return content
    
    def format_user_prompt(self, prompt_type: str, data: Dict) -> str:
        """
        格式化用户提示词
        
        Args:
            prompt_type: 提示词类型
            data: 要填充的数据字典
        
        Returns:
            格式化后的用户提示词
        
        Example:
            data = {
                "symbol": "BTCUSDT",
                "current_price": "95000",
                "change_24h": "+3.5"
            }
            prompt = pm.format_user_prompt("analysis", data)
        """
        template = self.get_user_template(prompt_type)
        
        try:
            # 使用 format_map 填充模板
            # 对于缺失的键，保持原样
            formatted = template.format_map(SafeDict(data))
            return formatted
        
        except Exception as e:
            logger.error(f"格式化用户提示词失败: {e}")
            raise
    
    def get_full_prompt(
        self,
        prompt_type: str,
        data: Optional[Dict] = None
    ) -> list:
        """
        获取完整的提示词消息列表
        
        Args:
            prompt_type: 提示词类型
            data: 用户数据（可选）
        
        Returns:
            OpenAI 格式的消息列表
        
        Example:
            messages = pm.get_full_prompt("analysis", market_data)
            response = await provider.chat(messages)
        """
        messages = [
            {
                "role": "system",
                "content": self.get_system_prompt(prompt_type)
            }
        ]
        
        if data:
            messages.append({
                "role": "user",
                "content": self.format_user_prompt(prompt_type, data)
            })
        
        return messages
    
    def clear_cache(self):
        """清除提示词缓存"""
        self._cache.clear()
        logger.debug("清除提示词缓存")
    
    def get_prompt_config(self, prompt_type: str) -> Dict[str, Any]:
        """
        获取提示词配置（仅 JSON 格式）
        
        Args:
            prompt_type: 提示词类型
        
        Returns:
            配置字典 {temperature, max_tokens, output_format等}
        """
        if self.use_json and self._json_prompts:
            if prompt_type in self._json_prompts:
                config = {
                    "temperature": self._json_prompts[prompt_type].get("temperature", 0.7),
                    "max_tokens": self._json_prompts[prompt_type].get("max_tokens", 2000),
                    "output_format": self._json_prompts[prompt_type].get("output_format", "text")
                }
                return config
        
        # 默认配置
        return {
            "temperature": 0.7,
            "max_tokens": 2000,
            "output_format": "text"
        }
    
    def reload_prompt(self, prompt_type: str):
        """
        重新加载提示词（清除指定类型的缓存）
        
        Args:
            prompt_type: 提示词类型
        """
        for key in [f"{prompt_type}_system", f"{prompt_type}_user"]:
            if key in self._cache:
                del self._cache[key]
        
        # 如果是 JSON 格式，重新加载 JSON 文件
        if self.use_json:
            self._load_json_prompts()
        
        logger.debug(f"重新加载提示词: {prompt_type}")


class SafeDict(dict):
    """
    安全字典，对于缺失的键返回占位符而不是抛出异常
    """
    def __missing__(self, key):
        return f"{{{key}}}"

