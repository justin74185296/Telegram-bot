"""
Exchange interface — thin wrapper around CCXT for Aster / Binance Futures.

Aster Pro API is **Binance-futures compatible**, so we use
``ccxt.binance`` with ``defaultType = 'future'``.

If Aster publishes a dedicated base URL (e.g. https://pro-api.asterdex.com),
set the ``ASTER_API_URL`` environment variable and we will override the
endpoint accordingly.

Reference: https://docs.asterdex.com/product/aster-perpetuals/api
"""

from __future__ import annotations

import logging
import time
from typing import Any

import ccxt
import pandas as pd

from aster_perpetuals_bot.config import (
    API_KEY,
    API_SECRET,
    ASTER_API_URL,
    IS_PAPER_TRADING,
    LEVERAGE,
    MARGIN_TYPE,
    MAX_RETRIES,
    OHLCV_LIMIT,
    RETRY_DELAY_BASE_SEC,
    TIMEFRAME,
)

logger = logging.getLogger("aster_bot.exchange")


# ======================================================================
# Exchange singleton
# ======================================================================

_exchange_instance: ccxt.binance | None = None


def get_exchange() -> ccxt.binance:
    """
    Return (and lazily create) a ccxt.binance exchange instance configured
    for **Binance-compatible futures** trading on Aster DEX.
    """
    global _exchange_instance
    if _exchange_instance is not None:
        return _exchange_instance

    options: dict[str, Any] = {
        "defaultType": "future",       # perpetual futures
        "adjustForTimeDifference": True,
    }

    exchange = ccxt.binance(
        {
            "apiKey": API_KEY,
            "secret": API_SECRET,
            "enableRateLimit": True,     # built-in ccxt rate limiter
            "options": options,
        }
    )

    # ---- Override base URL if Aster exposes its own endpoint ----
    # Aster Pro API mirrors Binance futures REST format.
    # Set ASTER_API_URL to e.g. "https://pro-api.asterdex.com" if needed.
    if ASTER_API_URL:
        # ccxt stores futures URLs under exchange.urls['api']['fapiPublic'] etc.
        # The simplest override is to replace the hostname in all fapi* urls.
        for key in list(exchange.urls.get("api", {}).keys()):
            if key.startswith("fapi"):
                original = exchange.urls["api"][key]
                # Replace Binance hostname with Aster hostname
                exchange.urls["api"][key] = original.replace(
                    "https://fapi.binance.com", ASTER_API_URL
                )
        logger.info("Aster custom API URL applied: %s", ASTER_API_URL)

    # Paper-trading: if sandbox mode available, enable it
    if IS_PAPER_TRADING:
        if exchange.urls.get("test"):
            exchange.set_sandbox_mode(True)
            logger.info("CCXT sandbox mode enabled for paper trading")
        else:
            logger.info(
                "No sandbox URL; paper-trading logic handled in-app"
            )

    _exchange_instance = exchange
    logger.info("Exchange instance created (type=future)")
    return exchange


# ======================================================================
# Retry decorator
# ======================================================================

def _retry(func):
    """Decorator: retry on transient ccxt errors with exponential back-off."""

    def wrapper(*args, **kwargs):
        last_exc: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except (
                ccxt.NetworkError,
                ccxt.ExchangeNotAvailable,
                ccxt.RequestTimeout,
                ccxt.RateLimitExceeded,
            ) as exc:
                wait = RETRY_DELAY_BASE_SEC * (2 ** (attempt - 1))
                logger.warning(
                    "%s attempt %d/%d failed (%s). Retrying in %.1fs …",
                    func.__name__,
                    attempt,
                    MAX_RETRIES,
                    exc,
                    wait,
                )
                last_exc = exc
                time.sleep(wait)
            except ccxt.BaseError:
                # Non-transient exchange error — don't retry
                raise
        # All retries exhausted
        raise last_exc  # type: ignore[misc]

    wrapper.__name__ = func.__name__
    return wrapper


# ======================================================================
# Market Data
# ======================================================================

