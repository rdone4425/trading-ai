"""
Web服务器模块
提供HTTP接口和静态页面服务
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

from flask import Flask, render_template, jsonify, send_from_directory, request
from flask_cors import CORS
from datetime import datetime

from .stats import TradingStats

logger = logging.getLogger(__name__)


class WebServer:
    """Web监控服务器"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080, data_dir: str = "data", platform=None):
        """
        初始化Web服务器
        
        Args:
            host: 监听地址
            port: 监听端口
            data_dir: 数据目录
            platform: 交易平台实例（用于获取真实余额）
        """
        self.host = host
        self.port = port
        self.data_dir = data_dir
        self.platform = platform
        self.stats = TradingStats(data_dir)
        self.start_time = datetime.now()  # 记录启动时间
        
        # 创建Flask应用
        self.app = Flask(__name__, 
                        template_folder=str(Path(__file__).parent / 'templates'),
                        static_folder=str(Path(__file__).parent / 'static'))
        CORS(self.app)
        
        # 注册路由
        self._register_routes()
        
        logger.info(f"Web服务器初始化完成: http://{host}:{port}")
    
    def _register_routes(self):
        """注册路由"""
        
        @self.app.route('/')
        def index():
            """主页"""
            return render_template('index.html')
        
        @self.app.route('/review-learning')
        def review_learning():
            """复盘学习结果页面"""
            return render_template('review_learning.html')
        
        @self.app.route('/api/stats')
        def get_stats():
            """获取统计数据"""
            try:
                days = request.args.get('days', 30, type=int)
                stats = self.stats.calculate_stats(days=days)
                return jsonify({
                    'success': True,
                    'data': stats
                })
            except Exception as e:
                logger.error(f"获取统计数据失败: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/analysis')
        def get_analysis():
            """获取分析结果"""
            try:
                limit = request.args.get('limit', 20, type=int)
                results = self.stats.get_recent_analysis(limit=limit)
                return jsonify({
                    'success': True,
                    'data': results
                })
            except Exception as e:
                logger.error(f"获取分析结果失败: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/trades')
        def get_trades():
            """获取交易记录"""
            try:
                trades = self.stats.load_trades()
                return jsonify({
                    'success': True,
                    'data': trades[-50:]  # 最近50条
                })
            except Exception as e:
                logger.error(f"获取交易记录失败: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/dashboard')
        def get_dashboard():
            """获取仪表板数据"""
            try:
                data = self.stats.get_dashboard_data()
                
                # 获取真实账户余额（优先从交易所获取）
                account_balance = None
                balance_source = 'config'  # 默认来源为配置值
                balance_error = None  # 记录错误信息
                if self.platform:
                    try:
                        import asyncio
                        # 尝试从交易所获取真实余额
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        balance = loop.run_until_complete(self.platform.get_balance())
                        if balance and balance > 0:
                            account_balance = balance
                            balance_source = 'exchange'  # 来自交易所
                            logger.debug(f"✅ 成功从交易所获取余额: {balance:.2f} USDT")
                        else:
                            balance_error = "余额为0或无效"
                            logger.warning(f"⚠️  从交易所获取的余额无效: {balance}")
                        loop.close()
                    except Exception as e:
                        balance_error = str(e)
                        logger.warning(f"⚠️  从交易所获取余额失败: {e}，将使用配置值")
                else:
                    balance_error = "未连接交易平台（可能是观察模式）"
                    logger.debug("ℹ️  未连接交易平台，使用配置余额")
                
                # 如果获取失败，使用配置值
                if account_balance is None:
                    try:
                        from tradingai import config
                        account_balance = getattr(config, 'ACCOUNT_BALANCE', None)
                        balance_source = 'config'  # 来自配置
                    except:
                        pass
                
                # 计算系统运行时间
                uptime_seconds = (datetime.now() - self.start_time).total_seconds()
                
                # 添加到返回数据中
                data['account_balance'] = account_balance
                data['balance_source'] = balance_source  # 余额来源标识
                if balance_error:
                    data['balance_error'] = balance_error  # 余额获取错误信息（用于调试）
                data['uptime_seconds'] = uptime_seconds
                
                return jsonify({
                    'success': True,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"获取仪表板数据失败: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/performance')
        def get_performance():
            """获取表现历史"""
            try:
                days = request.args.get('days', 30, type=int)
                history = self.stats.get_performance_history(days=days)
                return jsonify({
                    'success': True,
                    'data': history
                })
            except Exception as e:
                logger.error(f"获取表现历史失败: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/symbols')
        def get_symbols():
            """获取交易对统计"""
            try:
                limit = request.args.get('limit', 10, type=int)
                symbols = self.stats.get_symbol_performance(limit=limit)
                return jsonify({
                    'success': True,
                    'data': symbols
                })
            except Exception as e:
                logger.error(f"获取交易对统计失败: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/balance')
        def get_balance():
            """获取账户余额（真实余额）"""
            try:
                balance = None
                
                # 优先从交易所获取真实余额
                if self.platform:
                    try:
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        balance = loop.run_until_complete(self.platform.get_balance())
                        loop.close()
                        
                        if balance and balance > 0:
                            return jsonify({
                                'success': True,
                                'balance': balance,
                                'source': 'exchange'
                            })
                    except Exception as e:
                        logger.debug(f"从交易所获取余额失败: {e}")
                
                # 如果获取失败，使用配置值
                from tradingai import config
                balance = getattr(config, 'ACCOUNT_BALANCE', 0)
                
                return jsonify({
                    'success': True,
                    'balance': balance,
                    'source': 'config'
                })
            except Exception as e:
                logger.error(f"获取账户余额失败: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'balance': 0
                }), 500
        
        @self.app.route('/api/review-knowledge')
        def get_review_knowledge():
            """获取复盘知识"""
            try:
                from tradingai.ai.context_manager import ContextManager
                context_manager = ContextManager()
                
                # 同步加载（在Flask上下文中）
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                knowledge = loop.run_until_complete(context_manager.load_review_knowledge())
                loop.close()
                
                return jsonify({
                    'success': True,
                    'data': knowledge
                })
            except Exception as e:
                logger.error(f"获取复盘知识失败: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'data': []
                }), 500
        
        @self.app.route('/api/optimized-strategies')
        def get_optimized_strategies():
            """获取优化策略"""
            try:
                from tradingai.ai.context_manager import ContextManager
                context_manager = ContextManager()
                
                # 同步加载
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                strategies = loop.run_until_complete(context_manager.load_optimized_strategies())
                loop.close()
                
                return jsonify({
                    'success': True,
                    'data': strategies
                })
            except Exception as e:
                logger.error(f"获取优化策略失败: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'data': []
                }), 500
        
        @self.app.route('/api/learning-results')
        def get_learning_results():
            """获取学习结果"""
            try:
                from tradingai.ai.context_manager import ContextManager
                context_manager = ContextManager()
                
                # 同步加载
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(context_manager.load_learning_results())
                loop.close()
                
                return jsonify({
                    'success': True,
                    'data': results
                })
            except Exception as e:
                logger.error(f"获取学习结果失败: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'data': []
                }), 500
        
        @self.app.route('/health')
        def health():
            """健康检查"""
            return jsonify({
                'status': 'ok',
                'timestamp': datetime.now().isoformat()
            })
    
    def run(self, debug: bool = False):
        """
        启动服务器（同步模式）
        
        Args:
            debug: 是否开启调试模式
        """
        logger.info(f"🌐 Web服务器启动: http://{self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=debug, use_reloader=False)
    
    async def run_async(self):
        """
        启动服务器（异步模式）
        在后台线程中运行Flask
        """
        import threading
        
        def run_flask():
            self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)
        
        thread = threading.Thread(target=run_flask, daemon=True)
        thread.start()
        logger.info(f"🌐 Web服务器已在后台启动: http://{self.host}:{self.port}")

