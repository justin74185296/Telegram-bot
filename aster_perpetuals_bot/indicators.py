"""
Technical indicator calculations.

Uses **pure pandas** — no external TA library required.
Supports both Bollinger Bands (primary) and EMA crossover (legacy) strategies.
"""

from __future__ import annotations

import logging

import pandas as pd

from aster_perpetuals_bot.config import (
    BB_PERIOD,
    BB_STD_DEV,
    EMA_LONG_PERIOD,
    EMA_SHORT_PERIOD,
    RSI_PERIOD,
    VOLUME_AVG_PERIOD,
    VOLUME_THRESHOLD_PCT,
)

logger = logging.getLogger("aster_bot.indicators")


# ------------------------------------------------------------------
# Pure-pandas indicator implementations
# ------------------------------------------------------------------

def _ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average using pandas ewm."""
    return series.ewm(span=period, adjust=False).mean()


def _sma(series: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average."""
    return series.rolling(window=period).mean()


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


def _bollinger_bands(series: pd.Series, period: int, std_dev: float) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.

    Returns (bb_upper, bb_middle, bb_lower).
    """
    middle = _sma(series, period)
    std = series.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    return upper, middle, lower


# ------------------------------------------------------------------
# Public helpers
# ------------------------------------------------------------------

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all indicator columns to an OHLCV DataFrame **in-place**.

    Adds:
      - Bollinger Bands: bb_upper, bb_middle, bb_lower
      - Volume filter: vol_avg, vol_above_threshold (bool)
      - RSI
      - EMA short/long (kept for compatibility)
    """
    if "close" not in df.columns:
        raise ValueError("DataFrame must contain a 'close' column")

    # --- Bollinger Bands ---
    df["bb_upper"], df["bb_middle"], df["bb_lower"] = _bollinger_bands(
        df["close"], BB_PERIOD, BB_STD_DEV
    )

    # --- Volume Filter ---
    df["vol_avg"] = _sma(df["volume"], VOLUME_AVG_PERIOD)
    vol_threshold = df["vol_avg"] * (1 + VOLUME_THRESHOLD_PCT / 100.0)
    df["vol_above_threshold"] = df["volume"] > vol_threshold

    # --- RSI ---
    df["rsi"] = _rsi(df["close"], RSI_PERIOD)

    # --- EMA (kept for backward compatibility) ---
    df["ema_short"] = _ema(df["close"], EMA_SHORT_PERIOD)
    df["ema_long"] = _ema(df["close"], EMA_LONG_PERIOD)

    logger.debug(
        "Indicators — BB[%.2f / %.2f / %.2f]  RSI=%.2f  Vol_ok=%s  Price=%.2f",
        df["bb_upper"].iloc[-1] if pd.notna(df["bb_upper"].iloc[-1]) else 0,
        df["bb_middle"].iloc[-1] if pd.notna(df["bb_middle"].iloc[-1]) else 0,
        df["bb_lower"].iloc[-1] if pd.notna(df["bb_lower"].iloc[-1]) else 0,
        df["rsi"].iloc[-1] if pd.notna(df["rsi"].iloc[-1]) else 0,
        df["vol_above_threshold"].iloc[-1] if len(df) > 0 else False,
        df["close"].iloc[-1] if len(df) > 0 else 0,
    )
    return df


# ------------------------------------------------------------------
# Bollinger Band signal detection
# ------------------------------------------------------------------

def detect_bollinger_signals(df: pd.DataFrame) -> tuple[bool, bool]:
    """
    Detect Bollinger Band bounce signals on the latest candle.

    Returns
    -------
    (long_signal, short_signal)
        long_signal  = True  →  Price < lower band (support zone)
        short_signal = True  →  Price > upper band (resistance zone)
    """
    if len(df) < 1:
        return False, False

    curr = df.iloc[-1]

    for col in ("bb_upper", "bb_lower", "close"):
        if pd.isna(curr.get(col)):
            return False, False

    price = curr["close"]
    upper = curr["bb_upper"]
    lower = curr["bb_lower"]

    long_signal = price < lower
    short_signal = price > upper

    if long_signal:
        logger.info(
            "BB long signal: price %.2f < lower band %.2f (support zone)",
            price, lower,
        )
    if short_signal:
        logger.info(
            "BB short signal: price %.2f > upper band %.2f (resistance zone)",
            price, upper,
        )

    return long_signal, short_signal


def is_volume_confirmed(df: pd.DataFrame) -> bool:
    """Check if latest candle volume exceeds the average by the threshold."""
    if len(df) < 1 or "vol_above_threshold" not in df.columns:
        return False
    val = df["vol_above_threshold"].iloc[-1]
    return bool(val) if pd.notna(val) else False


def get_current_rsi(df: pd.DataFrame) -> float | None:
    """Return the RSI value of the latest candle, or None if unavailable."""
    if "rsi" not in df.columns or len(df) == 0:
        return None
    val = df["rsi"].iloc[-1]
    return float(val) if pd.notna(val) else None


def get_bollinger_values(df: pd.DataFrame) -> tuple[float, float, float] | None:
    """Return (upper, middle, lower) Bollinger Band values, or None."""
    if len(df) < 1:
        return None
    curr = df.iloc[-1]
    for col in ("bb_upper", "bb_middle", "bb_lower"):
        if pd.isna(curr.get(col)):
            return None
    return (
        float(curr["bb_upper"]),
        float(curr["bb_middle"]),
        float(curr["bb_lower"]),
    )


# ------------------------------------------------------------------
# Legacy EMA crossover detection (kept for alternative strategy)
# ------------------------------------------------------------------

def detect_ema_crossover(df: pd.DataFrame) -> tuple[bool, bool]:
    """
    Detect EMA crossover on the last two completed candles.

    Returns (golden_cross, death_cross).
    """
    if len(df) < 2:
        return False, False

    prev = df.iloc[-2]
    curr = df.iloc[-1]

    for col in ("ema_short", "ema_long"):
        if pd.isna(prev[col]) or pd.isna(curr[col]):
            return False, False

    prev_diff = prev["ema_short"] - prev["ema_long"]
    curr_diff = curr["ema_short"] - curr["ema_long"]

    golden_cross = prev_diff <= 0 and curr_diff > 0
    death_cross = prev_diff >= 0 and curr_diff < 0

    return golden_cross, death_cross
