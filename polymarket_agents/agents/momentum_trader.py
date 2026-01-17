"""
Momentum Trader Agent
=====================

Specializes in detecting and trading price trends and momentum.
Uses Claude Sonnet 4.5 for cost-effective analysis.

Responsibilities:
- Detect price trends (upward/downward momentum)
- Analyze volume changes and patterns
- Identify breakout opportunities
- Generate momentum-based trading signals
"""

from crewai import Agent
from langchain_anthropic import ChatAnthropic

from ..config import MODEL_CONFIG, get_config
from ..tools.market_data import (
    get_polymarket_data,
    get_historical_prices,
    calculate_statistics,
)
from ..tools.sentiment import search_x_sentiment


def create_momentum_trader_agent() -> Agent:
    """
    Create the Momentum Trader agent.
    
    This agent focuses on:
    1. Price trend detection (short-term and medium-term)
    2. Volume analysis and confirmation
    3. Momentum indicators (rate of change, acceleration)
    4. Breakout identification
    """
    config = get_config()
    model_config = MODEL_CONFIG["momentum_trader"]
    
    # Initialize the LLM
    llm = ChatAnthropic(
        model=model_config["model"],
        temperature=model_config["temperature"],
        max_tokens=model_config["max_tokens"],
        anthropic_api_key=config.llm.anthropic_api_key,
    )
    
    momentum_trader = Agent(
        role="動量策略交易員 (Momentum Strategy Trader)",
        goal="""
        作為動量策略專家，你的目標是：
        1. 識別價格趨勢和動能方向（上漲或下跌）
        2. 分析成交量變化是否確認趨勢
        3. 計算動量指標（價格變化率、加速度）
        4. 偵測突破機會和趨勢延續信號
        5. 輸出清晰的買/賣信號，附帶信心分數（0-100）和詳細理由
        
        你必須在辯論中清楚解釋你的分析依據，並願意根據新證據調整觀點。
        """,
        backstory="""
        你是一位專注於動量交易的量化分析師，在預測市場有 8 年經驗。
        
        你的專長：
        - 趨勢識別：使用移動平均線交叉、價格通道等技術
        - 動量計算：ROC (Rate of Change)、價格加速度分析
        - 成交量分析：量價關係確認趨勢強度
        - 突破交易：識別關鍵價位的突破
        
        你的交易風格：
        - "趨勢是你的朋友"
        - "量增價漲是最強的多頭信號"
        - "不追高，等待回調進場"
        - "設定嚴格的止損位"
        
        你相信市場有慣性，上漲的市場傾向繼續上漲，下跌的市場傾向繼續下跌。
        但你也知道動量會耗盡，因此會密切關注趨勢衰減的信號。
        
        在團隊辯論中，你會用數據支持你的觀點，但也尊重其他策略的視角。
        """,
        tools=[
            get_polymarket_data,
            get_historical_prices,
            calculate_statistics,
            search_x_sentiment,
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        memory=True,
    )
    
    return momentum_trader


# Momentum analysis template for structured output
MOMENTUM_ANALYSIS_TEMPLATE = """
## 動量分析報告

### 市場資訊
- 市場 ID: {market_id}
- 當前 YES 價格: {yes_price}
- 當前 NO 價格: {no_price}

### 趨勢分析
- **短期趨勢 (7日)**: {short_term_trend}
- **中期趨勢 (21日)**: {medium_term_trend}
- **趨勢強度**: {trend_strength}/10
- **趨勢持續天數**: {trend_duration} 天

### 動量指標
- **7日價格變化率 (ROC)**: {roc_7d}%
- **價格加速度**: {acceleration}
- **動量評分**: {momentum_score}/100

### 成交量分析
- **24小時成交量**: ${volume_24h}
- **成交量變化**: {volume_change}%
- **量價關係**: {volume_price_relationship}

### 交易信號
```json
{{
    "signal": "{signal}",
    "confidence": {confidence},
    "entry_price": {entry_price},
    "target_price": {target_price},
    "stop_loss": {stop_loss},
    "time_horizon": "{time_horizon}",
    "rationale": "{rationale}"
}}
```

### 風險因素
{risk_factors}

### 辯論立場
{debate_position}
"""


def calculate_momentum_score(
    price_change_7d: float,
    price_change_21d: float,
    volume_change: float,
    trend_consistency: float
) -> float:
    """
    Calculate a composite momentum score (0-100).
    
    Args:
        price_change_7d: 7-day price change percentage
        price_change_21d: 21-day price change percentage
        volume_change: Volume change percentage
        trend_consistency: Consistency of trend (0-1)
    
    Returns:
        Momentum score from 0-100
    """
    # Normalize components to 0-25 scale
    price_7d_score = min(25, max(0, price_change_7d * 100 + 12.5))
    price_21d_score = min(25, max(0, price_change_21d * 50 + 12.5))
    volume_score = min(25, max(0, volume_change * 25 + 12.5))
    consistency_score = trend_consistency * 25
    
    return price_7d_score + price_21d_score + volume_score + consistency_score


def identify_trend_direction(
    short_term_mean: float,
    long_term_mean: float,
    current_price: float
) -> str:
    """
    Identify trend direction based on moving averages.
    
    Returns:
        "BULLISH", "BEARISH", or "NEUTRAL"
    """
    if current_price > short_term_mean > long_term_mean:
        return "BULLISH"
    elif current_price < short_term_mean < long_term_mean:
        return "BEARISH"
    else:
        return "NEUTRAL"


def assess_momentum_strength(
    roc_7d: float,
    roc_21d: float,
    volume_ratio: float
) -> tuple:
    """
    Assess momentum strength and direction.
    
    Returns:
        Tuple of (strength: str, score: int, description: str)
    """
    # Calculate momentum score
    momentum = (roc_7d * 0.6 + roc_21d * 0.4) * volume_ratio
    
    if momentum > 0.05:
        return ("STRONG_BULLISH", 85, "強勁上漲動能，成交量確認")
    elif momentum > 0.02:
        return ("MODERATE_BULLISH", 70, "溫和上漲動能")
    elif momentum > -0.02:
        return ("NEUTRAL", 50, "動能不明確，觀望為主")
    elif momentum > -0.05:
        return ("MODERATE_BEARISH", 30, "溫和下跌動能")
    else:
        return ("STRONG_BEARISH", 15, "強勁下跌動能")
