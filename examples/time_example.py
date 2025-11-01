"""
时间工具使用示例
展示时间转换和K线周期对准功能
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tradingai import (
    config,
    utc_to_shanghai,
    shanghai_to_utc,
    now_shanghai,
    format_time,
    time_ago,
    align_to_timeframe,
    get_kline_range,
    get_next_kline_time,
    is_kline_closed,
    time_until_next_kline,
)
from tradingai.logger import get_logger

logger = get_logger("time_example")


async def main():
    """主程序"""
    try:
        logger.info("="*60)
        logger.info("⏰ 时间工具使用示例")
        logger.info("="*60)
        
        # 1. 时区转换
        logger.info("\n📍 1. 时区转换示例")
        logger.info("-" * 40)
        
        # 当前时间
        utc_now = datetime.utcnow()
        shanghai_now = now_shanghai()
        
        logger.info(f"   UTC时间: {utc_now}")
        logger.info(f"   上海时间: {format_time(shanghai_now)}")
        
        # 时间戳转换
        timestamp = 1698840000
        shanghai_time = utc_to_shanghai(timestamp)
        logger.info(f"   时间戳 {timestamp} → {format_time(shanghai_time)}")
        
        # 2. 时间格式化
        logger.info("\n📅 2. 时间格式化示例")
        logger.info("-" * 40)
        
        current = now_shanghai()
        logger.info(f"   默认格式: {format_time(current, 'default')}")
        logger.info(f"   完整格式: {format_time(current, 'full')}")
        logger.info(f"   简短格式: {format_time(current, 'short')}")
        logger.info(f"   仅日期: {format_time(current, 'date')}")
        logger.info(f"   仅时间: {format_time(current, 'time')}")
        logger.info(f"   ISO格式: {format_time(current, 'iso')}")
        
        # 3. 相对时间
        logger.info("\n⏱️  3. 相对时间示例")
        logger.info("-" * 40)
        
        past_times = [
            (30, "秒"),
            (5 * 60, "5分钟"),
            (2 * 3600, "2小时"),
            (3 * 86400, "3天"),
        ]
        
        for seconds, desc in past_times:
            past = current - timedelta(seconds=seconds)
            logger.info(f"   {desc}前: {time_ago(past)}")
        
        # 4. K线周期对准
        logger.info("\n🎯 4. K线周期对准示例")
        logger.info("-" * 40)
        
        # 测试时间：2024-11-01 13:25:30
        test_time = now_shanghai()
        logger.info(f"   原始时间: {format_time(test_time)}")
        logger.info("")
        
        # 不同周期的对准
        timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
        
        for tf in timeframes:
            aligned = align_to_timeframe(test_time, tf)
            logger.info(f"   {tf:>4} 周期对准: {format_time(aligned)}")
        
        # 5. K线时间范围
        logger.info("\n📊 5. K线时间范围示例")
        logger.info("-" * 40)
        
        timeframe = config.TIMEFRAME
        logger.info(f"   当前配置周期: {timeframe}")
        logger.info("")
        
        # 获取当前K线范围
        start, end = get_kline_range(test_time, timeframe)
        logger.info(f"   当前K线范围:")
        logger.info(f"     开始: {format_time(start)}")
        logger.info(f"     结束: {format_time(end)}")
        
        # 获取下一根K线时间
        next_kline = get_next_kline_time(test_time, timeframe)
        logger.info(f"   下根K线: {format_time(next_kline)}")
        
        # 6. K线状态检测
        logger.info("\n✅ 6. K线状态检测示例")
        logger.info("-" * 40)
        
        # 检测不同时间的K线是否完成
        test_times = [
            ("1小时前", test_time - timedelta(hours=1)),
            ("30分钟前", test_time - timedelta(minutes=30)),
            ("5分钟前", test_time - timedelta(minutes=5)),
            ("当前时间", test_time),
        ]
        
        logger.info(f"   周期: {timeframe}")
        for desc, t in test_times:
            closed = is_kline_closed(t, timeframe)
            status = "✅ 已完成" if closed else "⏳ 进行中"
            logger.info(f"   {desc:>8}: {format_time(t, 'time')} → {status}")
        
        # 7. 倒计时功能
        logger.info("\n⏳ 7. K线倒计时示例")
        logger.info("-" * 40)
        
        for tf in ["1m", "5m", "15m", "1h"]:
            time_left = time_until_next_kline(tf)
            total_seconds = int(time_left.total_seconds())
            
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if hours > 0:
                time_str = f"{hours}小时{minutes}分钟{seconds}秒"
            elif minutes > 0:
                time_str = f"{minutes}分钟{seconds}秒"
            else:
                time_str = f"{seconds}秒"
            
            logger.info(f"   {tf:>4} 周期: 距离下根K线还有 {time_str}")
        
        # 8. 实战场景
        logger.info("\n💼 8. 实战场景示例")
        logger.info("-" * 40)
        
        # 场景：检查当前是否适合下单（在K线结束前1分钟不下单）
        current_time = now_shanghai()
        time_left = time_until_next_kline(config.TIMEFRAME, current_time)
        
        if time_left.total_seconds() < 60:
            logger.warning(f"   ⚠️  当前K线即将结束（剩余{int(time_left.total_seconds())}秒）")
            logger.warning(f"   建议等待下一根K线")
        else:
            logger.info(f"   ✅ 当前可以下单（K线剩余{int(time_left.total_seconds())}秒）")
        
        # 场景：批量对准历史K线时间
        logger.info("\n   批量对准示例:")
        historical_times = [
            current_time - timedelta(hours=i) for i in range(5, 0, -1)
        ]
        
        for i, ht in enumerate(historical_times, 1):
            aligned = align_to_timeframe(ht, config.TIMEFRAME)
            logger.info(f"     K线 {i}: {format_time(aligned)}")
        
        logger.info("\n✅ 示例完成")
    
    except KeyboardInterrupt:
        logger.info("\n⏹️  中断")
    except Exception as e:
        logger.error(f"❌ 错误: {e}", exc_info=True)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())

