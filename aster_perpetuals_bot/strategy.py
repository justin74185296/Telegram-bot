"""
Trading strategy — Bollinger Band bounce, limit orders, fee-aware.

Key changes:
* Limit orders instead of market orders (±0.1% offset).
* ATR filter: skip trades when volatility is below average.
* Fee-aware: simulate_pnl() deducts fees; skip trades that can't cover costs.
* Trailing stop + max hold time + BB middle exit all preserved.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Literal

import pandas as pd

from aster_perpetuals_bot.config import (
    FEE_RATE,
    MAX_HOLD_SECONDS,
    MIN_TAKE_PROFIT_PCT,
    RSI_LONG_MAX,
    RSI_SHORT_MIN,
    SLIPPAGE_ESTIMATE,
    SUPPORT_RESISTANCE_METHOD,
    TRAILING_STOP_CALLBACK_PCT,
    TRAILING_STOP_INITIAL_PCT,
)
from aster_perpetuals_bot.indicators import (
    add_indicators,
    detect_bollinger_signals,
    detect_ema_crossover,
    get_bollinger_values,
    get_current_atr,
    get_current_rsi,
    is_atr_sufficient,
    is_volume_confirmed,
)
from aster_perpetuals_bot.exchange import (
    cancel_all_orders,
    close_position,
    create_entry_order,
    create_exit_order,
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
    estimate_effective_cost,
    is_trade_profitable,
    simulate_pnl,
)

logger = logging.getLogger("aster_bot.strategy")


# ======================================================================
# Signal
# ======================================================================

class Signal:
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


# ======================================================================
# Signal Generation
# ======================================================================

def generate_signal(
    df: pd.DataFrame,
    current_position_side: str | None,
) -> Signal:
    df = add_indicators(df)
    if SUPPORT_RESISTANCE_METHOD == "bollinger":
        return _generate_bollinger_signal(df, current_position_side)
    return _generate_ema_signal(df, current_position_side)


def _generate_bollinger_signal(
    df: pd.DataFrame,
    current_position_side: str | None,
) -> Signal:
    """Bollinger Band bounce + volume + RSI + ATR filter + fee filter."""
    bb_long, bb_short = detect_bollinger_signals(df)
    vol_ok = is_volume_confirmed(df)
    atr_ok = is_atr_sufficient(df)
    rsi = get_current_rsi(df)
    atr = get_current_atr(df)
    bb_vals = get_bollinger_values(df)

    if rsi is None or bb_vals is None:
        return Signal(Signal.NONE, "indicators_unavailable")

    bb_upper, bb_middle, bb_lower = bb_vals
    price = float(df["close"].iloc[-1])

    logger.info(
        "Signal: price=%.2f BB[%.0f/%.0f/%.0f] RSI=%.1f ATR=%.2f "
        "vol=%s atr=%s pos=%s",
        price, bb_upper, bb_middle, bb_lower, rsi,
        atr or 0, vol_ok, atr_ok, current_position_side,
    )

    # --- Exit: price back to middle band ---
    if current_position_side == "long" and price >= bb_middle:
        return Signal(Signal.CLOSE_LONG, f"price>BB_mid")
    if current_position_side == "short" and price <= bb_middle:
        return Signal(Signal.CLOSE_SHORT, f"price<BB_mid")

    # --- Entry (only if flat) ---
    if current_position_side is None:
        # ATR gate: skip low-volatility
        if not atr_ok:
            if bb_long or bb_short:
                logger.info("[ATR FILTER] Signal suppressed — volatility too low")
            return Signal(Signal.NONE, "atr_too_low")

        # Fee-profitability gate
        if bb_long or bb_short:
            # Expected profit = distance to middle band / price
            if bb_long:
                expected_pct = (bb_middle - price) / price
            else:
                expected_pct = (price - bb_middle) / price

            if not is_trade_profitable(expected_pct):
                return Signal(Signal.NONE, "insufficient_profit_vs_fees")

        if bb_long and vol_ok and rsi < RSI_LONG_MAX:
            return Signal(Signal.LONG,
                          f"BB_lower+vol+RSI={rsi:.0f}+ATR_ok")
        if bb_short and vol_ok and rsi > RSI_SHORT_MIN:
            return Signal(Signal.SHORT,
                          f"BB_upper+vol+RSI={rsi:.0f}+ATR_ok")

    return Signal(Signal.NONE, "no_signal")


def _generate_ema_signal(df, current_position_side):
    golden, death = detect_ema_crossover(df)
    rsi = get_current_rsi(df)
    if rsi is None:
        return Signal(Signal.NONE, "rsi_unavailable")
    if current_position_side == "long" and death:
        return Signal(Signal.CLOSE_LONG, f"death_cross")
    if current_position_side == "short" and golden:
        return Signal(Signal.CLOSE_SHORT, f"golden_cross")
    if current_position_side is None:
        if golden and rsi < RSI_LONG_MAX:
            return Signal(Signal.LONG, f"golden+RSI={rsi:.0f}")
        if death and rsi > RSI_SHORT_MIN:
            return Signal(Signal.SHORT, f"death+RSI={rsi:.0f}")
    return Signal(Signal.NONE, "no_signal")


# ======================================================================
# Max Hold Time
# ======================================================================

def check_max_hold_time(symbol: str, monitor: OpenClawMonitor) -> Signal:
    from aster_perpetuals_bot.config import IS_PAPER_TRADING
    if IS_PAPER_TRADING:
        paper_pos = getattr(monitor, "_paper_position", None)
        if paper_pos and paper_pos.get("symbol") == symbol:
            elapsed = (datetime.now(timezone.utc) - paper_pos["opened_at"]).total_seconds()
            if elapsed >= MAX_HOLD_SECONDS:
                side = paper_pos["side"]
                logger.warning("[MAX HOLD] Force-close %s %s after %.0fs", side, symbol, elapsed)
                return Signal(
                    Signal.CLOSE_LONG if side == "long" else Signal.CLOSE_SHORT,
                    f"max_hold_{elapsed:.0f}s",
                )
    return Signal(Signal.NONE)


# ======================================================================
# Trade Execution (limit orders)
# ======================================================================

def execute_signal(
    signal: Signal,
    symbol: str,
    monitor: OpenClawMonitor,
    *,
    paper_balance: float | None = None,
) -> float | None:
    if signal.action == Signal.NONE:
        return paper_balance
    if signal.is_exit:
        return _handle_exit(signal, symbol, monitor, paper_balance=paper_balance)
    if signal.is_entry:
        return _handle_entry(signal, symbol, monitor, paper_balance=paper_balance)
    return paper_balance


def _handle_entry(
    signal: Signal,
    symbol: str,
    monitor: OpenClawMonitor,
    *,
    paper_balance: float | None = None,
) -> float | None:
    from aster_perpetuals_bot.config import IS_PAPER_TRADING, ORDER_TYPE

    side: Literal["long", "short"] = "long" if signal.action == Signal.LONG else "short"
    order_side = "buy" if side == "long" else "sell"

    if not IS_PAPER_TRADING:
        set_leverage_and_margin(symbol)

    balance = (paper_balance or 0.0) if IS_PAPER_TRADING else get_usdt_balance()
    entry_price = get_last_price(symbol)

    quantity = calculate_position_size(balance, entry_price, symbol)
    if quantity <= 0:
        return paper_balance

    sl_price, tp_price = calculate_sl_tp(entry_price, side)

    # Log fee estimate
    est_cost = estimate_effective_cost(entry_price, quantity)
    logger.info(
        "[FEE] Entry %s %s @ %.2f  qty=%.6f  est_cost=%.4f USDT  order_type=%s",
        side, symbol, entry_price, quantity, est_cost, ORDER_TYPE,
    )

    if IS_PAPER_TRADING:
        logger.info(
            "[PAPER] Opened %s %s @ %.2f  qty=%.6f  SL=%.2f  TP=%.2f  "
            "trailing=%.1f%%/%.1f%%  est_fees=%.4f",
            side.upper(), symbol, entry_price, quantity,
            sl_price, tp_price,
            TRAILING_STOP_INITIAL_PCT, TRAILING_STOP_CALLBACK_PCT,
            est_cost,
        )
        monitor._paper_position = {  # type: ignore[attr-defined]
            "symbol": symbol,
            "side": side,
            "entry_price": entry_price,
            "quantity": quantity,
            "sl": sl_price,
            "tp": tp_price,
            "trailing_high": entry_price,
            "trailing_low": entry_price,
            "opened_at": datetime.now(timezone.utc),
        }
    else:
        # Limit or market entry
        create_entry_order(symbol, order_side, quantity)

        # Trailing stop
        close_side = "sell" if side == "long" else "buy"
        try:
            create_trailing_stop_order(
                symbol=symbol, side=close_side, amount=quantity,
                callback_rate=TRAILING_STOP_CALLBACK_PCT,
                activation_price=_calc_trailing_activation(entry_price, side),
            )
        except Exception:
            logger.exception("[DEBUG] Trailing stop FAILED — fallback to fixed SL/TP")
            from aster_perpetuals_bot.exchange import (
                create_stop_loss_order, create_take_profit_order,
            )
            create_stop_loss_order(symbol, close_side, quantity, sl_price)
            create_take_profit_order(symbol, close_side, quantity, tp_price)

    return paper_balance


def _calc_trailing_activation(entry_price: float, side: str) -> float:
    pct = TRAILING_STOP_INITIAL_PCT / 100.0
    if side == "long":
        return round(entry_price * (1 + pct), 2)
    return round(entry_price * (1 - pct), 2)


def _handle_exit(
    signal: Signal,
    symbol: str,
    monitor: OpenClawMonitor,
    *,
    paper_balance: float | None = None,
) -> float | None:
    from aster_perpetuals_bot.config import IS_PAPER_TRADING

    if IS_PAPER_TRADING:
        paper_pos: dict[str, Any] | None = getattr(monitor, "_paper_position", None)
        if paper_pos is None:
            return paper_balance

        exit_price = get_last_price(symbol)
        gross = _calc_pnl(paper_pos["side"], paper_pos["entry_price"],
                          exit_price, paper_pos["quantity"])
        position_value = paper_pos["entry_price"] * paper_pos["quantity"]
        net_pnl, fees = simulate_pnl(gross, position_value)
        pnl_pct = (net_pnl / position_value * 100) if position_value else 0.0

        trade = TradeRecord(
            symbol=symbol, side=paper_pos["side"],
            entry_price=paper_pos["entry_price"], exit_price=exit_price,
            quantity=paper_pos["quantity"],
            pnl=net_pnl, pnl_pct=pnl_pct,
            gross_pnl=gross, fees=fees,
            opened_at=paper_pos["opened_at"],
        )
        monitor.record_trade(trade)
        monitor._paper_position = None  # type: ignore[attr-defined]

        new_balance = (paper_balance or 0.0) + net_pnl
        logger.info(
            "[PAPER] Closed %s %s @ %.2f  gross=%.4f  fees=%.4f  net=%.4f  bal=%.2f",
            paper_pos["side"].upper(), symbol, exit_price,
            gross, fees, net_pnl, new_balance,
        )
        return new_balance
    else:
        position = get_open_position(symbol)
        if position is None:
            return paper_balance

        entry_price = float(position.get("entryPrice", 0))
        exit_price = get_last_price(symbol)
        contracts = abs(float(position.get("contracts", 0)))
        pos_side = str(position.get("side", "")).lower()

        close_position(symbol, position)

        gross = _calc_pnl(pos_side, entry_price, exit_price, contracts)
        position_value = entry_price * contracts
        net_pnl, fees = simulate_pnl(gross, position_value)
        pnl_pct = (net_pnl / position_value * 100) if position_value else 0.0

        trade = TradeRecord(
            symbol=symbol, side=pos_side,  # type: ignore[arg-type]
            entry_price=entry_price, exit_price=exit_price,
            quantity=contracts,
            pnl=net_pnl, pnl_pct=pnl_pct,
            gross_pnl=gross, fees=fees,
            opened_at=datetime.now(timezone.utc),
        )
        monitor.record_trade(trade)
        return paper_balance


# ------------------------------------------------------------------
# Paper trailing stop
# ------------------------------------------------------------------

def check_paper_sl_tp(symbol: str, monitor: OpenClawMonitor) -> Signal:
    paper_pos: dict[str, Any] | None = getattr(monitor, "_paper_position", None)
    if paper_pos is None or paper_pos.get("symbol") != symbol:
        return Signal(Signal.NONE)

    current_price = get_last_price(symbol)
    side = paper_pos["side"]
    sl = paper_pos["sl"]
    cb = TRAILING_STOP_CALLBACK_PCT / 100.0

    if side == "long":
        best = max(paper_pos.get("trailing_high", paper_pos["entry_price"]), current_price)
        paper_pos["trailing_high"] = best
        trailing_sl = best * (1 - cb)
        if current_price <= trailing_sl and best > paper_pos["entry_price"]:
            return Signal(Signal.CLOSE_LONG, f"trailing_stop(best={best:.0f})")
        if current_price <= sl:
            return Signal(Signal.CLOSE_LONG, "hard_sl")
    else:
        best = min(paper_pos.get("trailing_low", paper_pos["entry_price"]), current_price)
        paper_pos["trailing_low"] = best
        trailing_sl = best * (1 + cb)
        if current_price >= trailing_sl and best < paper_pos["entry_price"]:
            return Signal(Signal.CLOSE_SHORT, f"trailing_stop(best={best:.0f})")
        if current_price >= sl:
            return Signal(Signal.CLOSE_SHORT, "hard_sl")

    return Signal(Signal.NONE)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _calc_pnl(side: str, entry: float, exit_: float, qty: float) -> float:
    return (exit_ - entry) * qty if side == "long" else (entry - exit_) * qty


def get_position_side(symbol: str, monitor: OpenClawMonitor) -> str | None:
    from aster_perpetuals_bot.config import IS_PAPER_TRADING
    if IS_PAPER_TRADING:
        pp = getattr(monitor, "_paper_position", None)
        if pp and pp.get("symbol") == symbol:
            return pp["side"]
        return None
    pos = get_open_position(symbol)
    return str(pos.get("side", "")).lower() or None if pos else None
