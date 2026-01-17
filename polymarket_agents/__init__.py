"""
Polymarket Multi-Agent Trading System
=====================================

A multi-agent trading system for Polymarket prediction markets,
built with CrewAI, LangChain, and Anthropic Claude API.

Team:
- Supervisor (Claude Opus 4.5) - Final decision maker
- Momentum Trader (Claude Sonnet 4.5) - Trend following
- Mean Reversion Trader (Claude Sonnet 4.5) - Statistical arbitrage
- Arbitrage Trader (Claude Sonnet 4.5) - Risk-free opportunities
- Data Optimizer (Claude Sonnet 4.5) - Data collection & optimization

Features:
- Multi-round debate mechanism (2-4 rounds)
- Human-in-the-loop for critical decisions
- Risk management (5% per trade, 20% total exposure)
- Simulation mode (no real trades)

Usage:
    from polymarket_agents import create_crew, analyze
    
    # Quick analysis
    results = analyze("will-bitcoin-reach-100k-2025")
    
    # Or with crew object
    crew = create_crew()
    results = crew.analyze_market(
        market_id="will-bitcoin-reach-100k-2025",
        market_question="Will Bitcoin reach $100,000?"
    )
"""

__version__ = "1.0.0"
__author__ = "Polymarket Agents Team"

from .crew import PolymarketTradingCrew, create_crew, analyze
from .config import get_config, update_config

__all__ = [
    "PolymarketTradingCrew",
    "create_crew",
    "analyze",
    "get_config",
    "update_config",
]
