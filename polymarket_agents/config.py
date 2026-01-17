"""
Polymarket Multi-Agent Trading System - Configuration Module
============================================================

This module contains all configuration settings for the trading system,
including LLM configurations, risk parameters, and system constants.
"""

import os
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


class ModelTier(Enum):
    """Model tier enumeration for different agent roles."""
    SUPERVISOR = "supervisor"  # Highest tier - Claude Opus 4.5
    TRADER = "trader"          # Standard tier - Claude Sonnet 4.5


@dataclass
class LLMConfig:
    """Configuration for Language Model settings."""
    
    # Anthropic API Key (from environment)
    anthropic_api_key: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", "")
    )
    
    # Model names for different tiers
    supervisor_model: str = "claude-sonnet-4-20250514"  # Highest capability
    trader_model: str = "claude-sonnet-4-20250514"      # Cost-effective for traders
    
    # Model parameters
    temperature: float = 0.3  # Lower for more consistent trading decisions
    max_tokens: int = 4096
    
    # Rate limiting
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def get_model_for_tier(self, tier: ModelTier) -> str:
        """Get the appropriate model name for a given tier."""
        if tier == ModelTier.SUPERVISOR:
            return self.supervisor_model
        return self.trader_model


@dataclass
class RiskConfig:
    """Risk management configuration."""
    
    # Position limits
    max_single_trade_percent: float = 5.0      # Max 5% of portfolio per trade
    max_total_exposure_percent: float = 20.0   # Max 20% total exposure
    
    # Debate thresholds
    disagreement_threshold: float = 30.0       # 30% disagreement triggers extra round
    max_debate_rounds: int = 4                 # Maximum debate rounds
    min_debate_rounds: int = 2                 # Minimum debate rounds
    
    # Confidence thresholds
    min_confidence_for_trade: float = 60.0     # Min confidence to recommend trade
    high_confidence_threshold: float = 85.0    # High confidence level
    
    # Human intervention triggers
    large_trade_threshold_percent: float = 4.0  # Ask human if > 4% of portfolio
    high_disagreement_threshold: float = 40.0   # Ask human if > 40% disagreement
    
    # Stop-loss settings (for future implementation)
    default_stop_loss_percent: float = 10.0
    trailing_stop_percent: float = 5.0


@dataclass 
class PolymarketConfig:
    """Polymarket-specific configuration."""
    
    # API endpoints (placeholder for actual implementation)
    base_url: str = "https://clob.polymarket.com"
    gamma_url: str = "https://gamma-api.polymarket.com"
    
    # Default parameters
    default_slippage_tolerance: float = 0.02   # 2% slippage tolerance
    min_liquidity_threshold: float = 1000.0    # Min liquidity for trading
    
    # Data refresh intervals (seconds)
    price_refresh_interval: int = 10
    orderbook_refresh_interval: int = 5
    
    # Simulation mode
    simulation_mode: bool = True  # Always start in simulation mode


@dataclass
class SystemConfig:
    """Overall system configuration."""
    
    llm: LLMConfig = field(default_factory=LLMConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    polymarket: PolymarketConfig = field(default_factory=PolymarketConfig)
    
    # Logging
    verbose: bool = True
    log_level: str = "INFO"
    
    # Output formatting
    output_format: str = "json"  # "json" or "text"
    
    # Portfolio simulation
    initial_portfolio_value: float = 10000.0  # $10,000 simulated portfolio


# Global configuration instance
config = SystemConfig()


def get_config() -> SystemConfig:
    """Get the global configuration instance."""
    return config


def update_config(**kwargs) -> SystemConfig:
    """Update configuration values."""
    global config
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        elif hasattr(config.llm, key):
            setattr(config.llm, key, value)
        elif hasattr(config.risk, key):
            setattr(config.risk, key, value)
        elif hasattr(config.polymarket, key):
            setattr(config.polymarket, key, value)
    return config


# Validation
def validate_config() -> bool:
    """Validate that required configuration is present."""
    errors = []
    
    if not config.llm.anthropic_api_key:
        errors.append("ANTHROPIC_API_KEY environment variable not set")
    
    if config.risk.max_single_trade_percent > config.risk.max_total_exposure_percent:
        errors.append("Single trade limit cannot exceed total exposure limit")
    
    if errors:
        for error in errors:
            print(f"Configuration Error: {error}")
        return False
    
    return True


# Quick reference for model configuration
MODEL_CONFIG = {
    "supervisor": {
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.2,  # More deterministic for final decisions
        "max_tokens": 8192,  # More tokens for comprehensive analysis
    },
    "momentum_trader": {
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.3,
        "max_tokens": 4096,
    },
    "mean_reversion_trader": {
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.3,
        "max_tokens": 4096,
    },
    "arbitrage_trader": {
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.2,  # Lower for precise calculations
        "max_tokens": 4096,
    },
    "data_optimizer": {
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.4,  # Slightly higher for creative optimization suggestions
        "max_tokens": 4096,
    },
}
