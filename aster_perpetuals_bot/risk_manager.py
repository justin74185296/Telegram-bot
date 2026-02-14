"""
Risk management & OpenClaw supervisor — fee-aware edition.

Key changes from previous version:
* simulate_pnl() computes net profit after fees + slippage.
* Pre-trade filter: skip if expected profit < min_take_profit + 2×fee.
* OpenClaw tracks cumulative fees, daily fee %, net win rate.
* Pauses if daily fees > 2% of balance or net win rate < 55%.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Literal

from aster_perpetuals_bot.config import (
    FEE_RATE,
    LEVERAGE,
    MAX_CONSECUTIVE_LOSSES,
    MAX_DAILY_FEE_PCT,
    MAX_TOTAL_LOSS_PCT,
    MAX_TRADES_PER_HOUR,
    MIN_NET_WIN_RATE_PCT,
    MIN_TAKE_PROFIT_PCT,
    RISK_PER_TRADE_PCT,
    SLIPPAGE_ESTIMATE,
    STOP_LOSS_PCT,
    TAKE_PROFIT_PCT,
)

logger = logging.getLogger("aster_bot.risk")


# ======================================================================
# Data classes
# ======================================================================

@dataclass
class TradeRecord:
    """Record of a completed trade (includes fee info)."""

    symbol: str
    side: Literal["long", "short"]
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float                # NET PnL after fees
    pnl_pct: float            # NET PnL as % of entry notional
    gross_pnl: float = 0.0    # PnL before fees
    fees: float = 0.0         # Total fees for this round-trip
    opened_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    closed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ======================================================================
# Fee-aware PnL simulation
# ======================================================================

def simulate_pnl(
    gross_profit: float,
    position_value: float,
    fee_rate: float = FEE_RATE,
    slippage: float = SLIPPAGE_ESTIMATE,
) -> tuple[float, float]:
    """
    Calculate net PnL after fees and slippage.

    Parameters
    ----------
    gross_profit   : raw price movement × quantity
    position_value : entry_price × quantity (notional)
    fee_rate       : per-side fee rate (default 0.04%)
    slippage       : estimated slippage as fraction (default 0.1%)

    Returns
    -------
    (net_pnl, total_fees)
    """
    # Fees: charged on both open and close (2 sides)
    fees = fee_rate * position_value * 2
    # Slippage: one-time estimate on position value
    slip_cost = slippage * position_value
    total_cost = fees + slip_cost
    net_pnl = gross_profit - total_cost
    return net_pnl, fees


def estimate_effective_cost(entry_price: float, quantity: float) -> float:
    """
    Estimate the total cost (fees + slippage) for a round-trip trade.

    Returns cost in USDT.
    """
    position_value = entry_price * quantity
    fees = FEE_RATE * position_value * 2
    slip = SLIPPAGE_ESTIMATE * position_value
    return fees + slip


def is_trade_profitable(
    expected_profit_pct: float,
) -> bool:
    """
    Pre-trade filter: only enter if expected profit exceeds
    min_take_profit + 2 × fee_rate + slippage.

    Parameters
    ----------
    expected_profit_pct : expected gross profit as a fraction (e.g. 0.003 = 0.3%)
    """
    min_required = (MIN_TAKE_PROFIT_PCT / 100.0) + (FEE_RATE * 2) + SLIPPAGE_ESTIMATE
    profitable = expected_profit_pct >= min_required
    if not profitable:
        logger.info(
            "[FEE FILTER] Trade skipped: expected=%.4f%% < required=%.4f%% "
            "(min_tp=%.3f%% + 2×fee=%.4f%% + slip=%.3f%%)",
            expected_profit_pct * 100,
            min_required * 100,
            MIN_TAKE_PROFIT_PCT,
            FEE_RATE * 2 * 100,
            SLIPPAGE_ESTIMATE * 100,
        )
    return profitable


# ======================================================================
# Position Sizing
# ======================================================================

def calculate_position_size(
    balance: float,
    entry_price: float,
    symbol: str,
) -> float:
    """Position size: risk RISK_PER_TRADE_PCT of balance per SL distance."""
    risk_amount = balance * (RISK_PER_TRADE_PCT / 100.0)
    sl_distance = entry_price * (STOP_LOSS_PCT / 100.0)

    if sl_distance == 0:
        logger.error("SL distance is zero — cannot calculate size")
        return 0.0

    quantity = risk_amount / sl_distance
    max_qty = (balance * LEVERAGE) / entry_price
    quantity = min(quantity, max_qty)

    if "BTC" in symbol.upper():
        quantity = round(quantity, 5)
    elif "ETH" in symbol.upper():
        quantity = round(quantity, 4)
    else:
        quantity = round(quantity, 6)

    # Log with fee estimate
    est_fees = estimate_effective_cost(entry_price, quantity)
    logger.info(
        "Position size %s: qty=%.6f  risk=%.2f  est_fees=%.4f USDT",
        symbol, quantity, risk_amount, est_fees,
    )
    return quantity


# ======================================================================
# SL / TP (fallback)
# ======================================================================

def calculate_sl_tp(
    entry_price: float,
    side: Literal["long", "short"],
) -> tuple[float, float]:
    """Return (sl_price, tp_price). TP must be >= MIN_TAKE_PROFIT_PCT."""
    sl_mult = STOP_LOSS_PCT / 100.0
    # Ensure TP covers fees: max(configured TP, min TP that covers fees)
    min_tp_needed = (MIN_TAKE_PROFIT_PCT / 100.0) + (FEE_RATE * 2) + SLIPPAGE_ESTIMATE
    tp_mult = max(TAKE_PROFIT_PCT / 100.0, min_tp_needed)

    if side == "long":
        sl = entry_price * (1 - sl_mult)
        tp = entry_price * (1 + tp_mult)
    else:
        sl = entry_price * (1 + sl_mult)
        tp = entry_price * (1 - tp_mult)

    sl, tp = round(sl, 2), round(tp, 2)
    logger.info("SL/TP for %s @ %.2f: SL=%.2f  TP=%.2f (min_tp_pct=%.3f%%)",
                side, entry_price, sl, tp, tp_mult * 100)
    return sl, tp


# ======================================================================
# OpenClaw Monitor — fee-aware
# ======================================================================

class OpenClawMonitor:
    """
    Tracks trade results with fee awareness.

    Additional rules:
    4. Daily cumulative fees > MAX_DAILY_FEE_PCT % of balance → pause.
    5. Net win rate (after fees) < MIN_NET_WIN_RATE_PCT % (after 10+ trades) → pause.
    """

    def __init__(self, starting_balance: float) -> None:
        self.starting_balance = starting_balance
        self.trades: list[TradeRecord] = []
        self.total_pnl: float = 0.0
        self.total_gross_pnl: float = 0.0
        self.total_fees: float = 0.0
        self.consecutive_losses: int = 0
        self.is_paused: bool = False

        self._trade_timestamps: deque[datetime] = deque()
        self.trades_this_hour: int = 0

        # Daily fee tracking
        self._daily_fees: deque[tuple[datetime, float]] = deque()
        self.daily_fee_total: float = 0.0

    def record_trade(self, trade: TradeRecord) -> None:
        self.trades.append(trade)
        self.total_pnl += trade.pnl
        self.total_gross_pnl += trade.gross_pnl
        self.total_fees += trade.fees

        if trade.pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        now = datetime.now(timezone.utc)
        self._trade_timestamps.append(now)
        self._prune_old_timestamps(now)

        # Track daily fees
        self._daily_fees.append((now, trade.fees))
        self._prune_daily_fees(now)

        logger.info(
            "[OpenClaw] %s %s  gross=%.4f  fees=%.4f  net=%.4f USDT (%.2f%%)  "
            "| cum_net=%.4f  cum_fees=%.4f  consec=%d  trades/hr=%d",
            trade.side, trade.symbol,
            trade.gross_pnl, trade.fees, trade.pnl, trade.pnl_pct,
            self.total_pnl, self.total_fees,
            self.consecutive_losses, self.trades_this_hour,
        )
        self._check_thresholds()

    def _prune_old_timestamps(self, now: datetime) -> None:
        cutoff = now - timedelta(hours=1)
        while self._trade_timestamps and self._trade_timestamps[0] < cutoff:
            self._trade_timestamps.popleft()
        self.trades_this_hour = len(self._trade_timestamps)

    def _prune_daily_fees(self, now: datetime) -> None:
        cutoff = now - timedelta(hours=24)
        while self._daily_fees and self._daily_fees[0][0] < cutoff:
            self._daily_fees.popleft()
        self.daily_fee_total = sum(f for _, f in self._daily_fees)

    def _check_thresholds(self) -> None:
        # Rule 1: consecutive losses
        if self.consecutive_losses >= MAX_CONSECUTIVE_LOSSES:
            self.is_paused = True
            logger.critical("[OpenClaw] PAUSED — %d consecutive losses (limit=%d)",
                            self.consecutive_losses, MAX_CONSECUTIVE_LOSSES)

        # Rule 2: cumulative loss
        if self.starting_balance > 0:
            loss_pct = abs(self.total_pnl) / self.starting_balance * 100
            if self.total_pnl < 0 and loss_pct >= MAX_TOTAL_LOSS_PCT:
                self.is_paused = True
                logger.critical("[OpenClaw] PAUSED — loss %.2f%% >= limit %.2f%%",
                                loss_pct, MAX_TOTAL_LOSS_PCT)

        # Rule 3: trades/hour
        if self.trades_this_hour > MAX_TRADES_PER_HOUR:
            self.is_paused = True
            logger.critical("[OpenClaw] PAUSED — %d trades/hr > limit %d",
                            self.trades_this_hour, MAX_TRADES_PER_HOUR)

        # Rule 4: daily fees too high
        if self.starting_balance > 0:
            daily_fee_pct = self.daily_fee_total / self.starting_balance * 100
            if daily_fee_pct >= MAX_DAILY_FEE_PCT:
                self.is_paused = True
                logger.critical("[OpenClaw] PAUSED — daily fees %.2f%% >= limit %.2f%%",
                                daily_fee_pct, MAX_DAILY_FEE_PCT)

        # Rule 5: net win rate too low (after 10+ trades)
        total = len(self.trades)
        if total >= 10:
            net_wins = sum(1 for t in self.trades if t.pnl > 0)
            net_wr = net_wins / total * 100
            if net_wr < MIN_NET_WIN_RATE_PCT:
                self.is_paused = True
                logger.critical(
                    "[OpenClaw] PAUSED — net win rate %.1f%% < required %.1f%% "
                    "(%d wins / %d trades)",
                    net_wr, MIN_NET_WIN_RATE_PCT, net_wins, total,
                )

    def can_trade(self) -> bool:
        self._prune_old_timestamps(datetime.now(timezone.utc))
        self._prune_daily_fees(datetime.now(timezone.utc))
        if self.is_paused:
            logger.warning("[OpenClaw] Trading PAUSED. Manual resume needed.")
        return not self.is_paused

    def resume(self) -> None:
        self.is_paused = False
        self.consecutive_losses = 0
        logger.info("[OpenClaw] Trading RESUMED.")

    @property
    def net_win_rate(self) -> float:
        total = len(self.trades)
        if total == 0:
            return 0.0
        return sum(1 for t in self.trades if t.pnl > 0) / total * 100

    def summary(self) -> str:
        wins = sum(1 for t in self.trades if t.pnl > 0)
        losses = sum(1 for t in self.trades if t.pnl < 0)
        total = len(self.trades)
        wr = (wins / total * 100) if total else 0.0
        return (
            f"[OpenClaw] Trades={total} W/L={wins}/{losses} NetWin%={wr:.1f}%  "
            f"NetPnL={self.total_pnl:.4f} GrossPnL={self.total_gross_pnl:.4f} "
            f"Fees={self.total_fees:.4f} DailyFees={self.daily_fee_total:.4f}  "
            f"Trades/hr={self.trades_this_hour} Paused={self.is_paused}"
        )
