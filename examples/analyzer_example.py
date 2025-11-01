"""
MarketAnalyzer 完整示例

演示如何使用 MarketAnalyzer 的三种模式：
1. 市场分析 (analysis) - 自动使用 prompts/analysis/
2. 学习辅导 (learning) - 自动使用 prompts/learning/
3. 交易复盘 (review) - 自动使用 prompts/review/
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tradingai.ai import AIProviderFactory
from tradingai.ai.analyzers import MarketAnalyzer
from tradingai.logger import get_logger

logger = get_logger("examples.analyzer")


async def test_market_analysis():
    """
    测试市场分析功能
    
    自动使用提示词：
    - 系统提示词: prompts/analysis/system.txt
    - 用户提示词: prompts/analysis/user.txt
    """
    logger.info("=" * 60)
    logger.info("测试 1: 市场分析 (使用 prompts/analysis/)")
    logger.info("=" * 60)
    
    # 1. 创建 AI 提供商
    provider = AIProviderFactory.create_from_config()
    logger.info(f"✅ AI 提供商: {provider.get_provider_name()}")
    
    # 2. 创建市场分析器（自动加载提示词管理器）
    analyzer = MarketAnalyzer(provider)
    logger.info(f"✅ 市场分析器已初始化")
    logger.info(f"📁 提示词目录: prompts/analysis/")
    
    # 3. 准备模拟市场数据
    klines = [
        {
            'open': 94800.0,
            'high': 95500.0,
            'low': 94200.0,
            'close': 95234.5,
            'volume': 28500.0
        }
    ]
    
    indicators = {
        'ema_7': [94800.0],
        'ema_20': [94500.0],
        'ema_50': [93200.0],
        'rsi': [68.5],
        'macd': [150.23],
        'atr': [1250.50]
    }
    
    try:
        # 4. 调用分析（自动使用 prompts/analysis/ 提示词）
        logger.info("\n📊 开始分析...")
        logger.info("提示词流程:")
        logger.info("  1. 加载 prompts/analysis/system.txt (定义分析师角色)")
        logger.info("  2. 加载 prompts/analysis/user.txt (填充市场数据)")
        logger.info("  3. 发送到 AI 提供商")
        logger.info("  4. 解析 AI 响应为结构化数据\n")
        
        result = await analyzer.analyze_market(
            symbol="BTCUSDT",
            klines=klines,
            indicators=indicators,
            timeframe="1h"
        )
        
        # 5. 显示分析结果
        logger.info("\n📥 分析结果:")
        logger.info(f"  交易对: {result['symbol']}")
        logger.info(f"  趋势: {result['trend']}")
        logger.info(f"  建议: {result['action']}")
        logger.info(f"  置信度: {result['confidence']:.1%}")
        logger.info(f"  入场价: ${result['entry_price']:,.2f}")
        logger.info(f"  止损: ${result['stop_loss']:,.2f}")
        logger.info(f"  止盈: ${result['take_profit']:,.2f}")
        logger.info(f"  支撑位: ${result['support']:,.2f}")
        logger.info(f"  阻力位: ${result['resistance']:,.2f}")
        logger.info(f"  风险回报比: {result['risk_reward_ratio']}")
        logger.info(f"\n  分析原因:\n  {result['reason']}")
        
        if result.get('warnings'):
            logger.info(f"\n  ⚠️  风险提示:")
            for warning in result['warnings']:
                logger.info(f"    - {warning}")
        
        logger.info(f"\n  提供商: {result['provider']}")
        logger.info(f"  分析时间: {result['analyzed_at']}")
        
    except Exception as e:
        logger.error(f"❌ 分析失败: {e}")
    
    finally:
        await analyzer.close()


async def test_learning():
    """
    测试学习辅导功能
    
    自动使用提示词：
    - 系统提示词: prompts/learning/system.txt
    - 用户提示词: prompts/learning/user.txt
    """
    logger.info("\n" + "=" * 60)
    logger.info("测试 2: 学习辅导 (使用 prompts/learning/)")
    logger.info("=" * 60)
    
    provider = AIProviderFactory.create_from_config()
    analyzer = MarketAnalyzer(provider)
    
    logger.info(f"✅ AI 提供商: {provider.get_provider_name()}")
    logger.info(f"📁 提示词目录: prompts/learning/")
    
    try:
        logger.info("\n📚 请求学习辅导...")
        logger.info("提示词流程:")
        logger.info("  1. 加载 prompts/learning/system.txt (定义导师角色)")
        logger.info("  2. 加载 prompts/learning/user.txt (填充学习主题)")
        logger.info("  3. 发送到 AI 提供商")
        logger.info("  4. 返回教学内容\n")
        
        learning_content = await analyzer.provide_learning(
            topic="EMA 指标的实战应用",
            level="初级",
            questions=[
                "EMA 和 MA 有什么本质区别？",
                "如何判断 EMA 金叉和死叉？",
                "EMA 7/20/50 在实际交易中如何配合使用？"
            ],
            goals="能够独立使用 EMA 指标进行趋势判断和交易决策"
        )
        
        logger.info("📥 学习内容:")
        logger.info(f"\n{learning_content}\n")
        
    except Exception as e:
        logger.error(f"❌ 学习辅导失败: {e}")
    
    finally:
        await analyzer.close()


async def test_trade_review():
    """
    测试交易复盘功能
    
    自动使用提示词：
    - 系统提示词: prompts/review/system.txt
    - 用户提示词: prompts/review/user.txt
    """
    logger.info("\n" + "=" * 60)
    logger.info("测试 3: 交易复盘 (使用 prompts/review/)")
    logger.info("=" * 60)
    
    provider = AIProviderFactory.create_from_config()
    analyzer = MarketAnalyzer(provider)
    
    logger.info(f"✅ AI 提供商: {provider.get_provider_name()}")
    logger.info(f"📁 提示词目录: prompts/review/")
    
    # 准备交易数据
    trade_data = {
        "symbol": "ETHUSDT",
        "direction": "做多",
        "trade_time": "2025-11-01 10:30:00",
        "duration": "3小时15分钟",
        "entry_price": "3250.00",
        "exit_price": "3380.00",
        "stop_loss": "3180.00",
        "take_profit": "3450.00",
        "profit_loss": "+1300.00",
        "profit_loss_percentage": "+4.0",
        "risk_reward_ratio": "1:2.86",
        "reasoning": "EMA7上穿EMA20形成金叉，RSI从45上升到62，突破前期阻力位3200，成交量放大",
        "entry_market_state": "震荡上行，突破阻力位",
        "exit_market_state": "快速上涨后遇到阻力",
        "indicators": "入场时: EMA7=3240, RSI=62, MACD正值增长\n出场时: EMA7=3365, RSI=75(接近超买), MACD柱状图减小",
        "entry_mindset": "看到金叉和突破信号后，按计划入场",
        "holding_process": "持仓过程比较顺利，价格稳步上涨",
        "exit_reason": "RSI接近超买区域(75)，MACD柱状图开始减小，选择提前止盈"
    }
    
    try:
        logger.info("\n🔍 开始复盘...")
        logger.info(f"交易: {trade_data['symbol']} {trade_data['direction']}")
        logger.info(f"盈亏: {trade_data['profit_loss']} ({trade_data['profit_loss_percentage']}%)")
        logger.info("\n提示词流程:")
        logger.info("  1. 加载 prompts/review/system.txt (定义复盘分析师角色)")
        logger.info("  2. 加载 prompts/review/user.txt (填充交易数据)")
        logger.info("  3. 发送到 AI 提供商")
        logger.info("  4. 解析复盘结果为结构化数据\n")
        
        review_result = await analyzer.review_trade(trade_data)
        
        logger.info("📥 复盘结果:")
        logger.info(f"  总体评价: {review_result.get('overall_rating', 'N/A')}")
        
        # 决策质量
        decision = review_result.get('decision_quality', {})
        logger.info(f"\n  决策质量: {decision.get('score', 0)}/10")
        logger.info(f"    {decision.get('comment', 'N/A')}")
        
        # 执行质量
        execution = review_result.get('execution_quality', {})
        logger.info(f"\n  执行质量: {execution.get('score', 0)}/10")
        logger.info(f"    {execution.get('comment', 'N/A')}")
        
        # 风险管理
        risk = review_result.get('risk_management', {})
        logger.info(f"\n  风险管理: {risk.get('score', 0)}/10")
        logger.info(f"    {risk.get('comment', 'N/A')}")
        
        # 优点
        if review_result.get('strengths'):
            logger.info("\n  ✅ 优点:")
            for strength in review_result['strengths']:
                logger.info(f"    - {strength}")
        
        # 缺点
        if review_result.get('weaknesses'):
            logger.info("\n  ⚠️  缺点:")
            for weakness in review_result['weaknesses']:
                logger.info(f"    - {weakness}")
        
        # 教训
        if review_result.get('lessons_learned'):
            logger.info("\n  📖 经验教训:")
            for lesson in review_result['lessons_learned']:
                logger.info(f"    - {lesson}")
        
        # 改进建议
        if review_result.get('improvements'):
            logger.info("\n  💡 改进建议:")
            for improvement in review_result['improvements']:
                logger.info(f"    - {improvement}")
        
        # 总结
        summary = review_result.get('summary', '')
        if summary:
            logger.info(f"\n  📝 总结:\n    {summary}")
        
        logger.info(f"\n  提供商: {review_result.get('provider', 'N/A')}")
        logger.info(f"  复盘时间: {review_result.get('reviewed_at', 'N/A')}")
        
    except Exception as e:
        logger.error(f"❌ 交易复盘失败: {e}")
    
    finally:
        await analyzer.close()


async def test_prompt_system():
    """测试提示词系统"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 4: 提示词系统验证")
    logger.info("=" * 60)
    
    from tradingai.ai.prompts import PromptManager
    
    pm = PromptManager()
    logger.info(f"📁 提示词根目录: {pm.prompts_dir}")
    logger.info(f"📋 支持的提示词类型: {', '.join(pm.PROMPT_TYPES)}")
    
    # 验证每种提示词
    for prompt_type in pm.PROMPT_TYPES:
        logger.info(f"\n✅ {prompt_type}:")
        
        # 系统提示词
        system_prompt = pm.get_system_prompt(prompt_type)
        logger.info(f"  - system.txt: {len(system_prompt)} 字符")
        logger.info(f"    前100字: {system_prompt[:100]}...")
        
        # 用户提示词模板
        user_template = pm.get_user_template(prompt_type)
        logger.info(f"  - user.txt: {len(user_template)} 字符")
        
        # 检查占位符
        import re
        placeholders = re.findall(r'\{(\w+)\}', user_template)
        logger.info(f"    占位符: {', '.join(placeholders[:5])}{'...' if len(placeholders) > 5 else ''}")


async def main():
    """主函数"""
    logger.info("🚀 MarketAnalyzer 完整示例")
    logger.info("=" * 60)
    logger.info("MarketAnalyzer 自动使用 prompts/ 目录下的提示词：")
    logger.info("  1. analysis/ - 市场分析和交易建议")
    logger.info("  2. learning/ - 交易知识学习辅导")
    logger.info("  3. review/ - 历史交易复盘分析")
    logger.info("=" * 60)
    
    print("\n选择测试:")
    print("1. 市场分析 (使用 prompts/analysis/)")
    print("2. 学习辅导 (使用 prompts/learning/)")
    print("3. 交易复盘 (使用 prompts/review/)")
    print("4. 提示词系统验证")
    print("5. 运行所有测试")
    choice = input("请输入 (1/2/3/4/5): ").strip()
    
    if choice == "1":
        await test_market_analysis()
    elif choice == "2":
        await test_learning()
    elif choice == "3":
        await test_trade_review()
    elif choice == "4":
        await test_prompt_system()
    elif choice == "5":
        await test_prompt_system()
        await test_market_analysis()
        await test_learning()
        await test_trade_review()
    else:
        logger.error("无效的选择")


if __name__ == "__main__":
    asyncio.run(main())

