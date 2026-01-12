"""
格式化工具模块
提供数字、表格、文本的格式化功能
"""

from typing import Union, Optional
from decimal import Decimal


def format_number(
    value: Union[int, float, None],
    decimals: int = 2,
    use_chinese: bool = True
) -> str:
    """
    格式化数字，支持中文单位
    
    Args:
        value: 数值
        decimals: 小数位数
        use_chinese: 是否使用中文单位（万/亿）
        
    Returns:
        格式化后的字符串
    """
    if value is None:
        return "N/A"
    
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "N/A"
    
    abs_value = abs(value)
    sign = "-" if value < 0 else ""
    
    if use_chinese:
        if abs_value >= 1e12:
            return f"{sign}{abs_value/1e12:.{decimals}f}万亿"
        elif abs_value >= 1e8:
            return f"{sign}{abs_value/1e8:.{decimals}f}亿"
        elif abs_value >= 1e4:
            return f"{sign}{abs_value/1e4:.{decimals}f}万"
    else:
        if abs_value >= 1e12:
            return f"{sign}{abs_value/1e12:.{decimals}f}T"
        elif abs_value >= 1e9:
            return f"{sign}{abs_value/1e9:.{decimals}f}B"
        elif abs_value >= 1e6:
            return f"{sign}{abs_value/1e6:.{decimals}f}M"
        elif abs_value >= 1e3:
            return f"{sign}{abs_value/1e3:.{decimals}f}K"
    
    return f"{sign}{abs_value:,.{decimals}f}"


def format_percentage(
    value: Union[float, None],
    decimals: int = 2,
    include_sign: bool = True
) -> str:
    """
    格式化百分比
    
    Args:
        value: 数值（0.1 表示 10%，或直接是 10）
        decimals: 小数位数
        include_sign: 是否包含正负号
        
    Returns:
        格式化后的百分比字符串
    """
    if value is None:
        return "N/A"
    
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "N/A"
    
    # 如果值小于1，假设是小数形式的百分比
    if abs(value) < 1 and value != 0:
        value *= 100
    
    if include_sign:
        return f"{value:+.{decimals}f}%"
    else:
        return f"{value:.{decimals}f}%"


def format_currency(
    value: Union[float, None],
    currency: str = "USD",
    decimals: int = 2
) -> str:
    """
    格式化货币金额
    
    Args:
        value: 数值
        currency: 货币代码
        decimals: 小数位数
        
    Returns:
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
    formatted_value = format_number(value, decimals, use_chinese=True)
    
    return f"{symbol}{formatted_value}"


def format_change(
    value: Union[float, None],
    percent: Union[float, None] = None
) -> str:
    """
    格式化涨跌变化
    
    Args:
        value: 变化值
        percent: 变化百分比
        
    Returns:
        带emoji的变化字符串
    """
    if value is None:
        return "N/A"
    
    emoji = "📈" if value >= 0 else "📉"
    
    result = f"{emoji} {value:+.2f}"
    
    if percent is not None:
        result += f" ({percent:+.2f}%)"
    
    return result


def format_table_row(
    columns: list,
    widths: list = None,
    separator: str = " | "
) -> str:
    """
    格式化表格行
    
    Args:
        columns: 列内容列表
        widths: 各列宽度
        separator: 分隔符
        
    Returns:
        格式化的表格行
    """
    if widths:
        formatted_cols = []
        for col, width in zip(columns, widths):
            formatted_cols.append(str(col).ljust(width))
        return separator.join(formatted_cols)
    else:
        return separator.join(str(col) for col in columns)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后的后缀
        
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def escape_markdown(text: str) -> str:
    """
    转义Markdown特殊字符
    
    Args:
        text: 原始文本
        
    Returns:
        转义后的文本
    """
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text
