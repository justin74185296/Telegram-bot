"""
Technical indicator calculations — pure pandas, no external TA library.

Supports: Bollinger Bands, ATR, Volume filter, RSI, EMA.
"""

from __future__ import annotations

import logging

import pandas as pd

from aster_perpetuals_bot.config import (
    ATR_PERIOD,
    ATR_THRESHOLD_PCT,
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
# Core implementations
# ------------------------------------------------------------------

def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()

def _sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()

def _rsi(series: pd.Series, period: int) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def _bollinger_bands(series: pd.Series, period: int, std_dev: float):
    middle = _sma(series, period)
    std = series.rolling(window=period).std()
    return middle + std * std_dev, middle, middle - std * std_dev

def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    """Average True Range."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


# ------------------------------------------------------------------
# Public: add all indicators
# ------------------------------------------------------------------

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add BB, ATR, volume filter, RSI, EMA columns in-place."""
    if "close" not in df.columns:
        raise ValueError("DataFrame must contain a 'close' column")

    # Bollinger Bands
    df["bb_upper"], df["bb_middle"], df["bb_lower"] = _bollinger_bands(
        df["close"], BB_PERIOD, BB_STD_DEV
    )

    # ATR
    df["atr"] = _atr(df["high"], df["low"], df["close"], ATR_PERIOD)
    df["atr_avg"] = _sma(df["atr"], ATR_PERIOD)
    atr_threshold = df["atr_avg"] * (1 + ATR_THRESHOLD_PCT / 100.0)
    df["atr_above_threshold"] = df["atr"] > atr_threshold

    # Volume filter
    df["vol_avg"] = _sma(df["volume"], VOLUME_AVG_PERIOD)
    df["vol_above_threshold"] = df["volume"] > df["vol_avg"] * (1 + VOLUME_THRESHOLD_PCT / 100.0)

    # RSI
    df["rsi"] = _rsi(df["close"], RSI_PERIOD)

    # EMA (backward compat)
    df["ema_short"] = _ema(df["close"], EMA_SHORT_PERIOD)
    df["ema_long"] = _ema(df["close"], EMA_LONG_PERIOD)

    logger.debug(
        "Indicators — BB[%.2f/%.2f/%.2f] ATR=%.4f(avg=%.4f,ok=%s) RSI=%.2f Vol_ok=%s",
        df["bb_upper"].iloc[-1] if pd.notna(df["bb_upper"].iloc[-1]) else 0,
        df["bb_middle"].iloc[-1] if pd.notna(df["bb_middle"].iloc[-1]) else 0,
        df["bb_lower"].iloc[-1] if pd.notna(df["bb_lower"].iloc[-1]) else 0,
        df["atr"].iloc[-1] if pd.notna(df["atr"].iloc[-1]) else 0,
        df["atr_avg"].iloc[-1] if pd.notna(df["atr_avg"].iloc[-1]) else 0,
        df["atr_above_threshold"].iloc[-1] if len(df) > 0 else False,
        df["rsi"].iloc[-1] if pd.notna(df["rsi"].iloc[-1]) else 0,
        df["vol_above_threshold"].iloc[-1] if len(df) > 0 else False,
    )
    return df


# ------------------------------------------------------------------
# Signal detection helpers
# ------------------------------------------------------------------

def detect_bollinger_signals(df: pd.DataFrame) -> tuple[bool, bool]:
    """Return (long_signal, short_signal) based on BB band breach."""
    if len(df) < 1:
        return False, False
    curr = df.iloc[-1]
    for col in ("bb_upper", "bb_lower", "close"):
        if pd.isna(curr.get(col)):
            return False, False
    price, upper, lower = curr["close"], curr["bb_upper"], curr["bb_lower"]
    long_signal = price < lower
    short_signal = price > upper
    if long_signal:
        logger.info("BB long: price %.2f < lower %.2f", price, lower)
    if short_signal:
        logger.info("BB short: price %.2f > upper %.2f", price, upper)
    return long_signal, short_signal


def is_volume_confirmed(df: pd.DataFrame) -> bool:
    if len(df) < 1 or "vol_above_threshold" not in df.columns:
        return False
    val = df["vol_above_threshold"].iloc[-1]
    return bool(val) if pd.notna(val) else False


def is_atr_sufficient(df: pd.DataFrame) -> bool:
    """Check if volatility (ATR) is above average threshold."""
    if len(df) < 1 or "atr_above_threshold" not in df.columns:
        return False
    val = df["atr_above_threshold"].iloc[-1]
    return bool(val) if pd.notna(val) else False


def get_current_atr(df: pd.DataFrame) -> float | None:
    if "atr" not in df.columns or len(df) == 0:
        return None
    val = df["atr"].iloc[-1]
    return float(val) if pd.notna(val) else None


def get_current_rsi(df: pd.DataFrame) -> float | None:
    if "rsi" not in df.columns or len(df) == 0:
        return None
    val = df["rsi"].iloc[-1]
    return float(val) if pd.notna(val) else None


def get_bollinger_values(df: pd.DataFrame) -> tuple[float, float, float] | None:
    if len(df) < 1:
        return None
    curr = df.iloc[-1]
    for col in ("bb_upper", "bb_middle", "bb_lower"):
        if pd.isna(curr.get(col)):
            return None
    return float(curr["bb_upper"]), float(curr["bb_middle"]), float(curr["bb_lower"])


def detect_ema_crossover(df: pd.DataFrame) -> tuple[bool, bool]:
    if len(df) < 2:
        return False, False
    prev, curr = df.iloc[-2], df.iloc[-1]
    for col in ("ema_short", "ema_long"):
        if pd.isna(prev[col]) or pd.isna(curr[col]):
            return False, False
    pd_diff = prev["ema_short"] - prev["ema_long"]
    cd_diff = curr["ema_short"] - curr["ema_long"]
    return (pd_diff <= 0 and cd_diff > 0), (pd_diff >= 0 and cd_diff < 0)
