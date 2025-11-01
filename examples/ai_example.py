#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 提供商示例 - 演示如何使用 AI 工厂
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tradingai import config
from tradingai.ai import AIProviderFactory
from tradingai.scanner import MarketScanner
from tradingai.indicators import IndicatorEngine
from tradingai.logger import get_logger

logger = get_logger("example.ai")


async def main():
    """主函数"""
    try:
        logger.info("="*60)
        logger.info("AI 提供商示例")
        logger.info("="*60)
        logger.info("")
        
        # 1. 列出所有支持的提供商
        providers = AIProviderFactory.list_providers()
        logger.info(f"支持的 AI 提供商: {', '.join(providers)}")
        logger.info("")
        
        # 2. 从配置创建 AI 提供商
        logger.info("从配置创建 AI 提供商...")
        ai_provider = AIProviderFactory.create_from_config()
        logger.info(f"提供商: {ai_provider.get_provider_name()}")
        logger.info("")
        
        # 3. 获取市场数据
        logger.info("获取市场数据...")
        scanner = MarketScanner()
        await scanner.connect()
        
        symbols = await scanner.scan_symbols()
        if not symbols:
            logger.warning("未找到交易对")
            return
        
        symbol = symbols[0]
        logger.info(f"分析交易对: {symbol}")
        logger.info("")
        
        # 4. 获取K线数据
        klines = await scanner.platform.get_klines(
            symbol=symbol,
            interval=config.TIMEFRAME,
            limit=config.LOOKBACK,
            include_current=(config.KLINE_TYPE == 'open')
        )
        
        if not klines:
            logger.warning("未获取到K线数据")
            return
        
        logger.info(f"获取到 {len(klines)} 根K线")
        
        # 5. 计算指标
        logger.info("计算技术指标...")
        indicator_engine = IndicatorEngine()
        indicators = indicator_engine.calculate_all(klines)
        
        if indicators:
            logger.info(f"计算了 {len(indicators)} 个指标")
        
        # 6. 使用 AI 分析市场
        logger.info("")
        logger.info("="*60)
        logger.info("AI 市场分析")
        logger.info("="*60)
        
        analysis_result = await ai_provider.analyze_market(
            symbol=symbol,
            klines=klines,
            indicators=indicators
        )
        
        # 7. 显示分析结果
        logger.info("")
        logger.info("分析结果:")
        logger.info(f"  交易对: {symbol}")
        logger.info(f"  信号: {analysis_result.get('signal', 'N/A').upper()}")
        logger.info(f"  置信度: {analysis_result.get('confidence', 0):.2%}")
        logger.info(f"  当前价格: ${analysis_result.get('current_price', 0):.4f}")
        logger.info(f"  目标价格: ${analysis_result.get('target_price', 0):.4f}")
        logger.info(f"  止损价格: ${analysis_result.get('stop_loss', 0):.4f}")
        logger.info(f"  分析原因: {analysis_result.get('reason', 'N/A')}")
        logger.info("")
        
        # 8. 测试对话功能
        logger.info("="*60)
        logger.info("AI 对话测试")
        logger.info("="*60)
        
        messages = [
            {
                "role": "user",
                "content": f"请简要分析 {symbol} 的当前市场情况"
            }
        ]
        
        response = await ai_provider.chat(messages)
        logger.info(f"AI 响应: {response}")
        logger.info("")
        
        # 断开连接
        await scanner.disconnect()
        await ai_provider.close()
        
        logger.info("="*60)
        logger.info("示例完成！")
        logger.info("="*60)
    
    except Exception as e:
        logger.error(f"错误: {e}", exc_info=True)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())


