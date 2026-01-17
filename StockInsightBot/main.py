#!/usr/bin/env python3
"""
StockInsightBot - 專業股票分析 Telegram 機器人
程序入口
"""
import asyncio
import logging
from telegram.ext import Application

from config import settings
from bot.handlers import setup_handlers
from utils.loggers import setup_logging


def main():
    """主函數 - 初始化並啟動機器人"""
    
    # 設置日誌
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info("StockInsightBot 啟動中...")
    logger.info("=" * 50)
    
    # 驗證配置
    if not settings.validate():
        logger.error("配置驗證失敗，請檢查環境變量")
        return
    
    logger.info(f"Bot Token: {settings.TELEGRAM_BOT_TOKEN[:20]}...")
    logger.info(f"AI Model: {settings.AI_MODEL}")
    
    # 創建應用
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    # 設置處理器
    setup_handlers(application)
    
    logger.info("機器人已準備就緒，開始輪詢...")
    logger.info("按 Ctrl+C 停止機器人")
    
    # 啟動輪詢
    application.run_polling(
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
