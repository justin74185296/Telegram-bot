# -*- coding: utf-8 -*-
"""
格式化工具模块
提供数字、文本、表格等格式化功能
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import locale


class NumberFormatter:
    """
    数字格式化工具类
    处理各种数值的显示格式
    """
    
    @staticmethod
    def format_currency(
        value: Union[int, float, None],
        currency: str = "USD",
        decimal_places: int = 2
    ) -> str:
        """
        格式化货币值
        
        参数:
            value: 数值
            currency: 货币代码
            decimal_places: 小数位数
        返回:
            格式化后的货币字符串
        """
        if value is None:
            return "N/A"
        
        currency_symbols = {
            "USD": "$",
            "CNY": "¥",
            "HKD": "HK$",
            "EUR": "€",
            "GBP": "£",
            "JPY": "¥"
        }
        
        symbol = currency_symbols.get(currency, currency + " ")
        
        try:
            return f"{symbol}{value:,.{decimal_places}f}"
        except (ValueError, TypeError):
            return "N/A"
    
    @staticmethod
    def format_large_number(value: Union[int, float, None], precision: int = 2) -> str:
        """
        格式化大数字（自动选择单位）
        
        参数:
            value: 数值
            precision: 精度
        返回:
            如 1.5B, 300M, 50K 等
        """
        if value is None:
            return "N/A"
        
        try:
            value = float(value)
            
            if abs(value) >= 1_000_000_000_000:
                return f"{value / 1_000_000_000_000:.{precision}f}T"
            elif abs(value) >= 1_000_000_000:
                return f"{value / 1_000_000_000:.{precision}f}B"
            elif abs(value) >= 1_000_000:
                return f"{value / 1_000_000:.{precision}f}M"
            elif abs(value) >= 1_000:
                return f"{value / 1_000:.{precision}f}K"
            else:
                return f"{value:,.{precision}f}"
        except (ValueError, TypeError):
            return "N/A"
    
    @staticmethod
    def format_percentage(
        value: Union[int, float, None],
        decimal_places: int = 2,
        include_sign: bool = False
    ) -> str:
        """
        格式化百分比
        
        参数:
            value: 数值（0.15 或 15 都表示15%）
            decimal_places: 小数位数
            include_sign: 是否包含正负号
        返回:
            格式化后的百分比字符串
        """
        if value is None:
            return "N/A"
        
        try:
            # 判断是小数还是已经是百分比形式
            if abs(value) < 1:
                value = value * 100
            
            if include_sign:
                return f"{value:+.{decimal_places}f}%"
            else:
                return f"{value:.{decimal_places}f}%"
        except (ValueError, TypeError):
            return "N/A"
    
    @staticmethod
    def format_ratio(value: Union[int, float, None], decimal_places: int = 2) -> str:
        """
        格式化比率
        
        参数:
            value: 数值
            decimal_places: 小数位数
        返回:
            格式化后的比率字符串
        """
        if value is None:
            return "N/A"
        
        try:
            return f"{float(value):.{decimal_places}f}"
        except (ValueError, TypeError):
            return "N/A"
    
    @staticmethod
    def format_price_change(change: float, change_percent: float, currency: str = "USD") -> str:
        """
        格式化价格变动
        
        参数:
            change: 涨跌额
            change_percent: 涨跌幅
            currency: 货币代码
        返回:
            格式化后的变动字符串
        """
        currency_symbols = {"USD": "$", "CNY": "¥", "HKD": "HK$"}
        symbol = currency_symbols.get(currency, "")
        
        if change >= 0:
            return f"📈 +{symbol}{change:.2f} (+{change_percent:.2f}%)"
        else:
            return f"📉 {symbol}{change:.2f} ({change_percent:.2f}%)"


class TextFormatter:
    """
    文本格式化工具类
    处理文本、表格等显示格式
    """
    
    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = "...") -> str:
        """
        截断文本
        
        参数:
            text: 原始文本
            max_length: 最大长度
            suffix: 截断后缀
        返回:
            截断后的文本
        """
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def build_markdown_table(
        headers: List[str],
        rows: List[List[str]],
        alignment: List[str] = None
    ) -> str:
        """
        构建Markdown表格
        
        参数:
            headers: 表头列表
            rows: 数据行列表
            alignment: 对齐方式列表 ('left', 'center', 'right')
        返回:
            Markdown表格字符串
        """
        if not headers or not rows:
            return ""
        
        # 默认左对齐
        if alignment is None:
            alignment = ['left'] * len(headers)
        
        # 构建对齐分隔符
        separators = []
        for align in alignment:
            if align == 'center':
                separators.append(':---:')
            elif align == 'right':
                separators.append('---:')
            else:
                separators.append('---')
        
        # 构建表格
        lines = []
        lines.append('| ' + ' | '.join(headers) + ' |')
        lines.append('| ' + ' | '.join(separators) + ' |')
        
        for row in rows:
            # 确保行数据与列数匹配
            row_data = row + [''] * (len(headers) - len(row))
            lines.append('| ' + ' | '.join(row_data[:len(headers)]) + ' |')
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_datetime(
        dt: datetime,
        format_str: str = "%Y-%m-%d %H:%M"
    ) -> str:
        """
        格式化日期时间
        
        参数:
            dt: datetime 对象
            format_str: 格式字符串
        返回:
            格式化后的日期时间字符串
        """
        if dt is None:
            return "N/A"
        
        try:
            return dt.strftime(format_str)
        except (ValueError, AttributeError):
            return str(dt)
    
    @staticmethod
    def format_list_to_bullets(items: List[str], bullet: str = "•") -> str:
        """
        将列表格式化为项目符号列表
        
        参数:
            items: 字符串列表
            bullet: 项目符号
        返回:
            格式化后的列表字符串
        """
        if not items:
            return ""
        
        return '\n'.join(f"{bullet} {item}" for item in items)
    
    @staticmethod
    def format_key_value(
        data: Dict[str, Any],
        separator: str = "：",
        bullet: str = "•"
    ) -> str:
        """
        格式化键值对数据
        
        参数:
            data: 键值对字典
            separator: 键值分隔符
            bullet: 项目符号
        返回:
            格式化后的字符串
        """
        if not data:
            return ""
        
        lines = []
        for key, value in data.items():
            if value is not None:
                lines.append(f"{bullet} **{key}**{separator}{value}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """
        转义Markdown特殊字符
        
        参数:
            text: 原始文本
        返回:
            转义后的文本
        """
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        
        return text
    
    @staticmethod
    def format_stock_symbol(symbol: str) -> str:
        """
        格式化股票代码显示
        
        参数:
            symbol: 原始代码
        返回:
            格式化后的代码
        """
        symbol = symbol.upper().strip()
        
        # 检测市场类型并添加标识
        if symbol.endswith('.SS') or symbol.endswith('.SZ'):
            market = "🇨🇳 A股"
        elif symbol.endswith('.HK'):
            market = "🇭🇰 港股"
        else:
            market = "🇺🇸 美股"
        
        return f"{symbol} ({market})"
    
    @staticmethod
    def format_trend_indicator(
        current: float,
        previous: float,
        precision: int = 2
    ) -> str:
        """
        格式化趋势指示器
        
        参数:
            current: 当前值
            previous: 前值
            precision: 精度
        返回:
            带趋势箭头的字符串
        """
        if current is None or previous is None or previous == 0:
            return "N/A"
        
        change = ((current - previous) / abs(previous)) * 100
        
        if change > 5:
            arrow = "🔺"
        elif change > 0:
            arrow = "▲"
        elif change < -5:
            arrow = "🔻"
        elif change < 0:
            arrow = "▼"
        else:
            arrow = "➡️"
        
        return f"{current:.{precision}f} {arrow} {change:+.1f}%"


class TableBuilder:
    """
    表格构建器
    用于构建复杂的数据表格
    """
    
    def __init__(self):
        """初始化表格构建器"""
        self.headers: List[str] = []
        self.rows: List[List[str]] = []
        self.alignments: List[str] = []
    
    def add_header(self, header: str, alignment: str = 'left') -> 'TableBuilder':
        """
        添加表头列
        
        参数:
            header: 列标题
            alignment: 对齐方式
        返回:
            self (支持链式调用)
        """
        self.headers.append(header)
        self.alignments.append(alignment)
        return self
    
    def add_row(self, *values) -> 'TableBuilder':
        """
        添加数据行
        
        参数:
            *values: 行数据
        返回:
            self (支持链式调用)
        """
        self.rows.append([str(v) if v is not None else "N/A" for v in values])
        return self
    
    def build(self) -> str:
        """
        构建表格
        
        返回:
            Markdown表格字符串
        """
        return TextFormatter.build_markdown_table(
            self.headers,
            self.rows,
            self.alignments
        )
    
    def clear(self) -> 'TableBuilder':
        """
        清空表格数据
        
        返回:
            self (支持链式调用)
        """
        self.headers = []
        self.rows = []
        self.alignments = []
        return self
