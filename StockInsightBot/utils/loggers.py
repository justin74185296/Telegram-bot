"""
日誌配置模組
統一的日誌格式和處理
"""
import logging
import sys
from typing import Optional


def setup_logger(name: str = "StockInsightBot", level: str = "INFO") -> logging.Logger:
    """
    設置並返回一個配置好的日誌記錄器
    
    Args:
        name: 日誌記錄器名稱
        level: 日誌級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        配置好的 Logger 實例
    """
    logger = logging.getLogger(name)
    
    # 避免重複添加處理器
    if logger.handlers:
        return logger
    
    # 設置日誌級別
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # 創建控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # 設置日誌格式
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加處理器
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    獲取日誌記錄器
    
    Args:
        name: 子日誌記錄器名稱（可選）
    
    Returns:
        Logger 實例
    """
    base_name = "StockInsightBot"
    if name:
        return logging.getLogger(f"{base_name}.{name}")
    return logging.getLogger(base_name)
