# -*- coding: utf-8 -*-
"""
日志配置模块
提供统一的日志记录器配置
"""

import logging
import sys
from typing import Optional
from config import settings


# 日志格式
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 全局日志器缓存
_loggers = {}


def setup_logger(
    name: str = "StockInsightBot",
    level: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    设置并返回日志记录器
    
    参数:
        name: 日志器名称
        level: 日志级别，默认从配置读取
        log_file: 日志文件路径，默认从配置读取
    返回:
        配置好的 Logger 实例
    """
    # 如果已经配置过，直接返回
    if name in _loggers:
        return _loggers[name]
    
    # 创建日志器
    logger = logging.getLogger(name)
    
    # 设置日志级别
    log_level = level or settings.log_level
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 防止重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建格式化器
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # 控制台处理器（始终添加）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.addHandler(console_handler)
    
    # 文件处理器（可选）
    file_path = log_file or settings.log_file
    if file_path:
        try:
            file_handler = logging.FileHandler(file_path, encoding='utf-8')
            file_handler.setFormatter(formatter)
            file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"无法创建日志文件 {file_path}: {e}")
    
    # 缓存日志器
    _loggers[name] = logger
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志记录器
    
    参数:
        name: 日志器名称，如果为None则返回根日志器
    返回:
        Logger 实例
    """
    if name is None:
        name = "StockInsightBot"
    
    # 如果是子模块名称，创建子日志器
    if name.startswith("StockInsightBot."):
        parent = setup_logger("StockInsightBot")
        return logging.getLogger(name)
    
    # 如果已缓存，直接返回
    if name in _loggers:
        return _loggers[name]
    
    # 否则创建新的日志器
    return setup_logger(name)


class LoggerMixin:
    """
    日志混入类
    为类添加统一的日志记录功能
    """
    
    @property
    def logger(self) -> logging.Logger:
        """获取当前类的日志器"""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(f"StockInsightBot.{self.__class__.__name__}")
        return self._logger


# 初始化根日志器
root_logger = setup_logger()
