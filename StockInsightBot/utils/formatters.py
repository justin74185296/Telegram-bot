"""
格式化工具模組
處理數字、文本和表格的格式化
"""
from typing import Union, Optional
from datetime import datetime


class Formatters:
    """格式化工具類"""
    
    @staticmethod
    def format_number(value: Union[int, float], decimals: int = 2) -> str:
        """
        格式化數字，添加千分位分隔符
        
        Args:
            value: 要格式化的數字
            decimals: 小數位數
        
        Returns:
            格式化後的字符串
        """
        if value is None:
            return "N/A"
        
        try:
            if isinstance(value, float):
                return f"{value:,.{decimals}f}"
            return f"{value:,}"
        except (ValueError, TypeError):
            return str(value)
    
    @staticmethod
    def format_percentage(value: Union[int, float], decimals: int = 2) -> str:
        """
        格式化百分比
        
        Args:
            value: 要格式化的數字（已經是百分比形式，如 5.5 表示 5.5%）
            decimals: 小數位數
        
        Returns:
            格式化後的字符串，帶正負號和 % 符號
        """
        if value is None:
            return "N/A"
        
        try:
            sign = "+" if value > 0 else ""
            return f"{sign}{value:.{decimals}f}%"
        except (ValueError, TypeError):
            return str(value)
    
    @staticmethod
    def format_market_cap(value: Union[int, float]) -> str:
        """
        格式化市值（自動轉換為適當的單位）
        
        Args:
            value: 市值（原始數字）
        
        Returns:
            格式化後的字符串（如 1.5T, 500B, 50M）
        """
        if value is None:
            return "N/A"
        
        try:
            value = float(value)
            if value >= 1e12:
                return f"{value/1e12:.2f}T"
            elif value >= 1e9:
                return f"{value/1e9:.2f}B"
            elif value >= 1e6:
                return f"{value/1e6:.2f}M"
            elif value >= 1e3:
                return f"{value/1e3:.2f}K"
            else:
                return f"{value:.2f}"
        except (ValueError, TypeError):
            return str(value)
    
    @staticmethod
    def format_volume(value: Union[int, float]) -> str:
        """
        格式化成交量
        
        Args:
            value: 成交量數字
        
        Returns:
            格式化後的字符串
        """
        return Formatters.format_market_cap(value)
    
    @staticmethod
    def format_price(value: Union[int, float], currency: str = "$") -> str:
        """
        格式化價格
        
        Args:
            value: 價格數字
            currency: 貨幣符號
        
        Returns:
            格式化後的字符串
        """
        if value is None:
            return "N/A"
        
        try:
            return f"{currency}{value:,.2f}"
        except (ValueError, TypeError):
            return str(value)
    
    @staticmethod
    def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M") -> str:
        """
        格式化日期時間
        
        Args:
            dt: datetime 對象
            fmt: 格式字符串
        
        Returns:
            格式化後的字符串
        """
        if dt is None:
            return "N/A"
        
        try:
            return dt.strftime(fmt)
        except (ValueError, AttributeError):
            return str(dt)
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """
        截斷過長的文本
        
        Args:
            text: 原始文本
            max_length: 最大長度
            suffix: 截斷後添加的後綴
        
        Returns:
            截斷後的文本
        """
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def get_trend_emoji(value: Union[int, float]) -> str:
        """
        根據數值返回趨勢表情符號
        
        Args:
            value: 數值（正數表示上漲，負數表示下跌）
        
        Returns:
            表情符號
        """
        if value is None:
            return "➖"
        
        try:
            if value > 0:
                return "📈"
            elif value < 0:
                return "📉"
            else:
                return "➖"
        except (ValueError, TypeError):
            return "➖"
