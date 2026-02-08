"""
配置管理模組
從環境變量讀取所有敏感配置
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# 載入 .env 文件
load_dotenv()


@dataclass
class Settings:
    """應用程式配置類"""
    
    # Telegram Bot 配置
    telegram_token: str = ""
    
    # AI API 配置 (支援 OpenAI 或 SiliconFlow)
    ai_api_key: str = ""
    ai_api_base: str = "https://api.siliconflow.cn/v1"
    ai_model: str = "deepseek-ai/DeepSeek-V3"
    
    # 快取配置
    cache_ttl: int = 300  # 快取有效期（秒）
    cache_maxsize: int = 100  # 快取最大條目數
    
    # 日誌配置
    log_level: str = "INFO"
    
    def __post_init__(self):
        """初始化後從環境變量讀取配置"""
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", self.telegram_token)
        self.ai_api_key = os.getenv("AI_API_KEY", self.ai_api_key)
        self.ai_api_base = os.getenv("AI_API_BASE", self.ai_api_base)
        self.ai_model = os.getenv("AI_MODEL", self.ai_model)
        self.cache_ttl = int(os.getenv("CACHE_TTL", self.cache_ttl))
        self.cache_maxsize = int(os.getenv("CACHE_MAXSIZE", self.cache_maxsize))
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
    
    @property
    def ai_enabled(self) -> bool:
        """檢查 AI 功能是否可用"""
        return bool(self.ai_api_key)

    def validate(self) -> bool:
        """驗證必要配置是否存在"""
        if not self.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN 未設置")
        if not self.ai_api_key:
            import logging
            logging.getLogger("StockInsightBot").warning(
                "AI_API_KEY 未設置，AI 分析功能已停用，將使用基礎報告"
            )
        return True


# 全局配置實例
settings = Settings()
