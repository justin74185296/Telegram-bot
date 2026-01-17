"""
Trading Execution Tools
=======================

Tools for simulating order execution and risk management.
All orders are simulated - no real trades are executed.
"""

import json
import random
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from crewai.tools import tool


class OrderSide(Enum):
    """Order side enumeration."""
    BUY_YES = "BUY_YES"
    BUY_NO = "BUY_NO"
    SELL_YES = "SELL_YES"
    SELL_NO = "SELL_NO"


class OrderStatus(Enum):
    """Order status enumeration."""
    SIMULATED = "SIMULATED"
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class SimulatedPosition:
    """Represents a simulated position."""
    market_id: str
    side: str  # YES or NO
    quantity: float
    avg_price: float
    current_price: float
    unrealized_pnl: float
    entry_time: str


@dataclass
class SimulatedOrder:
    """Represents a simulated order."""
    order_id: str
    market_id: str
    side: str
    quantity: float
    price: float
    status: str
    timestamp: str
    reason: str
    risk_check_passed: bool


# Simulated portfolio state
SIMULATED_PORTFOLIO = {
    "cash_balance": 10000.0,  # Starting with $10,000
    "total_value": 10000.0,
    "positions": {},
    "order_history": [],
    "risk_metrics": {
        "current_exposure_percent": 0.0,
        "largest_position_percent": 0.0,
        "total_trades": 0,
        "winning_trades": 0,
        "losing_trades": 0,
    }
}


def _generate_order_id() -> str:
    """Generate a unique order ID."""
    return f"SIM-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"


def _check_risk_limits_internal(
    order_value: float,
    portfolio_value: float,
    current_exposure: float,
    max_single_trade_pct: float = 5.0,
    max_total_exposure_pct: float = 20.0,
) -> Dict[str, Any]:
    """Internal function to check risk limits."""
    
    trade_percent = (order_value / portfolio_value) * 100
    new_exposure = current_exposure + (order_value / portfolio_value) * 100
    
    checks = {
        "single_trade_check": {
            "passed": trade_percent <= max_single_trade_pct,
            "trade_percent": round(trade_percent, 2),
            "limit": max_single_trade_pct,
            "message": f"Trade is {trade_percent:.2f}% of portfolio (limit: {max_single_trade_pct}%)"
        },
        "total_exposure_check": {
            "passed": new_exposure <= max_total_exposure_pct,
            "new_exposure_percent": round(new_exposure, 2),
            "limit": max_total_exposure_pct,
            "message": f"New exposure would be {new_exposure:.2f}% (limit: {max_total_exposure_pct}%)"
        },
        "overall_passed": trade_percent <= max_single_trade_pct and new_exposure <= max_total_exposure_pct,
    }
    
    return checks


@tool("Simulate Trade Order")
def simulate_order(
    market_id: str,
    side: str,
    quantity: float,
    price: float,
    reason: str = "No reason provided"
) -> str:
    """
    Simulate placing a trade order on Polymarket. NO REAL ORDER IS PLACED.
    This is for simulation and testing purposes only.
    
    Args:
        market_id: The market identifier
        side: Order side - one of: BUY_YES, BUY_NO, SELL_YES, SELL_NO
        quantity: Number of shares to trade
        price: Limit price per share (0-1 range)
        reason: Reason for the trade
        
    Returns:
        JSON string containing simulated order details and execution result
    """
    order_value = quantity * price
    
    # Check risk limits
    risk_check = _check_risk_limits_internal(
        order_value=order_value,
        portfolio_value=SIMULATED_PORTFOLIO["total_value"],
        current_exposure=SIMULATED_PORTFOLIO["risk_metrics"]["current_exposure_percent"],
    )
    
    # Create simulated order
    order = SimulatedOrder(
        order_id=_generate_order_id(),
        market_id=market_id,
        side=side,
        quantity=quantity,
        price=price,
        status=OrderStatus.SIMULATED.value,
        timestamp=datetime.now().isoformat(),
        reason=reason,
        risk_check_passed=risk_check["overall_passed"],
    )
    
    # Simulate execution with slippage
    simulated_fill_price = price * (1 + random.uniform(-0.005, 0.005))  # ±0.5% slippage
    execution_cost = quantity * simulated_fill_price
    
    # Update portfolio (simulation only)
    if risk_check["overall_passed"]:
        SIMULATED_PORTFOLIO["cash_balance"] -= execution_cost
        SIMULATED_PORTFOLIO["risk_metrics"]["total_trades"] += 1
        SIMULATED_PORTFOLIO["order_history"].append(asdict(order))
    
    # Generate detailed output
    result = {
        "simulation_notice": "⚠️ THIS IS A SIMULATED ORDER - NO REAL TRADE EXECUTED ⚠️",
        "order_details": asdict(order),
        "execution_simulation": {
            "requested_price": price,
            "simulated_fill_price": round(simulated_fill_price, 4),
            "slippage": round((simulated_fill_price - price) / price * 100, 4),
            "total_cost": round(execution_cost, 2),
            "would_execute": risk_check["overall_passed"],
        },
        "risk_assessment": risk_check,
        "portfolio_impact": {
            "current_cash": round(SIMULATED_PORTFOLIO["cash_balance"], 2),
            "position_value": round(order_value, 2),
            "new_exposure_percent": round(
                SIMULATED_PORTFOLIO["risk_metrics"]["current_exposure_percent"] + 
                (order_value / SIMULATED_PORTFOLIO["total_value"]) * 100, 2
            ),
        },
        "human_readable": _generate_order_summary(order, risk_check),
    }
    
    # Print simulation message (visible in console)
    print(f"\n{'='*60}")
    print(f"🎮 模擬下單 (SIMULATED ORDER)")
    print(f"{'='*60}")
    print(f"市場: {market_id}")
    print(f"方向: {side}")
    print(f"數量: {quantity} 股")
    print(f"價格: ${price:.4f}")
    print(f"總值: ${execution_cost:.2f}")
    print(f"原因: {reason}")
    print(f"風險檢查: {'✅ 通過' if risk_check['overall_passed'] else '❌ 未通過'}")
    print(f"{'='*60}\n")
    
    return json.dumps(result, indent=2)


