#!/usr/bin/env python3
"""
StockInsightBot - 專業股票分析 Telegram 機器人
程序入口
"""
import asyncio
import logging
import traceback
from telegram import Update
from telegram.ext import Application, ContextTypes

from config import settings
from bot.handlers import setup_handlers
from utils.loggers import setup_logging

# 全局 logger
logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    全局錯誤處理器
    捕獲所有未處理的異常
    """
    logger.error(f"處理更新時發生異常: {context.error}")
    logger.error(f"異常詳情: {traceback.format_exc()}")
    
    # 嘗試通知用戶
    if update and isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ 抱歉，處理您的請求時發生錯誤。請稍後再試。"
            )
        except Exception as e:
            logger.error(f"發送錯誤通知失敗: {e}")


def main():
    """主函數 - 初始化並啟動機器人"""
    
    # 設置日誌
    setup_logging()
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
    
    # 設置全局錯誤處理器
    application.add_error_handler(error_handler)
    
    logger.info("機器人已準備就緒，開始輪詢...")
    logger.info("按 Ctrl+C 停止機器人")
    logger.info("等待接收訊息...")
    
    # 啟動輪詢
    application.run_polling(
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True,
        poll_interval=1.0,  # 每秒檢查一次更新
        timeout=30  # 長輪詢超時
    )


if __name__ == "__main__":
    main()
