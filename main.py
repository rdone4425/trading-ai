#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Trading AI - 智能交易系统

集成市场扫描、技术指标计算和 AI 分析
"""
import asyncio
import sys
from tradingai import config, format_price, format_percentage, format_volume
from tradingai.scanner import MarketScanner
from tradingai.indicators import IndicatorEngine, IndicatorConfigParser
from tradingai.ai import AIProviderFactory
from tradingai.ai.analyzers import MarketAnalyzer
from tradingai.trader import Trader
from tradingai.logger import get_logger
from typing import List, Dict, Any, Optional
from datetime import datetime

# 初始化日志
logger = get_logger("main")


async def enhance_analysis_with_learning_and_review(
    analyzer: MarketAnalyzer,
    analysis_results: List[Dict[str, Any]],
    platform=None
):
    """
    通过学习和复盘辅助分析，提升分析质量
    
    Args:
        analyzer: 市场分析器
        analysis_results: 分析结果列表
        platform: 交易平台实例（用于获取交易历史）
    """
    if not analysis_results:
        return
    
    try:
        logger.info(f"\n{'='*60}")
        logger.info("📚 开始学习和复盘（辅助分析改进）")
        logger.info(f"{'='*60}")
        
        # 1. 学习：从本次分析中提取知识点
        if config.ENABLE_AUTO_LEARNING:
            await perform_learning_from_analysis(analyzer, analysis_results)
        
        # 2. 复盘：从交易所获取历史交易，复盘并学习
        if config.ENABLE_AUTO_REVIEW:
            await perform_review_from_history(analyzer, analysis_results, platform)
        
        logger.info("✅ 学习和复盘完成，分析能力已提升")
        
    except Exception as e:
        logger.error(f"❌ 学习和复盘过程出错: {e}", exc_info=True)


async def perform_learning_from_analysis(
    analyzer: MarketAnalyzer,
    analysis_results: List[Dict[str, Any]]
):
    """
    从分析结果中学习，提取交易策略和指标使用方法
    
    Args:
        analyzer: 市场分析器
        analysis_results: 分析结果列表
    """
    try:
        # 提取本次分析中的关键信息
        trading_standards = []
        indicators_used = set()
        actions = {}
        
        for result in analysis_results:
            # 收集交易标准
            standard = result.get('trading_standard', '')
            if standard and standard != '未提供':
                trading_standards.append(standard)
            
            # 收集使用的指标（从 reason 中提取）
            reason = result.get('reason', '')
            if reason:
                # 简单提取：EMA, MA, RSI, MACD 等
                indicator_keywords = ['EMA', 'MA', 'RSI', 'MACD', 'KDJ', 'BOLL', 'ATR']
                for keyword in indicator_keywords:
                    if keyword in reason.upper():
                        indicators_used.add(keyword)
            
            # 统计操作
            action = result.get('action', '观望')
            actions[action] = actions.get(action, 0) + 1
        
        # 构建学习主题
        topics = []
        
        if trading_standards:
            topics.append(f"交易标准应用：{', '.join(set(trading_standards[:3]))}")
        
        if indicators_used:
            topics.append(f"技术指标实战：{', '.join(sorted(indicators_used))}")
        
        if actions:
            most_action = max(actions.items(), key=lambda x: x[1])[0]
            if most_action != '观望':
                topics.append(f"交易信号判断：如何识别{most_action}机会")
        
        # 如果没有自动生成的主题，使用配置的主题
        if not topics and config.AUTO_LEARNING_TOPICS:
            topics = config.AUTO_LEARNING_TOPICS
        
        if not topics:
            topics = ["技术指标综合应用", "风险管理策略"]
        
        # 生成学习内容
        for i, topic in enumerate(topics[:2], 1):  # 最多学习2个主题
            try:
                logger.info(f"\n📖 学习主题 {i}: {topic}")
                
                learning_result = await analyzer.provide_learning(
                    topic=topic,
                    level="中级",  # 基于实际分析经验
                    questions=[
                        "如何在实际交易中应用这个策略？",
                        "有哪些需要注意的风险点？",
                        "如何与本次分析结果结合？"
                    ],
                    goals="提升分析准确性和交易判断能力"
                )
                
                # 将学习结果添加到知识库（并保存到上下文）
                if learning_result:
                    await analyzer.add_learning_result(learning_result)
                    
                    # 提取关键信息
                    key_points = learning_result.get('content', '')
                    if isinstance(key_points, str):
                        logger.info(f"✅ 学习完成")
                        logger.debug(f"学习内容: {key_points[:200]}...")
                    else:
                        logger.info(f"✅ 学习完成: {learning_result.get('topic', 'N/A')}")
                
            except Exception as e:
                logger.warning(f"⚠️  学习主题 '{topic}' 失败: {e}")
        
    except Exception as e:
        logger.error(f"❌ 学习过程失败: {e}", exc_info=True)


async def perform_review_from_history(
    analyzer: MarketAnalyzer,
    analysis_results: List[Dict[str, Any]],
    platform=None
):
    """
    复盘历史交易，改进分析策略（从交易所自动获取）
    
    Args:
        analyzer: 市场分析器
        analysis_results: 当前分析结果（用于对比）
        platform: 交易平台实例（用于获取交易历史）
    """
    try:
        logger.info("\n📊 复盘历史交易（从交易所自动获取）")
        
        if not platform:
            logger.info("  ℹ️  未提供交易平台实例，跳过复盘")
            logger.info("  💡 提示：需要连接交易所才能获取交易历史")
            return
        
        # 从交易所获取最近1天的已平仓交易
        try:
            # 不传递时间参数，让 get_closed_trades 使用默认的最近1天
            closed_trades = await platform.get_closed_trades(limit=100)  # 最多100笔
            
            if not closed_trades:
                # 没有交易历史，静默跳过（可能是没有交易或API权限问题）
                return
            
            # 转换为复盘格式（需要配对买入和卖出，计算完整交易）
            reviewed_trades = _process_trades_for_review(closed_trades)
            
            if not reviewed_trades:
                logger.info("  ℹ️  无完整交易可复盘（需要配对买入和卖出）")
                return
            
            # 复盘最近的交易（最多5个）
            recent_trades = reviewed_trades[:5]
            
            logger.info(f"  📋 复盘最近1天的 {len(recent_trades)} 笔完整交易")
            
            # 加载已复盘的交易对记录
            context_manager = analyzer.context_manager
            reviewed_symbols = await context_manager.load_reviewed_symbols()
            
            reviewed_count = 0
            skipped_count = 0
            
            for i, trade in enumerate(recent_trades, 1):
                try:
                    symbol = trade.get('symbol', 'N/A')
                    
                    # 检查该交易对是否已经复盘过
                    if context_manager.is_symbol_reviewed(symbol, reviewed_symbols):
                        logger.info(f"\n  [{i}/{len(recent_trades)}] 跳过: {symbol} (已复盘过)")
                        skipped_count += 1
                        continue
                    
                    logger.info(f"\n  [{i}/{len(recent_trades)}] 复盘: {symbol}")
                    
                    # 调用复盘功能
                    review_result = await analyzer.review_trade(trade)
                    
                    # 将复盘结果添加到知识库（供后续分析使用）
                    # 同时自动优化策略（从复盘结果中提取并生成优化策略）
                    await analyzer.add_review_knowledge(review_result)
                    
                    # 记录该交易对已复盘
                    await context_manager.save_reviewed_symbol(symbol, trade)
                    reviewed_symbols[symbol] = {
                        "symbol": symbol,
                        "reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "trade_info": trade
                    }
                    reviewed_count += 1
                    
                    # 提取改进建议
                    improvements = review_result.get('improvements', [])
                    lessons = review_result.get('lessons_learned', [])
                    
                    if improvements:
                        logger.info(f"    💡 改进: {improvements[0]}")
                    
                    if lessons:
                        logger.info(f"    📚 教训: {lessons[0]}")
                    
                    # 显示优化后的策略（如果有）
                    optimized_strategies = analyzer.get_optimized_strategies()
                    if optimized_strategies:
                        latest_strategy = optimized_strategies[-1]
                        logger.info(f"    🎯 已生成优化策略: {latest_strategy.get('strategy_name', '未命名')}")
                        logger.debug(f"      策略规则: {len(latest_strategy.get('rules', []))} 条")
                    
                except Exception as e:
                    logger.warning(f"    ⚠️  复盘失败: {e}")
            
            if skipped_count > 0:
                logger.info(f"\n  ⏭️  跳过已复盘的交易对: {skipped_count} 个")
            if reviewed_count > 0:
                logger.info(f"\n  ✅ 本次新复盘: {reviewed_count} 个交易对")
            
            logger.info(f"\n  ✅ 复盘完成，改进建议和优化策略已应用到后续分析")
            logger.info(f"  📚 复盘知识库: {analyzer.get_review_knowledge_count()} 条经验")
            
            # 显示优化策略统计
            optimized_strategies = analyzer.get_optimized_strategies()
            if optimized_strategies:
                logger.info(f"  🎯 优化策略库: {len(optimized_strategies)} 条策略")
                for strategy in optimized_strategies[-3:]:  # 显示最近3条
                    logger.info(f"     - {strategy.get('strategy_name', '未命名')} ({len(strategy.get('rules', []))} 条规则)")
            
        except Exception as e:
            # 获取交易历史失败，静默跳过（可能是权限问题或网络问题）
            # 不显示错误信息，避免干扰用户
            pass
        
    except Exception as e:
        logger.error(f"❌ 复盘过程失败: {e}", exc_info=True)


def _process_trades_for_review(closed_trades: List[Dict]) -> List[Dict]:
    """
    处理交易数据，配对买入和卖出，计算完整交易信息
    
    Args:
        closed_trades: 从交易所获取的原始交易数据
    
    Returns:
        格式化后的完整交易列表
    """
    from datetime import datetime
    from collections import defaultdict
    
    # 按交易对和订单ID分组
    trades_by_symbol_order = defaultdict(list)
    
    for trade in closed_trades:
        symbol = trade.get('symbol', '')
        order_id = trade.get('order_id', 0)
        key = f"{symbol}_{order_id}"
        trades_by_symbol_order[key].append(trade)
    
    complete_trades = []
    
    for key, trades in trades_by_symbol_order.items():
        if len(trades) < 2:  # 至少需要买入和卖出
            continue
        
        # 按时间排序
        trades.sort(key=lambda x: x.get('timestamp', 0))
        
        # 找出买入和卖出
        buy_trades = [t for t in trades if t.get('is_buyer', False)]
        sell_trades = [t for t in trades if not t.get('is_buyer', False)]
        
        if not buy_trades or not sell_trades:
            continue
        
        # 计算平均入场和出场价格
        entry_price = sum(t['price'] * t['quantity'] for t in buy_trades) / sum(t['quantity'] for t in buy_trades)
        exit_price = sum(t['price'] * t['quantity'] for t in sell_trades) / sum(t['quantity'] for t in sell_trades)
        
        entry_time = min(t.get('timestamp', 0) for t in buy_trades)
        exit_time = max(t.get('timestamp', 0) for t in sell_trades)
        
        quantity = sum(t['quantity'] for t in buy_trades)
        total_fee = sum(t.get('fee', 0) for t in trades)
        
        # 计算盈亏
        if buy_trades[0].get('position_side', 'BOTH') in ['LONG', 'BOTH']:
            # 做多
            direction = "做多"
            profit_loss = (exit_price - entry_price) * quantity - total_fee
            profit_loss_percent = (exit_price / entry_price - 1) * 100 if entry_price > 0 else 0
        else:
            # 做空
            direction = "做空"
            profit_loss = (entry_price - exit_price) * quantity - total_fee
            profit_loss_percent = (entry_price / exit_price - 1) * 100 if exit_price > 0 else 0
        
        # 计算持仓时长
        duration_seconds = (exit_time - entry_time) / 1000
        hours = duration_seconds / 3600
        duration = f"{hours:.1f}小时" if hours < 24 else f"{hours/24:.1f}天"
        
        # 构建复盘数据
        complete_trade = {
            "symbol": buy_trades[0].get('symbol', ''),
            "direction": direction,
            "trade_time": datetime.fromtimestamp(entry_time / 1000).strftime("%Y-%m-%d %H:%M:%S"),
            "duration": duration,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "stop_loss": entry_price * 0.95 if direction == "做多" else entry_price * 1.05,  # 估算
            "take_profit": entry_price * 1.05 if direction == "做多" else entry_price * 0.95,  # 估算
            "profit_loss": profit_loss,
            "profit_loss_percentage": profit_loss_percent,
            "risk_reward_ratio": "1:2",  # 估算
            "reasoning": "从交易所获取的历史交易",
            "entry_market_state": "未知",
            "exit_market_state": "未知",
            "indicators": "未知",
            "entry_mindset": "未知",
            "holding_process": "未知",
            "exit_reason": "平仓"
        }
        
        complete_trades.append(complete_trade)
    
    # 按时间排序（最新的在前）
    complete_trades.sort(key=lambda x: x.get('trade_time', ''), reverse=True)
    
    return complete_trades


async def scan_callback(scanner, symbols, tickers, trader=None):
    """
    扫描回调函数（支持 AI 分析和自动交易）
    
    Args:
        scanner: 市场扫描器实例
        symbols: 扫描到的交易对列表
        tickers: 交易对的行情数据字典
        trader: 交易执行器实例（可选）
    """
    logger.info("")
    logger.info(f"📊 扫描结果: {len(symbols)} 个交易对")
    
    # 如果配置了 AI 分析器，进行分析
    if scanner.analyzer and scanner.indicator_engine:
        logger.info("🤖 开始 AI 分析...")
        
        # 清空之前的分析结果
        scanner.analysis_results = []
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"\n进度: {i}/{len(symbols)} - {symbol}")
            result = await scanner.analyze_symbol(symbol)
            
            if result:
                scanner.analysis_results.append(result)  # 添加到结果列表
                logger.info(f"  趋势: {result['trend']}")
                logger.info(f"  建议: {result['action']} (置信度: {result['confidence']:.1%})")
                
                # 显示交易标准
                trading_standard = result.get('trading_standard', '')
                if trading_standard and trading_standard != '未提供':
                    logger.info(f"  📋 {trading_standard[:60]}..." if len(trading_standard) > 60 else f"  📋 {trading_standard}")
                
                logger.info(f"  入场: {format_price(result['entry_price'])}")
                logger.info(f"  止损: {format_price(result['stop_loss'])}")
                logger.info(f"  止盈: {format_price(result['take_profit'])}")
                
                # 显示风险管理信息（包括杠杆）
                if 'leverage' in result:
                    logger.info(f"  杠杆: {result['leverage']}x")
                if 'position_size' in result:
                    logger.info(f"  仓位: {result['position_size']:.4f} 币")
                if 'margin_required' in result:
                    logger.info(f"  保证金: {format_price(result['margin_required'])}")
                if 'potential_profit' in result and 'potential_loss' in result:
                    logger.info(f"  潜在盈亏: +{format_price(result['potential_profit'])} / -{format_price(result['potential_loss'])}")
        
        # 显示汇总
        if scanner.analysis_results:
            summary = scanner.get_analysis_summary()
            logger.info(f"\n{'='*40}")
            logger.info(f"本轮分析汇总: {summary.get('total', 0)} 个")
            
            actions = summary.get('actions', {})
            for action, count in sorted(actions.items()):
                logger.info(f"  {action}: {count}")
            
            # 保存分析结果（如果启用）
            if config.SAVE_ANALYSIS_RESULTS:
                scanner.save_analysis_results()
            
            # 执行自动交易（仅在非观察模式且有交易执行器时）
            # 从 scanner 获取 trader（如果参数没有传递）
            if not trader:
                trader = getattr(scanner, 'trader', None)
            
            if trader and config.TRADING_ENVIRONMENT != "observe":
                high_conf_results = [
                    r for r in scanner.analysis_results 
                    if r.get('confidence', 0) >= config.AI_CONFIDENCE_THRESHOLD 
                    and r.get('action') != '观望'
                ]
                
                if high_conf_results:
                    logger.info("")
                    logger.info("="*60)
                    logger.info("💰 开始执行自动交易")
                    logger.info("="*60)
                    
                    executed_count = 0
                    skipped_count = 0
                    
                    for result in high_conf_results:
                        symbol = result.get('symbol')
                        action = result.get('action')
                        confidence = result.get('confidence', 0)
                        
                        logger.info(f"\n📈 {symbol}: {action} (置信度: {confidence:.1%})")
                        
                        # 执行交易
                        trade_result = await trader.execute_trade(result)
                        
                        if trade_result.get('success'):
                            executed_count += 1
                            logger.info(f"   ✅ 交易执行成功: {trade_result.get('message')}")
                            
                            # 显示订单信息
                            orders = trade_result.get('orders', {})
                            if orders.get('entry'):
                                logger.info(f"   📝 入场订单ID: {orders['entry'].get('order_id', 'N/A')}")
                            if orders.get('stop_loss'):
                                logger.info(f"   🛡️  止损订单ID: {orders['stop_loss'].get('order_id', 'N/A')}")
                            if orders.get('take_profit'):
                                logger.info(f"   🎯 止盈订单ID: {orders['take_profit'].get('order_id', 'N/A')}")
                        else:
                            skipped_count += 1
                            reason = trade_result.get('message', '未知原因')
                            logger.info(f"   ⏭️  跳过交易: {reason}")
                    
                    logger.info("")
                    logger.info(f"📊 交易执行汇总:")
                    logger.info(f"   执行成功: {executed_count} 笔")
                    logger.info(f"   跳过: {skipped_count} 笔")
            
            # 学习和复盘（辅助分析改进）
            if scanner.analyzer and scanner.analysis_results:
                # 传递平台实例以获取交易历史
                platform = scanner.platform if hasattr(scanner, 'platform') else None
                await enhance_analysis_with_learning_and_review(scanner.analyzer, scanner.analysis_results, platform)
    
    else:
        # 仅显示价格信息
        if symbols:
            logger.info("")
            logger.info("💰 价格信息（前5个）:")
            for symbol in symbols[:5]:
                ticker = tickers.get(symbol)
                if ticker:
                    price = ticker.get('price', 0)
                    change = ticker.get('price_change_percent', 0)
                    volume = ticker.get('volume', 0)
                    logger.info(
                        f"   {symbol:12s} "
                        f"{format_price(price):>12s} "
                        f"({format_percentage(change):>8s}) "
                        f"量: {format_volume(volume):>10s}"
                    )
    
    logger.info("")


async def run_single_scan(scanner, trader=None):
    """执行单次扫描"""
    logger.info(f"Scanner analyzer: {scanner.analyzer}")
    logger.info(f"Scanner indicator_engine: {scanner.indicator_engine}")
    
    if scanner.analyzer:
        # 扫描并自动 AI 分析（扫描器获取数据 → 计算指标 → 传递给AI）
        logger.info("开始扫描并进行 AI 分析...")
        logger.info("📊 数据流程: 扫描器获取数据 → 计算指标 → AI分析")
        results = await scanner.scan_and_analyze()
        
        # 显示汇总
        summary = scanner.get_analysis_summary()
        
        logger.info(f"\n{'='*60}")
        logger.info("📊 分析汇总")
        logger.info(f"{'='*60}")
        logger.info(f"总分析数: {summary.get('total', 0)}")
        
        actions = summary.get('actions', {})
        if actions:
            logger.info("\n建议分布:")
            for action, count in sorted(actions.items()):
                logger.info(f"  {action}: {count}")
        
        high_conf = summary.get('high_confidence_results', [])
        if high_conf:
            threshold = summary.get('threshold', 0.6)
            logger.info(f"\n⭐ 高置信度建议 (>={threshold:.0%}):")
            for result in high_conf[:5]:
                logger.info(f"\n  {result['symbol']}:")
                logger.info(f"    建议: {result['action']}")
                logger.info(f"    置信度: {result['confidence']:.1%}")
                logger.info(f"    入场: {format_price(result['entry_price'])}")
                logger.info(f"    止损: {format_price(result['stop_loss'])}")
                logger.info(f"    止盈: {format_price(result['take_profit'])}")
                
                # 显示风险管理信息
                if 'leverage' in result:
                    logger.info(f"    杠杆: {result['leverage']}x")
                if 'position_size' in result:
                    logger.info(f"    仓位: {result['position_size']:.4f} 币")
                if 'margin_required' in result:
                    logger.info(f"    保证金: {format_price(result['margin_required'])}")
        
        # 执行交易（仅在非观察模式且有交易执行器时）
        # 从 scanner 获取 trader（如果 run_single_scan 中没有传递）
        if not trader:
            trader = getattr(scanner, 'trader', None)
        
        if trader and high_conf:
            logger.info("")
            logger.info("="*60)
            logger.info("💰 开始执行交易")
            logger.info("="*60)
            
            executed_count = 0
            skipped_count = 0
            
            for result in high_conf:
                symbol = result.get('symbol')
                action = result.get('action')
                confidence = result.get('confidence', 0)
                
                logger.info(f"\n📈 {symbol}: {action} (置信度: {confidence:.1%})")
                
                # 执行交易
                trade_result = await trader.execute_trade(result)
                
                if trade_result.get('success'):
                    executed_count += 1
                    logger.info(f"   ✅ 交易执行成功: {trade_result.get('message')}")
                    
                    # 显示订单信息
                    orders = trade_result.get('orders', {})
                    if orders.get('entry'):
                        logger.info(f"   📝 入场订单ID: {orders['entry'].get('order_id', 'N/A')}")
                    if orders.get('stop_loss'):
                        logger.info(f"   🛡️  止损订单ID: {orders['stop_loss'].get('order_id', 'N/A')}")
                    if orders.get('take_profit'):
                        logger.info(f"   🎯 止盈订单ID: {orders['take_profit'].get('order_id', 'N/A')}")
                else:
                    skipped_count += 1
                    reason = trade_result.get('message', '未知原因')
                    logger.info(f"   ⏭️  跳过交易: {reason}")
            
            logger.info("")
            logger.info(f"📊 交易执行汇总:")
            logger.info(f"   执行成功: {executed_count} 笔")
            logger.info(f"   跳过: {skipped_count} 笔")
            logger.info("")
        
        # 自动学习和复盘（辅助分析，提升分析质量）
        if scanner.analyzer:
            analysis_results = results if 'results' in locals() else (scanner.analysis_results if hasattr(scanner, 'analysis_results') else [])
            if analysis_results:
                # 传递平台实例以获取交易历史
                platform = scanner.platform if hasattr(scanner, 'platform') else None
                await enhance_analysis_with_learning_and_review(scanner.analyzer, analysis_results, platform)
    
    else:
        # 仅扫描，不分析
        symbols = await scanner.scan_symbols()
        logger.info(f"📊 找到 {len(symbols)} 个交易对")
        
        # 显示前5个交易对的价格信息
        if symbols:
            logger.info("")
            logger.info("💰 价格信息（前5个）:")
            for symbol in symbols[:5]:
                ticker = scanner.get_ticker(symbol)
                if ticker:
                    price = ticker.get('price', 0)
                    change = ticker.get('price_change_percent', 0)
                    volume = ticker.get('volume', 0)
                    logger.info(
                        f"   {symbol:12s} "
                        f"{format_price(price):>12s} "
                        f"({format_percentage(change):>8s}) "
                        f"量: {format_volume(volume):>10s}"
                    )
    
    logger.info("")
    logger.info("✅ 扫描完成")


async def run_auto_scan(scanner):
    """执行自动扫描"""
    logger.info("提示: 按 Ctrl+C 停止扫描")
    logger.info("")
    
    # 获取交易执行器（如果存在）
    trader = getattr(scanner, 'trader', None)
    
    # 定义异步回调函数包装器
    async def callback_wrapper(s, symbols, tickers):
        await scan_callback(s, symbols, tickers, trader)
    
    # 启动自动扫描（传递异步回调）
    await scanner.start_auto_scan(
        callback=callback_wrapper,
        align_to_kline=True,
        wait_for_close=True
    )
    
    # 等待运行
    try:
        while scanner.is_scanning:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("")
        logger.info("⏹️  收到中断信号，停止扫描...")
        await scanner.stop_auto_scan()


async def main():
    """主程序"""
    scanner = None
    
    try:
        logger.info("="*60)
        logger.info("🤖 Trading AI 启动")
        logger.info("="*60)
        logger.info("")
        
        # 先初始化平台（用于Web服务器获取真实余额）
        platform = None
        if config.TRADING_ENVIRONMENT != "observe":
            try:
                from tradingai.exchange.factory import PlatformFactory
                platform = PlatformFactory.create(
                    exchange_name=config.EXCHANGE_NAME,
                    api_key=config.BINANCE_API_KEY,
                    api_secret=config.BINANCE_API_SECRET,
                    testnet=config.TESTNET
                )
                await platform.connect()
                logger.info("   ✅ 交易平台已连接（用于Web余额显示）")
            except Exception as e:
                logger.warning(f"   ⚠️  交易平台连接失败: {e}")
                platform = None
        
        # 启动Web监控服务器（后台运行）
        if config.WEB_ENABLED:
            try:
                from tradingai.web import WebServer
                import os
                # 确保使用正确的data目录路径
                data_dir = os.path.join(os.path.dirname(__file__), "data")
                web_server = WebServer(host="0.0.0.0", port=config.WEB_PORT, data_dir=data_dir, platform=platform)
                await web_server.run_async()
                logger.info("")
            except Exception as e:
                logger.warning(f"⚠️  Web服务器启动失败（不影响主程序）: {e}")
                logger.info("")
        
        # 显示配置
        logger.info("⚙️  配置:")
        logger.info(f"   交易所: {config.EXCHANGE_NAME}")
        logger.info(f"   环境: {config.TRADING_ENVIRONMENT}")
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
        
        # 初始化技术指标引擎
        indicator_config = IndicatorConfigParser.parse_from_env()
        indicator_engine = IndicatorEngine()
        indicator_engine.config = indicator_config
        logger.info(f"   指标: {', '.join(indicator_config.keys())}")
        
        # 如果之前没有连接平台（observe模式下），现在连接用于扫描
        if platform is None:
            from tradingai.exchange.factory import PlatformFactory
            platform = PlatformFactory.create(
                exchange_name=config.EXCHANGE_NAME,
                api_key=config.BINANCE_API_KEY,
                api_secret=config.BINANCE_API_SECRET,
                testnet=config.TESTNET
            )
            await platform.connect()
            logger.info("   ✅ 交易平台已连接")
        
        # 🧪 测试：验证API密钥是否真的有效（通过获取余额）
        try:
            logger.info("\n🧪 API密钥有效性测试...")
            balance = await platform.get_balance()
            if balance is not None and balance > 0:
                logger.info(f"   ✅ 余额查询成功: {balance:.2f} USDT")
                logger.info(f"   📊 这证明了 API 密钥是有效的！")
            else:
                logger.warning(f"   ⚠️  余额返回值异常: {balance}")
                logger.warning(f"   这可能表示 API 密钥有问题或账户余额为 0")
        except Exception as e:
            logger.error(f"   ❌ 余额查询失败: {e}")
            logger.error(f"   这说明 API 密钥可能存在问题，建议检查")
            logger.debug(f"   详细错误: {repr(e)}", exc_info=True)
        
        # 初始化 AI 分析器（如果启用）
        analyzer = None
        if config.USE_AI_ANALYSIS:
            logger.info("初始化 AI 分析器...")
            try:
                ai_provider = AIProviderFactory.create_from_config()
                # 传入平台实例，用于获取实际账户余额
                analyzer = MarketAnalyzer(ai_provider, platform=platform)
                logger.info(f"   AI 提供商: {ai_provider.get_provider_name()}")
                logger.info("   ✅ AI 分析器初始化成功")
            except Exception as e:
                logger.error(f"   ❌ AI 分析器初始化失败: {e}", exc_info=True)
                analyzer = None
        else:
            logger.info("   AI 分析: 已禁用")
        
        # 初始化交易执行器（仅在非观察模式下启用）
        trader = None
        if config.TRADING_ENVIRONMENT != "observe":
            logger.info("初始化交易执行器...")
            try:
                trader = Trader(platform)
                logger.info("   ✅ 交易执行器初始化成功")
                logger.info(f"   ⚠️  交易模式: {config.TRADING_ENVIRONMENT} (将执行真实交易)")
            except Exception as e:
                logger.error(f"   ❌ 交易执行器初始化失败: {e}", exc_info=True)
                trader = None
        else:
            logger.info("   交易执行: 观察模式（已禁用）")
        
        logger.info("")
        
        # 创建市场扫描器（集成 AI 分析器和指标引擎）
        scanner = MarketScanner(
            analyzer=analyzer,
            indicator_engine=indicator_engine
        )
        # 将平台实例传递给扫描器（用于后续复盘时获取交易历史）
        scanner.platform = platform
        # 将交易执行器传递给扫描器（用于自动执行交易）
        scanner.trader = trader
        await scanner.connect()
        
        # 选择扫描模式
        # 如果需要单次扫描，使用 run_single_scan
        # 如果需要自动扫描，使用 run_auto_scan
        
        # 选择扫描模式
        if config.AUTO_SCAN:
            logger.info("模式: 自动循环扫描")
            await run_auto_scan(scanner)
        else:
            logger.info("模式: 单次扫描")
            await run_single_scan(scanner, trader)
    
    except KeyboardInterrupt:
        logger.info("")
        logger.info("⏹️  中断")
    except Exception as e:
        logger.error(f"❌ 错误: {e}", exc_info=True)
    finally:
        if scanner:
            if scanner.is_scanning:
                await scanner.stop_auto_scan()
            await scanner.disconnect()
        # 断开平台连接
        if 'platform' in locals() and platform:
            await platform.disconnect()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())
