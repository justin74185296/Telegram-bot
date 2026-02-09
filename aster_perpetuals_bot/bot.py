"""
Main bot loop — orchestrates data fetching, signal generation, trade
execution, the OpenClaw safety monitor, and the live web dashboard.

Usage
-----
    python -m aster_perpetuals_bot.bot

Or:
    python bot.py          (when run from the package directory)
"""

from __future__ import annotations

import logging
import signal
import sys
import time
from datetime import datetime, timezone

import pandas as pd

from aster_perpetuals_bot.config import (
    DASHBOARD_HOST,
    DASHBOARD_PORT,
    IS_PAPER_TRADING,
    PAPER_INITIAL_BALANCE,
    POLL_INTERVAL_SEC,
    SYMBOLS,
    TRADING_MODE,
)
from aster_perpetuals_bot.exchange import fetch_ohlcv, get_last_price
from aster_perpetuals_bot.indicators import add_indicators
from aster_perpetuals_bot.paper_engine import PaperAccount
from aster_perpetuals_bot.risk_manager import OpenClawMonitor
from aster_perpetuals_bot.shared_state import (
    IndicatorSnapshot,
    PositionSnapshot,
    TradeSnapshot,
    bot_state,
)
from aster_perpetuals_bot.strategy import (
    Signal,
    check_paper_sl_tp,
    execute_signal,
    generate_signal,
    get_position_side,
)

logger = logging.getLogger("aster_bot.main")

# ======================================================================
# Custom logging handler → push to shared_state for the dashboard
# ======================================================================

