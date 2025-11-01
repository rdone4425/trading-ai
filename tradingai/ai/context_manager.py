"""
上下文管理器：持久化存储复盘知识和优化策略
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    import aiofiles
    import aiofiles.os
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False

import asyncio  # 即使没有aiofiles也需要asyncio.gather

from tradingai.logger import get_logger
from tradingai.config import ANALYSIS_RESULTS_DIR

logger = get_logger(__name__)


class ContextManager:
    """上下文管理器：管理复盘知识和优化策略的持久化存储"""
    
    def __init__(self, context_dir: Optional[str] = None):
        """
        初始化上下文管理器
        
        Args:
            context_dir: 上下文存储目录（默认使用 ANALYSIS_RESULTS_DIR）
        """
        # 确定上下文存储目录
        if context_dir:
            self.context_dir = Path(context_dir)
        else:
            # 使用配置中的分析结果目录
            # context_manager.py 位于 tradingai/ai/context_manager.py
            # 需要找到项目根目录（trading-ai/）
            # __file__ = tradingai/ai/context_manager.py
            # parent = tradingai/ai/
            # parent.parent = tradingai/
            # parent.parent.parent = trading-ai/（项目根目录）
            # 与 market_scanner.py 使用相同的路径计算方式
            project_root = Path(__file__).parent.parent.parent
            base_dir = project_root / ANALYSIS_RESULTS_DIR
            self.context_dir = base_dir / "context"
            
            # 调试日志：输出实际路径
            logger.debug(f"📁 项目根目录: {project_root}")
            logger.debug(f"📁 数据目录: {base_dir}")
            logger.debug(f"📁 上下文目录: {self.context_dir}")
        
        # 确保目录存在
        self.context_dir.mkdir(parents=True, exist_ok=True)
        
        # 上下文文件路径
        self.review_knowledge_file = self.context_dir / "review_knowledge.json"
        self.strategies_file = self.context_dir / "optimized_strategies.json"
        self.learning_file = self.context_dir / "learning_results.json"
        
        logger.info(f"📁 上下文存储目录: {self.context_dir}")
    
    async def save_review_knowledge(self, review_knowledge: List[Dict[str, Any]]) -> bool:
        """
        保存复盘知识到文件
        
        Args:
            review_knowledge: 复盘知识列表
        
        Returns:
            是否保存成功
        """
        try:
            # 准备保存的数据（包含元数据）
            data = {
                "version": "1.0",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "count": len(review_knowledge),
                "knowledge": review_knowledge
            }
            
            # 保存到文件（异步）
            if HAS_AIOFILES:
                async with aiofiles.open(self.review_knowledge_file, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                # 降级为同步I/O（如果没有aiofiles）
                with open(self.review_knowledge_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"✅ 已保存复盘知识: {len(review_knowledge)} 条")
            return True
        
        except Exception as e:
            logger.error(f"❌ 保存复盘知识失败: {e}", exc_info=True)
            return False
    
    async def load_review_knowledge(self) -> List[Dict[str, Any]]:
        """
        从文件加载复盘知识
        
        Returns:
            复盘知识列表
        """
        try:
            # 检查文件是否存在（异步）
            if HAS_AIOFILES:
                exists = await aiofiles.os.path.exists(str(self.review_knowledge_file))
            else:
                exists = self.review_knowledge_file.exists()
            
            if not exists:
                logger.debug("📁 复盘知识文件不存在，返回空列表")
                return []
            
            # 读取文件（异步）
            if HAS_AIOFILES:
                async with aiofiles.open(self.review_knowledge_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    data = json.loads(content)
            else:
                # 降级为同步I/O
                with open(self.review_knowledge_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            knowledge = data.get("knowledge", [])
            updated_at = data.get("updated_at", "未知")
            logger.info(f"📚 已加载复盘知识: {len(knowledge)} 条（更新于: {updated_at}）")
            
            return knowledge
        
        except Exception as e:
            logger.warning(f"⚠️  加载复盘知识失败: {e}，返回空列表")
            return []
    
    async def save_optimized_strategies(self, strategies: List[Dict[str, Any]]) -> bool:
        """
        保存优化策略到文件
        
        Args:
            strategies: 优化策略列表
        
        Returns:
            是否保存成功
        """
        try:
            # 准备保存的数据（包含元数据）
            data = {
                "version": "1.0",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "count": len(strategies),
                "strategies": strategies
            }
            
            # 保存到文件（异步）
            if HAS_AIOFILES:
                async with aiofiles.open(self.strategies_file, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                with open(self.strategies_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"✅ 已保存优化策略: {len(strategies)} 条")
            return True
        
        except Exception as e:
            logger.error(f"❌ 保存优化策略失败: {e}", exc_info=True)
            return False
    
    async def load_optimized_strategies(self) -> List[Dict[str, Any]]:
        """
        从文件加载优化策略
        
        Returns:
            优化策略列表
        """
        try:
            # 检查文件是否存在（异步）
            if HAS_AIOFILES:
                exists = await aiofiles.os.path.exists(str(self.strategies_file))
            else:
                exists = self.strategies_file.exists()
            
            if not exists:
                logger.debug("📁 优化策略文件不存在，返回空列表")
                return []
            
            # 读取文件（异步）
            if HAS_AIOFILES:
                async with aiofiles.open(self.strategies_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    data = json.loads(content)
            else:
                with open(self.strategies_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            strategies = data.get("strategies", [])
            updated_at = data.get("updated_at", "未知")
            logger.info(f"🎯 已加载优化策略: {len(strategies)} 条（更新于: {updated_at}）")
            
            return strategies
        
        except Exception as e:
            logger.warning(f"⚠️  加载优化策略失败: {e}，返回空列表")
            return []
    
    async def save_learning_results(self, learning_results: List[Dict[str, Any]]) -> bool:
        """
        保存学习结果到文件
        
        Args:
            learning_results: 学习结果列表
        
        Returns:
            是否保存成功
        """
        try:
            # 准备保存的数据（包含元数据）
            data = {
                "version": "1.0",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "count": len(learning_results),
                "results": learning_results
            }
            
            # 保存到文件（异步）
            if HAS_AIOFILES:
                async with aiofiles.open(self.learning_file, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                with open(self.learning_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"✅ 已保存学习结果: {len(learning_results)} 条")
            return True
        
        except Exception as e:
            logger.error(f"❌ 保存学习结果失败: {e}", exc_info=True)
            return False
    
    async def load_learning_results(self) -> List[Dict[str, Any]]:
        """
        从文件加载学习结果
        
        Returns:
            学习结果列表
        """
        try:
            # 检查文件是否存在（异步）
            if HAS_AIOFILES:
                exists = await aiofiles.os.path.exists(str(self.learning_file))
            else:
                exists = self.learning_file.exists()
            
            if not exists:
                logger.debug("📁 学习结果文件不存在，返回空列表")
                return []
            
            # 读取文件（异步）
            if HAS_AIOFILES:
                async with aiofiles.open(self.learning_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    data = json.loads(content)
            else:
                with open(self.learning_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            results = data.get("results", [])
            updated_at = data.get("updated_at", "未知")
            logger.info(f"📖 已加载学习结果: {len(results)} 条（更新于: {updated_at}）")
            
            return results
        
        except Exception as e:
            logger.warning(f"⚠️  加载学习结果失败: {e}，返回空列表")
            return []
    
    async def load_all_context(self) -> Dict[str, Any]:
        """
        加载所有上下文数据（异步）
        
        Returns:
            包含所有上下文数据的字典
        """
        review_knowledge, optimized_strategies, learning_results = await asyncio.gather(
            self.load_review_knowledge(),
            self.load_optimized_strategies(),
            self.load_learning_results()
        )
        return {
            "review_knowledge": review_knowledge,
            "optimized_strategies": optimized_strategies,
            "learning_results": learning_results
        }
    
    async def save_all_context(
        self,
        review_knowledge: Optional[List[Dict[str, Any]]] = None,
        optimized_strategies: Optional[List[Dict[str, Any]]] = None,
        learning_results: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        保存所有上下文数据（异步）
        
        Args:
            review_knowledge: 复盘知识列表（可选）
            optimized_strategies: 优化策略列表（可选）
            learning_results: 学习结果列表（可选）
        
        Returns:
            是否全部保存成功
        """
        tasks = []
        
        if review_knowledge is not None:
            tasks.append(self.save_review_knowledge(review_knowledge))
        
        if optimized_strategies is not None:
            tasks.append(self.save_optimized_strategies(optimized_strategies))
        
        if learning_results is not None:
            tasks.append(self.save_learning_results(learning_results))
        
        if tasks:
            results = await asyncio.gather(*tasks)
            return all(results)
        
        return False
    
    def clear_all(self) -> bool:
        """
        清空所有上下文数据（删除文件）
        
        Returns:
            是否清空成功
        """
        try:
            deleted = []
            
            if self.review_knowledge_file.exists():
                self.review_knowledge_file.unlink()
                deleted.append("复盘知识")
            
            if self.strategies_file.exists():
                self.strategies_file.unlink()
                deleted.append("优化策略")
            
            if self.learning_file.exists():
                self.learning_file.unlink()
                deleted.append("学习结果")
            
            if deleted:
                logger.info(f"🗑️  已清空上下文数据: {', '.join(deleted)}")
            else:
                logger.info("📁 上下文数据文件不存在，无需清空")
            
            return True
        
        except Exception as e:
            logger.error(f"❌ 清空上下文数据失败: {e}", exc_info=True)
            return False
    
    def get_context_stats(self) -> Dict[str, Any]:
        """
        获取上下文统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "review_knowledge": {
                "count": 0,
                "file_exists": self.review_knowledge_file.exists(),
                "updated_at": None
            },
            "optimized_strategies": {
                "count": 0,
                "file_exists": self.strategies_file.exists(),
                "updated_at": None
            },
            "learning_results": {
                "count": 0,
                "file_exists": self.learning_file.exists(),
                "updated_at": None
            }
        }
        
        # 加载并统计
        try:
            if self.review_knowledge_file.exists():
                with open(self.review_knowledge_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    stats["review_knowledge"]["count"] = data.get("count", 0)
                    stats["review_knowledge"]["updated_at"] = data.get("updated_at")
            
            if self.strategies_file.exists():
                with open(self.strategies_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    stats["optimized_strategies"]["count"] = data.get("count", 0)
                    stats["optimized_strategies"]["updated_at"] = data.get("updated_at")
            
            if self.learning_file.exists():
                with open(self.learning_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    stats["learning_results"]["count"] = data.get("count", 0)
                    stats["learning_results"]["updated_at"] = data.get("updated_at")
        
        except Exception as e:
            logger.warning(f"⚠️  获取上下文统计失败: {e}")
        
        return stats

