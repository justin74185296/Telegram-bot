"""
配置管理模組
從環境變量讀取所有配置
"""
import os
from dotenv import load_dotenv

# 載入 .env 文件
load_dotenv()


class Settings:
    """應用配置類"""
    
    def __init__(self):
        # Telegram Bot 配置
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
        
        # AI API 配置 (SiliconFlow)
        self.AI_API_KEY = os.getenv("AI_API_KEY", "")
        self.AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.siliconflow.cn/v1")
        self.AI_MODEL = os.getenv("AI_MODEL", "deepseek-ai/DeepSeek-V3")
        
        # 緩存配置
        self.CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))
    
    def validate(self) -> bool:
        """驗證必要的配置是否存在"""
        if not self.TELEGRAM_BOT_TOKEN:
            print("錯誤: TELEGRAM_BOT_TOKEN 未設置")
            return False
        if not self.AI_API_KEY:
            print("警告: AI_API_KEY 未設置，AI 報告功能將不可用")
        return True
