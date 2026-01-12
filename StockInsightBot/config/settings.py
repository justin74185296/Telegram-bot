"""
配置管理模块
从环境变量读取所有配置项，提供统一的配置访问接口
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


@dataclass
class Settings:
    """应用配置类"""
    
    # Telegram Bot 配置
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # OpenAI API 配置
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")
    openai_model: str = os.getenv("OPENAI_MODEL", "deepseek-ai/DeepSeek-V3")
    
    # 缓存配置（秒）
    cache_ttl_quote: int = int(os.getenv("CACHE_TTL_QUOTE", "60"))
    cache_ttl_financials: int = int(os.getenv("CACHE_TTL_FINANCIALS", "3600"))
    cache_ttl_news: int = int(os.getenv("CACHE_TTL_NEWS", "1800"))
    
    # 日志配置
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    def validate(self) -> bool:
        """
        验证必要的配置项是否已设置
        返回: True 如果所有必要配置都已设置
        """
        if not self.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN 未设置")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY 未设置")
        return True


# 全局配置实例
settings = Settings()
