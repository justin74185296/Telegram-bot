"""
Configuration module for Aster Perpetuals Trading Bot.

All trading parameters, API credentials, and bot settings are defined here.
API keys are loaded from environment variables for security.
Optionally loads from config.yaml if present.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env file (if present) so local development doesn't need exports
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Optional: load config.yaml overrides
# ---------------------------------------------------------------------------
_yaml_config: dict = {}
_yaml_path = Path(__file__).resolve().parent.parent / "config.yaml"
if _yaml_path.exists():
    try:
        import yaml  # type: ignore[import-untyped]
        with open(_yaml_path, "r") as _f:
            _yaml_config = yaml.safe_load(_f) or {}
    except ImportError:
        pass  # PyYAML not installed — skip yaml config

def _cfg(key: str, default, typ=str):
    """Resolve config value: env var → yaml → default."""
    env = os.getenv(key)
    if env is not None:
        return typ(env)
    yaml_val = _yaml_config.get(key)
    if yaml_val is not None:
        return typ(yaml_val)
    return default

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
LOG_LEVEL = _cfg("LOG_LEVEL", "INFO", str).upper()
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
)

logger = logging.getLogger("aster_bot")

# ---------------------------------------------------------------------------
# Trading Mode  ("paper" = simulation, "live" = real money)
# ---------------------------------------------------------------------------
TRADING_MODE: str = _cfg("TRADING_MODE", "paper", str).lower()
IS_PAPER_TRADING: bool = TRADING_MODE != "live"

if IS_PAPER_TRADING:
    logger.info("*** PAPER TRADING MODE (simulated) ***")
else:
    logger.warning("*** LIVE TRADING MODE — real funds at risk ***")

# ---------------------------------------------------------------------------
# API Credentials
# ---------------------------------------------------------------------------
API_KEY: str = _cfg("ASTER_API_KEY", "", str)
API_SECRET: str = _cfg("ASTER_API_SECRET", "", str)

# Optional: Custom Aster Pro API base URL.
ASTER_API_URL: str = _cfg("ASTER_API_URL", "", str)

# ---------------------------------------------------------------------------
# Symbols to trade (CCXT unified perpetual format)
# ---------------------------------------------------------------------------
SYMBOLS: list[str] = ["BTC/USDT:USDT", "ETH/USDT:USDT"]

# ---------------------------------------------------------------------------
# Strategy Method
# ---------------------------------------------------------------------------
SUPPORT_RESISTANCE_METHOD: str = _cfg("SUPPORT_RESISTANCE_METHOD", "bollinger", str)

# ---------------------------------------------------------------------------
# Timeframe & Polling  (HIGH-FREQUENCY: 1m candles, 10s polling)
# ---------------------------------------------------------------------------
TIMEFRAME: str = _cfg("TIMEFRAME", "1m", str)
OHLCV_LIMIT: int = _cfg("OHLCV_LIMIT", 100, int)
POLL_INTERVAL_SEC: int = _cfg("POLL_INTERVAL_SEC", 10, int)

# ---------------------------------------------------------------------------
# Leverage & Margin
# ---------------------------------------------------------------------------
LEVERAGE: int = _cfg("LEVERAGE", 5, int)
MARGIN_TYPE: str = "ISOLATED"

# ---------------------------------------------------------------------------
# Bollinger Bands Parameters
# ---------------------------------------------------------------------------
BB_PERIOD: int = _cfg("BB_PERIOD", 20, int)
BB_STD_DEV: float = _cfg("BB_STD_DEV", 2.0, float)

# ---------------------------------------------------------------------------
# Volume Filter
# ---------------------------------------------------------------------------
VOLUME_AVG_PERIOD: int = _cfg("VOLUME_AVG_PERIOD", 20, int)
VOLUME_THRESHOLD_PCT: float = _cfg("VOLUME_THRESHOLD_PCT", 30.0, float)
# Volume must be > avg * (1 + VOLUME_THRESHOLD_PCT/100)

# ---------------------------------------------------------------------------
# RSI Parameters
# ---------------------------------------------------------------------------
RSI_PERIOD: int = _cfg("RSI_PERIOD", 14, int)
RSI_LONG_MAX: float = _cfg("RSI_LONG_MAX", 50.0, float)   # Long: RSI < 50
RSI_SHORT_MIN: float = _cfg("RSI_SHORT_MIN", 50.0, float)  # Short: RSI > 50

# ---------------------------------------------------------------------------
# EMA Parameters (kept for backward compatibility / alternative strategy)
# ---------------------------------------------------------------------------
EMA_SHORT_PERIOD: int = _cfg("EMA_SHORT_PERIOD", 9, int)
EMA_LONG_PERIOD: int = _cfg("EMA_LONG_PERIOD", 21, int)

# ---------------------------------------------------------------------------
# Risk Management
# ---------------------------------------------------------------------------
RISK_PER_TRADE_PCT: float = _cfg("RISK_PER_TRADE_PCT", 0.3, float)

# ---------------------------------------------------------------------------
# Trailing Stop Configuration
# ---------------------------------------------------------------------------
TRAILING_STOP_INITIAL_PCT: float = _cfg("TRAILING_STOP_INITIAL_PCT", 0.5, float)
TRAILING_STOP_CALLBACK_PCT: float = _cfg("TRAILING_STOP_CALLBACK_PCT", 0.3, float)

# Legacy fixed SL/TP (used as fallback if trailing stop fails)
STOP_LOSS_PCT: float = _cfg("STOP_LOSS_PCT", 0.5, float)
TAKE_PROFIT_PCT: float = _cfg("TAKE_PROFIT_PCT", 1.5, float)

# ---------------------------------------------------------------------------
# Maximum Hold Time
# ---------------------------------------------------------------------------
MAX_HOLD_SECONDS: int = _cfg("MAX_HOLD_SECONDS", 3600, int)  # 1 hour max

# ---------------------------------------------------------------------------
# OpenClaw Supervisor — high-frequency limits
# ---------------------------------------------------------------------------
MAX_CONSECUTIVE_LOSSES: int = _cfg("MAX_CONSECUTIVE_LOSSES", 5, int)
MAX_TOTAL_LOSS_PCT: float = _cfg("MAX_TOTAL_LOSS_PCT", 2.0, float)
MAX_TRADES_PER_HOUR: int = _cfg("MAX_TRADES_PER_HOUR", 40, int)

# ---------------------------------------------------------------------------
# Paper Trading — simulated balance
# ---------------------------------------------------------------------------
PAPER_INITIAL_BALANCE: float = _cfg("PAPER_INITIAL_BALANCE", 10_000.0, float)

# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
DASHBOARD_HOST: str = _cfg("DASHBOARD_HOST", "0.0.0.0", str)
DASHBOARD_PORT: int = _cfg("DASHBOARD_PORT", 8080, int)

# ---------------------------------------------------------------------------
# Retry / Rate-limit Settings
# ---------------------------------------------------------------------------
MAX_RETRIES: int = 5
RETRY_DELAY_BASE_SEC: float = 2.0
