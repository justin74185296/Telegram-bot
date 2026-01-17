"""
Helper Utilities
================

Various helper functions for the trading system.
"""

import json
import logging
import re
from typing import Any, Optional, Dict
from datetime import datetime


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Set up logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        format_string: Custom format string
    
    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    logger = logging.getLogger("polymarket_agents")
    return logger


def parse_json_response(response: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON from an LLM response that may contain markdown code blocks.
    
    Args:
        response: Raw response string that may contain JSON
    
    Returns:
        Parsed dictionary or None if parsing fails
    """
    # Try direct JSON parsing first
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    json_patterns = [
        r"```json\s*([\s\S]*?)\s*```",  # ```json ... ```
        r"```\s*([\s\S]*?)\s*```",       # ``` ... ```
        r"\{[\s\S]*\}",                   # Bare JSON object
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, response)
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue
    
    return None


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format a number as currency.
    
    Args:
        amount: The amount to format
        currency: Currency code (default: USD)
    
    Returns:
        Formatted currency string
    """
    if currency == "USD":
        if amount >= 1_000_000:
            return f"${amount/1_000_000:.2f}M"
        elif amount >= 1_000:
            return f"${amount/1_000:.2f}K"
        else:
            return f"${amount:.2f}"
    else:
        return f"{amount:.2f} {currency}"


def calculate_portfolio_metrics(
    total_value: float,
    cash_balance: float,
    positions: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Calculate portfolio metrics.
    
    Args:
        total_value: Total portfolio value
        cash_balance: Available cash
        positions: Dictionary of current positions
    
    Returns:
        Portfolio metrics dictionary
    """
    positions_value = total_value - cash_balance
    exposure_percent = (positions_value / total_value * 100) if total_value > 0 else 0
    
    # Calculate position weights
    position_weights = {}
    for market_id, position in positions.items():
        pos_value = position.get("value", 0)
        weight = (pos_value / total_value * 100) if total_value > 0 else 0
        position_weights[market_id] = round(weight, 2)
    
    # Find largest position
    largest_position = max(position_weights.values()) if position_weights else 0
    
    return {
        "total_value": round(total_value, 2),
        "cash_balance": round(cash_balance, 2),
        "positions_value": round(positions_value, 2),
        "exposure_percent": round(exposure_percent, 2),
        "largest_position_percent": round(largest_position, 2),
        "position_count": len(positions),
        "position_weights": position_weights,
        "cash_ratio": round((cash_balance / total_value * 100) if total_value > 0 else 100, 2),
    }


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format a datetime as ISO string.
    
    Args:
        dt: Datetime to format (default: now)
    
    Returns:
        ISO formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate a string to max_length, adding suffix if truncated.
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.
    """
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    Clamp a value to a range.
    """
    return max(min_value, min(max_value, value))


def format_percentage(value: float, decimal_places: int = 2) -> str:
    """
    Format a decimal as a percentage string.
    """
    return f"{value * 100:.{decimal_places}f}%"


def format_change(value: float, include_sign: bool = True) -> str:
    """
    Format a change value with appropriate sign and color indicator.
    """
    if value > 0:
        sign = "+" if include_sign else ""
        indicator = "📈"
    elif value < 0:
        sign = "" if include_sign else ""  # Negative sign is automatic
        indicator = "📉"
    else:
        sign = ""
        indicator = "➡️"
    
    return f"{indicator} {sign}{value:.2%}"


class Timer:
    """Simple timer context manager for measuring execution time."""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, *args):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        print(f"⏱️ {self.name} completed in {duration:.2f} seconds")
    
    @property
    def elapsed(self) -> float:
        if self.start_time is None:
            return 0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()


def print_banner(text: str, char: str = "=", width: int = 60):
    """
    Print a banner with text centered.
    """
    border = char * width
    padding = (width - len(text) - 2) // 2
    centered = f"{char}{' ' * padding}{text}{' ' * padding}{char}"
    if len(centered) < width:
        centered += char
    print(border)
    print(centered)
    print(border)


def print_section(title: str, content: str = ""):
    """
    Print a section with a title.
    """
    print(f"\n{'─' * 60}")
    print(f"📌 {title}")
    print(f"{'─' * 60}")
    if content:
        print(content)
