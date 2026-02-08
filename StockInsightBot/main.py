#!/usr/bin/env python3
"""
StockInsightBot - 專業股票分析 Telegram 機器人
程式入口點
"""
import sys
import os

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram.ext import Application
from config.settings import settings
from bot.handlers import setup_handlers
from utils.loggers import setup_logger

# 設置日誌
logger = setup_logger("StockInsightBot", settings.log_level)


async def post_init(application) -> None:
    """應用程式初始化後的回調"""
    bot_info = await application.bot.get_me()
    logger.info(f"✅ Bot 已連接: @{bot_info.username}")
    logger.info(f"   Bot 名稱: {bot_info.first_name}")
    logger.info(f"   Bot ID: {bot_info.id}")
    logger.info("=" * 50)
    logger.info("🚀 機器人已啟動，正在監聽消息...")
    logger.info("   按 Ctrl+C 停止")
    logger.info("=" * 50)


def main() -> None:
    """
    主函數 - 初始化並啟動機器人
    """
    logger.info("=" * 50)
    logger.info("StockInsightBot 正在啟動...")
    logger.info("=" * 50)
    
    # 驗證配置
    try:
        settings.validate()
        logger.info("✅ 配置驗證通過")
    except ValueError as e:
        logger.error(f"❌ 配置錯誤: {e}")
        sys.exit(1)
    
    # 創建 Application
    application = (
        Application.builder()
        .token(settings.telegram_token)
        .post_init(post_init)
        .build()
    )
    
    # 設置處理器
    setup_handlers(application)
    logger.info("✅ 處理器設置完成")
    
    # 啟動輪詢 (這會自己管理事件循環)
    application.run_polling(
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True  # 丟棄離線期間的消息
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 機器人已停止")
    except Exception as e:
        logger.error(f"❌ 啟動失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
