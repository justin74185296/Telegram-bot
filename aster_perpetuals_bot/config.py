"""
Configuration module for Aster Perpetuals Trading Bot.

All trading parameters, API credentials, and bot settings are defined here.
API keys are loaded from environment variables for security.
"""

import os
import logging
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env file (if present) so local development doesn't need exports
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
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
TRADING_MODE: str = os.getenv("TRADING_MODE", "paper").lower()
IS_PAPER_TRADING: bool = TRADING_MODE != "live"

if IS_PAPER_TRADING:
    logger.info("*** PAPER TRADING MODE (simulated) ***")
else:
    logger.warning("*** LIVE TRADING MODE — real funds at risk ***")

# ---------------------------------------------------------------------------
# API Credentials
# ---------------------------------------------------------------------------
API_KEY: str = os.getenv("ASTER_API_KEY", "")
API_SECRET: str = os.getenv("ASTER_API_SECRET", "")

# Optional: Custom Aster Pro API base URL.
# Aster Pro API is Binance-futures compatible.  If empty, ccxt default is used.
# Reference: https://docs.asterdex.com/product/aster-perpetuals/api
ASTER_API_URL: str = os.getenv("ASTER_API_URL", "")

# ---------------------------------------------------------------------------
# Symbols to trade (CCXT unified perpetual format)
# ---------------------------------------------------------------------------
SYMBOLS: list[str] = ["BTC/USDT:USDT", "ETH/USDT:USDT"]

# ---------------------------------------------------------------------------
# Timeframe & Polling
# ---------------------------------------------------------------------------
TIMEFRAME: str = "15m"           # K-line interval
OHLCV_LIMIT: int = 100           # Number of candles to fetch per request
POLL_INTERVAL_SEC: int = 60      # Seconds between each main-loop iteration

# ---------------------------------------------------------------------------
# Leverage & Margin
# ---------------------------------------------------------------------------
LEVERAGE: int = 5                 # Fixed leverage multiplier
MARGIN_TYPE: str = "ISOLATED"     # Isolated margin mode

# ---------------------------------------------------------------------------
# Technical Indicator Parameters
# ---------------------------------------------------------------------------
EMA_SHORT_PERIOD: int = 9        # Fast EMA period
EMA_LONG_PERIOD: int = 21        # Slow EMA period
RSI_PERIOD: int = 14             # RSI look-back period

# RSI filters to avoid false signals
RSI_LONG_MAX: float = 60.0       # Only enter long if RSI < this (not overbought)
RSI_SHORT_MIN: float = 40.0      # Only enter short if RSI > this (not oversold)

# ---------------------------------------------------------------------------
# Risk Management
# ---------------------------------------------------------------------------
RISK_PER_TRADE_PCT: float = 1.0  # Risk 1% of account balance per trade
STOP_LOSS_PCT: float = 1.5       # Stop-loss distance from entry (%)
TAKE_PROFIT_PCT: float = 3.0     # Take-profit distance from entry (%)

# ---------------------------------------------------------------------------
# OpenClaw Supervisor — automatic safety net
# ---------------------------------------------------------------------------
MAX_CONSECUTIVE_LOSSES: int = 3        # Pause after N consecutive losses
MAX_TOTAL_LOSS_PCT: float = 5.0        # Pause if cumulative loss > this % of
                                       # starting balance
# ---------------------------------------------------------------------------
# Paper Trading — simulated balance
# ---------------------------------------------------------------------------
PAPER_INITIAL_BALANCE: float = 10_000.0  # Starting USDT for paper trading

# ---------------------------------------------------------------------------
# Retry / Rate-limit Settings
# ---------------------------------------------------------------------------
MAX_RETRIES: int = 5
RETRY_DELAY_BASE_SEC: float = 2.0  # Exponential back-off base (2, 4, 8 …)
