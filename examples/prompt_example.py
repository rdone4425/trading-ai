"""
提示词管理器使用示例

演示如何使用不同类型的提示词
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tradingai.ai import AIProviderFactory
from tradingai.ai.prompts import PromptManager
from tradingai.logger import get_logger

logger = get_logger("examples.prompt")


async def test_analysis_prompt():
    """测试市场分析提示词"""
    logger.info("=" * 60)
    logger.info("测试市场分析提示词")
    logger.info("=" * 60)
    
    # 创建提示词管理器
    pm = PromptManager()
    
    # 准备市场数据
    market_data = {
        "symbol": "BTCUSDT",
        "current_price": "95,234.50",
        "change_24h": "+3.45",
        "volume_24h": "28,500,000,000",
        "timeframe": "1h",
        "indicators": """
- EMA7: $94,800.00
- EMA20: $94,500.00
- EMA50: $93,200.00
- RSI: 68.5
- MACD: 150.23
- ATR: 1,250.50""",
        "high": "96,100.00",
        "low": "94,200.00",
        "open": "94,800.00",
        "close": "95,234.50"
    }
    
    # 获取完整提示词
    messages = pm.get_full_prompt("analysis", market_data)
    
    logger.info("📋 系统提示词（部分）:")
    logger.info(messages[0]["content"][:200] + "...")
    logger.info("\n📋 用户提示词（部分）:")
    logger.info(messages[1]["content"][:300] + "...")
    
    # 发送到 AI
    try:
        provider = AIProviderFactory.create_from_config()
        logger.info(f"\n✅ 使用提供商: {provider.get_provider_name()}")
        logger.info("📤 发送分析请求...\n")
        
        response = await provider.chat(messages, temperature=0.3)
        
        logger.info("📥 AI 分析结果:")
        logger.info(f"\n{response}\n")
        
        # 尝试解析 JSON
        try:
            import json
            analysis = json.loads(response)
            logger.info("✅ 成功解析为 JSON 格式")
            logger.info(f"  趋势: {analysis.get('trend')}")
            logger.info(f"  建议: {analysis.get('action')}")
            logger.info(f"  置信度: {analysis.get('confidence')}")
        except:
            logger.warning("⚠️  响应不是 JSON 格式")
        
        await provider.close()
        
    except Exception as e:
        logger.error(f"❌ 分析失败: {e}")


async def test_learning_prompt():
    """测试学习提示词"""
    logger.info("=" * 60)
    logger.info("测试学习辅导提示词")
    logger.info("=" * 60)
    
    pm = PromptManager()
    
    # 准备学习数据
    learning_data = {
        "topic": "EMA 指标的使用方法",
        "level": "初级",
        "questions": """
1. EMA 和 MA 有什么区别？
2. 如何判断 EMA 金叉和死叉？
3. EMA 7/20/50 分别代表什么意义？
4. 在实际交易中如何使用 EMA？""",
        "goals": "能够在实际交易中正确使用 EMA 指标进行趋势判断"
    }
    
    # 获取提示词
    messages = pm.get_full_prompt("learning", learning_data)
    
    logger.info("📋 学习主题: EMA 指标")
    logger.info("📋 学习水平: 初级\n")
    
    try:
        provider = AIProviderFactory.create_from_config()
        logger.info(f"✅ 使用提供商: {provider.get_provider_name()}")
        logger.info("📤 发送学习请求...\n")
        
        response = await provider.chat(messages, temperature=0.7)
        
        logger.info("📥 AI 教学内容:")
        logger.info(f"\n{response}\n")
        
        await provider.close()
        
    except Exception as e:
        logger.error(f"❌ 学习请求失败: {e}")


async def test_review_prompt():
    """测试复盘提示词"""
    logger.info("=" * 60)
    logger.info("测试交易复盘提示词")
    logger.info("=" * 60)
    
    pm = PromptManager()
    
    # 准备交易复盘数据
    review_data = {
        "symbol": "ETHUSDT",
        "direction": "做多",
        "trade_time": "2025-11-01 10:30:00",
        "duration": "3小时15分钟",
        "entry_price": "3,250.00",
        "exit_price": "3,380.00",
        "stop_loss": "3,180.00",
        "take_profit": "3,450.00",
        "profit_loss": "+1,300.00",
        "profit_loss_percentage": "+4.0",
        "risk_reward_ratio": "1:2.86",
        "reasoning": """