def _generate_order_summary(order: SimulatedOrder, risk_check: Dict) -> str:
    """Generate human-readable order summary."""
    status = "WOULD EXECUTE" if risk_check["overall_passed"] else "BLOCKED BY RISK LIMITS"
    return (
        f"Simulated {order.side} order for {order.quantity} shares of {order.market_id} "
        f"@ ${order.price:.4f} - Status: {status}"
    )


@tool("Calculate Position Size")
def calculate_position_size(
    market_id: str,
    price: float,
    confidence: float,
    max_risk_percent: float = 5.0
) -> str:
    """
    Calculate optimal position size based on portfolio value, confidence, and risk limits.
    
    Args:
        market_id: The market identifier
        price: Current price of the position
        confidence: Confidence level (0-100) in the trade
        max_risk_percent: Maximum percentage of portfolio to risk (default 5%)
        
    Returns:
        JSON string containing recommended position size and rationale
    """
    portfolio_value = SIMULATED_PORTFOLIO["total_value"]
    
    # Adjust position size based on confidence
    # Higher confidence = larger position (up to the max)
    confidence_multiplier = min(confidence / 100, 1.0)
    
    # Calculate base position value
    max_position_value = portfolio_value * (max_risk_percent / 100)
    adjusted_position_value = max_position_value * confidence_multiplier
    
    # Calculate number of shares
    shares = adjusted_position_value / price if price > 0 else 0
    
    # Kelly Criterion approximation (simplified)
    # f* = (bp - q) / b where b = odds, p = probability of win, q = 1-p
    # For binary markets: b = (1 - price) / price for YES bets
    if price > 0 and price < 1:
        implied_prob = price
        odds = (1 - price) / price
        kelly_fraction = (odds * (confidence / 100) - (1 - confidence / 100)) / odds
        kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
    else:
        kelly_fraction = 0
    
    kelly_position_value = portfolio_value * kelly_fraction
    kelly_shares = kelly_position_value / price if price > 0 else 0
    
    result = {
        "market_id": market_id,
        "calculation_inputs": {
            "portfolio_value": portfolio_value,
            "current_price": price,
            "confidence_level": confidence,
            "max_risk_percent": max_risk_percent,
        },
        "standard_sizing": {
            "recommended_shares": round(shares, 2),
            "position_value": round(adjusted_position_value, 2),
            "portfolio_percent": round((adjusted_position_value / portfolio_value) * 100, 2),
        },
        "kelly_criterion": {
            "kelly_fraction": round(kelly_fraction * 100, 2),
            "kelly_shares": round(kelly_shares, 2),
            "kelly_position_value": round(kelly_position_value, 2),
            "note": "Kelly criterion suggests optimal bet sizing based on edge",
        },
        "recommendation": {
            "final_shares": round(min(shares, kelly_shares) if kelly_shares > 0 else shares, 2),
            "rationale": _generate_sizing_rationale(confidence, kelly_fraction),
        },
        "risk_warnings": _generate_sizing_warnings(confidence, price, adjusted_position_value, portfolio_value),
    }
    
    return json.dumps(result, indent=2)


