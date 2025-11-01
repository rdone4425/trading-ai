"""
测试扫描器传递给AI的数据结构

这个示例展示：
1. 扫描器获取的K线数据结构
2. 扫描器计算的指标数据结构
3. AI分析器接收到的数据格式
"""

import asyncio
import json
from pathlib import Path

# 添加项目根目录到路径
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingai.scanner.market_scanner import MarketScanner
from tradingai.indicators.indicator_engine import IndicatorEngine
from tradingai.ai.analyzers.market_analyzer import MarketAnalyzer
from tradingai.ai.factory import AIProviderFactory
from tradingai.exchange.factory import PlatformFactory
from tradingai.logger import get_logger
import tradingai.config as config

logger = get_logger(__name__)


async def test_data_flow():
    """测试数据流：扫描器 → AI分析器"""
    
    logger.info("=" * 60)
    logger.info("测试数据流：扫描器 → AI分析器")
    logger.info("=" * 60)
    
    # 1. 创建交易所平台
    logger.info("\n1️⃣  创建交易所平台...")
    platform = await PlatformFactory.create_from_config()
    if not platform:
        logger.error("❌ 无法创建交易所平台")
        return
    
    logger.info(f"✅ 平台创建成功: {platform.__class__.__name__}")
    
    # 2. 创建指标引擎
    logger.info("\n2️⃣  创建指标引擎...")
    indicator_engine = IndicatorEngine()
    indicator_engine.load_from_env()
    logger.info(f"✅ 指标引擎创建成功，配置了 {len(indicator_engine.config)} 个指标")
    
    # 3. 创建AI提供商和分析器
    logger.info("\n3️⃣  创建AI分析器...")
    try:
        ai_provider = AIProviderFactory.create_from_config()
        if not ai_provider:
            logger.warning("⚠️  未配置AI提供商，将只测试数据获取")
            analyzer = None
        else:
            analyzer = MarketAnalyzer(
                provider=ai_provider,
                indicator_engine=indicator_engine,
                enable_risk_calculation=True,
                platform=platform
            )
            logger.info(f"✅ AI分析器创建成功: {ai_provider.get_provider_name()}")
    except Exception as e:
        logger.error(f"❌ 创建AI分析器失败: {e}")
        analyzer = None
    
    # 4. 创建扫描器
    logger.info("\n4️⃣  创建市场扫描器...")
    scanner = MarketScanner(
        platform=platform,
        analyzer=analyzer,
        indicator_engine=indicator_engine
    )
    logger.info("✅ 扫描器创建成功")
    
    # 5. 扫描一个交易对
    logger.info("\n5️⃣  扫描交易对（仅测试第一个）...")
    symbols = await scanner.scan_symbols()
    if not symbols:
        logger.warning("⚠️  未扫描到交易对")
        await platform.disconnect()
        return
    
    test_symbol = symbols[0]
    logger.info(f"✅ 测试交易对: {test_symbol}")
    
    # 6. 分析该交易对（展示数据流）
    logger.info("\n" + "=" * 60)
    logger.info(f"6️⃣  分析 {test_symbol}（展示数据流）")
    logger.info("=" * 60)
    
    result = await scanner.analyze_symbol(test_symbol)
    
    if result:
        logger.info("\n✅ 分析完成！")
        logger.info(f"\n分析结果摘要:")
        logger.info(f"  - 交易对: {result.get('symbol', 'N/A')}")
        logger.info(f"  - 操作建议: {result.get('action', 'N/A')}")
        logger.info(f"  - 置信度: {result.get('confidence', 0):.1%}")
        logger.info(f"  - 趋势: {result.get('trend', 'N/A')}")
        logger.info(f"  - 入场价格: {result.get('entry_price', 'N/A')}")
        logger.info(f"  - 止损: {result.get('stop_loss', 'N/A')}")
        logger.info(f"  - 止盈: {result.get('take_profit', 'N/A')}")
        logger.info(f"  - 杠杆: {result.get('leverage', 'N/A')}")
        
        # 保存完整结果到文件
        output_file = project_root / "data" / "data_flow_test_result.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"\n💾 完整分析结果已保存到: {output_file}")
    else:
        logger.warning("⚠️  分析失败或返回空结果")
    
    # 7. 清理
    logger.info("\n7️⃣  清理资源...")
    if analyzer:
        analyzer.close()
    await platform.disconnect()
    logger.info("✅ 清理完成")
    
    logger.info("\n" + "=" * 60)
    logger.info("测试完成！")
    logger.info("=" * 60)
    logger.info("\n💡 提示：查看上述日志中的 DEBUG 级别信息，可以看到详细的数据结构")


if __name__ == "__main__":
    # 设置日志级别为DEBUG以查看详细数据流
    import logging
    logging.getLogger("tradingai").setLevel(logging.DEBUG)
    
    asyncio.run(test_data_flow())

