"""
Technical indicator calculations.

Uses *pandas_ta* (pure-Python, no C dependencies) so the bot is easy to
install anywhere.  If you prefer TA-Lib, swap the implementations below
while keeping the same function signatures.
"""

from __future__ import annotations

import logging

import pandas as pd
import pandas_ta as ta  # noqa: F401  (imported for pd.DataFrame.ta accessor)

from aster_perpetuals_bot.config import (
    EMA_LONG_PERIOD,
    EMA_SHORT_PERIOD,
    RSI_PERIOD,
)

logger = logging.getLogger("aster_bot.indicators")


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

    df["ema_short"] = df.ta.ema(length=EMA_SHORT_PERIOD)
    df["ema_long"] = df.ta.ema(length=EMA_LONG_PERIOD)
    df["rsi"] = df.ta.rsi(length=RSI_PERIOD)

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