@_retry
def fetch_ohlcv(symbol: str) -> pd.DataFrame:
    """
    Fetch the latest OHLCV candles and return a pandas DataFrame.

    Columns: ``timestamp, open, high, low, close, volume``
    """
    exchange = get_exchange()
    raw = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=OHLCV_LIMIT)
    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df.set_index("timestamp", inplace=True)
    logger.debug("Fetched %d candles for %s", len(df), symbol)
    return df


# ======================================================================
# Account & Position Helpers
# ======================================================================

@_retry
def fetch_balance() -> dict[str, Any]:
    """Return the full balance dict from the exchange."""
    exchange = get_exchange()
    return exchange.fetch_balance()


def get_usdt_balance() -> float:
    """Return free USDT balance available for new orders."""
    bal = fetch_balance()
    free = float(bal.get("USDT", {}).get("free", 0.0))
    logger.debug("USDT free balance: %.4f", free)
    return free


@_retry
def fetch_positions(symbol: str) -> list[dict[str, Any]]:
    """
    Return open positions for *symbol*.

    Each element follows the CCXT unified position structure.
    """
    exchange = get_exchange()
    positions = exchange.fetch_positions([symbol])
    # Filter out zero-size "ghost" positions
    return [p for p in positions if float(p.get("contracts", 0)) != 0]


def get_open_position(symbol: str) -> dict[str, Any] | None:
    """
    Return the first non-zero position for *symbol*, or ``None``.
    """
    positions = fetch_positions(symbol)
    if positions:
        pos = positions[0]
        logger.debug(
            "Open position on %s: side=%s  size=%.6f  entryPrice=%.2f",
            symbol,
            pos.get("side"),
            float(pos.get("contracts", 0)),
            float(pos.get("entryPrice", 0)),
        )
        return pos
    return None


# ======================================================================
# Leverage & Margin Configuration
# ======================================================================

@_retry
def set_leverage_and_margin(symbol: str) -> None:
    """
    Ensure the symbol is configured with the correct margin type and
    leverage **before** opening a position.

    Must be called before every new trade.
    """
    exchange = get_exchange()

    # --- Set margin type (ISOLATED) ---
    try:
        exchange.set_margin_mode(MARGIN_TYPE.lower(), symbol)
        logger.info("Margin type set to %s for %s", MARGIN_TYPE, symbol)
    except ccxt.BaseError as exc:
        # "No need to change margin type" is common if already set
        if "No need to change" in str(exc) or "already" in str(exc).lower():
            logger.debug("Margin type already %s for %s", MARGIN_TYPE, symbol)
        else:
            raise

    # --- Set leverage ---
    exchange.set_leverage(LEVERAGE, symbol)
    logger.info("Leverage set to %dx for %s", LEVERAGE, symbol)


# ======================================================================
# Order Execution
# ======================================================================

