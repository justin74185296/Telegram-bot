"""
Technical indicator calculations.

Uses **pure pandas** — no external TA library required.
This ensures compatibility with all Python versions (including 3.14+)
without needing numba or other C-compiled dependencies.
"""

from __future__ import annotations

import logging

import pandas as pd

from aster_perpetuals_bot.config import (
    EMA_LONG_PERIOD,
    EMA_SHORT_PERIOD,
    RSI_PERIOD,
)

logger = logging.getLogger("aster_bot.indicators")


# ------------------------------------------------------------------
# Pure-pandas indicator implementations
# ------------------------------------------------------------------

def _ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average using pandas ewm."""
    return series.ewm(span=period, adjust=False).mean()


def _rsi(series: pd.Series, period: int) -> pd.Series:
    """
    Calculate Relative Strength Index.

    RSI = 100 - (100 / (1 + RS))
    RS  = avg_gain / avg_loss  (exponential moving average)
    """
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


# ------------------------------------------------------------------
# Public helpers
# ------------------------------------------------------------------

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add EMA (short & long) and RSI columns to an OHLCV DataFrame **in-place**
    and return it for chaining convenience.

    Expected columns in *df*: ``open, high, low, close, volume``
    (standard CCXT naming).
    """
    if "close" not in df.columns:
        raise ValueError("DataFrame must contain a 'close' column")

    df["ema_short"] = _ema(df["close"], EMA_SHORT_PERIOD)
    df["ema_long"] = _ema(df["close"], EMA_LONG_PERIOD)
    df["rsi"] = _rsi(df["close"], RSI_PERIOD)

    logger.debug(
        "Indicators added — last row: ema_short=%.2f  ema_long=%.2f  rsi=%.2f",
        df["ema_short"].iloc[-1] if pd.notna(df["ema_short"].iloc[-1]) else 0,
        df["ema_long"].iloc[-1] if pd.notna(df["ema_long"].iloc[-1]) else 0,
        df["rsi"].iloc[-1] if pd.notna(df["rsi"].iloc[-1]) else 0,
    )
    return df


def detect_ema_crossover(df: pd.DataFrame) -> tuple[bool, bool]:
    """
    Detect EMA crossover on the **last two completed candles**.

    Returns
    -------
    (golden_cross, death_cross)
        golden_cross = True  →  EMA short crossed **above** EMA long
        death_cross  = True  →  EMA short crossed **below** EMA long
    """
    if len(df) < 2:
        return False, False

    prev = df.iloc[-2]
    curr = df.iloc[-1]

    # Guard against NaN (not enough history for the slow EMA)
    for col in ("ema_short", "ema_long"):
        if pd.isna(prev[col]) or pd.isna(curr[col]):
            return False, False

    prev_diff = prev["ema_short"] - prev["ema_long"]
    curr_diff = curr["ema_short"] - curr["ema_long"]

    golden_cross = prev_diff <= 0 and curr_diff > 0  # short crosses above long
    death_cross = prev_diff >= 0 and curr_diff < 0   # short crosses below long

    if golden_cross:
        logger.info("EMA golden cross detected (bullish)")
    if death_cross:
        logger.info("EMA death cross detected (bearish)")

    return golden_cross, death_cross


def get_current_rsi(df: pd.DataFrame) -> float | None:
    """Return the RSI value of the latest candle, or None if unavailable."""
    if "rsi" not in df.columns or len(df) == 0:
        return None
    val = df["rsi"].iloc[-1]
    return float(val) if pd.notna(val) else None
