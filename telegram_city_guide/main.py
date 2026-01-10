"""
Main Module - 主程式入口
==========================
Telegram 城市指南 Bot 主程式入口點。
Telegram City Guide Bot main entry point.

⚠️ 此 Bot 純粹用於程式學習、資料結構研究與全球地點匹配實驗，嚴禁公開部署或用於任何商業用途。
⚠️ This Bot is purely for programming learning and experiments. Do not deploy publicly.

使用方式 / How to use:
1. 複製 .env.example 為 .env 並填入你的 BOT_TOKEN
   Copy .env.example to .env and fill in your BOT_TOKEN
2. 安裝依賴: pip install -r requirements.txt
   Install dependencies: pip install -r requirements.txt
3. 執行: python main.py
   Run: python main.py
"""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# 載入本地模組 / Load local modules
from handlers import router
from database import get_database

# 載入環境變數 / Load environment variables
load_dotenv()

# 設定日誌 / Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """
    主函數 - 初始化並啟動 Bot
    Main function - Initialize and start the bot
    """
    # 取得 Bot Token
    # Get Bot Token
    bot_token = os.getenv("BOT_TOKEN")
    
    if not bot_token:
        logger.error("❌ BOT_TOKEN 環境變數未設定!")
        logger.error("❌ BOT_TOKEN environment variable not set!")
        logger.info("請在 .env 檔案中設定 BOT_TOKEN=your_token_here")
        logger.info("Please set BOT_TOKEN=your_token_here in .env file")
        sys.exit(1)
    
    # 預先載入資料庫以驗證 JSON 檔案
    # Pre-load database to validate JSON file
    logger.info("📂 正在載入地點資料庫...")
    logger.info("📂 Loading location database...")
    db = get_database()
    
    if not db.locations:
        logger.warning("⚠️ 資料庫為空或載入失敗!")
        logger.warning("⚠️ Database is empty or failed to load!")
    
    # 建立 Bot 實例
    # Create Bot instance
    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2)
    )
    
    # 建立 Dispatcher
    # Create Dispatcher
    dp = Dispatcher()
    
    # 註冊路由器
    # Register router
    dp.include_router(router)
    
    # 啟動訊息
    # Startup message
    logger.info("=" * 50)
    logger.info("🤖 城市指南 Bot 正在啟動...")
    logger.info("🤖 City Guide Bot is starting...")
    logger.info(f"📊 已載入 {len(db.locations)} 筆地點資料")
    logger.info(f"📊 Loaded {len(db.locations)} location records")
    logger.info("=" * 50)
    
    try:
        # 刪除舊的 webhook（如果有的話）並開始 polling
        # Delete old webhook (if any) and start polling
        await bot.delete_webhook(drop_pending_updates=True)
        
        logger.info("✅ Bot 已成功啟動! 正在監聽訊息...")
        logger.info("✅ Bot started successfully! Listening for messages...")
        logger.info("按 Ctrl+C 停止 / Press Ctrl+C to stop")
        
        # 開始輪詢
        # Start polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Bot 執行錯誤: {e}")
        logger.error(f"❌ Bot execution error: {e}")
        raise
    finally:
        # 關閉 Bot 連線
        # Close Bot connection
        await bot.session.close()
        logger.info("👋 Bot 已停止")
        logger.info("👋 Bot stopped")


if __name__ == "__main__":
    try:
        # 執行主函數
        # Run main function
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 收到停止信號，正在關閉...")
        logger.info("🛑 Received stop signal, shutting down...")
