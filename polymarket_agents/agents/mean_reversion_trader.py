"""
Mean Reversion Trader Agent
===========================

Specializes in identifying overbought/oversold conditions and mean reversion opportunities.
Uses Claude Sonnet 4.5 for statistical analysis.

Responsibilities:
- Calculate statistical deviations from historical averages
- Identify overbought/oversold conditions using z-scores
- Detect price extremes likely to revert
- Generate contrarian trading signals
"""

from crewai import Agent
from langchain_anthropic import ChatAnthropic

from ..config import MODEL_CONFIG, get_config
from ..tools.market_data import (
    get_polymarket_data,
    get_historical_prices,
    calculate_statistics,
)


def create_mean_reversion_trader_agent() -> Agent:
    """
    Create the Mean Reversion Trader agent.
    
    This agent focuses on:
    1. Statistical analysis of price deviations
    2. Z-score calculations for overbought/oversold detection
    3. Historical range analysis
    4. Contrarian signal generation
    """
    config = get_config()
    model_config = MODEL_CONFIG["mean_reversion_trader"]
    
    # Initialize the LLM
    llm = ChatAnthropic(
        model=model_config["model"],
        temperature=model_config["temperature"],
        max_tokens=model_config["max_tokens"],
        anthropic_api_key=config.llm.anthropic_api_key,
    )
    
    mean_reversion_trader = Agent(
        role="均值回歸策略交易員 (Mean Reversion Strategy Trader)",
        goal="""
        作為均值回歸策略專家，你的目標是：
        1. 計算價格相對於歷史平均的偏離程度（z-score）
        2. 識別超買（overbought）和超賣（oversold）狀態
        3. 分析價格是否處於歷史極端區域
        4. 預測價格回歸均值的概率和幅度
        5. 輸出反向交易信號，附帶信心分數（0-100）和統計依據
        
        你必須用嚴謹的統計數據支持你的觀點，並在辯論中清楚解釋你的邏輯。
        """,
        backstory="""
        你是一位統計學博士，專注於金融市場的均值回歸現象研究已有 10 年。
        
        你的專長：
        - 統計分析：z-score、標準差、置信區間計算
        - 歷史模式識別：價格範圍、分布特徵
        - 極端值檢測：識別統計異常
        - 時間序列分析：自相關、均值回歸速度
        
        你的交易哲學：
        - "萬物終將回歸平均"
        - "在別人恐懼時貪婪，在別人貪婪時恐懼"
        - "極端總是短暫的"
        - "統計優勢是長期獲利的關鍵"
        
        你相信市場經常過度反應，價格會偏離其「公平價值」，
        但最終會回歸到合理水平。你的策略就是捕捉這種回歸過程。
        
        你知道均值回歸不是立即發生的，需要耐心等待。
        你也明白有時候「趨勢」會持續很長時間，所以你會設定嚴格的止損。
        
        在團隊辯論中，你常常與動量交易員持相反觀點，但你尊重數據和邏輯。
        """,
        tools=[
            get_polymarket_data,
            get_historical_prices,
            calculate_statistics,
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        memory=True,
    )
    
    return mean_reversion_trader


# Mean reversion analysis template
MEAN_REVERSION_ANALYSIS_TEMPLATE = """
## 均值回歸分析報告

### 市場資訊
- 市場 ID: {market_id}
- 當前 YES 價格: {yes_price}
- 當前 NO 價格: {no_price}

### 統計分析
- **30日均價**: {mean_30d}
- **30日標準差**: {std_30d}
- **當前 Z-Score**: {z_score}
- **歷史最高價**: {max_30d}
- **歷史最低價**: {min_30d}
- **當前百分位排名**: {percentile_rank}%

### 超買/超賣狀態
- **狀態判定**: {overbought_oversold_status}
- **偏離均值幅度**: {deviation_from_mean}
- **預期回歸幅度**: {expected_reversion}
- **回歸概率**: {reversion_probability}%

### 交易信號
```json
{{
    "signal": "{signal}",
    "confidence": {confidence},
    "entry_price": {entry_price},
    "target_price": {target_price},
    "stop_loss": {stop_loss},
    "expected_holding_period": "{holding_period}",
    "statistical_edge": "{statistical_edge}",
    "rationale": "{rationale}"
}}
```

### 統計依據
- Z-Score 解讀: {z_score_interpretation}
- 歷史回歸案例: {historical_reversion_cases}
- 置信水平: {confidence_level}%

### 風險因素
{risk_factors}

### 辯論立場
{debate_position}
"""


def calculate_z_score(current_price: float, mean: float, std_dev: float) -> float:
    """
    Calculate z-score for current price.
    
    Args:
        current_price: Current market price
        mean: Historical mean price
        std_dev: Historical standard deviation
    
    Returns:
        Z-score (number of standard deviations from mean)
    """
    if std_dev == 0:
        return 0.0
    return (current_price - mean) / std_dev


def interpret_z_score(z_score: float) -> dict:
    """
    Interpret z-score and provide trading guidance.
    
    Returns:
        Dictionary with interpretation and recommendation
    """
    abs_z = abs(z_score)
    
    if abs_z >= 3.0:
        level = "EXTREME"
        confidence = 90
        description = "極端偏離（3個標準差以上），強烈回歸預期"
    elif abs_z >= 2.0:
        level = "HIGH"
        confidence = 75
        description = "顯著偏離（2-3個標準差），高回歸概率"
    elif abs_z >= 1.5:
        level = "MODERATE"
        confidence = 60
        description = "中度偏離（1.5-2個標準差），回歸可能"
    elif abs_z >= 1.0:
        level = "LOW"
        confidence = 45
        description = "輕度偏離（1-1.5個標準差），觀望為主"
    else:
        level = "NORMAL"
        confidence = 30
        description = "正常範圍內，無明顯回歸機會"
    
    direction = "SELL" if z_score > 0 else "BUY" if z_score < 0 else "HOLD"
    
    return {
        "level": level,
        "confidence": confidence,
        "description": description,
        "direction": direction,
        "z_score": round(z_score, 3),
    }


def calculate_reversion_target(
    current_price: float,
    mean: float,
    z_score: float,
    reversion_factor: float = 0.5
) -> float:
    """
    Calculate expected reversion target price.
    
    Args:
        current_price: Current market price
        mean: Historical mean
        z_score: Current z-score
        reversion_factor: How much reversion to expect (0-1)
    
    Returns:
        Expected target price after reversion
    """
    # Expect partial reversion to mean
    deviation = current_price - mean
    expected_reversion = deviation * reversion_factor
    return current_price - expected_reversion


def assess_mean_reversion_opportunity(
    z_score: float,
    volume_ratio: float,
    trend_strength: float
) -> dict:
    """
    Assess the quality of a mean reversion opportunity.
    
    Args:
        z_score: Current z-score
        volume_ratio: Recent volume vs average (>1 = higher volume)
        trend_strength: Strength of current trend (0-1)
    
    Returns:
        Assessment dictionary
    """
    # Higher z-score = better opportunity
    # Lower trend strength = better for reversion
    # Moderate volume = better execution
    
    opportunity_score = abs(z_score) * 20  # Base score from z-score
    
    # Adjust for trend (strong trend = harder reversion)
    trend_penalty = trend_strength * 15
    opportunity_score -= trend_penalty
    
    # Adjust for volume (too high or too low is bad)
    if 0.8 <= volume_ratio <= 1.5:
        volume_bonus = 10
    elif volume_ratio > 2.0:
        volume_bonus = -5  # Might be news-driven, harder to revert
    else:
        volume_bonus = 0
    
    opportunity_score += volume_bonus
    opportunity_score = max(0, min(100, opportunity_score))
    
    return {
        "opportunity_score": round(opportunity_score, 1),
        "quality": "HIGH" if opportunity_score >= 70 else "MEDIUM" if opportunity_score >= 50 else "LOW",
        "recommendation": _generate_reversion_recommendation(opportunity_score, z_score),
    }


def _generate_reversion_recommendation(score: float, z_score: float) -> str:
    """Generate trading recommendation based on reversion analysis."""
    if score >= 70:
        direction = "買入 YES" if z_score < -2 else "賣出/做空 YES" if z_score > 2 else "觀望"
        return f"強烈回歸機會 - 建議{direction}"
    elif score >= 50:
        return "中等回歸機會 - 可小倉位參與，設定嚴格止損"
    elif score >= 30:
        return "弱回歸機會 - 建議觀望或等待更好入場點"
    else:
        return "不建議交易 - 回歸信號不足"
