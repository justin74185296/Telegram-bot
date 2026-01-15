"""
Telegram 內聯鍵盤組件
提供互動按鈕
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional


class InlineKeyboards:
    """內聯鍵盤工廠類"""
    
    @staticmethod
    def get_analysis_actions(symbol: str) -> InlineKeyboardMarkup:
        """
        獲取分析報告的操作按鈕
        
        Args:
            symbol: 股票代碼
        
        Returns:
            InlineKeyboardMarkup
        """
        keyboard = [
            [
                InlineKeyboardButton("🔄 刷新報告", callback_data=f"refresh_{symbol}"),
                InlineKeyboardButton("📰 更多新聞", callback_data=f"news_{symbol}"),
            ],
            [
                InlineKeyboardButton("📊 詳細指標", callback_data=f"indicators_{symbol}"),
                InlineKeyboardButton("📈 歷史走勢", callback_data=f"history_{symbol}"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_quick_symbols() -> InlineKeyboardMarkup:
        """
        獲取常用股票快捷按鈕
        
        Returns:
            InlineKeyboardMarkup
        """
        keyboard = [
            [
                InlineKeyboardButton("🍎 AAPL", callback_data="analyze_AAPL"),
                InlineKeyboardButton("🚗 TSLA", callback_data="analyze_TSLA"),
                InlineKeyboardButton("📱 GOOGL", callback_data="analyze_GOOGL"),
            ],
            [
                InlineKeyboardButton("💻 MSFT", callback_data="analyze_MSFT"),
                InlineKeyboardButton("📦 AMZN", callback_data="analyze_AMZN"),
                InlineKeyboardButton("👤 META", callback_data="analyze_META"),
            ],
            [
                InlineKeyboardButton("🎮 NVDA", callback_data="analyze_NVDA"),
                InlineKeyboardButton("🇭🇰 0700.HK", callback_data="analyze_0700"),
                InlineKeyboardButton("🇨🇳 BABA", callback_data="analyze_BABA"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_period_selector(symbol: str) -> InlineKeyboardMarkup:
        """
        獲取時間週期選擇器
        
        Args:
            symbol: 股票代碼
        
        Returns:
            InlineKeyboardMarkup
        """
        keyboard = [
            [
                InlineKeyboardButton("1週", callback_data=f"period_{symbol}_1wk"),
                InlineKeyboardButton("1月", callback_data=f"period_{symbol}_1mo"),
                InlineKeyboardButton("3月", callback_data=f"period_{symbol}_3mo"),
            ],
            [
                InlineKeyboardButton("6月", callback_data=f"period_{symbol}_6mo"),
                InlineKeyboardButton("1年", callback_data=f"period_{symbol}_1y"),
                InlineKeyboardButton("全部", callback_data=f"period_{symbol}_max"),
            ],
            [
                InlineKeyboardButton("◀️ 返回", callback_data=f"back_{symbol}"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_help_menu() -> InlineKeyboardMarkup:
        """
        獲取幫助選單
        
        Returns:
            InlineKeyboardMarkup
        """
        keyboard = [
            [
                InlineKeyboardButton("📖 使用指南", callback_data="help_guide"),
                InlineKeyboardButton("🔍 搜索股票", callback_data="help_search"),
            ],
            [
                InlineKeyboardButton("❓ 常見問題", callback_data="help_faq"),
                InlineKeyboardButton("📞 聯繫我們", callback_data="help_contact"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_confirm_buttons(action: str, data: str) -> InlineKeyboardMarkup:
        """
        獲取確認/取消按鈕
        
        Args:
            action: 動作類型
            data: 相關數據
        
        Returns:
            InlineKeyboardMarkup
        """
        keyboard = [
            [
                InlineKeyboardButton("✅ 確認", callback_data=f"confirm_{action}_{data}"),
                InlineKeyboardButton("❌ 取消", callback_data="cancel"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
