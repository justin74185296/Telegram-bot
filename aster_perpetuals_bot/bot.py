"""
Main bot loop — orchestrates data fetching, signal generation, trade
execution, and the OpenClaw safety monitor.

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

from aster_perpetuals_bot.config import (
    IS_PAPER_TRADING,
    PAPER_INITIAL_BALANCE,
    POLL_INTERVAL_SEC,
    SYMBOLS,
)
from aster_perpetuals_bot.exchange import fetch_ohlcv, get_last_price
from aster_perpetuals_bot.indicators import add_indicators
from aster_perpetuals_bot.paper_engine import PaperAccount
from aster_perpetuals_bot.risk_manager import OpenClawMonitor
from aster_perpetuals_bot.strategy import (
    Signal,
    check_paper_sl_tp,
    execute_signal,
    generate_signal,
    get_position_side,
)

logger = logging.getLogger("aster_bot.main")

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

    # --- Initialise paper account (if paper mode) ---
    paper_account: PaperAccount | None = None
    if IS_PAPER_TRADING:
        paper_account = PaperAccount(PAPER_INITIAL_BALANCE)

    # --- One OpenClaw monitor shared across all symbols ---
    starting_balance = (
        paper_account.balance if paper_account else PAPER_INITIAL_BALANCE
    )
    monitor = OpenClawMonitor(starting_balance)

    cycle = 0

    while not _shutdown_requested:
        cycle += 1
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        logger.info("--- Cycle #%d  [%s] ---", cycle, ts)

        # Check if OpenClaw has paused the bot
        if not monitor.can_trade():
            logger.warning(
                "Bot is PAUSED by OpenClaw monitor. Sleeping %ds …",
                POLL_INTERVAL_SEC,
            )
            logger.info(monitor.summary())
            _sleep(POLL_INTERVAL_SEC)
            continue

        for symbol in SYMBOLS:
            if _shutdown_requested:
                break
            try:
                _process_symbol(symbol, monitor, paper_account)
            except Exception:
                logger.exception("Unhandled error processing %s", symbol)

        # Print periodic summary every 10 cycles
        if cycle % 10 == 0:
            logger.info(monitor.summary())
            if paper_account:
                logger.info("[Paper] %s", paper_account)

        _sleep(POLL_INTERVAL_SEC)

    # --- Shutdown ---
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

    # 4. In paper mode, check SL/TP first
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
            # Re-check position after close
            pos_side = get_position_side(symbol, monitor)

    # 5. Generate strategy signal
    sig = generate_signal(df, pos_side)
    logger.info("Signal for %s: %s", symbol, sig)

    if sig.action == Signal.NONE:
        return

    # 6. Execute signal
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
