"""
Risk management & OpenClaw supervisor.

Responsibilities
----------------
* Calculate position size based on account balance and risk-per-trade %.
* Compute stop-loss and take-profit prices.
* Track trade history and PnL (the "OpenClaw monitor").
* Auto-pause the bot when consecutive losses or cumulative loss thresholds
  are breached.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from aster_perpetuals_bot.config import (
    LEVERAGE,
    MAX_CONSECUTIVE_LOSSES,
    MAX_TOTAL_LOSS_PCT,
    RISK_PER_TRADE_PCT,
    STOP_LOSS_PCT,
    TAKE_PROFIT_PCT,
)

logger = logging.getLogger("aster_bot.risk")


# ======================================================================
# Data classes
# ======================================================================

@dataclass
class TradeRecord:
    """Immutable record of a completed trade."""

    symbol: str
    side: Literal["long", "short"]
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float                        # realised PnL in USDT
    pnl_pct: float                    # PnL as % of entry notional
    opened_at: datetime
    closed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ======================================================================
# Position Sizing
# ======================================================================

def calculate_position_size(
    balance: float,
    entry_price: float,
    symbol: str,
) -> float:
    """
    Determine the order quantity so that a full stop-loss hit loses at most
    ``RISK_PER_TRADE_PCT`` % of the account balance.

    Formula
    -------
    risk_amount  = balance * (RISK_PER_TRADE_PCT / 100)
    sl_distance  = entry_price * (STOP_LOSS_PCT / 100)
    quantity     = risk_amount / sl_distance

    The result is in **base-asset units** (e.g. BTC).
    Leverage is already factored in on the exchange side.
    """
    risk_amount = balance * (RISK_PER_TRADE_PCT / 100.0)
    sl_distance = entry_price * (STOP_LOSS_PCT / 100.0)

    if sl_distance == 0:
        logger.error("Stop-loss distance is zero — cannot calculate size")
        return 0.0

    quantity = risk_amount / sl_distance

    # Sanity: ensure we don't exceed what the leveraged balance allows
    max_notional = balance * LEVERAGE
    max_qty = max_notional / entry_price
    quantity = min(quantity, max_qty)

    # Round to a sensible precision (exchange will enforce its own step)
    if "BTC" in symbol.upper():
        quantity = round(quantity, 5)   # 0.00001 BTC min
    elif "ETH" in symbol.upper():
        quantity = round(quantity, 4)   # 0.0001 ETH min
    else:
        quantity = round(quantity, 6)

    logger.info(
        "Position size for %s: qty=%.6f  (balance=%.2f  risk=%.2f  "
        "entry=%.2f  SL_dist=%.2f)",
        symbol,
        quantity,
        balance,
        risk_amount,
        entry_price,
        sl_distance,
    )
    return quantity


# ======================================================================
# SL / TP price calculation
# ======================================================================

def calculate_sl_tp(
    entry_price: float,
    side: Literal["long", "short"],
) -> tuple[float, float]:
    """
    Return (stop_loss_price, take_profit_price) for a given entry.

    Long  → SL = entry * (1 - SL%)   TP = entry * (1 + TP%)
    Short → SL = entry * (1 + SL%)   TP = entry * (1 - TP%)
    """
    sl_mult = STOP_LOSS_PCT / 100.0
    tp_mult = TAKE_PROFIT_PCT / 100.0

    if side == "long":
        sl = entry_price * (1 - sl_mult)
        tp = entry_price * (1 + tp_mult)
    else:
        sl = entry_price * (1 + sl_mult)
        tp = entry_price * (1 - tp_mult)

    sl = round(sl, 2)
    tp = round(tp, 2)
    logger.info(
        "SL/TP for %s @ %.2f: SL=%.2f  TP=%.2f",
        side,
        entry_price,
        sl,
        tp,
    )
    return sl, tp


# ======================================================================
# OpenClaw Monitor (trade supervisor)
# ======================================================================

class OpenClawMonitor:
    """
    Tracks trade results and enforces automatic safety rules.

    Rules
    -----
    1. If ``MAX_CONSECUTIVE_LOSSES`` consecutive trades are losers → pause.
    2. If cumulative PnL drops below ``-MAX_TOTAL_LOSS_PCT`` % of starting
       balance → pause.
    """

    def __init__(self, starting_balance: float) -> None:
        self.starting_balance = starting_balance
        self.trades: list[TradeRecord] = []
        self.total_pnl: float = 0.0
        self.consecutive_losses: int = 0
        self.is_paused: bool = False

    # ----- recording ---------------------------------------------------

    def record_trade(self, trade: TradeRecord) -> None:
        """Append a completed trade and update counters."""
        self.trades.append(trade)
        self.total_pnl += trade.pnl

        if trade.pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0  # reset on a win

        logger.info(
            "[OpenClaw] Trade recorded: %s %s  PnL=%.4f USDT (%.2f%%)  "
            "| cum_PnL=%.4f  consec_losses=%d",
            trade.side,
            trade.symbol,
            trade.pnl,
            trade.pnl_pct,
            self.total_pnl,
            self.consecutive_losses,
        )

        self._check_thresholds()

    # ----- safety checks -----------------------------------------------

    def _check_thresholds(self) -> None:
        # Rule 1: consecutive losses
        if self.consecutive_losses >= MAX_CONSECUTIVE_LOSSES:
            self.is_paused = True
            logger.critical(
                "[OpenClaw] *** BOT PAUSED *** — %d consecutive losing "
                "trades reached (limit=%d).",
                self.consecutive_losses,
                MAX_CONSECUTIVE_LOSSES,
            )

        # Rule 2: cumulative loss exceeds threshold
        loss_pct = abs(self.total_pnl) / self.starting_balance * 100
        if self.total_pnl < 0 and loss_pct >= MAX_TOTAL_LOSS_PCT:
            self.is_paused = True
            logger.critical(
                "[OpenClaw] *** BOT PAUSED *** — cumulative loss %.2f%% "
                "exceeds limit %.2f%%.",
                loss_pct,
                MAX_TOTAL_LOSS_PCT,
            )

    # ----- status ------------------------------------------------------

    def can_trade(self) -> bool:
        """Return ``True`` if the bot is allowed to open new positions."""
        if self.is_paused:
            logger.warning(
                "[OpenClaw] Trading is PAUSED. Manual intervention needed "
                "to resume."
            )
        return not self.is_paused

    def resume(self) -> None:
        """Manually resume trading after investigation."""
        self.is_paused = False
        self.consecutive_losses = 0
        logger.info("[OpenClaw] Trading RESUMED by operator.")

    def summary(self) -> str:
        """Return a human-readable performance summary."""
        wins = sum(1 for t in self.trades if t.pnl > 0)
        losses = sum(1 for t in self.trades if t.pnl < 0)
        total = len(self.trades)
        win_rate = (wins / total * 100) if total else 0.0
        return (
            f"[OpenClaw Summary] Trades={total}  W/L={wins}/{losses}  "
            f"Win%={win_rate:.1f}%  Total PnL={self.total_pnl:.4f} USDT  "
            f"Paused={self.is_paused}"
        )
