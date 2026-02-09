"""
Trading strategy — signal generation & trade execution logic.

Strategy Overview
-----------------
* Enter **long** when EMA9 crosses above EMA21 AND RSI < 60.
* Enter **short** when EMA9 crosses below EMA21 AND RSI > 40.
* Exit on a reverse EMA crossover **or** when SL/TP is hit (exchange-side).
* Only one position per symbol at a time (no hedging / no pyramiding).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Literal

import pandas as pd

from aster_perpetuals_bot.config import (
    RSI_LONG_MAX,
    RSI_SHORT_MIN,
)
from aster_perpetuals_bot.indicators import (
    add_indicators,
    detect_ema_crossover,
    get_current_rsi,
)
from aster_perpetuals_bot.exchange import (
    cancel_all_orders,
    close_position,
    create_market_order,
    create_stop_loss_order,
    create_take_profit_order,
    get_last_price,
    get_open_position,
    get_usdt_balance,
    set_leverage_and_margin,
)
from aster_perpetuals_bot.risk_manager import (
    OpenClawMonitor,
    TradeRecord,
    calculate_position_size,
    calculate_sl_tp,
)

logger = logging.getLogger("aster_bot.strategy")


# ======================================================================
# Signal Detection
# ======================================================================

class Signal:
    """Lightweight value object describing a trading signal."""

    NONE = "none"
    LONG = "long"
    SHORT = "short"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"

    def __init__(self, action: str, reason: str = "") -> None:
        self.action = action
        self.reason = reason

    def __repr__(self) -> str:
        return f"Signal({self.action}, reason={self.reason!r})"

    @property
    def is_entry(self) -> bool:
        return self.action in (self.LONG, self.SHORT)

    @property
    def is_exit(self) -> bool:
        return self.action in (self.CLOSE_LONG, self.CLOSE_SHORT)


def generate_signal(
    df: pd.DataFrame,
    current_position_side: str | None,
) -> Signal:
    """
    Evaluate the latest candle data and return a Signal.

    Parameters
    ----------
    df : DataFrame with indicator columns already computed.
    current_position_side : "long", "short", or None.
    """
    # Compute indicators (idempotent — safe to call even if already added)
    df = add_indicators(df)

    golden_cross, death_cross = detect_ema_crossover(df)
    rsi = get_current_rsi(df)

    if rsi is None:
        logger.warning("RSI unavailable — skipping signal generation")
        return Signal(Signal.NONE, "rsi_unavailable")

    logger.info("Signal eval: golden=%s  death=%s  RSI=%.2f  pos=%s",
                golden_cross, death_cross, rsi, current_position_side)

    # ----- Exit signals (reverse crossover while holding) ----
    if current_position_side == "long" and death_cross:
        return Signal(Signal.CLOSE_LONG, f"death_cross (RSI={rsi:.1f})")

    if current_position_side == "short" and golden_cross:
        return Signal(Signal.CLOSE_SHORT, f"golden_cross (RSI={rsi:.1f})")

    # ----- Entry signals (only if flat) ----
    if current_position_side is None:
        if golden_cross and rsi < RSI_LONG_MAX:
            return Signal(Signal.LONG, f"golden_cross & RSI={rsi:.1f}<{RSI_LONG_MAX}")

        if death_cross and rsi > RSI_SHORT_MIN:
            return Signal(Signal.SHORT, f"death_cross & RSI={rsi:.1f}>{RSI_SHORT_MIN}")

    return Signal(Signal.NONE, "no_signal")


# ======================================================================
# Trade Execution
# ======================================================================

def execute_signal(
    signal: Signal,
    symbol: str,
    monitor: OpenClawMonitor,
    *,
    paper_balance: float | None = None,
) -> float | None:
    """
    Execute the given signal on the exchange.

    Returns
    -------
    Updated paper_balance (if paper mode), else None.
    """
    if signal.action == Signal.NONE:
        return paper_balance

    # ------------------------------------------------------------------
    # EXIT logic
    # ------------------------------------------------------------------
    if signal.is_exit:
        return _handle_exit(signal, symbol, monitor, paper_balance=paper_balance)

    # ------------------------------------------------------------------
    # ENTRY logic
    # ------------------------------------------------------------------
    if signal.is_entry:
        return _handle_entry(signal, symbol, monitor, paper_balance=paper_balance)

    return paper_balance


# ------------------------------------------------------------------
# Internal: entry
# ------------------------------------------------------------------

def _handle_entry(
    signal: Signal,
    symbol: str,
    monitor: OpenClawMonitor,
    *,
    paper_balance: float | None = None,
) -> float | None:
    """Open a new position (long or short)."""
    from aster_perpetuals_bot.config import IS_PAPER_TRADING

    side: Literal["long", "short"] = "long" if signal.action == Signal.LONG else "short"  # type: ignore[assignment]
    order_side = "buy" if side == "long" else "sell"

    # 1. Pre-trade: leverage & margin
    if not IS_PAPER_TRADING:
        set_leverage_and_margin(symbol)

    # 2. Determine balance & entry price
    if IS_PAPER_TRADING:
        balance = paper_balance or 0.0
    else:
        balance = get_usdt_balance()

    entry_price = get_last_price(symbol)

    # 3. Position size
    quantity = calculate_position_size(balance, entry_price, symbol)
    if quantity <= 0:
        logger.warning("Calculated quantity ≤ 0 — skipping trade")
        return paper_balance

    # 4. SL / TP
    sl_price, tp_price = calculate_sl_tp(entry_price, side)

    # 5. Place orders
    if IS_PAPER_TRADING:
        logger.info(
            "[PAPER] Opened %s %s @ %.2f  qty=%.6f  SL=%.2f  TP=%.2f",
            side.upper(),
            symbol,
            entry_price,
            quantity,
            sl_price,
            tp_price,
        )
        # Store position info on the monitor for later paper-close
        monitor._paper_position = {  # type: ignore[attr-defined]
            "symbol": symbol,
            "side": side,
            "entry_price": entry_price,
            "quantity": quantity,
            "sl": sl_price,
            "tp": tp_price,
            "opened_at": datetime.now(timezone.utc),
        }
    else:
        # Market entry
        create_market_order(symbol, order_side, quantity)
        # Protective SL order
        sl_side = "sell" if side == "long" else "buy"
        create_stop_loss_order(symbol, sl_side, quantity, sl_price)
        # TP order
        create_take_profit_order(symbol, sl_side, quantity, tp_price)

    logger.info("Signal executed: %s", signal)
    return paper_balance


# ------------------------------------------------------------------
# Internal: exit
# ------------------------------------------------------------------

def _handle_exit(
    signal: Signal,
    symbol: str,
    monitor: OpenClawMonitor,
    *,
    paper_balance: float | None = None,
) -> float | None:
    """Close an existing position on a reverse signal."""
    from aster_perpetuals_bot.config import IS_PAPER_TRADING

    if IS_PAPER_TRADING:
        paper_pos: dict[str, Any] | None = getattr(monitor, "_paper_position", None)
        if paper_pos is None:
            logger.warning("[PAPER] No paper position to close")
            return paper_balance

        exit_price = get_last_price(symbol)
        pnl = _calc_pnl(
            paper_pos["side"],
            paper_pos["entry_price"],
            exit_price,
            paper_pos["quantity"],
        )
        entry_notional = paper_pos["entry_price"] * paper_pos["quantity"]
        pnl_pct = (pnl / entry_notional * 100) if entry_notional else 0.0

        trade = TradeRecord(
            symbol=symbol,
            side=paper_pos["side"],
            entry_price=paper_pos["entry_price"],
            exit_price=exit_price,
            quantity=paper_pos["quantity"],
            pnl=pnl,
            pnl_pct=pnl_pct,
            opened_at=paper_pos["opened_at"],
        )
        monitor.record_trade(trade)
        monitor._paper_position = None  # type: ignore[attr-defined]

        new_balance = (paper_balance or 0.0) + pnl
        logger.info(
            "[PAPER] Closed %s %s @ %.2f  PnL=%.4f USDT  Balance=%.2f",
            paper_pos["side"].upper(),
            symbol,
            exit_price,
            pnl,
            new_balance,
        )
        return new_balance

    else:
        # Live: close the real position
        position = get_open_position(symbol)
        if position is None:
            logger.warning("No open position to close for %s", symbol)
            return paper_balance

        entry_price = float(position.get("entryPrice", 0))
        exit_price = get_last_price(symbol)
        contracts = abs(float(position.get("contracts", 0)))
        pos_side = str(position.get("side", "")).lower()

        close_position(symbol, position)

        pnl = _calc_pnl(pos_side, entry_price, exit_price, contracts)
        entry_notional = entry_price * contracts
        pnl_pct = (pnl / entry_notional * 100) if entry_notional else 0.0

        trade = TradeRecord(
            symbol=symbol,
            side=pos_side,  # type: ignore[arg-type]
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=contracts,
            pnl=pnl,
            pnl_pct=pnl_pct,
            opened_at=datetime.now(timezone.utc),  # best-effort
        )
        monitor.record_trade(trade)
        return paper_balance


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _calc_pnl(
    side: str,
    entry: float,
    exit_: float,
    qty: float,
) -> float:
    """Simple PnL calculation (before fees)."""
    if side == "long":
        return (exit_ - entry) * qty
    else:  # short
        return (entry - exit_) * qty


def get_position_side(symbol: str, monitor: OpenClawMonitor) -> str | None:
    """
    Return "long", "short", or None for the current position on *symbol*.

    Works for both paper and live modes.
    """
    from aster_perpetuals_bot.config import IS_PAPER_TRADING

    if IS_PAPER_TRADING:
        paper_pos = getattr(monitor, "_paper_position", None)
        if paper_pos and paper_pos.get("symbol") == symbol:
            return paper_pos["side"]
        return None

    pos = get_open_position(symbol)
    if pos:
        return str(pos.get("side", "")).lower() or None
    return None


def check_paper_sl_tp(symbol: str, monitor: OpenClawMonitor) -> Signal:
    """
    In paper mode, check if current price has breached the SL or TP of the
    simulated position. Returns a close signal if so.
    """
    paper_pos: dict[str, Any] | None = getattr(monitor, "_paper_position", None)
    if paper_pos is None or paper_pos.get("symbol") != symbol:
        return Signal(Signal.NONE)

    current_price = get_last_price(symbol)
    side = paper_pos["side"]
    sl = paper_pos["sl"]
    tp = paper_pos["tp"]

    if side == "long":
        if current_price <= sl:
            logger.info("[PAPER] SL hit for long %s @ %.2f (SL=%.2f)", symbol, current_price, sl)
            return Signal(Signal.CLOSE_LONG, "paper_sl_hit")
        if current_price >= tp:
            logger.info("[PAPER] TP hit for long %s @ %.2f (TP=%.2f)", symbol, current_price, tp)
            return Signal(Signal.CLOSE_LONG, "paper_tp_hit")
    else:  # short
        if current_price >= sl:
            logger.info("[PAPER] SL hit for short %s @ %.2f (SL=%.2f)", symbol, current_price, sl)
            return Signal(Signal.CLOSE_SHORT, "paper_sl_hit")
        if current_price <= tp:
            logger.info("[PAPER] TP hit for short %s @ %.2f (TP=%.2f)", symbol, current_price, tp)
            return Signal(Signal.CLOSE_SHORT, "paper_tp_hit")

    return Signal(Signal.NONE)