class _DashboardLogHandler(logging.Handler):
    """Forward log records to the shared bot_state for live display."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            bot_state.add_log(msg)
        except Exception:
            pass


# Install the handler on the root 'aster_bot' logger
_dh = _DashboardLogHandler()
_dh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", "%H:%M:%S"))
logging.getLogger("aster_bot").addHandler(_dh)


# ======================================================================
# Graceful shutdown
# ======================================================================

_shutdown_requested = False


def _signal_handler(signum, frame):  # noqa: ANN001
    global _shutdown_requested
    logger.info("Shutdown signal received (sig=%s). Finishing current cycle …", signum)
    _shutdown_requested = True


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


# ======================================================================
# Main entry point
# ======================================================================

def main() -> None:
    """Run the trading bot."""
    logger.info("=" * 60)
    logger.info("  Aster Perpetuals Bot — starting up")
    logger.info("  Mode : %s", "PAPER" if IS_PAPER_TRADING else "LIVE")
    logger.info("  Symbols : %s", ", ".join(SYMBOLS))
    logger.info("  Poll interval : %ds", POLL_INTERVAL_SEC)
    logger.info("=" * 60)

    # --- Start web dashboard ---
    from aster_perpetuals_bot.dashboard import start_dashboard
    start_dashboard(host=DASHBOARD_HOST, port=DASHBOARD_PORT)

    # --- Initialise paper account (if paper mode) ---
    paper_account: PaperAccount | None = None
    if IS_PAPER_TRADING:
        paper_account = PaperAccount(PAPER_INITIAL_BALANCE)

    # --- One OpenClaw monitor shared across all symbols ---
    starting_balance = (
        paper_account.balance if paper_account else PAPER_INITIAL_BALANCE
    )
    monitor = OpenClawMonitor(starting_balance)

    # --- Push initial state to dashboard ---
    bot_state.trading_mode = TRADING_MODE
    bot_state.set_balance(starting_balance, initial=starting_balance)
    bot_state.set_status("running")

    cycle = 0

    while not _shutdown_requested:
        cycle += 1
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        logger.info("--- Cycle #%d  [%s] ---", cycle, ts)
        bot_state.update_cycle(cycle)

        # Sync OpenClaw state to dashboard
        _sync_openclaw(monitor)

        # Check if OpenClaw has paused the bot
        if not monitor.can_trade():
            bot_state.set_status("paused")
            logger.warning(
                "Bot is PAUSED by OpenClaw monitor. Sleeping %ds …",
                POLL_INTERVAL_SEC,
            )
            logger.info(monitor.summary())
            _sleep(POLL_INTERVAL_SEC)
            continue

        bot_state.set_status("running")

        for symbol in SYMBOLS:
            if _shutdown_requested:
                break
            try:
                _process_symbol(symbol, monitor, paper_account)
            except Exception:
                logger.exception("Unhandled error processing %s", symbol)

        # Update balance on dashboard
        if paper_account:
            bot_state.set_balance(paper_account.balance)

        # Print periodic summary every 10 cycles
        if cycle % 10 == 0:
            logger.info(monitor.summary())
            if paper_account:
                logger.info("[Paper] %s", paper_account)

        _sleep(POLL_INTERVAL_SEC)

    # --- Shutdown ---
    bot_state.set_status("stopped")
    logger.info("Bot shutting down gracefully.")
    logger.info(monitor.summary())
    if paper_account:
        logger.info("[Paper] Final state: %s", paper_account)


# ======================================================================
# Per-symbol processing
# ======================================================================

def _process_symbol(
    symbol: str,
    monitor: OpenClawMonitor,
    paper_account: PaperAccount | None,
) -> None:
    """Fetch data, compute indicators, generate & execute signals for one symbol."""

    # 1. Fetch OHLCV
    df = fetch_ohlcv(symbol)
    if df.empty:
        logger.warning("Empty OHLCV data for %s — skipping", symbol)
        return

    # 2. Add indicators
    df = add_indicators(df)

    # 3. Current position side
    pos_side = get_position_side(symbol, monitor)

    # 4. Push indicators to dashboard
    _sync_indicators(df, symbol, Signal(Signal.NONE))

    # 5. Push position to dashboard
    _sync_position(symbol, monitor)

    # 6. In paper mode, check SL/TP first
    if IS_PAPER_TRADING and pos_side is not None:
        sltp_signal = check_paper_sl_tp(symbol, monitor)
        if sltp_signal.action != Signal.NONE:
            logger.info("Paper SL/TP signal for %s: %s", symbol, sltp_signal)
            new_balance = execute_signal(
                sltp_signal,
                symbol,
                monitor,
                paper_balance=paper_account.balance if paper_account else None,
            )
            if paper_account and new_balance is not None:
                pnl_delta = new_balance - paper_account.balance
                paper_account.update(pnl_delta)
            # Sync trades after close
            _sync_trades(monitor)
            _sync_openclaw(monitor)
            _sync_position(symbol, monitor)
            if paper_account:
                bot_state.set_balance(paper_account.balance)
            # Re-check position after close
            pos_side = get_position_side(symbol, monitor)

    # 7. Generate strategy signal
    sig = generate_signal(df, pos_side)
    logger.info("Signal for %s: %s", symbol, sig)

    # Update indicator snapshot with latest signal
    _sync_indicators(df, symbol, sig)

    if sig.action == Signal.NONE:
        return

    # 8. Execute signal
    if not monitor.can_trade() and sig.is_entry:
        logger.warning("OpenClaw blocked entry signal for %s", symbol)
        return

    new_balance = execute_signal(
        sig,
        symbol,
        monitor,
        paper_balance=paper_account.balance if paper_account else None,
    )
    if paper_account and new_balance is not None and sig.is_exit:
        pnl_delta = new_balance - paper_account.balance
        paper_account.update(pnl_delta)

    # 9. Sync everything to dashboard after trade
    _sync_position(symbol, monitor)
    _sync_trades(monitor)
    _sync_openclaw(monitor)
    if paper_account:
        bot_state.set_balance(paper_account.balance)


# ======================================================================
# Dashboard sync helpers
# ======================================================================

def _sync_indicators(df: pd.DataFrame, symbol: str, sig: Signal) -> None:
    """Push latest indicator values to the shared state."""
    try:
        last = df.iloc[-1]
        snap = IndicatorSnapshot(
            symbol=symbol,
            ema_short=float(last.get("ema_short", 0)) if pd.notna(last.get("ema_short")) else 0.0,
            ema_long=float(last.get("ema_long", 0)) if pd.notna(last.get("ema_long")) else 0.0,
            rsi=float(last.get("rsi", 0)) if pd.notna(last.get("rsi")) else 0.0,
            last_price=float(last.get("close", 0)),
            last_signal=sig.action,
            signal_reason=sig.reason,
        )
        bot_state.set_indicators(snap)
    except Exception:
        logger.debug("Failed to sync indicators for %s", symbol, exc_info=True)


def _sync_position(symbol: str, monitor: OpenClawMonitor) -> None:
    """Push current position snapshot to shared state."""
    try:
        if IS_PAPER_TRADING:
            paper_pos = getattr(monitor, "_paper_position", None)
            if paper_pos and paper_pos.get("symbol") == symbol:
                # Calculate unrealised PnL
                try:
                    current_price = get_last_price(symbol)
                except Exception:
                    current_price = paper_pos["entry_price"]

                if paper_pos["side"] == "long":
                    upnl = (current_price - paper_pos["entry_price"]) * paper_pos["quantity"]
                else:
                    upnl = (paper_pos["entry_price"] - current_price) * paper_pos["quantity"]

                snap = PositionSnapshot(
                    symbol=symbol,
                    side=paper_pos["side"],
                    entry_price=paper_pos["entry_price"],
                    quantity=paper_pos["quantity"],
                    sl_price=paper_pos["sl"],
                    tp_price=paper_pos["tp"],
                    unrealised_pnl=upnl,
                    opened_at=paper_pos["opened_at"].isoformat()
                    if hasattr(paper_pos["opened_at"], "isoformat")
                    else str(paper_pos["opened_at"]),
                )
                bot_state.set_position(symbol, snap)
            else:
                bot_state.set_position(symbol, None)
        else:
            from aster_perpetuals_bot.exchange import get_open_position
            pos = get_open_position(symbol)
            if pos:
                entry = float(pos.get("entryPrice", 0))
                qty = abs(float(pos.get("contracts", 0)))
                side = str(pos.get("side", "")).lower()
                upnl = float(pos.get("unrealizedPnl", 0))
                snap = PositionSnapshot(
                    symbol=symbol,
                    side=side,
                    entry_price=entry,
                    quantity=qty,
                    sl_price=0.0,
                    tp_price=0.0,
                    unrealised_pnl=upnl,
                    opened_at="",
                )
                bot_state.set_position(symbol, snap)
            else:
                bot_state.set_position(symbol, None)
    except Exception:
        logger.debug("Failed to sync position for %s", symbol, exc_info=True)


def _sync_trades(monitor: OpenClawMonitor) -> None:
    """Push the full trade list from the monitor to the dashboard."""
    try:
        # Only push new trades (compare lengths)
        existing = len(bot_state.trades)
        monitor_trades = monitor.trades
        if len(monitor_trades) > existing:
            for t in monitor_trades[existing:]:
                snap = TradeSnapshot(
                    symbol=t.symbol,
                    side=t.side,
                    entry_price=t.entry_price,
                    exit_price=t.exit_price,
                    quantity=t.quantity,
                    pnl=t.pnl,
                    pnl_pct=t.pnl_pct,
                    opened_at=t.opened_at.isoformat() if hasattr(t.opened_at, "isoformat") else str(t.opened_at),
                    closed_at=t.closed_at.isoformat() if hasattr(t.closed_at, "isoformat") else str(t.closed_at),
                )
                bot_state.add_trade(snap)
    except Exception:
        logger.debug("Failed to sync trades", exc_info=True)


def _sync_openclaw(monitor: OpenClawMonitor) -> None:
    """Push OpenClaw stats to the dashboard."""
    try:
        wins = sum(1 for t in monitor.trades if t.pnl > 0)
        losses = sum(1 for t in monitor.trades if t.pnl < 0)
        bot_state.set_openclaw(
            total_pnl=monitor.total_pnl,
            consecutive_losses=monitor.consecutive_losses,
            is_paused=monitor.is_paused,
            wins=wins,
            losses=losses,
        )
    except Exception:
        logger.debug("Failed to sync openclaw", exc_info=True)


# ======================================================================
# Utility
# ======================================================================

def _sleep(seconds: int) -> None:
    """Interruptible sleep — check shutdown flag every second."""
    for _ in range(seconds):
        if _shutdown_requested:
            break
        time.sleep(1)


# ======================================================================
# Script entry point
# ======================================================================

if __name__ == "__main__":
    main()
