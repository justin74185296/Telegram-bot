"""
Trading strategy — Bollinger Band bounce with volume + RSI filter.

Strategy (method = 'bollinger')
-------------------------------
* Enter **long** : price < BB lower  AND  volume > avg*130%  AND  RSI < 50
* Enter **short**: price > BB upper  AND  volume > avg*130%  AND  RSI > 50
* Exit: trailing stop callback  OR  max hold time (1 hour)  OR  price
  crosses back through BB middle band.
* Only one position per symbol at a time.

Trailing Stop
-------------
* Initial activation distance : 0.5 % from entry.
* Callback (follow) rate      : 0.3 %.
* Implemented via Binance TRAILING_STOP_MARKET order type on live,
  and simulated in paper mode.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Literal

import pandas as pd

from aster_perpetuals_bot.config import (
    MAX_HOLD_SECONDS,
    RSI_LONG_MAX,
    RSI_SHORT_MIN,
    SUPPORT_RESISTANCE_METHOD,
    TRAILING_STOP_CALLBACK_PCT,
    TRAILING_STOP_INITIAL_PCT,
)
from aster_perpetuals_bot.indicators import (
    add_indicators,
    detect_bollinger_signals,
    detect_ema_crossover,
    get_bollinger_values,
    get_current_rsi,
    is_volume_confirmed,
)
from aster_perpetuals_bot.exchange import (
    cancel_all_orders,
    close_position,
    create_market_order,
    create_trailing_stop_order,
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

    Dispatches to Bollinger or EMA strategy based on config.
    """
    df = add_indicators(df)

    if SUPPORT_RESISTANCE_METHOD == "bollinger":
        return _generate_bollinger_signal(df, current_position_side)
    else:
        return _generate_ema_signal(df, current_position_side)


# ------------------------------------------------------------------
# Bollinger Band strategy
# ------------------------------------------------------------------

def _generate_bollinger_signal(
    df: pd.DataFrame,
    current_position_side: str | None,
) -> Signal:
    """Bollinger Band bounce + volume + RSI filter."""
    bb_long, bb_short = detect_bollinger_signals(df)
    vol_ok = is_volume_confirmed(df)
    rsi = get_current_rsi(df)
    bb_vals = get_bollinger_values(df)

    if rsi is None or bb_vals is None:
        logger.warning("Indicators unavailable — skipping signal")
        return Signal(Signal.NONE, "indicators_unavailable")

    bb_upper, bb_middle, bb_lower = bb_vals
    price = float(df["close"].iloc[-1])

    logger.info(
        "BB signal eval: price=%.2f  BB[%.2f/%.2f/%.2f]  RSI=%.2f  "
        "vol_ok=%s  bb_long=%s  bb_short=%s  pos=%s",
        price, bb_upper, bb_middle, bb_lower, rsi,
        vol_ok, bb_long, bb_short, current_position_side,
    )

    # ----- Exit: price crossed back to middle band -----
    if current_position_side == "long" and price >= bb_middle:
        return Signal(Signal.CLOSE_LONG, f"price {price:.0f} >= BB_mid {bb_middle:.0f}")

    if current_position_side == "short" and price <= bb_middle:
        return Signal(Signal.CLOSE_SHORT, f"price {price:.0f} <= BB_mid {bb_middle:.0f}")

    # ----- Entry signals (only if flat) -----
    if current_position_side is None:
        # LONG: price < lower band + volume above avg + RSI < 50
        if bb_long and vol_ok and rsi < RSI_LONG_MAX:
            return Signal(
                Signal.LONG,
                f"price<BB_lower & vol>avg+30% & RSI={rsi:.1f}<{RSI_LONG_MAX}",
            )

        # SHORT: price > upper band + volume above avg + RSI > 50
        if bb_short and vol_ok and rsi > RSI_SHORT_MIN:
            return Signal(
                Signal.SHORT,
                f"price>BB_upper & vol>avg+30% & RSI={rsi:.1f}>{RSI_SHORT_MIN}",
            )

    return Signal(Signal.NONE, "no_signal")


# ------------------------------------------------------------------
# Legacy EMA strategy (fallback)
# ------------------------------------------------------------------

