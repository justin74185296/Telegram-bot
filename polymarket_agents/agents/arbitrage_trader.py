"""
Arbitrage Trader Agent
======================

Specializes in identifying and exploiting arbitrage opportunities.
Uses Claude Sonnet 4.5 for precise calculations.

Responsibilities:
- Detect YES + NO price deviations from 1.0
- Identify cross-market arbitrage opportunities
- Assess liquidity and execution feasibility
- Calculate risk-free profit potential
"""

from crewai import Agent
from langchain_anthropic import ChatAnthropic

from ..config import MODEL_CONFIG, get_config
from ..tools.market_data import (
    get_polymarket_data,
    get_orderbook,
    calculate_statistics,
)
from ..tools.trading import analyze_arbitrage_opportunity


def create_arbitrage_trader_agent() -> Agent:
    """
    Create the Arbitrage Trader agent.
    
    This agent focuses on:
    1. YES + NO price sum analysis
    2. Cross-market correlations and spreads
    3. Liquidity and slippage assessment
    4. Risk-free profit calculations
    """
    config = get_config()
    model_config = MODEL_CONFIG["arbitrage_trader"]
    
    # Initialize the LLM
    llm = ChatAnthropic(
        model=model_config["model"],
        temperature=model_config["temperature"],
        max_tokens=model_config["max_tokens"],
        anthropic_api_key=config.llm.anthropic_api_key,
    )
    
    arbitrage_trader = Agent(
        role="套利策略交易員 (Arbitrage Strategy Trader)",
        goal="""
        作為套利策略專家，你的目標是：
        1. 檢查 YES + NO 價格總和是否明顯偏離 1.0
        2. 識別相關市場之間的價差機會
        3. 評估流動性和滑點對套利的影響
        4. 計算預期無風險收益
        5. 輸出套利機會信號，附帶預期收益和風險評估
        
        你必須精確計算所有成本（滑點、手續費），確保套利是真正的「無風險」。
        """,
        backstory="""
        你是一位專注於市場微觀結構的量化交易員，擁有 7 年套利交易經驗。
        
        你的專長：
        - 價格發現：識別市場定價效率低下
        - 流動性分析：評估大額交易的執行可行性
        - 風險計算：精確估計滑點和執行風險
        - 跨市場分析：識別相關事件的價差
        
        你的交易哲學：
        - "真正的套利是無風險的"
        - "流動性是執行的關鍵"
        - "看似的套利機會可能隱藏風險"
        - "速度決定套利的成敗"
        
        你知道在 Polymarket 這樣的預測市場中，YES + NO 的價格理論上應該等於 1。
        當偏離超過交易成本時，就存在套利機會。
        
        你也關注相關事件的價差，例如：
        - "比特幣達到 10 萬" vs "比特幣達到 9 萬" 的價格關係
        - 同一事件在不同到期日的定價差異
        
        你非常謹慎，因為套利機會通常很小且稍縱即逝。
        你會仔細計算所有成本，只在真正有利可圖時才建議交易。
        
        在團隊辯論中，你提供的是「安全」選項 - 當其他策略不確定時，套利可能是更好的選擇。
        """,
        tools=[
            get_polymarket_data,
            get_orderbook,
            calculate_statistics,
            analyze_arbitrage_opportunity,
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        memory=True,
    )
    
    return arbitrage_trader


# Arbitrage analysis template
ARBITRAGE_ANALYSIS_TEMPLATE = """
## 套利分析報告

### 市場資訊
- 市場 ID: {market_id}
- YES 價格: {yes_price}
- NO 價格: {no_price}
- 價格總和: {price_sum}
- 偏離度: {deviation}%

### 套利機會分析
- **套利類型**: {arbitrage_type}
- **理論利潤/單位**: ${profit_per_unit}
- **預估滑點**: {estimated_slippage}%
- **淨利潤/單位**: ${net_profit_per_unit}
- **機會等級**: {opportunity_grade}

### 流動性評估
- **YES 側流動性**: ${yes_liquidity}
- **NO 側流動性**: ${no_liquidity}
- **最大可執行規模**: ${max_executable_size}
- **流動性評級**: {liquidity_grade}

### 執行建議
```json
{{
    "should_execute": {should_execute},
    "recommended_size": {recommended_size},
    "expected_profit": {expected_profit},
    "execution_strategy": "{execution_strategy}",
    "urgency": "{urgency}",
    "confidence": {confidence}
}}
```

### 風險分析
- **執行風險**: {execution_risk}
- **滑點風險**: {slippage_risk}
- **時效風險**: {timing_risk}
- **整體風險評級**: {overall_risk}

### 相關市場套利
{related_market_arbitrage}

### 辯論立場
{debate_position}
"""


def analyze_price_sum_arbitrage(yes_price: float, no_price: float) -> dict:
    """
    Analyze arbitrage opportunity from YES + NO price deviation.
    
    Args:
        yes_price: Current YES price
        no_price: Current NO price
    
    Returns:
        Arbitrage analysis dictionary
    """
    price_sum = yes_price + no_price
    deviation = abs(1.0 - price_sum)
    deviation_pct = deviation * 100
    
    # Determine arbitrage type
    if price_sum < 1.0:
        arb_type = "UNDERPRICED"
        action = "BUY_BOTH"
        profit_per_unit = 1.0 - price_sum
    elif price_sum > 1.0:
        arb_type = "OVERPRICED"
        action = "SELL_BOTH"
        profit_per_unit = price_sum - 1.0
    else:
        arb_type = "NONE"
        action = "NO_ACTION"
        profit_per_unit = 0
    
    # Estimate costs
    estimated_slippage = 0.02  # 2% estimated slippage
    platform_fee = 0.002  # 0.2% platform fee (if any)
    total_cost = estimated_slippage + platform_fee
    
    net_profit = profit_per_unit - total_cost
    
    # Determine if opportunity is actionable
    is_actionable = net_profit > 0.005  # Minimum 0.5% net profit
    
    return {
        "price_sum": round(price_sum, 4),
        "deviation": round(deviation, 4),
        "deviation_percent": round(deviation_pct, 2),
        "arbitrage_type": arb_type,
        "action": action,
        "gross_profit_per_unit": round(profit_per_unit, 4),
        "estimated_costs": round(total_cost, 4),
        "net_profit_per_unit": round(net_profit, 4),
        "is_actionable": is_actionable,
        "confidence": _calculate_arbitrage_confidence(deviation_pct, net_profit),
    }


def _calculate_arbitrage_confidence(deviation_pct: float, net_profit: float) -> int:
    """Calculate confidence score for arbitrage opportunity."""
    if net_profit <= 0:
        return 10
    elif net_profit < 0.01:
        return 30 + int(deviation_pct * 5)
    elif net_profit < 0.02:
        return 60 + int(deviation_pct * 3)
    else:
        return min(95, 80 + int(deviation_pct * 2))


def assess_liquidity_for_arbitrage(
    yes_bids: list,
    yes_asks: list,
    no_bids: list,
    no_asks: list,
    target_size: float = 100
) -> dict:
    """
    Assess if there's enough liquidity to execute arbitrage.
    
    Args:
        yes_bids: YES side bid levels
        yes_asks: YES side ask levels
        no_bids: NO side bid levels
        no_asks: NO side ask levels
        target_size: Desired trade size in shares
    
    Returns:
        Liquidity assessment dictionary
    """
    # Calculate available liquidity at each level
    yes_bid_liquidity = sum(level.get("size", 0) for level in yes_bids[:3])
    yes_ask_liquidity = sum(level.get("size", 0) for level in yes_asks[:3])
    no_bid_liquidity = sum(level.get("size", 0) for level in no_bids[:3])
    no_ask_liquidity = sum(level.get("size", 0) for level in no_asks[:3])
    
    # For buying both sides, we need ask liquidity
    buy_both_liquidity = min(yes_ask_liquidity, no_ask_liquidity)
    
    # For selling both sides, we need bid liquidity
    sell_both_liquidity = min(yes_bid_liquidity, no_bid_liquidity)
    
    max_executable = max(buy_both_liquidity, sell_both_liquidity)
    
    # Grade liquidity
    if max_executable >= target_size * 2:
        grade = "EXCELLENT"
    elif max_executable >= target_size:
        grade = "GOOD"
    elif max_executable >= target_size * 0.5:
        grade = "FAIR"
    else:
        grade = "POOR"
    
    return {
        "yes_bid_liquidity": yes_bid_liquidity,
        "yes_ask_liquidity": yes_ask_liquidity,
        "no_bid_liquidity": no_bid_liquidity,
        "no_ask_liquidity": no_ask_liquidity,
        "buy_both_capacity": buy_both_liquidity,
        "sell_both_capacity": sell_both_liquidity,
        "max_executable_size": max_executable,
        "liquidity_grade": grade,
        "execution_feasible": max_executable >= target_size * 0.5,
    }


def estimate_slippage(
    order_size: float,
    available_liquidity: float,
    spread: float
) -> float:
    """
    Estimate slippage for a given order size.
    
    Args:
        order_size: Size of the order
        available_liquidity: Available liquidity at best levels
        spread: Current bid-ask spread
    
    Returns:
        Estimated slippage as a decimal (0.02 = 2%)
    """
    # Base slippage is half the spread
    base_slippage = spread / 2
    
    # Additional slippage based on order size vs liquidity
    if available_liquidity == 0:
        size_impact = 0.1  # 10% if no liquidity
    else:
        fill_ratio = order_size / available_liquidity
        size_impact = fill_ratio * 0.05  # 5% impact at 100% of available liquidity
    
    total_slippage = base_slippage + size_impact
    
    return min(0.15, total_slippage)  # Cap at 15% slippage


def find_related_market_arbitrage(markets: list) -> list:
    """
    Find arbitrage opportunities between related markets.
    
    This would compare markets like:
    - "BTC > $100k by Dec 2024" vs "BTC > $90k by Dec 2024"
    - Same event at different timeframes
    
    Args:
        markets: List of market data dictionaries
    
    Returns:
        List of potential cross-market arbitrage opportunities
    """
    opportunities = []
    
    # This is a placeholder for real implementation
    # In production, this would:
    # 1. Identify related markets by question/category
    # 2. Check for logical price inconsistencies
    # 3. Calculate arbitrage potential
    
    # Example logic:
    # If "BTC > 100k" = 0.40 and "BTC > 90k" = 0.35, that's inconsistent
    # BTC > 100k should be <= BTC > 90k
    
    return opportunities
