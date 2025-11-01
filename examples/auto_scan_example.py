#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动扫描示例 - 演示如何使用市场扫描器的自动扫描功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tradingai import config, format_price, format_percentage, format_volume
from tradingai.scanner import MarketScanner
from tradingai.logger import get_logger

logger = get_logger("example.auto_scan")


async def scan_callback(symbols, tickers):
    """
    扫描完成后的回调函数
    
    Args:
        symbols: 扫描到的交易对列表
        tickers: 交易对的行情数据字典
    """
    logger.info("")
    logger.info("📊 扫描结果:")
    logger.info(f"   交易对数量: {len(symbols)}")
    
    # 显示前5个交易对的详细信息
    if symbols:
        logger.info("")
        logger.info("💰 前5个交易对:")
        for symbol in symbols[:5]:
            ticker = tickers.get(symbol)
            if ticker:
                price = ticker.get('price', 0)
                change = ticker.get('price_change_percent', 0)
                volume = ticker.get('volume', 0)
                logger.info(
                    f"   {symbol:12s} "
                    f"价格: {format_price(price):>12s} "
                    f"涨跌: {format_percentage(change):>8s} "
                    f"量: {format_volume(volume):>10s}"
                )
    
    logger.info("")


async def main():
    """主函数"""
    try:
        logger.info("="*60)
        logger.info("🤖 自动扫描示例")
        logger.info("="*60)
        logger.info("")
        
        # 显示配置
        logger.info("⚙️  配置:")
        logger.info(f"   交易所: {config.EXCHANGE_NAME}")
        logger.info(f"   周期: {config.TIMEFRAME}")
        logger.info(f"   K线数: {config.LOOKBACK}")
        logger.info(f"   K线类型: {config.KLINE_TYPE} ({'已完成' if config.KLINE_TYPE == 'closed' else '进行中'})")
        
        # 扫描配置
        if config.CUSTOM_SYMBOLS_RAW:
            logger.info(f"   扫描模式: 自定义交易对")
            logger.info(f"   交易对: {config.CUSTOM_SYMBOLS_RAW}")
        else:
            logger.info(f"   扫描模式: {config.SCAN_TYPES}")
            logger.info(f"   数量: {config.SCAN_TOP_N}")
        
        logger.info("")
        logger.info("提示: 按 Ctrl+C 停止扫描")
        logger.info("")
        
        # 创建扫描器
        scanner = MarketScanner()
        await scanner.connect()
        
        # 启动自动扫描
        # align_to_kline=True: 对准K线周期
        # wait_for_close=True: 等待K线完成后再扫描（仅在 KLINE_TYPE='closed' 时有效）
        await scanner.start_auto_scan(
            callback=scan_callback,
            align_to_kline=True,
            wait_for_close=True
        )
        
        # 等待扫描运行（直到被中断）
        while scanner.is_scanning:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("")
        logger.info("⏹️  收到中断信号，停止扫描...")
        if scanner.is_scanning:
            await scanner.stop_auto_scan()
        await scanner.disconnect()
        logger.info("✅ 已停止")
    
    except Exception as e:
        logger.error(f"❌ 错误: {e}", exc_info=True)
        if scanner and scanner.is_scanning:
            await scanner.stop_auto_scan()
        if scanner:
            await scanner.disconnect()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())

