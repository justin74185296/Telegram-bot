"""
Telegram 內聯鍵盤組件
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_report_keyboard(symbol: str) -> InlineKeyboardMarkup:
    """
    生成報告操作鍵盤
    """
    keyboard = [
        [
            InlineKeyboardButton("🔄 刷新報告", callback_data=f"refresh_{symbol}"),
            InlineKeyboardButton("📰 更多新聞", callback_data=f"news_{symbol}")
        ],
        [
            InlineKeyboardButton("📊 詳細財務", callback_data=f"financials_{symbol}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_news_keyboard(symbol: str) -> InlineKeyboardMarkup:
    """
    新聞頁面鍵盤
    """
    keyboard = [
        [
            InlineKeyboardButton("🔙 返回報告", callback_data=f"back_{symbol}"),
            InlineKeyboardButton("🔄 刷新新聞", callback_data=f"news_{symbol}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_start_keyboard() -> InlineKeyboardMarkup:
    """
    開始頁面鍵盤 - 熱門股票快速分析
    """
    keyboard = [
        [
            InlineKeyboardButton("🍎 AAPL", callback_data="analyze_AAPL"),
            InlineKeyboardButton("🚗 TSLA", callback_data="analyze_TSLA"),
            InlineKeyboardButton("🔍 GOOGL", callback_data="analyze_GOOGL")
        ],
        [
            InlineKeyboardButton("📱 微軟 MSFT", callback_data="analyze_MSFT"),
            InlineKeyboardButton("📦 亞馬遜 AMZN", callback_data="analyze_AMZN")
        ],
        [
            InlineKeyboardButton("🇭🇰 騰訊 0700", callback_data="analyze_0700"),
            InlineKeyboardButton("🇨🇳 茅台 600519", callback_data="analyze_600519")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