@_retry
def create_market_order(
    symbol: str,
    side: str,
    amount: float,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Place a market order.

    Parameters
    ----------
    symbol : str  e.g. "BTC/USDT:USDT"
    side   : str  "buy" or "sell"
    amount : float  quantity in base asset
    params : dict   extra exchange-specific params (e.g. reduceOnly)
    """
    exchange = get_exchange()
    params = params or {}
    order = exchange.create_order(symbol, "market", side, amount, None, params)
    logger.info(
        "Market %s order placed: %s  qty=%.6f  id=%s",
        side.upper(),
        symbol,
        amount,
        order.get("id"),
    )
    return order


@_retry
def create_stop_loss_order(
    symbol: str,
    side: str,
    amount: float,
    stop_price: float,
) -> dict[str, Any]:
    """
    Place a stop-market (stop-loss) order.

    *side* should be the **closing** side (e.g. "sell" to close a long).
    """
    exchange = get_exchange()
    params = {
        "stopPrice": stop_price,
        "reduceOnly": True,
        "type": "STOP_MARKET",
    }
    order = exchange.create_order(
        symbol, "STOP_MARKET", side, amount, None, params
    )
    logger.info(
        "Stop-loss %s @ %.2f placed for %s  qty=%.6f  id=%s",
        side.upper(),
        stop_price,
        symbol,
        amount,
        order.get("id"),
    )
    return order


@_retry
def create_take_profit_order(
    symbol: str,
    side: str,
    amount: float,
    stop_price: float,
) -> dict[str, Any]:
    """
    Place a take-profit-market order.

    *side* should be the **closing** side.
    """
    exchange = get_exchange()
    params = {
        "stopPrice": stop_price,
        "reduceOnly": True,
        "type": "TAKE_PROFIT_MARKET",
    }
    order = exchange.create_order(
        symbol, "TAKE_PROFIT_MARKET", side, amount, None, params
    )
    logger.info(
        "Take-profit %s @ %.2f placed for %s  qty=%.6f  id=%s",
        side.upper(),
        stop_price,
        symbol,
        amount,
        order.get("id"),
    )
    return order


@_retry
def create_trailing_stop_order(
    symbol: str,
    side: str,
    amount: float,
    callback_rate: float,
    activation_price: float | None = None,
) -> dict[str, Any]:
    """
    Place a TRAILING_STOP_MARKET order on Binance futures.

    Parameters
    ----------
    symbol           : e.g. "BTC/USDT:USDT"
    side             : "buy" or "sell" (closing side)
    amount           : quantity in base asset
    callback_rate    : trailing callback percentage (e.g. 0.3 for 0.3%)
    activation_price : price at which trailing begins (optional)

    Debug notes
    -----------
    Binance requires ``callbackRate`` as a float 0.1–5.0 (percent).
    ``activationPrice`` is optional; if omitted, trailing starts immediately.
    The order type must be ``TRAILING_STOP_MARKET`` and ``reduceOnly=True``.

    If this call fails, the caller should fall back to a fixed SL/TP.
    """
    exchange = get_exchange()

    # --- Build params ---
    params: dict[str, Any] = {
        "reduceOnly": True,
        "type": "TRAILING_STOP_MARKET",
        "callbackRate": callback_rate,  # e.g. 0.3
    }
    if activation_price is not None:
        params["activationPrice"] = activation_price

    # --- Debug logging: show exactly what we're sending ---
    logger.info(
        "[DEBUG] Trailing stop API call → symbol=%s  side=%s  amount=%.6f  "
        "callbackRate=%.2f%%  activationPrice=%s  params=%s",
        symbol, side, amount, callback_rate,
        activation_price, params,
    )

    try:
        order = exchange.create_order(
            symbol, "TRAILING_STOP_MARKET", side, amount, None, params
        )
        logger.info(
            "[DEBUG] Trailing stop order SUCCESS → id=%s  status=%s  "
            "symbol=%s  side=%s  amount=%.6f  callbackRate=%.2f%%",
            order.get("id"), order.get("status"),
            symbol, side, amount, callback_rate,
        )
        return order
    except Exception as exc:
        logger.error(
            "[DEBUG] Trailing stop order FAILED → symbol=%s  side=%s  "
            "amount=%.6f  callbackRate=%.2f%%  activationPrice=%s  "
            "error_type=%s  error=%s",
            symbol, side, amount, callback_rate, activation_price,
            type(exc).__name__, exc,
        )
        raise


@_retry
def cancel_all_orders(symbol: str) -> None:
    """Cancel every open order for *symbol*."""
    exchange = get_exchange()
    exchange.cancel_all_orders(symbol)
    logger.info("All open orders cancelled for %s", symbol)


@_retry
def close_position(symbol: str, position: dict[str, Any]) -> dict[str, Any]:
    """
    Market-close an existing position.

    Determines the closing side automatically from the position dict.
    """
    contracts = abs(float(position.get("contracts", 0)))
    pos_side = str(position.get("side", "")).lower()
    close_side = "sell" if pos_side == "long" else "buy"

    cancel_all_orders(symbol)
    order = create_market_order(
        symbol, close_side, contracts, {"reduceOnly": True}
    )
    logger.info("Position closed on %s via market %s", symbol, close_side)
    return order


@_retry
def fetch_ticker(symbol: str) -> dict[str, Any]:
    """Return the latest ticker for *symbol* (includes last price, bid, ask)."""
    exchange = get_exchange()
    return exchange.fetch_ticker(symbol)


def get_last_price(symbol: str) -> float:
    """Convenience: return the last traded price for *symbol*."""
    ticker = fetch_ticker(symbol)
    return float(ticker["last"])
