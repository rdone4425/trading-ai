"""
配置管理
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ==================== 交易平台 ====================
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "binance")  # binance, okx, bybit等

# ==================== API 配置 ====================
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")

# ==================== 交易配置 ====================
# 交易环境：observe(观察), testnet(测试网), mainnet(实盘)
TRADING_ENVIRONMENT = os.getenv("TRADING_ENVIRONMENT", "observe")
TESTNET = TRADING_ENVIRONMENT == "testnet"

# 交易参数
TIMEFRAME = os.getenv("TIMEFRAME", "1h")
MAX_POSITIONS = int(os.getenv("MAX_POSITIONS", "5"))
DEFAULT_LEVERAGE = int(os.getenv("DEFAULT_LEVERAGE", "10"))

# 风险管理
MAX_LOSS_PER_TRADE = float(os.getenv("MAX_LOSS_PER_TRADE", "0.02"))
MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", "0.3"))

# ==================== 扫描配置 ====================
# 基础配置
LOOKBACK = int(os.getenv("LOOKBACK", "100"))
DEFAULT_QUOTE = os.getenv("DEFAULT_QUOTE", "USDT")

# K线类型：closed(已完成), open(进行中)
KLINE_TYPE = os.getenv("KLINE_TYPE", "closed")  # closed 或 open

# 自定义交易对（逗号分隔，优先使用）
# 会通过 SymbolParser 解析并标准化
CUSTOM_SYMBOLS_RAW = os.getenv("CUSTOM_SYMBOLS", "")  # 原始字符串

# 扫描类型（仅当 CUSTOM_SYMBOLS 为空时使用）
# 可选：hot(热门), volume(24h成交量), gainers(涨幅), losers(跌幅)
# 多个类型用逗号分隔，合并去重后返回 SCAN_TOP_N 个
SCAN_TYPES = os.getenv("SCAN_TYPES", "hot,volume,gainers,losers")
SCAN_TOP_N = int(os.getenv("SCAN_TOP_N", "20"))  # 最终返回的统一数量

# 解析后的自定义交易对（延迟初始化）
CUSTOM_SYMBOLS = None  # 将在首次使用时通过 SymbolParser 解析

# ==================== AI 配置 ====================
USE_AI_ANALYSIS = os.getenv("USE_AI_ANALYSIS", "true").lower() == "true"
AI_CONFIDENCE_THRESHOLD = float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.6"))

# AI 提供商配置
AI_PROVIDER = os.getenv("AI_PROVIDER", "mock")  # deepseek, openai, claude, gemini, local, mock
AI_API_KEY = os.getenv("AI_API_KEY", "")        # 统一的 API 密钥
AI_MODEL = os.getenv("AI_MODEL", "")            # 模型名称（可选）

# 自动循环扫描配置
AUTO_SCAN = os.getenv("AUTO_SCAN", "false").lower() == "true"

# 保存分析结果配置
SAVE_ANALYSIS_RESULTS = os.getenv("SAVE_ANALYSIS_RESULTS", "false").lower() == "true"
ANALYSIS_RESULTS_DIR = os.getenv("ANALYSIS_RESULTS_DIR", "data")

# AI 并发分析配置
MAX_CONCURRENT_ANALYSIS = int(os.getenv("MAX_CONCURRENT_ANALYSIS", "3"))  # 最大并发分析数量

# ============= 风险管理配置 =============
# 账户余额（USDT）
ACCOUNT_BALANCE = float(os.getenv("ACCOUNT_BALANCE", "10000"))

# 单笔风险百分比（账户余额的百分比）
RISK_PERCENT = float(os.getenv("RISK_PERCENT", "1.0"))

# 风险回报比（止盈/止损比例）
RISK_REWARD_RATIO = float(os.getenv("RISK_REWARD_RATIO", "2.0"))

# ATR 倍数（用于计算止损距离）
ATR_MULTIPLIER = float(os.getenv("ATR_MULTIPLIER", "2.0"))

# 最大杠杆
MAX_LEVERAGE = int(os.getenv("MAX_LEVERAGE", "10"))

# ============= 学习和复盘配置（辅助分析改进） =============
# 扫描后自动学习（基于本次分析结果，提升分析能力）
# 从分析结果中提取交易标准、指标使用等知识点进行学习
ENABLE_AUTO_LEARNING = os.getenv("ENABLE_AUTO_LEARNING", "true").lower() == "true"

# 扫描后自动复盘（需要有历史交易数据，复盘后改进分析策略）
# 复盘历史交易，提取经验教训，应用到后续分析中
ENABLE_AUTO_REVIEW = os.getenv("ENABLE_AUTO_REVIEW", "true").lower() == "true"

# 学习主题（如果为空，则根据分析结果自动生成）
# 例如: EMA指标使用,风险管理,趋势判断
AUTO_LEARNING_TOPICS = [t.strip() for t in os.getenv("AUTO_LEARNING_TOPICS", "").split(",") if t.strip()] if os.getenv("AUTO_LEARNING_TOPICS", "") else []

# ==================== 日志配置 ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_RETENTION_HOURS = int(os.getenv("LOG_RETENTION_HOURS", "3"))

# ==================== 代理配置 ====================
USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"
PROXY_HOST = os.getenv("PROXY_HOST", "127.0.0.1")
PROXY_PORT = int(os.getenv("PROXY_PORT", "7890"))

# ==================== 指标配置 ====================
# 支持多组指标配置，格式：组ID_指标名=参数1,参数2,...
# 示例：
#   INDICATOR_1_EMA=20,120
#   INDICATOR_1_ATR=14
#   INDICATOR_1_MA=20,30,60
#   INDICATOR_2_MACD=12,26,9
INDICATOR_CONFIG_RAW = os.getenv("INDICATOR_CONFIG", "")

def is_production():
    """是否为实盘环境"""
    return TRADING_ENVIRONMENT == "mainnet"

def is_testnet():
    """是否为测试网"""
    return TRADING_ENVIRONMENT == "testnet"

def is_observe():
    """是否为观察模式"""
    return TRADING_ENVIRONMENT == "observe"

