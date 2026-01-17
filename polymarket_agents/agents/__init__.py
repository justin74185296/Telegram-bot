"""
Polymarket Trading Agents Module
================================

This module contains the definitions for all trading agents in the system:
- Supervisor (Team Manager & Final Decision Maker)
- Momentum Trader
- Mean Reversion Trader
- Arbitrage Trader
- Data & Optimizer Agent
"""

from .supervisor import create_supervisor_agent
from .momentum_trader import create_momentum_trader_agent
from .mean_reversion_trader import create_mean_reversion_trader_agent
from .arbitrage_trader import create_arbitrage_trader_agent
from .data_optimizer import create_data_optimizer_agent

__all__ = [
    "create_supervisor_agent",
    "create_momentum_trader_agent",
    "create_mean_reversion_trader_agent",
    "create_arbitrage_trader_agent",
    "create_data_optimizer_agent",
]
