#!/usr/bin/env python3
"""
StockInsightBot - 专业股票分析 Telegram 机器人
主入口文件

功能：
- 获取多市场股票数据（美股、港股、A股）
- AI驱动的深度分析报告
- 实时行情、财务分析、新闻整合

启动命令：
    python main.py
"""

import asyncio
import logging
import sys
from telegram import Update
from telegram.ext import Application

# 导入配置和模块
from config.settings import settings
from utils.loggers import setup_logging
from bot.handlers import setup_handlers


def main() -> None:
    """
    主函数：初始化并启动机器人
    """
    # 1. 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 50)
    logger.info("StockInsightBot 正在启动...")
    logger.info("=" * 50)
    
    # 2. 验证配置
    try:
        settings.validate()
        logger.info("✅ 配置验证通过")
    except ValueError as e:
        logger.error(f"❌ 配置错误: {e}")
        logger.error("请检查 .env 文件或环境变量设置")
        sys.exit(1)
    
    # 3. 创建 Application
    logger.info("正在创建 Telegram Application...")
    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .build()
    )
    
    # 4. 设置处理器
    logger.info("正在设置命令和消息处理器...")
    setup_handlers(application)
    
    # 5. 启动机器人
    logger.info("✅ 初始化完成，机器人正在启动...")
    logger.info(f"📊 AI模型: {settings.openai_model}")
    logger.info(f"🌐 API端点: {settings.openai_base_url}")
    logger.info("-" * 50)
    logger.info("机器人已准备就绪，等待用户消息...")
    logger.info("按 Ctrl+C 停止运行")
    logger.info("-" * 50)
    
    # 运行轮询
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True  # 忽略离线期间的消息
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 收到停止信号，正在关闭机器人...")
    except Exception as e:
        logging.error(f"发生致命错误: {e}", exc_info=True)
        sys.exit(1)
