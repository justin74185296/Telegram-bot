"""
Thread-safe shared state between the trading bot and the web dashboard.

The bot writes to this state every cycle; the dashboard reads it via
Flask API endpoints.  All mutations go through methods that hold a lock.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class PositionSnapshot:
    """Current open position for one symbol."""

    symbol: str
    side: str              # "long" or "short"
    entry_price: float
    quantity: float
    sl_price: float
    tp_price: float
    unrealised_pnl: float
    opened_at: str         # ISO-format string


@dataclass
class TradeSnapshot:
    """One completed trade (for the trade history table)."""

    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    opened_at: str
    closed_at: str


@dataclass
class IndicatorSnapshot:
    """Latest indicator values for one symbol."""

    symbol: str
    ema_short: float
    ema_long: float
    rsi: float
    last_price: float
    last_signal: str       # "long", "short", "close_long", "close_short", "none"
    signal_reason: str


class BotState:
    """
    Central shared state object.

    All public methods are thread-safe.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()

        # Bot metadata
        self.started_at: str = datetime.now(timezone.utc).isoformat()
        self.status: str = "starting"          # starting / running / paused / stopped
        self.trading_mode: str = "paper"
        self.cycle: int = 0
        self.last_cycle_at: str = ""

        # Balance
        self.balance: float = 0.0
        self.initial_balance: float = 0.0

        # Positions  {symbol: PositionSnapshot | None}
        self.positions: dict[str, PositionSnapshot | None] = {}

        # Indicators  {symbol: IndicatorSnapshot}
        self.indicators: dict[str, IndicatorSnapshot] = {}

        # Trade history (newest first)
        self.trades: list[TradeSnapshot] = []

        # OpenClaw stats
        self.total_pnl: float = 0.0
        self.consecutive_losses: int = 0
        self.is_openclaw_paused: bool = False
        self.win_count: int = 0
        self.loss_count: int = 0

        # Errors / log buffer (last N messages)
        self.recent_logs: list[str] = []
        self._max_logs: int = 200

    # ------------------------------------------------------------------
    # Writers (called by the bot)
    # ------------------------------------------------------------------

    def update_cycle(self, cycle: int) -> None:
        with self._lock:
            self.cycle = cycle
            self.last_cycle_at = datetime.now(timezone.utc).isoformat()

    def set_status(self, status: str) -> None:
        with self._lock:
            self.status = status

    def set_balance(self, balance: float, initial: float | None = None) -> None:
        with self._lock:
            self.balance = balance
            if initial is not None:
                self.initial_balance = initial

    def set_position(self, symbol: str, pos: PositionSnapshot | None) -> None:
        with self._lock:
            self.positions[symbol] = pos

    def set_indicators(self, snap: IndicatorSnapshot) -> None:
        with self._lock:
            self.indicators[snap.symbol] = snap

    def add_trade(self, t: TradeSnapshot) -> None:
        with self._lock:
            self.trades.insert(0, t)  # newest first
            if len(self.trades) > 500:
                self.trades = self.trades[:500]

    def set_openclaw(
        self,
        total_pnl: float,
        consecutive_losses: int,
        is_paused: bool,
        wins: int,
        losses: int,
    ) -> None:
        with self._lock:
            self.total_pnl = total_pnl
            self.consecutive_losses = consecutive_losses
            self.is_openclaw_paused = is_paused
            self.win_count = wins
            self.loss_count = losses

    def add_log(self, message: str) -> None:
        with self._lock:
            self.recent_logs.append(message)
            if len(self.recent_logs) > self._max_logs:
                self.recent_logs = self.recent_logs[-self._max_logs:]

    # ------------------------------------------------------------------
    # Reader (called by the dashboard)
    # ------------------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-serialisable snapshot of the entire state."""
        with self._lock:
            total_trades = self.win_count + self.loss_count
            win_rate = (self.win_count / total_trades * 100) if total_trades else 0.0
            pnl_pct = (
                (self.total_pnl / self.initial_balance * 100)
                if self.initial_balance
                else 0.0
            )

            return {
                "bot": {
                    "status": self.status,
                    "trading_mode": self.trading_mode,
                    "started_at": self.started_at,
                    "cycle": self.cycle,
                    "last_cycle_at": self.last_cycle_at,
                },
                "balance": {
                    "current": round(self.balance, 2),
                    "initial": round(self.initial_balance, 2),
                    "pnl": round(self.total_pnl, 4),
                    "pnl_pct": round(pnl_pct, 2),
                },
                "positions": {
                    sym: (
                        {
                            "symbol": p.symbol,
                            "side": p.side,
                            "entry_price": p.entry_price,
                            "quantity": p.quantity,
                            "sl_price": p.sl_price,
                            "tp_price": p.tp_price,
                            "unrealised_pnl": round(p.unrealised_pnl, 4),
                            "opened_at": p.opened_at,
                        }
                        if p
                        else None
                    )
                    for sym, p in self.positions.items()
                },
                "indicators": {
                    sym: {
                        "symbol": ind.symbol,
                        "ema_short": round(ind.ema_short, 2),
                        "ema_long": round(ind.ema_long, 2),
                        "rsi": round(ind.rsi, 2),
                        "last_price": round(ind.last_price, 2),
                        "last_signal": ind.last_signal,
                        "signal_reason": ind.signal_reason,
                    }
                    for sym, ind in self.indicators.items()
                },
                "openclaw": {
                    "total_pnl": round(self.total_pnl, 4),
                    "consecutive_losses": self.consecutive_losses,
                    "is_paused": self.is_openclaw_paused,
                    "wins": self.win_count,
                    "losses": self.loss_count,
                    "total_trades": total_trades,
                    "win_rate": round(win_rate, 1),
                },
                "trades": [
                    {
                        "symbol": t.symbol,
                        "side": t.side,
                        "entry_price": t.entry_price,
                        "exit_price": t.exit_price,
                        "quantity": t.quantity,
                        "pnl": round(t.pnl, 4),
                        "pnl_pct": round(t.pnl_pct, 2),
                        "opened_at": t.opened_at,
                        "closed_at": t.closed_at,
                    }
                    for t in self.trades[:50]  # last 50 for the API
                ],
                "recent_logs": self.recent_logs[-50:],
            }


# ======================================================================
# Global singleton
# ======================================================================
bot_state = BotState()