def _generate_ema_signal(
    df: pd.DataFrame,
    current_position_side: str | None,
) -> Signal:
    """EMA crossover + RSI filter (legacy)."""
    golden_cross, death_cross = detect_ema_crossover(df)
    rsi = get_current_rsi(df)

    if rsi is None:
        return Signal(Signal.NONE, "rsi_unavailable")

    if current_position_side == "long" and death_cross:
        return Signal(Signal.CLOSE_LONG, f"death_cross (RSI={rsi:.1f})")
    if current_position_side == "short" and golden_cross:
        return Signal(Signal.CLOSE_SHORT, f"golden_cross (RSI={rsi:.1f})")

    if current_position_side is None:
        if golden_cross and rsi < RSI_LONG_MAX:
            return Signal(Signal.LONG, f"golden_cross & RSI={rsi:.1f}")
        if death_cross and rsi > RSI_SHORT_MIN:
            return Signal(Signal.SHORT, f"death_cross & RSI={rsi:.1f}")

    return Signal(Signal.NONE, "no_signal")


# ======================================================================
# Max Hold Time Check
# ======================================================================

def check_max_hold_time(symbol: str, monitor: OpenClawMonitor) -> Signal:
    """
    Force-close a position if it has been held longer than MAX_HOLD_SECONDS.
    """
    from aster_perpetuals_bot.config import IS_PAPER_TRADING

    if IS_PAPER_TRADING:
        paper_pos = getattr(monitor, "_paper_position", None)
        if paper_pos and paper_pos.get("symbol") == symbol:
            opened_at = paper_pos["opened_at"]
            elapsed = (datetime.now(timezone.utc) - opened_at).total_seconds()
            if elapsed >= MAX_HOLD_SECONDS:
                side = paper_pos["side"]
                logger.warning(
                    "[MAX HOLD] Force-closing %s %s after %.0fs (limit=%ds)",
                    side, symbol, elapsed, MAX_HOLD_SECONDS,
                )
                close_action = Signal.CLOSE_LONG if side == "long" else Signal.CLOSE_SHORT
                return Signal(close_action, f"max_hold_{elapsed:.0f}s")
    return Signal(Signal.NONE)


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
    """Execute the given signal. Returns updated paper_balance or None."""
    if signal.action == Signal.NONE:
        return paper_balance

    if signal.is_exit:
        return _handle_exit(signal, symbol, monitor, paper_balance=paper_balance)

    if signal.is_entry:
        return _handle_entry(signal, symbol, monitor, paper_balance=paper_balance)

    return paper_balance


# ------------------------------------------------------------------
# Entry with trailing stop
# ------------------------------------------------------------------

def _handle_entry(
    signal: Signal,
    symbol: str,
    monitor: OpenClawMonitor,
    *,
    paper_balance: float | None = None,
) -> float | None:
    """Open a new position with trailing stop protection."""
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

    # 3. Position size (risk 0.3%)
    quantity = calculate_position_size(balance, entry_price, symbol)
    if quantity <= 0:
        logger.warning("Calculated quantity <= 0 — skipping trade")
        return paper_balance

    # 4. Compute fallback SL/TP
    sl_price, tp_price = calculate_sl_tp(entry_price, side)

    # 5. Place orders
    if IS_PAPER_TRADING:
        logger.info(
            "[PAPER] Opened %s %s @ %.2f  qty=%.6f  "
            "trailing_init=%.1f%%  trailing_cb=%.1f%%",
            side.upper(), symbol, entry_price, quantity,
            TRAILING_STOP_INITIAL_PCT, TRAILING_STOP_CALLBACK_PCT,
        )
        monitor._paper_position = {  # type: ignore[attr-defined]
            "symbol": symbol,
            "side": side,
            "entry_price": entry_price,
            "quantity": quantity,
            "sl": sl_price,
            "tp": tp_price,
            "trailing_high": entry_price if side == "long" else entry_price,
            "trailing_low": entry_price if side == "short" else entry_price,
            "opened_at": datetime.now(timezone.utc),
        }
    else:
        # Market entry
        create_market_order(symbol, order_side, quantity)

        # Place trailing stop order
        close_side = "sell" if side == "long" else "buy"
        try:
            create_trailing_stop_order(
                symbol=symbol,
                side=close_side,
                amount=quantity,
                callback_rate=TRAILING_STOP_CALLBACK_PCT,
                activation_price=_calc_trailing_activation(entry_price, side),
            )
        except Exception:
            logger.exception(
                "[DEBUG] Trailing stop API call FAILED for %s %s. "
                "Falling back to fixed SL/TP.",
                side, symbol,
            )
            # Fallback: place fixed SL and TP
            from aster_perpetuals_bot.exchange import (
                create_stop_loss_order,
                create_take_profit_order,
            )
            create_stop_loss_order(symbol, close_side, quantity, sl_price)
            create_take_profit_order(symbol, close_side, quantity, tp_price)

    logger.info("Signal executed: %s", signal)
    return paper_balance


