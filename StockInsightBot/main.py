#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StockInsightBot - 专业股票分析 Telegram Bot

主程序入口，负责初始化配置和启动机器人

使用方法:
    1. 复制 .env.example 为 .env
    2. 填入 TELEGRAM_BOT_TOKEN 和 OPENAI_API_KEY
    3. 运行: python main.py
"""

import asyncio
import signal
import sys
from telegram.ext import Application

from config import settings
from bot import setup_handlers
from utils import setup_logger, get_logger


# 初始化日志
logger = setup_logger("StockInsightBot")


def check_configuration() -> bool:
    """
    检查必要的配置项
    
    返回:
        配置是否有效
    """
    is_valid, errors = settings.validate()
    
    if not is_valid:
        logger.error("配置验证失败:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.error("")
        logger.error("请检查 .env 文件是否正确配置。")
        logger.error("可参考 .env.example 文件。")
        return False
    
    return True


def create_application() -> Application:
    """
    创建并配置 Telegram Bot Application
    
    返回:
        配置好的 Application 实例
    """
    logger.info("正在创建 Bot Application...")
    
    # 创建 Application
    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .build()
    )
    
    # 设置处理器
    setup_handlers(application)
    
    logger.info("Bot Application 创建完成")
    return application


async def post_init(application: Application):
    """
    Bot 启动后的初始化回调
    """
    bot_info = await application.bot.get_me()
    logger.info(f"Bot 启动成功！")
    logger.info(f"  用户名: @{bot_info.username}")
    logger.info(f"  名称: {bot_info.first_name}")
    logger.info(f"  ID: {bot_info.id}")
    logger.info("")
    logger.info(f"在 Telegram 中搜索 @{bot_info.username} 开始使用")


async def post_shutdown(application: Application):
    """
    Bot 关闭时的清理回调
    """
    logger.info("Bot 正在关闭...")


def setup_signal_handlers(application: Application):
    """
    设置信号处理器，优雅关闭
    """
    def signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}，正在停止...")
        # 这会触发 Application 的正常关闭流程
        raise SystemExit(0)
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main():
    """
    主函数，启动 Bot
    """
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   📈 StockInsightBot - 专业股票分析机器人                 ║
    ║                                                           ║
    ║   功能：实时行情 | 财务分析 | AI报告生成                  ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # 检查配置
    if not check_configuration():
        sys.exit(1)
    
    logger.info("配置检查通过")
    logger.info(f"日志级别: {settings.log_level}")
    logger.info(f"AI模型: {settings.openai_model}")
    logger.info(f"缓存TTL: {settings.cache_ttl}秒")
    logger.info("")
    
    try:
        # 创建 Application
        application = create_application()
        
        # 设置启动和关闭回调
        application.post_init = post_init
        application.post_shutdown = post_shutdown
        
        # 设置信号处理
        setup_signal_handlers(application)
        
        # 启动 Bot
        logger.info("正在启动 Bot...")
        application.run_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True  # 忽略离线期间的消息
        )
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在退出...")
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Bot 已停止")


if __name__ == "__main__":
    main()
