"""
DeepSeek AI 提供商示例

演示如何使用 DeepSeek 提供商进行市场分析
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tradingai.ai import AIProviderFactory
from tradingai.logger import get_logger

logger = get_logger("examples.deepseek")


async def test_deepseek_basic():
    """测试基础对话"""
    logger.info("=" * 60)
    logger.info("测试 DeepSeek 基础对话")
    logger.info("=" * 60)
    
    # 从配置创建 DeepSeek 提供商
    # 确保 .env 中配置了：
    # AI_PROVIDER=deepseek
    # AI_API_KEY=your_token
    provider = AIProviderFactory.create_from_config()
    
    logger.info(f"✅ 创建提供商: {provider.get_provider_name()}")
    
    # 发送简单对话
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "你好，请简单介绍一下你自己"}
    ]
    
    try:
        logger.info("📤 发送请求...")
        response = await provider.chat(messages)
        
        logger.info("📥 收到响应:")
        logger.info(f"\n{response}\n")
        
    except Exception as e:
        logger.error(f"❌ 请求失败: {e}")
    
    finally:
        await provider.close()


async def test_deepseek_market_analysis():
    """测试市场分析"""
    logger.info("=" * 60)
    logger.info("测试 DeepSeek 市场分析")
    logger.info("=" * 60)
    
    # 从配置创建提供商
    provider = AIProviderFactory.create_from_config()
    
    logger.info(f"✅ 创建提供商: {provider.get_provider_name()}")
    
    # 模拟市场数据
    market_data = {
        "symbol": "BTCUSDT",
        "current_price": 95234.50,
        "24h_change": 3.45,
        "24h_volume": 28500000000,
        "indicators": {
            "ema_7": 94800.00,
            "ema_20": 94500.00,
            "ema_50": 93200.00,
            "rsi": 68.5,
            "macd": 150.23,
            "atr": 1250.50,
        }
    }
    
    # 构建分析提示
    prompt = f"""
请分析以下加密货币市场数据，并给出交易建议：

交易对: {market_data['symbol']}
当前价格: ${market_data['current_price']:,.2f}
24小时涨跌: {market_data['24h_change']:+.2f}%
24小时成交量: ${market_data['24h_volume']:,.0f}

技术指标:
- EMA7: ${market_data['indicators']['ema_7']:,.2f}
- EMA20: ${market_data['indicators']['ema_20']:,.2f}
- EMA50: ${market_data['indicators']['ema_50']:,.2f}
- RSI: {market_data['indicators']['rsi']:.1f}
- MACD: {market_data['indicators']['macd']:,.2f}
- ATR: {market_data['indicators']['atr']:,.2f}

请提供：
1. 市场趋势分析（多头/空头）
2. 支撑位和阻力位
3. 交易建议（做多/做空/观望）
4. 风险提示和止损建议

请以 JSON 格式返回，包含以下字段：
{{
  "trend": "上升/下降/震荡",
  "support": 价格,
  "resistance": 价格,
  "action": "做多/做空/观望",
  "confidence": 0.0-1.0,
  "stop_loss": 价格,
  "take_profit": 价格,
  "reason": "分析原因"
}}
"""
    
    messages = [
        {"role": "system", "content": "你是一个专业的加密货币交易分析师。"},
        {"role": "user", "content": prompt}
    ]
    
    try:
        logger.info("📤 发送市场分析请求...")
        response = await provider.chat(messages, temperature=0.3)
        
        logger.info("📥 收到分析结果:")
        logger.info(f"\n{response}\n")
        
        # 尝试解析 JSON
        try:
            import json
            analysis = json.loads(response)
            logger.info("📊 结构化分析结果:")
            logger.info(f"  趋势: {analysis.get('trend')}")
            logger.info(f"  建议: {analysis.get('action')}")
            logger.info(f"  置信度: {analysis.get('confidence')}")
            logger.info(f"  支撑位: ${analysis.get('support'):,.2f}")
            logger.info(f"  阻力位: ${analysis.get('resistance'):,.2f}")
            logger.info(f"  止损: ${analysis.get('stop_loss'):,.2f}")
            logger.info(f"  止盈: ${analysis.get('take_profit'):,.2f}")
            logger.info(f"  理由: {analysis.get('reason')}")
        except json.JSONDecodeError:
            logger.warning("⚠️  响应不是有效的 JSON 格式")
        
    except Exception as e:
        logger.error(f"❌ 分析失败: {e}")
    
    finally:
        await provider.close()


async def test_deepseek_coder():
    """测试 DeepSeek Coder 模型"""
    logger.info("=" * 60)
    logger.info("测试 DeepSeek Coder 模型")
    logger.info("=" * 60)
    
    # 手动指定 Coder 模型
    from tradingai import config
    
    try:
        provider = AIProviderFactory.create(
            provider_name="deepseek",
            api_key=config.AI_API_KEY,
            model="deepseek-coder"  # 使用 Coder 模型
        )
        logger.info(f"✅ 创建提供商: {provider.get_provider_name()}")
        
        messages = [
            {"role": "system", "content": "You are a professional Python programmer."},
            {"role": "user", "content": "写一个 Python 函数，计算斐波那契数列的第 n 项"}
        ]
        
        response = await provider.chat(messages)
        logger.info(f"📥 响应:\n{response}")
        
        await provider.close()
        
    except Exception as e:
        logger.error(f"❌ 失败: {e}")


async def test_streaming_response():
    """测试流式响应（如果支持）"""
    logger.info("=" * 60)
    logger.info("测试流式响应")
    logger.info("=" * 60)
    
    logger.info("⚠️  当前版本使用非流式模式")
    logger.info("流式响应功能将在未来版本中支持")


async def main():
    """主函数"""
    logger.info("🚀 DeepSeek AI 提供商测试\n")
    
    # 提示用户
    logger.info("⚠️  注意：运行前请在 .env 中配置：")
    logger.info("AI_PROVIDER=deepseek")
    logger.info("AI_API_KEY=your_deepseek_api_key")
    logger.info("AI_MODEL=deepseek-chat  # 可选\n")
    
    # 选择测试
    print("选择测试:")
    print("1. 基础对话")
    print("2. 市场分析")
    print("3. DeepSeek Coder 模型")
    print("4. 流式响应（未实现）")
    choice = input("请输入 (1/2/3/4): ").strip()
    
    if choice == "1":
        await test_deepseek_basic()
    elif choice == "2":
        await test_deepseek_market_analysis()
    elif choice == "3":
        await test_deepseek_coder()
    elif choice == "4":
        await test_streaming_response()
    else:
        logger.error("无效的选择")


if __name__ == "__main__":
    asyncio.run(main())
