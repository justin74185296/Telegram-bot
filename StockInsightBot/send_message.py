#!/usr/bin/env python3
"""
主動發送訊息工具
用於向用戶發送通知或分析報告
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram import Bot
from telegram.constants import ParseMode
from config.settings import settings


async def send_message(chat_id: int, message: str, parse_mode=ParseMode.MARKDOWN) -> bool:
    """
    向指定用戶發送訊息
    
    Args:
        chat_id: 用戶或群組的 chat_id
        message: 要發送的訊息
        parse_mode: 解析模式
    
    Returns:
        是否發送成功
    """
    try:
        bot = Bot(token=settings.telegram_token)
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=parse_mode
        )
        print(f"✅ 訊息已發送到 {chat_id}")
        return True
    except Exception as e:
        print(f"❌ 發送失敗: {e}")
        return False


async def send_stock_alert(chat_id: int, symbol: str, message: str) -> bool:
    """
    發送股票提醒
    
    Args:
        chat_id: 用戶 chat_id
        symbol: 股票代碼
        message: 提醒內容
    
    Returns:
        是否發送成功
    """
    alert_text = f"""🔔 **股票提醒**

**{symbol}** - {message}

━━━━━━━━━━━━
_此為自動通知_"""
    
    return await send_message(chat_id, alert_text)


async def broadcast_message(chat_ids: list, message: str) -> dict:
    """
    批量發送訊息
    
    Args:
        chat_ids: chat_id 列表
        message: 要發送的訊息
    
    Returns:
        發送結果統計
    """
    results = {"success": 0, "failed": 0}
    
    for chat_id in chat_ids:
        success = await send_message(chat_id, message)
        if success:
            results["success"] += 1
        else:
            results["failed"] += 1
        await asyncio.sleep(0.5)  # 避免發送過快
    
    return results


def main():
    """命令行入口"""
    if len(sys.argv) < 3:
        print("用法: python send_message.py <chat_id> <message>")
        print("範例: python send_message.py 123456789 '這是測試訊息'")
        sys.exit(1)
    
    chat_id = int(sys.argv[1])
    message = sys.argv[2]
    
    asyncio.run(send_message(chat_id, message))


if __name__ == "__main__":
    main()
