# -*- coding: utf-8 -*-
"""
配置管理模块
从环境变量读取所有配置项，并提供默认值
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


@dataclass
class Settings:
    """
    应用配置类
    所有配置项从环境变量读取，支持默认值
    """
    
    # Telegram 配置
    telegram_bot_token: str = field(
        default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", "")
    )
    
    # OpenAI 配置
    openai_api_key: str = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", "")
    )
    openai_model: str = field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o")
    )
    openai_api_base: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENAI_API_BASE")
    )
    
    # 缓存配置
    cache_ttl: int = field(
        default_factory=lambda: int(os.getenv("CACHE_TTL", "300"))
    )
    cache_max_size: int = field(
        default_factory=lambda: int(os.getenv("CACHE_MAX_SIZE", "100"))
    )
    
    # 日志配置
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )
    log_file: Optional[str] = field(
        default_factory=lambda: os.getenv("LOG_FILE") or None
    )
    
    # 消息配置
    max_message_length: int = field(
        default_factory=lambda: int(os.getenv("MAX_MESSAGE_LENGTH", "4000"))
    )
    news_limit: int = field(
        default_factory=lambda: int(os.getenv("NEWS_LIMIT", "5"))
    )
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        验证必要的配置项是否已设置
        
        返回:
            tuple: (是否有效, 错误信息列表)
        """
        errors = []
        
        if not self.telegram_bot_token:
            errors.append("TELEGRAM_BOT_TOKEN 未设置")
        
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY 未设置")
        
        return len(errors) == 0, errors
    
    def __post_init__(self):
        """初始化后的处理"""
        # 确保日志级别为有效值
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            self.log_level = "INFO"
        else:
            self.log_level = self.log_level.upper()


# 创建全局配置实例
settings = Settings()
