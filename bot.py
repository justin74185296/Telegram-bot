#!/usr/bin/env python3
"""
Telegram Bot - 簡單的回應機器人
"""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 設定日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token
BOT_TOKEN = "8578604578:AAH0Kn29pPLFBsq_4OHBwPc69leD3vBGKx0"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /start 指令"""
    user = update.effective_user
    await update.message.reply_text(
        f"你好 {user.first_name}！👋\n"
        f"歡迎使用這個機器人！\n\n"
        f"可用指令：\n"
        f"/start - 開始使用\n"
        f"/help - 查看幫助\n"
        f"/echo <訊息> - 重複你的訊息"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /help 指令"""
    await update.message.reply_text(
        "📖 幫助說明：\n\n"
        "/start - 開始使用機器人\n"
        "/help - 顯示此幫助訊息\n"
        "/echo <訊息> - 機器人會重複你的訊息\n\n"
        "你也可以直接發送任何訊息，機器人會回覆你！"
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /echo 指令"""
    if context.args:
        message = ' '.join(context.args)
        await update.message.reply_text(f"🔊 {message}")
    else:
        await update.message.reply_text("請在 /echo 後面加上你想要重複的訊息")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理一般訊息"""
    text = update.message.text
    user = update.effective_user
    logger.info(f"收到來自 {user.first_name} 的訊息: {text}")
    
    # 簡單的回覆
    await update.message.reply_text(f"收到你的訊息：「{text}」✅")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理錯誤"""
    logger.error(f"發生錯誤: {context.error}")


def main() -> None:
    """啟動機器人"""
    # 建立 Application
    application = Application.builder().token(BOT_TOKEN).build()

    # 添加指令處理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("echo", echo))

    # 添加訊息處理器（處理所有文字訊息）
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 添加錯誤處理器
    application.add_error_handler(error_handler)

    # 啟動機器人
    logger.info("機器人正在啟動...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
