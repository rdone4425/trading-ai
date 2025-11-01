"""
ModelScope AI 提供商示例

演示如何使用 ModelScope 提供商进行市场分析
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tradingai.ai import AIProviderFactory
from tradingai.logger import get_logger

logger = get_logger("examples.modelscope")


async def test_modelscope_basic():
    """测试基础对话"""
    logger.info("=" * 60)
    logger.info("测试 ModelScope 基础对话")
    logger.info("=" * 60)
    
    # 从配置创建 ModelScope 提供商
    # 确保 .env 中配置了：
    # AI_PROVIDER=modelscope
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


async def test_modelscope_market_analysis():
    """测试市场分析"""
    logger.info("=" * 60)
    logger.info("测试 ModelScope 市场分析")
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
            "ema_20": 94500.00,
            "ema_50": 93200.00,
            "rsi": 68.5,
            "macd": 150.23,
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
- EMA20: ${market_data['indicators']['ema_20']:,.2f}
- EMA50: ${market_data['indicators']['ema_50']:,.2f}
- RSI: {market_data['indicators']['rsi']:.1f}
- MACD: {market_data['indicators']['macd']:,.2f}

请提供：
1. 市场趋势分析
2. 支撑位和阻力位
3. 交易建议（做多/做空/观望）
4. 风险提示
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
        
    except Exception as e:
        logger.error(f"❌ 分析失败: {e}")
    
    finally:
        await provider.close()


async def test_different_model():
    """测试使用不同的模型"""
    logger.info("=" * 60)
    logger.info("测试使用不同的 ModelScope 模型")
    logger.info("=" * 60)
    
    # 手动指定模型（覆盖 .env 配置）
    from tradingai import config
    
    try:
        provider = AIProviderFactory.create(
            provider_name="modelscope",
            api_key=config.AI_API_KEY,
            model="Qwen/Qwen2.5-72B-Instruct"  # 使用通义千问模型
        )
        logger.info(f"✅ 创建提供商: {provider.get_provider_name()}")
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "简单说一下比特币的特点"}
        ]
        
        response = await provider.chat(messages)
        logger.info(f"📥 响应: {response}")
        
        await provider.close()
        
    except Exception as e:
        logger.error(f"❌ 失败: {e}")


async def main():
    """主函数"""
    logger.info("🚀 ModelScope AI 提供商测试\n")
    
    # 提示用户
    logger.info("⚠️  注意：运行前请在 .env 中配置：")
    logger.info("AI_PROVIDER=modelscope")
    logger.info("AI_API_KEY=your_modelscope_token")
    logger.info("AI_MODEL=ZhipuAI/GLM-4.6  # 可选\n")
    
    # 选择测试
    choice = input("选择测试:\n1. 基础对话\n2. 市场分析\n3. 使用不同模型\n请输入 (1/2/3): ").strip()
    
    if choice == "1":
        await test_modelscope_basic()
    elif choice == "2":
        await test_modelscope_market_analysis()
    elif choice == "3":
        await test_different_model()
    else:
        logger.error("无效的选择")


if __name__ == "__main__":
    asyncio.run(main())

