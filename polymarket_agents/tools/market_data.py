"""
Market Data Tools
=================

Tools for fetching and processing Polymarket data.
Currently using mock data for simulation mode.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from crewai.tools import tool


@dataclass
class MarketData:
    """Structure for market data."""
    market_id: str
    question: str
    yes_price: float
    no_price: float
    yes_volume_24h: float
    no_volume_24h: float
    total_liquidity: float
    last_trade_price: float
    last_trade_side: str
    price_change_24h: float
    volume_change_24h: float
    end_date: str
    category: str
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OrderbookLevel:
    """Single orderbook level."""
    price: float
    size: float


@dataclass
class Orderbook:
    """Orderbook structure."""
    market_id: str
    yes_bids: List[OrderbookLevel]
    yes_asks: List[OrderbookLevel]
    no_bids: List[OrderbookLevel]
    no_asks: List[OrderbookLevel]
    spread_yes: float
    spread_no: float
    mid_price_yes: float
    mid_price_no: float


@dataclass
class PricePoint:
    """Historical price point."""
    timestamp: str
    yes_price: float
    no_price: float
    volume: float


# Mock data store for simulation
MOCK_MARKETS = {
    "will-bitcoin-reach-100k-2025": {
        "market_id": "will-bitcoin-reach-100k-2025",
        "question": "Will Bitcoin reach $100,000 by end of 2025?",
        "yes_price": 0.67,
        "no_price": 0.33,
        "yes_volume_24h": 125000.0,
        "no_volume_24h": 85000.0,
        "total_liquidity": 2500000.0,
        "last_trade_price": 0.68,
        "last_trade_side": "YES",
        "price_change_24h": 0.05,
        "volume_change_24h": 0.15,
        "end_date": "2025-12-31T23:59:59Z",
        "category": "Crypto",
        "created_at": "2024-01-15T10:00:00Z",
    },
    "fed-rate-cut-jan-2025": {
        "market_id": "fed-rate-cut-jan-2025",
        "question": "Will the Federal Reserve cut interest rates in January 2025?",
        "yes_price": 0.42,
        "no_price": 0.58,
        "yes_volume_24h": 95000.0,
        "no_volume_24h": 78000.0,
        "total_liquidity": 1800000.0,
        "last_trade_price": 0.41,
        "last_trade_side": "YES",
        "price_change_24h": -0.03,
        "volume_change_24h": 0.22,
        "end_date": "2025-01-31T23:59:59Z",
        "category": "Economics",
        "created_at": "2024-06-01T08:00:00Z",
    },
    "trump-wins-2024": {
        "market_id": "trump-wins-2024",
        "question": "Will Donald Trump win the 2024 US Presidential Election?",
        "yes_price": 0.52,
        "no_price": 0.48,
        "yes_volume_24h": 850000.0,
        "no_volume_24h": 820000.0,
        "total_liquidity": 15000000.0,
        "last_trade_price": 0.53,
        "last_trade_side": "YES",
        "price_change_24h": 0.02,
        "volume_change_24h": 0.35,
        "end_date": "2024-11-05T23:59:59Z",
        "category": "Politics",
        "created_at": "2023-01-01T00:00:00Z",
    },
    "eth-above-5k-2025": {
        "market_id": "eth-above-5k-2025",
        "question": "Will Ethereum be above $5,000 at any point in 2025?",
        "yes_price": 0.55,
        "no_price": 0.45,
        "yes_volume_24h": 68000.0,
        "no_volume_24h": 52000.0,
        "total_liquidity": 1200000.0,
        "last_trade_price": 0.54,
        "last_trade_side": "NO",
        "price_change_24h": -0.02,
        "volume_change_24h": 0.08,
        "end_date": "2025-12-31T23:59:59Z",
        "category": "Crypto",
        "created_at": "2024-03-01T12:00:00Z",
    },
}


def _generate_mock_historical_prices(
    market_id: str,
    days: int = 30
) -> List[Dict[str, Any]]:
    """Generate mock historical price data."""
    base_data = MOCK_MARKETS.get(market_id, list(MOCK_MARKETS.values())[0])
    current_yes = base_data["yes_price"]
    
    prices = []
    for i in range(days, 0, -1):
        timestamp = datetime.now() - timedelta(days=i)
        # Add some random walk variation
        variation = random.uniform(-0.03, 0.03)
        historical_yes = max(0.01, min(0.99, current_yes + variation * (i / days)))
        historical_no = 1.0 - historical_yes
        
        prices.append({
            "timestamp": timestamp.isoformat(),
            "yes_price": round(historical_yes, 4),
            "no_price": round(historical_no, 4),
            "volume": round(random.uniform(50000, 200000), 2),
        })
    
    return prices


def _generate_mock_orderbook(market_id: str) -> Dict[str, Any]:
    """Generate mock orderbook data."""
    base_data = MOCK_MARKETS.get(market_id, list(MOCK_MARKETS.values())[0])
    yes_mid = base_data["yes_price"]
    no_mid = base_data["no_price"]
    
    # Generate bid/ask levels
    yes_bids = [
        {"price": round(yes_mid - 0.01 * (i + 1), 4), "size": round(random.uniform(1000, 10000), 2)}
        for i in range(5)
    ]
    yes_asks = [
        {"price": round(yes_mid + 0.01 * (i + 1), 4), "size": round(random.uniform(1000, 10000), 2)}
        for i in range(5)
    ]
    no_bids = [
        {"price": round(no_mid - 0.01 * (i + 1), 4), "size": round(random.uniform(1000, 10000), 2)}
        for i in range(5)
    ]
    no_asks = [
        {"price": round(no_mid + 0.01 * (i + 1), 4), "size": round(random.uniform(1000, 10000), 2)}
        for i in range(5)
    ]
    
    return {
        "market_id": market_id,
        "yes_bids": yes_bids,
        "yes_asks": yes_asks,
        "no_bids": no_bids,
        "no_asks": no_asks,
        "spread_yes": round(yes_asks[0]["price"] - yes_bids[0]["price"], 4),
        "spread_no": round(no_asks[0]["price"] - no_bids[0]["price"], 4),
        "mid_price_yes": yes_mid,
        "mid_price_no": no_mid,
    }


@tool("Get Polymarket Data")
def get_polymarket_data(market_id: str) -> str:
    """
    Fetch current market data from Polymarket for a specific market.
    
    Args:
        market_id: The unique identifier for the Polymarket market
        
    Returns:
        JSON string containing market data including prices, volumes, and metadata
    """
    # In production, this would call the actual Polymarket API
    # For simulation, we use mock data
    
    if market_id in MOCK_MARKETS:
        data = MOCK_MARKETS[market_id].copy()
    else:
        # Generate dynamic mock data for unknown markets
        data = {
            "market_id": market_id,
            "question": f"Market: {market_id}",
            "yes_price": round(random.uniform(0.3, 0.7), 4),
            "no_price": 0.0,  # Will be calculated
            "yes_volume_24h": round(random.uniform(10000, 100000), 2),
            "no_volume_24h": round(random.uniform(10000, 100000), 2),
            "total_liquidity": round(random.uniform(500000, 5000000), 2),
            "last_trade_price": 0.0,
            "last_trade_side": random.choice(["YES", "NO"]),
            "price_change_24h": round(random.uniform(-0.1, 0.1), 4),
            "volume_change_24h": round(random.uniform(-0.3, 0.3), 4),
            "end_date": (datetime.now() + timedelta(days=random.randint(30, 365))).isoformat(),
            "category": "General",
            "created_at": datetime.now().isoformat(),
        }
        data["no_price"] = round(1.0 - data["yes_price"], 4)
        data["last_trade_price"] = data["yes_price"]
    
    # Add some real-time variation to simulate live data
    variation = random.uniform(-0.005, 0.005)
    data["yes_price"] = round(max(0.01, min(0.99, data["yes_price"] + variation)), 4)
    data["no_price"] = round(1.0 - data["yes_price"], 4)
    
    return json.dumps(data, indent=2)


@tool("Get Market Orderbook")
def get_orderbook(market_id: str) -> str:
    """
    Fetch the current orderbook for a Polymarket market.
    
    Args:
        market_id: The unique identifier for the market
        
    Returns:
        JSON string containing orderbook with bids and asks for YES and NO outcomes
    """
    orderbook = _generate_mock_orderbook(market_id)
    return json.dumps(orderbook, indent=2)


@tool("Get Historical Prices")
def get_historical_prices(market_id: str, days: int = 30) -> str:
    """
    Fetch historical price data for a Polymarket market.
    
    Args:
        market_id: The unique identifier for the market
        days: Number of days of historical data to fetch (default: 30)
        
    Returns:
        JSON string containing list of historical price points
    """
    prices = _generate_mock_historical_prices(market_id, days)
    
    result = {
        "market_id": market_id,
        "period_days": days,
        "data_points": len(prices),
        "prices": prices,
    }
    
    return json.dumps(result, indent=2)


@tool("Calculate Market Statistics")
def calculate_statistics(market_id: str) -> str:
    """
    Calculate statistical metrics for a Polymarket market based on historical data.
    
    Args:
        market_id: The unique identifier for the market
        
    Returns:
        JSON string containing statistical analysis including mean, std dev, z-score, etc.
    """
    # Get historical prices
    historical = _generate_mock_historical_prices(market_id, 30)
    yes_prices = [p["yes_price"] for p in historical]
    volumes = [p["volume"] for p in historical]
    
    # Calculate statistics
    import statistics
    
    mean_price = statistics.mean(yes_prices)
    std_dev = statistics.stdev(yes_prices) if len(yes_prices) > 1 else 0
    current_price = yes_prices[-1] if yes_prices else 0.5
    
    # Calculate z-score (how many standard deviations from mean)
    z_score = (current_price - mean_price) / std_dev if std_dev > 0 else 0
    
    # Calculate momentum indicators
    short_term_mean = statistics.mean(yes_prices[-7:]) if len(yes_prices) >= 7 else mean_price
    long_term_mean = statistics.mean(yes_prices[-21:]) if len(yes_prices) >= 21 else mean_price
    
    # Price trend (simple linear regression approximation)
    n = len(yes_prices)
    if n > 1:
        x_mean = (n - 1) / 2
        y_mean = mean_price
        numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(yes_prices))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        trend_slope = numerator / denominator if denominator != 0 else 0
    else:
        trend_slope = 0
    
    # Volume analysis
    avg_volume = statistics.mean(volumes)
    recent_volume = statistics.mean(volumes[-3:]) if len(volumes) >= 3 else avg_volume
    volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
    
    stats = {
        "market_id": market_id,
        "current_yes_price": current_price,
        "statistics": {
            "mean_30d": round(mean_price, 4),
            "std_dev_30d": round(std_dev, 4),
            "z_score": round(z_score, 4),
            "min_30d": round(min(yes_prices), 4),
            "max_30d": round(max(yes_prices), 4),
            "range_30d": round(max(yes_prices) - min(yes_prices), 4),
        },
        "momentum": {
            "short_term_mean_7d": round(short_term_mean, 4),
            "long_term_mean_21d": round(long_term_mean, 4),
            "trend_slope": round(trend_slope, 6),
            "trend_direction": "BULLISH" if trend_slope > 0.001 else "BEARISH" if trend_slope < -0.001 else "NEUTRAL",
        },
        "volume_analysis": {
            "avg_daily_volume": round(avg_volume, 2),
            "recent_3d_avg_volume": round(recent_volume, 2),
            "volume_ratio": round(volume_ratio, 4),
            "volume_trend": "INCREASING" if volume_ratio > 1.2 else "DECREASING" if volume_ratio < 0.8 else "STABLE",
        },
        "mean_reversion_signals": {
            "deviation_from_mean": round(current_price - mean_price, 4),
            "is_overbought": z_score > 2.0,
            "is_oversold": z_score < -2.0,
            "reversion_potential": "HIGH" if abs(z_score) > 2.0 else "MEDIUM" if abs(z_score) > 1.0 else "LOW",
        },
    }
    
    return json.dumps(stats, indent=2)


# Additional helper function for getting all available markets
def get_available_markets() -> List[str]:
    """Return list of available mock market IDs."""
    return list(MOCK_MARKETS.keys())