- EMA7 上穿 EMA20，形成金叉
- RSI 从 45 上升到 62，显示买盘增强
- 突破前期阻力位 3,200
- 成交量放大，确认突破有效""",
        "entry_market_state": "震荡上行，突破阻力位",
        "exit_market_state": "快速上涨后遇到阻力",
        "indicators": """
入场时:
- EMA7: 3,240 | EMA20: 3,220 | EMA50: 3,180
- RSI: 62
- MACD: 正值，柱状图增长

出场时:
- EMA7: 3,365 | EMA20: 3,310 | EMA50: 3,250
- RSI: 75（接近超买）
- MACD: 正值，柱状图开始减小""",
        "entry_mindset": "看到金叉和突破信号后，按计划入场",
        "holding_process": "持仓过程比较顺利，价格稳步上涨，中途没有太大波动",
        "exit_reason": "RSI 接近超买区域（75），且 MACD 柱状图开始减小，选择提前止盈"
    }
    
    # 获取提示词
    messages = pm.get_full_prompt("review", review_data)
    
    logger.info("📋 复盘交易: ETHUSDT 做多")
    logger.info(f"📋 盈亏: {review_data['profit_loss']} ({review_data['profit_loss_percentage']}%)\n")
    
    try:
        provider = AIProviderFactory.create_from_config()
        logger.info(f"✅ 使用提供商: {provider.get_provider_name()}")
        logger.info("📤 发送复盘请求...\n")
        
        response = await provider.chat(messages, temperature=0.5)
        
        logger.info("📥 AI 复盘分析:")
        logger.info(f"\n{response}\n")
        
        # 尝试解析 JSON
        try:
            import json
            review = json.loads(response)
            logger.info("✅ 成功解析为 JSON 格式")
            logger.info(f"  总体评价: {review.get('overall_rating')}")
            logger.info(f"  决策质量: {review.get('decision_quality', {}).get('score')}/10")
            logger.info(f"  执行质量: {review.get('execution_quality', {}).get('score')}/10")
            logger.info(f"  风险管理: {review.get('risk_management', {}).get('score')}/10")
        except:
            logger.warning("⚠️  响应不是 JSON 格式")
        
        await provider.close()
        
    except Exception as e:
        logger.error(f"❌ 复盘失败: {e}")


async def test_prompt_manager_features():
    """测试提示词管理器功能"""
    logger.info("=" * 60)
    logger.info("测试提示词管理器功能")
    logger.info("=" * 60)
    
    pm = PromptManager()
    
    # 1. 加载系统提示词
    logger.info("\n1️⃣ 加载系统提示词:")
    for prompt_type in ["analysis", "learning", "review"]:
        system_prompt = pm.get_system_prompt(prompt_type)
        logger.info(f"  {prompt_type}: {len(system_prompt)} 字符")
    
    # 2. 加载用户模板
    logger.info("\n2️⃣ 加载用户提示词模板:")
    for prompt_type in ["analysis", "learning", "review"]:
        user_template = pm.get_user_template(prompt_type)
        logger.info(f"  {prompt_type}: {len(user_template)} 字符")
    
    # 3. 格式化测试
    logger.info("\n3️⃣ 格式化用户提示词:")
    data = {"symbol": "BTCUSDT", "current_price": "95000"}
    formatted = pm.format_user_prompt("analysis", data)
    logger.info(f"  已填充占位符: symbol, current_price")
    logger.info(f"  未填充占位符保持原样: {{change_24h}}")
    
    # 4. 缓存测试
    logger.info("\n4️⃣ 测试缓存功能:")
    logger.info(f"  首次加载: analysis system")
    pm.get_system_prompt("analysis")
    logger.info(f"  二次加载（从缓存）: analysis system")
    pm.get_system_prompt("analysis")
    logger.info(f"  清除缓存")
    pm.clear_cache()
    logger.info(f"  清除后加载: analysis system")
    pm.get_system_prompt("analysis")
    
    logger.info("\n✅ 提示词管理器功能测试完成")


async def main():
    """主函数"""
    logger.info("🚀 提示词管理器示例\n")
    
    print("选择测试:")
    print("1. 市场分析提示词")
    print("2. 学习辅导提示词")
    print("3. 交易复盘提示词")
    print("4. 提示词管理器功能测试")
    choice = input("请输入 (1/2/3/4): ").strip()
    
    if choice == "1":
        await test_analysis_prompt()
    elif choice == "2":
        await test_learning_prompt()
    elif choice == "3":
        await test_review_prompt()
    elif choice == "4":
        await test_prompt_manager_features()
    else:
        logger.error("无效的选择")


if __name__ == "__main__":
    asyncio.run(main())

