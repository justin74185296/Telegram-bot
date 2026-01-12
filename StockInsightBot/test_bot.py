#!/usr/bin/env python3
"""簡單測試 Bot"""
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 啟用所有日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8578604578:AAH0Kn29pPLFBsq_4OHBwPc69leD3vBGKx0"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"收到 /start 命令來自 {update.effective_user.first_name}")
    await update.message.reply_text(
        "👋 你好！Bot 正常運作！\n\n"
        "發送任何訊息我都會回覆。"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"收到訊息: {update.message.text}")
    await update.message.reply_text(f"✅ 收到: {update.message.text}")

def main():
    logger.info("啟動測試 Bot...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    logger.info("Bot 開始輪詢...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
