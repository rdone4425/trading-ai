#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
指标计算示例
演示如何使用指标配置和计算引擎
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from tradingai import (
    config,
    smart_format,
    format_price,
    format_percentage,
    utc_to_shanghai,
    format_time,
    align_to_timeframe,
    get_kline_range,
    is_kline_closed,
    time_until_next_kline
)
from tradingai.scanner import MarketScanner
from tradingai.indicators import IndicatorEngine
from tradingai.logger import get_logger

logger = get_logger("example")


async def main():
    """主程序"""
    try:
        logger.info("="*60)
        logger.info("📊 指标计算示例")
        logger.info("="*60)
        
        # 检查实现方式
        from tradingai.indicators import IndicatorCalculator
        if IndicatorCalculator.using_talib():
            logger.info("✅ 使用 TA-Lib 实现（性能更优）")
        else:
            logger.info("ℹ️  使用纯 Python 实现")
        
        # 1. 创建扫描器并获取K线数据
        logger.info("\n🔍 步骤1: 获取K线数据")
        scanner = MarketScanner()
        await scanner.connect()
        
        symbols = await scanner.scan_symbols()
        symbol = symbols[0] if symbols else "BTCUSDT"
        logger.info(f"   选择交易对: {symbol}")
        
        klines = await scanner.get_klines(symbol)
        logger.info(f"   获取K线: {len(klines)} 根")
        
        if len(klines) < 30:
            logger.warning(f"   ⚠️  K线数据不足（少于30根），指标计算可能不准确")
        
        # 显示K线数据范围
        if klines:
            prices = [k['close'] for k in klines]
            logger.info(f"   价格范围: {format_price(min(prices))} - {format_price(max(prices))}")
            logger.info(f"   最后3根K线收盘价: {[format_price(p) for p in prices[-3:]]}")
            
            # 转换时间为上海时区
            start_time = utc_to_shanghai(klines[0]['timestamp'])
            end_time = utc_to_shanghai(klines[-1]['timestamp'])
            logger.info(f"   时间范围: {format_time(start_time)} 至 {format_time(end_time)} (上海时区)")
            
            # 显示K线周期对准信息
            logger.info(f"\n⏰ K线周期对准:")
            latest_kline_time = klines[-1]['timestamp']
            aligned_time = align_to_timeframe(latest_kline_time, config.TIMEFRAME)
            logger.info(f"   原始时间: {format_time(utc_to_shanghai(latest_kline_time))}")
            logger.info(f"   对准时间: {format_time(aligned_time)}")
            
            # 获取K线时间范围
            kline_start, kline_end = get_kline_range(latest_kline_time, config.TIMEFRAME)
            logger.info(f"   K线范围: {format_time(kline_start)} → {format_time(kline_end)}")
            
            # 判断K线是否完成
            is_closed = is_kline_closed(latest_kline_time, config.TIMEFRAME)
            logger.info(f"   K线状态: {'✅ 已完成' if is_closed else '⏳ 进行中'}")
            
            # 计算距离下一根K线的时间
            time_left = time_until_next_kline(config.TIMEFRAME)
            minutes, seconds = divmod(int(time_left.total_seconds()), 60)
            hours, minutes = divmod(minutes, 60)
            if hours > 0:
                logger.info(f"   下根K线: {hours}小时{minutes}分钟{seconds}秒后")
            elif minutes > 0:
                logger.info(f"   下根K线: {minutes}分钟{seconds}秒后")
            else:
                logger.info(f"   下根K线: {seconds}秒后")
        
        # 2. 方法一：使用配置字符串
        logger.info("\n⚙️  方法1: 使用配置字符串")
        config_str = """
        ema=7,20,120
        ma=20,30,60
        rsi=14
        atr=14
        macd=12,26,9
        """
        
        engine = IndicatorEngine(config_str)
        logger.info(engine.summary())
        
        # 计算所有指标
        logger.info("\n📈 计算所有指标:")
        all_indicators = engine.calculate_all(klines)
        logger.info(f"   计算完成，共 {len(all_indicators)} 个结果")
        
        # 显示每个指标的有效数据量（调试模式：显示原始值）
        if logger.level <= 10:  # DEBUG级别
            for name, values in all_indicators.items():
                valid_values = values[~np.isnan(values)]
                valid_count = len(valid_values)
                if valid_count > 0:
                    last_value = valid_values[-1]
                    logger.debug(f"   {name}: {valid_count}/{len(values)} 有效值, 最后值={smart_format(last_value)}")
                else:
                    logger.debug(f"   {name}: {valid_count}/{len(values)} 有效值")
        
        # 使用格式化输出
        latest = engine.get_latest_values(klines, format_output=True)
        
        logger.info("\n   最新值:")
        for name, value in latest.items():
            logger.info(f"     {name}: {value}")
        
        # 3. EMA 交叉检测
        logger.info("\n🔀 EMA 交叉检测:")
        cross_7_20 = engine.detect_ema_cross(klines, 7, 20)
        
        if cross_7_20:
            logger.info(f"   EMA(7) vs EMA(20):")
            logger.info(f"     最新交叉: {cross_7_20.get('latest_cross', 'None')} {'🟢' if cross_7_20.get('latest_cross') == 'golden' else '🔴' if cross_7_20.get('latest_cross') == 'death' else ''}")
            logger.info(f"     当前位置: {cross_7_20.get('current_position', 'unknown')}")
            logger.info(f"     EMA(7): {smart_format(cross_7_20.get('fast_value', 0))}")
            logger.info(f"     EMA(20): {smart_format(cross_7_20.get('slow_value', 0))}")
            logger.info(f"     金叉次数: {len(cross_7_20.get('golden_crosses', []))}")
            logger.info(f"     死叉次数: {len(cross_7_20.get('death_crosses', []))}")
            
            cross_20_120 = engine.detect_ema_cross(klines, 20, 120)
            logger.info(f"\n   EMA(20) vs EMA(120):")
            logger.info(f"     最新交叉: {cross_20_120.get('latest_cross', 'None')} {'🟢' if cross_20_120.get('latest_cross') == 'golden' else '🔴' if cross_20_120.get('latest_cross') == 'death' else ''}")
            logger.info(f"     当前位置: {cross_20_120.get('current_position', 'unknown')}")
        else:
            logger.warning("   交叉检测失败（可能是 TA-Lib 未安装）")
        
        # 4. 方法二：从环境变量加载
        logger.info("\n⚙️  方法2: 从环境变量加载")
        engine2 = IndicatorEngine()
        engine2.load_from_env("INDICATOR")
        
        if engine2.get_indicators():
            logger.info(engine2.summary())
            
            # 计算所有指标（使用格式化输出）
            env_latest = engine2.get_latest_values(klines, format_output=True)
            logger.info(f"\n📊 环境变量指标的最新值:")
            for name, value in env_latest.items():
                logger.info(f"    {name}: {value}")
        else:
            logger.info("   未配置环境变量指标")
        
        # 断开连接
        await scanner.disconnect()
        
        logger.info("\n✅ 示例完成")
    
    except KeyboardInterrupt:
        logger.info("\n⏹️  中断")
    except Exception as e:
        logger.error(f"❌ 错误: {e}", exc_info=True)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())

