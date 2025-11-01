#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自定义扫描示例 - 演示如何自定义扫描逻辑和回调
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tradingai import config, format_price, format_percentage, format_volume
from tradingai.scanner import MarketScanner
from tradingai.indicators import IndicatorEngine
from tradingai.logger import get_logger

logger = get_logger("example.custom_scan")


class CustomScanner:
    """自定义扫描器"""
    
    def __init__(self):
        self.scanner = None
        self.indicator_engine = None
        self.scan_count = 0
    
    async def initialize(self):
        """初始化"""
        logger.info("初始化扫描器...")
        
        # 创建市场扫描器
        self.scanner = MarketScanner()
        await self.scanner.connect()
        
        # 创建指标引擎
        self.indicator_engine = IndicatorEngine()
        
        logger.info("✅ 初始化完成")
    
    async def scan_callback(self, symbols, tickers):
        """
        自定义扫描回调 - 分析每个交易对并计算指标
        
        Args:
            symbols: 扫描到的交易对列表
            tickers: 交易对的行情数据字典
        """
        self.scan_count += 1
        
        logger.info("")
        logger.info(f"📊 第 {self.scan_count} 次扫描完成")
        logger.info(f"   交易对数量: {len(symbols)}")
        
        # 分析每个交易对
        signals = []
        
        for symbol in symbols[:10]:  # 只分析前10个
            try:
                # 获取K线数据
                klines = await self.scanner.platform.get_klines(
                    symbol=symbol,
                    interval=config.TIMEFRAME,
                    limit=config.LOOKBACK,
                    include_current=(config.KLINE_TYPE == 'open')
                )
                
                if not klines:
                    continue
                
                # 计算指标
                indicators = self.indicator_engine.calculate_all(klines)
                
                if not indicators:
                    continue
                
                # 获取最新指标值
                latest = self.indicator_engine.get_latest_values(indicators)
                
                # 检测EMA交叉
                ema_cross = None
                if 'ema_7' in latest and 'ema_20' in latest:
                    cross_info = self.indicator_engine.detect_ema_cross(
                        indicators, 'ema_7', 'ema_20', lookback=3
                    )
                    if cross_info:
                        ema_cross = cross_info
                
                # 获取价格信息
                ticker = tickers.get(symbol, {})
                price = ticker.get('price', 0)
                change = ticker.get('price_change_percent', 0)
                
                # 检查是否有交易信号
                has_signal = False
                signal_desc = []
                
                # 示例：EMA金叉/死叉
                if ema_cross:
                    has_signal = True
                    cross_type = "金叉 🔼" if ema_cross['cross_type'] == 'golden' else "死叉 🔽"
                    signal_desc.append(f"EMA(7/20) {cross_type}")
                
                # 示例：RSI超买超卖
                if 'rsi' in latest:
                    rsi = latest['rsi']
                    if rsi > 70:
                        has_signal = True
                        signal_desc.append(f"RSI超买({rsi:.1f})")
                    elif rsi < 30:
                        has_signal = True
                        signal_desc.append(f"RSI超卖({rsi:.1f})")
                
                # 记录有信号的交易对
                if has_signal:
                    signals.append({
                        'symbol': symbol,
                        'price': price,
                        'change': change,
                        'signals': signal_desc,
                        'indicators': latest
                    })
            
            except Exception as e:
                logger.debug(f"分析 {symbol} 失败: {e}")
                continue
        
        # 显示有信号的交易对
        if signals:
            logger.info("")
            logger.info(f"🎯 发现 {len(signals)} 个交易信号:")
            for sig in signals:
                logger.info(f"   {sig['symbol']:12s} {format_price(sig['price']):>12s} ({format_percentage(sig['change']):>8s})")
                for desc in sig['signals']:
                    logger.info(f"      ↳ {desc}")
        else:
            logger.info("   暂无交易信号")
        
        logger.info("")
    
    async def start(self):
        """启动自动扫描"""
        try:
            logger.info("="*60)
            logger.info("🤖 自定义扫描示例")
            logger.info("="*60)
            logger.info("")
            
            # 显示配置
            logger.info("⚙️  配置:")
            logger.info(f"   交易所: {config.EXCHANGE_NAME}")
            logger.info(f"   周期: {config.TIMEFRAME}")
            logger.info(f"   K线数: {config.LOOKBACK}")
            logger.info(f"   K线类型: {config.KLINE_TYPE}")
            logger.info("")
            logger.info("提示: 按 Ctrl+C 停止扫描")
            logger.info("")
            
            # 初始化
            await self.initialize()
            
            # 启动自动扫描
            await self.scanner.start_auto_scan(
                callback=self.scan_callback,
                align_to_kline=True,
                wait_for_close=True
            )
            
            # 等待运行
            while self.scanner.is_scanning:
                await asyncio.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("")
            logger.info("⏹️  收到中断信号，停止扫描...")
            await self.stop()
            logger.info("✅ 已停止")
        
        except Exception as e:
            logger.error(f"❌ 错误: {e}", exc_info=True)
            await self.stop()
    
    async def stop(self):
        """停止扫描"""
        if self.scanner:
            if self.scanner.is_scanning:
                await self.scanner.stop_auto_scan()
            await self.scanner.disconnect()


async def main():
    """主函数"""
    scanner = CustomScanner()
    await scanner.start()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())

