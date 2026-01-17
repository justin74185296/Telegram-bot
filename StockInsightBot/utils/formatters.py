"""
格式化工具模組
"""


def format_number(value: float, decimals: int = 2) -> str:
    """
    格式化數字，添加千分位分隔符
    """
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def format_percent(value: float, decimals: int = 2) -> str:
    """
    格式化百分比
    """
    if value is None:
        return "N/A"
    return f"{value * 100:+.{decimals}f}%"


def format_currency(value: float, currency: str = "USD", decimals: int = 2) -> str:
    """
    格式化貨幣
    """
    if value is None:
        return "N/A"
    
    symbols = {
        "USD": "$",
        "HKD": "HK$",
        "CNY": "¥",
        "EUR": "€",
        "GBP": "£"
    }
    
    symbol = symbols.get(currency, currency + " ")
    return f"{symbol}{value:,.{decimals}f}"


def format_market_cap(value: float) -> str:
    """
    格式化市值
    """
    if value is None or value == 0:
        return "N/A"
    
    if value >= 1e12:
        return f"{value / 1e12:.2f}兆"
    elif value >= 1e9:
        return f"{value / 1e9:.2f}億"
    elif value >= 1e6:
        return f"{value / 1e6:.2f}百萬"
    else:
        return f"{value:,.0f}"