def _generate_sizing_rationale(confidence: float, kelly_fraction: float) -> str:
    """Generate rationale for position sizing."""
    if confidence >= 80:
        return "High confidence trade - using maximum allowed position size"
    elif confidence >= 60:
        return "Moderate confidence - using standard position sizing"
    elif confidence >= 40:
        return "Lower confidence - reduced position size recommended"
    else:
        return "Low confidence - minimal position or pass on trade"


def _generate_sizing_warnings(
    confidence: float,
    price: float,
    position_value: float,
    portfolio_value: float
) -> List[str]:
    """Generate risk warnings for position sizing."""
    warnings = []
    
    if confidence < 50:
        warnings.append("⚠️ Confidence below 50% - consider skipping this trade")
    
    if price > 0.9 or price < 0.1:
        warnings.append("⚠️ Extreme price level - limited upside potential")
    
    position_pct = (position_value / portfolio_value) * 100
    if position_pct > 4:
        warnings.append(f"⚠️ Large position ({position_pct:.1f}% of portfolio) - requires human approval")
    
    if not warnings:
        warnings.append("✅ No significant warnings")
    
    return warnings


@tool("Check Risk Limits")
def check_risk_limits(
    proposed_trade_value: float,
    side: str = "BUY_YES"
) -> str:
    """
    Check if a proposed trade complies with risk management rules.
    
    Args:
        proposed_trade_value: The dollar value of the proposed trade
        side: The side of the trade (BUY_YES, BUY_NO, SELL_YES, SELL_NO)
        
    Returns:
        JSON string containing risk check results and recommendations
    """
    portfolio = SIMULATED_PORTFOLIO
    
    # Calculate current exposure
    current_exposure_pct = portfolio["risk_metrics"]["current_exposure_percent"]
    
    # Check limits
    risk_check = _check_risk_limits_internal(
        order_value=proposed_trade_value,
        portfolio_value=portfolio["total_value"],
        current_exposure=current_exposure_pct,
    )
    
    # Additional checks
    is_selling = side.startswith("SELL")
    requires_human_approval = (
        proposed_trade_value > portfolio["total_value"] * 0.04 or  # > 4% of portfolio
        not risk_check["overall_passed"]
    )
    
    result = {
        "proposed_trade": {
            "value": proposed_trade_value,
            "side": side,
            "percent_of_portfolio": round((proposed_trade_value / portfolio["total_value"]) * 100, 2),
        },
        "current_portfolio_state": {
            "total_value": portfolio["total_value"],
            "cash_balance": portfolio["cash_balance"],
            "current_exposure_percent": current_exposure_pct,
            "available_capacity_percent": round(20.0 - current_exposure_pct, 2),
        },
        "risk_checks": risk_check,
        "decision": {
            "can_proceed": risk_check["overall_passed"],
            "requires_human_approval": requires_human_approval,
            "recommendation": _generate_risk_recommendation(risk_check, requires_human_approval),
        },
        "risk_limits_summary": {
            "max_single_trade": "5% of portfolio",
            "max_total_exposure": "20% of portfolio",
            "human_approval_threshold": "4% of portfolio",
        },
    }
    
    if requires_human_approval:
        result["human_intervention_required"] = {
            "message": "🚨 此交易需要人類確認！",
            "reason": "交易金額超過 4% 的投資組合或風險檢查未通過",
            "question": f"人類，你是否批准這筆 ${proposed_trade_value:.2f} 的 {side} 交易？有額外資訊嗎？",
        }
    
    return json.dumps(result, indent=2)


def _generate_risk_recommendation(risk_check: Dict, requires_human: bool) -> str:
    """Generate risk management recommendation."""
    if not risk_check["overall_passed"]:
        return "REJECT - Trade exceeds risk limits. Reduce size or wait for capacity."
    elif requires_human:
        return "PENDING HUMAN APPROVAL - Large trade requires confirmation."
    else:
        return "APPROVED - Trade within all risk parameters."


