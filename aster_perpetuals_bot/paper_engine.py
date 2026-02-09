"""
Lightweight paper-trading engine.

When ``TRADING_MODE=paper``, the bot never touches a real exchange for order
placement.  Market-data calls (OHLCV, ticker) *still* go to the exchange so
that the simulation uses real prices — but no API key is required for public
endpoints.

This module provides a self-contained balance tracker that the strategy layer
uses in place of the real ``exchange.get_usdt_balance()`` when running in
paper mode.
"""

from __future__ import annotations

import logging

from aster_perpetuals_bot.config import PAPER_INITIAL_BALANCE

logger = logging.getLogger("aster_bot.paper")


class PaperAccount:
    """Track simulated USDT balance."""

    def __init__(self, initial_balance: float | None = None) -> None:
        self.balance = initial_balance or PAPER_INITIAL_BALANCE
        self._initial = self.balance
        logger.info("[Paper] Account initialised with %.2f USDT", self.balance)

    def update(self, pnl: float) -> None:
        self.balance += pnl
        logger.info(
            "[Paper] Balance updated by %.4f → %.2f USDT", pnl, self.balance
        )

    @property
    def pnl_total(self) -> float:
        return self.balance - self._initial

    def __repr__(self) -> str:
        return (
            f"PaperAccount(balance={self.balance:.2f}, "
            f"initial={self._initial:.2f}, pnl={self.pnl_total:.2f})"
        )
