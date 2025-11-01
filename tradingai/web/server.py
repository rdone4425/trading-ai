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
                if self.platform:
                    try:
                        import asyncio
                        # 尝试从交易所获取真实余额
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        balance = loop.run_until_complete(self.platform.get_balance())
                        if balance and balance > 0:
                            account_balance = balance
                        loop.close()
                    except Exception as e:
                        logger.debug(f"从交易所获取余额失败: {e}")
                
                # 如果获取失败，使用配置值
                if account_balance is None:
                    try:
                        from tradingai import config
                        account_balance = getattr(config, 'ACCOUNT_BALANCE', None)
                    except:
                        pass
                
                # 添加到返回数据中
                data['account_balance'] = account_balance
                
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