@tool("Get Portfolio Status")
def get_portfolio_status() -> str:
    """
    Get the current status of the simulated portfolio.
    
    Returns:
        JSON string containing portfolio value, positions, and risk metrics
    """
    portfolio = SIMULATED_PORTFOLIO
    
    result = {
        "portfolio_summary": {
            "total_value": portfolio["total_value"],
            "cash_balance": portfolio["cash_balance"],
            "positions_value": portfolio["total_value"] - portfolio["cash_balance"],
            "last_updated": datetime.now().isoformat(),
        },
        "positions": portfolio["positions"],
        "risk_metrics": portfolio["risk_metrics"],
        "recent_orders": portfolio["order_history"][-5:],  # Last 5 orders
        "performance": {
            "total_trades": portfolio["risk_metrics"]["total_trades"],
            "winning_trades": portfolio["risk_metrics"]["winning_trades"],
            "losing_trades": portfolio["risk_metrics"]["losing_trades"],
            "win_rate": (
                portfolio["risk_metrics"]["winning_trades"] / 
                portfolio["risk_metrics"]["total_trades"] * 100
                if portfolio["risk_metrics"]["total_trades"] > 0 else 0
            ),
        },
        "simulation_notice": "This is a simulated portfolio for testing purposes only.",
    }
    
    return json.dumps(result, indent=2)


@tool("Analyze Arbitrage Opportunity")  
def analyze_arbitrage_opportunity(market_id: str, yes_price: float, no_price: float) -> str:
    """
    Analyze potential arbitrage opportunities in a Polymarket market.
    
    Args:
        market_id: The market identifier
        yes_price: Current YES price
        no_price: Current NO price
        
    Returns:
        JSON string containing arbitrage analysis
    """
    # Check if YES + NO prices deviate from 1.0
    price_sum = yes_price + no_price
    deviation = abs(1.0 - price_sum)
    
    # Calculate potential arbitrage profit
    if price_sum < 1.0:
        # Can buy both YES and NO for less than $1, guaranteed $1 return
        arbitrage_type = "UNDERPRICED"
        profit_per_unit = 1.0 - price_sum
        action = "BUY BOTH YES AND NO"
    elif price_sum > 1.0:
        # Prices overpriced - could short both if possible
        arbitrage_type = "OVERPRICED"
        profit_per_unit = price_sum - 1.0
        action = "SELL BOTH YES AND NO (if positions exist)"
    else:
        arbitrage_type = "NONE"
        profit_per_unit = 0
        action = "NO ARBITRAGE OPPORTUNITY"
    
    # Estimate slippage impact
    estimated_slippage = 0.02  # 2% estimated slippage
    net_profit_per_unit = max(0, profit_per_unit - estimated_slippage)
    
    # Calculate recommended trade size
    portfolio_value = SIMULATED_PORTFOLIO["total_value"]
    max_arbitrage_value = min(portfolio_value * 0.05, 500)  # Max 5% or $500
    
    result = {
        "market_id": market_id,
        "price_analysis": {
            "yes_price": yes_price,
            "no_price": no_price,
            "price_sum": round(price_sum, 4),
            "deviation_from_unity": round(deviation, 4),
            "deviation_percent": round(deviation * 100, 2),
        },
        "arbitrage_opportunity": {
            "exists": deviation > 0.02,  # Only consider if > 2% deviation
            "type": arbitrage_type,
            "gross_profit_per_unit": round(profit_per_unit, 4),
            "estimated_slippage": estimated_slippage,
            "net_profit_per_unit": round(net_profit_per_unit, 4),
            "recommended_action": action,
        },
        "execution_recommendation": {
            "should_execute": deviation > 0.03 and net_profit_per_unit > 0.01,
            "recommended_size_usd": round(max_arbitrage_value, 2) if deviation > 0.03 else 0,
            "expected_profit_usd": round(max_arbitrage_value * net_profit_per_unit, 2) if deviation > 0.03 else 0,
            "risk_level": "LOW" if deviation > 0.05 else "MEDIUM" if deviation > 0.03 else "HIGH",
        },
        "liquidity_warning": _assess_arbitrage_liquidity(yes_price, no_price),
        "note": "Arbitrage profits are typically small and require quick execution. Slippage can eliminate profits.",
    }
    
    return json.dumps(result, indent=2)


def _assess_arbitrage_liquidity(yes_price: float, no_price: float) -> str:
    """Assess liquidity concerns for arbitrage."""
    if yes_price > 0.9 or yes_price < 0.1:
        return "⚠️ Extreme YES price - may have poor liquidity"
    if no_price > 0.9 or no_price < 0.1:
        return "⚠️ Extreme NO price - may have poor liquidity"
    return "✅ Prices in normal range - likely adequate liquidity"