def _calc_trailing_activation(entry_price: float, side: str) -> float:
    """
    Calculate the activation price for the trailing stop.

    The trailing stop activates after price moves TRAILING_STOP_INITIAL_PCT
    in our favour.
    """
    pct = TRAILING_STOP_INITIAL_PCT / 100.0
    if side == "long":
        return round(entry_price * (1 + pct), 2)
    else:
        return round(entry_price * (1 - pct), 2)


# ------------------------------------------------------------------
# Exit
# ------------------------------------------------------------------

def _handle_exit(
    signal: Signal,
    symbol: str,
    monitor: OpenClawMonitor,
    *,
    paper_balance: float | None = None,
) -> float | None:
    """Close an existing position."""
    from aster_perpetuals_bot.config import IS_PAPER_TRADING

    if IS_PAPER_TRADING:
        paper_pos: dict[str, Any] | None = getattr(monitor, "_paper_position", None)
        if paper_pos is None:
            logger.warning("[PAPER] No paper position to close")
            return paper_balance

        exit_price = get_last_price(symbol)
        pnl = _calc_pnl(paper_pos["side"], paper_pos["entry_price"], exit_price, paper_pos["quantity"])
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
            paper_pos["side"].upper(), symbol, exit_price, pnl, new_balance,
        )
        return new_balance
    else:
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
            opened_at=datetime.now(timezone.utc),
        )
        monitor.record_trade(trade)
        return paper_balance


# ------------------------------------------------------------------
# Paper trailing stop simulation
# ------------------------------------------------------------------

def check_paper_sl_tp(symbol: str, monitor: OpenClawMonitor) -> Signal:
    """
    In paper mode, simulate trailing stop behaviour.

    Tracks the best price seen since entry and triggers when the price
    pulls back by TRAILING_STOP_CALLBACK_PCT from the best.
    Also checks the fixed SL as a hard floor.
    """
    paper_pos: dict[str, Any] | None = getattr(monitor, "_paper_position", None)
    if paper_pos is None or paper_pos.get("symbol") != symbol:
        return Signal(Signal.NONE)

    current_price = get_last_price(symbol)
    side = paper_pos["side"]
    sl = paper_pos["sl"]
    callback_pct = TRAILING_STOP_CALLBACK_PCT / 100.0

    if side == "long":
        # Update trailing high
        best = max(paper_pos.get("trailing_high", paper_pos["entry_price"]), current_price)
        paper_pos["trailing_high"] = best

        # Trailing stop: price dropped callback_pct from best
        trailing_sl = best * (1 - callback_pct)
        if current_price <= trailing_sl and best > paper_pos["entry_price"]:
            logger.info(
                "[PAPER] Trailing stop hit for long %s: price=%.2f  "
                "best=%.2f  trailing_sl=%.2f",
                symbol, current_price, best, trailing_sl,
            )
            return Signal(Signal.CLOSE_LONG, f"trailing_stop (best={best:.0f})")

        # Hard SL floor
        if current_price <= sl:
            logger.info("[PAPER] Hard SL hit for long %s @ %.2f (SL=%.2f)", symbol, current_price, sl)
            return Signal(Signal.CLOSE_LONG, "hard_sl_hit")

    else:  # short
        # Update trailing low
        best = min(paper_pos.get("trailing_low", paper_pos["entry_price"]), current_price)
        paper_pos["trailing_low"] = best

        # Trailing stop: price rose callback_pct from best
        trailing_sl = best * (1 + callback_pct)
        if current_price >= trailing_sl and best < paper_pos["entry_price"]:
            logger.info(
                "[PAPER] Trailing stop hit for short %s: price=%.2f  "
                "best=%.2f  trailing_sl=%.2f",
                symbol, current_price, best, trailing_sl,
            )
            return Signal(Signal.CLOSE_SHORT, f"trailing_stop (best={best:.0f})")

        # Hard SL floor
        if current_price >= sl:
            logger.info("[PAPER] Hard SL hit for short %s @ %.2f (SL=%.2f)", symbol, current_price, sl)
            return Signal(Signal.CLOSE_SHORT, "hard_sl_hit")

    return Signal(Signal.NONE)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _calc_pnl(side: str, entry: float, exit_: float, qty: float) -> float:
    """Simple PnL calculation (before fees)."""
    if side == "long":
        return (exit_ - entry) * qty
    else:
        return (entry - exit_) * qty


def get_position_side(symbol: str, monitor: OpenClawMonitor) -> str | None:
    """Return "long", "short", or None for the current position."""
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
