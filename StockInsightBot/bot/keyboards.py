"""
Telegram 内联键盘组件
提供交互式按钮和快捷操作
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional


def create_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    创建主菜单键盘
    
    Returns:
        InlineKeyboardMarkup 主菜单
    """
    keyboard = [
        [
            InlineKeyboardButton("📊 分析股票", callback_data="menu_analyze"),
            InlineKeyboardButton("❓ 使用帮助", callback_data="menu_help")
        ],
        [
            InlineKeyboardButton("🔥 热门股票", callback_data="menu_popular"),
            InlineKeyboardButton("📈 市场概览", callback_data="menu_market")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_report_keyboard(symbol: str) -> InlineKeyboardMarkup:
    """
    创建报告操作键盘
    
    Args:
        symbol: 股票代码
        
    Returns:
        InlineKeyboardMarkup 报告操作按钮
    """
    keyboard = [
        [
            InlineKeyboardButton("🔄 刷新报告", callback_data=f"refresh_{symbol}"),
            InlineKeyboardButton("📈 查看K线", callback_data=f"chart_{symbol}")
        ],
        [
            InlineKeyboardButton("🏢 同行对比", callback_data=f"peers_{symbol}"),
            InlineKeyboardButton("📰 更多新闻", callback_data=f"news_{symbol}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_popular_stocks_keyboard() -> InlineKeyboardMarkup:
    """
    创建热门股票快捷键盘
    
    Returns:
        InlineKeyboardMarkup 热门股票按钮
    """
    # 热门美股
    us_stocks = [
        ("苹果", "AAPL"),
        ("特斯拉", "TSLA"),
        ("英伟达", "NVDA"),
        ("微软", "MSFT"),
    ]
    
    # 热门中概股
    cn_stocks = [
        ("阿里巴巴", "BABA"),
        ("腾讯", "0700.HK"),
        ("京东", "JD"),
        ("拼多多", "PDD"),
    ]
    
    keyboard = [
        [InlineKeyboardButton(f"{name}", callback_data=f"analyze_{symbol}") 
         for name, symbol in us_stocks[:2]],
        [InlineKeyboardButton(f"{name}", callback_data=f"analyze_{symbol}") 
         for name, symbol in us_stocks[2:]],
        [InlineKeyboardButton(f"{name}", callback_data=f"analyze_{symbol}") 
         for name, symbol in cn_stocks[:2]],
        [InlineKeyboardButton(f"{name}", callback_data=f"analyze_{symbol}") 
         for name, symbol in cn_stocks[2:]],
        [InlineKeyboardButton("🔙 返回主菜单", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_confirm_keyboard(action: str, data: str) -> InlineKeyboardMarkup:
    """
    创建确认操作键盘
    
    Args:
        action: 操作类型
        data: 相关数据
        
    Returns:
        InlineKeyboardMarkup 确认按钮
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ 确认", callback_data=f"confirm_{action}_{data}"),
            InlineKeyboardButton("❌ 取消", callback_data="cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_pagination_keyboard(
    current_page: int, 
    total_pages: int, 
    data_type: str,
    symbol: str
) -> InlineKeyboardMarkup:
    """
    创建分页键盘
    
    Args:
        current_page: 当前页码
        total_pages: 总页数
        data_type: 数据类型 (news, history等)
        symbol: 股票代码
        
    Returns:
        InlineKeyboardMarkup 分页按钮
    """
    buttons = []
    
    # 上一页
    if current_page > 1:
        buttons.append(InlineKeyboardButton(
            "⬅️ 上一页", 
            callback_data=f"page_{data_type}_{symbol}_{current_page-1}"
        ))
    
    # 页码显示
    buttons.append(InlineKeyboardButton(
        f"{current_page}/{total_pages}", 
        callback_data="noop"
    ))
    
    # 下一页
    if current_page < total_pages:
        buttons.append(InlineKeyboardButton(
            "➡️ 下一页", 
            callback_data=f"page_{data_type}_{symbol}_{current_page+1}"
        ))
    
    keyboard = [buttons]
    keyboard.append([InlineKeyboardButton("🔙 返回", callback_data=f"back_{symbol}")])
    
    return InlineKeyboardMarkup(keyboard)
