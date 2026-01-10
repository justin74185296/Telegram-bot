# -*- coding: utf-8 -*-
"""
Telegram 内联键盘组件
提供交互式按钮和快捷操作
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional


class InlineKeyboardBuilder:
    """
    内联键盘构建器
    用于创建各种交互式按钮组
    """
    
    @staticmethod
    def build_post_report_keyboard(symbol: str) -> InlineKeyboardMarkup:
        """
        构建报告末尾的操作键盘
        
        参数:
            symbol: 当前分析的股票代码
        返回:
            InlineKeyboardMarkup 对象
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 刷新报告",
                    callback_data=f"refresh:{symbol}"
                ),
                InlineKeyboardButton(
                    "📊 查看详细财务",
                    callback_data=f"financials:{symbol}"
                )
            ],
            [
                InlineKeyboardButton(
                    "📰 更多新闻",
                    callback_data=f"news:{symbol}"
                ),
                InlineKeyboardButton(
                    "📈 同业对比",
                    callback_data=f"compare:{symbol}"
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_help_keyboard() -> InlineKeyboardMarkup:
        """
        构建帮助页面的快捷键盘
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    "🍎 分析 AAPL",
                    callback_data="analyze:AAPL"
                ),
                InlineKeyboardButton(
                    "🚗 分析 TSLA",
                    callback_data="analyze:TSLA"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔍 分析 NVDA",
                    callback_data="analyze:NVDA"
                ),
                InlineKeyboardButton(
                    "☁️ 分析 MSFT",
                    callback_data="analyze:MSFT"
                )
            ],
            [
                InlineKeyboardButton(
                    "📖 使用指南",
                    callback_data="guide"
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_market_selector() -> InlineKeyboardMarkup:
        """
        构建市场选择键盘
        """
        keyboard = [
            [
                InlineKeyboardButton("🇺🇸 美股", callback_data="market:us"),
                InlineKeyboardButton("🇭🇰 港股", callback_data="market:hk"),
                InlineKeyboardButton("🇨🇳 A股", callback_data="market:cn")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_confirmation_keyboard(action: str, data: str) -> InlineKeyboardMarkup:
        """
        构建确认操作键盘
        
        参数:
            action: 操作类型
            data: 操作数据
        返回:
            InlineKeyboardMarkup 对象
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ 确认",
                    callback_data=f"confirm:{action}:{data}"
                ),
                InlineKeyboardButton(
                    "❌ 取消",
                    callback_data="cancel"
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_similar_stocks_keyboard(symbols: List[str]) -> InlineKeyboardMarkup:
        """
        构建同类股票快速分析键盘
        
        参数:
            symbols: 股票代码列表
        返回:
            InlineKeyboardMarkup 对象
        """
        # 每行最多3个按钮
        keyboard = []
        row = []
        
        for symbol in symbols[:6]:  # 最多6个
            row.append(
                InlineKeyboardButton(
                    f"📊 {symbol}",
                    callback_data=f"analyze:{symbol}"
                )
            )
            if len(row) == 3:
                keyboard.append(row)
                row = []
        
        if row:
            keyboard.append(row)
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_pagination_keyboard(
        current_page: int,
        total_pages: int,
        base_callback: str
    ) -> InlineKeyboardMarkup:
        """
        构建分页键盘
        
        参数:
            current_page: 当前页码（从1开始）
            total_pages: 总页数
            base_callback: 基础回调数据
        返回:
            InlineKeyboardMarkup 对象
        """
        buttons = []
        
        # 上一页按钮
        if current_page > 1:
            buttons.append(
                InlineKeyboardButton(
                    "◀️ 上一页",
                    callback_data=f"{base_callback}:page:{current_page - 1}"
                )
            )
        
        # 页码显示
        buttons.append(
            InlineKeyboardButton(
                f"📄 {current_page}/{total_pages}",
                callback_data="noop"
            )
        )
        
        # 下一页按钮
        if current_page < total_pages:
            buttons.append(
                InlineKeyboardButton(
                    "下一页 ▶️",
                    callback_data=f"{base_callback}:page:{current_page + 1}"
                )
            )
        
        return InlineKeyboardMarkup([buttons])


# 预定义的热门股票列表（用于快捷建议）
POPULAR_STOCKS = {
    "us": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK.B"],
    "hk": ["0700.HK", "9988.HK", "1810.HK", "3690.HK", "9618.HK", "2318.HK"],
    "cn": ["600519", "000858", "601318", "600036", "000333", "002415"]
}


def get_similar_stocks(symbol: str) -> List[str]:
    """
    获取同类/相关股票列表
    
    参数:
        symbol: 股票代码
    返回:
        相关股票代码列表
    """
    # 简化的相关股票映射
    similar_map = {
        # 科技股
        "AAPL": ["MSFT", "GOOGL", "AMZN", "META"],
        "MSFT": ["AAPL", "GOOGL", "AMZN", "CRM"],
        "GOOGL": ["META", "MSFT", "AMZN", "SNAP"],
        "META": ["GOOGL", "SNAP", "PINS", "TWTR"],
        "AMZN": ["MSFT", "GOOGL", "SHOP", "WMT"],
        "NVDA": ["AMD", "INTC", "TSM", "AVGO"],
        "TSLA": ["RIVN", "LCID", "NIO", "F"],
        
        # 电动车
        "NIO": ["TSLA", "XPEV", "LI", "RIVN"],
        "XPEV": ["NIO", "LI", "TSLA", "RIVN"],
        
        # 芯片
        "AMD": ["NVDA", "INTC", "TSM", "QCOM"],
        "INTC": ["AMD", "NVDA", "TSM", "MU"],
    }
    
    symbol_upper = symbol.upper().replace('.HK', '').replace('.SS', '').replace('.SZ', '')
    
    if symbol_upper in similar_map:
        return similar_map[symbol_upper]
    
    # 默认返回热门美股
    return POPULAR_STOCKS["us"][:4]
