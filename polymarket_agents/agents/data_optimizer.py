"""
Data & Optimizer Agent
======================

Specializes in data collection, analysis, and strategy optimization.
Uses Claude Sonnet 4.5 for comprehensive data processing.

Responsibilities:
- Collect and aggregate market data from multiple sources
- Gather news and social media sentiment
- Analyze historical performance of trading signals
- Suggest strategy parameter optimizations
- Update team knowledge base
"""

from crewai import Agent
from langchain_anthropic import ChatAnthropic

from ..config import MODEL_CONFIG, get_config
from ..tools.market_data import (
    get_polymarket_data,
    get_historical_prices,
    calculate_statistics,
)
from ..tools.sentiment import (
    search_x_sentiment,
    web_search_news,
    analyze_combined_sentiment,
)


def create_data_optimizer_agent() -> Agent:
    """
    Create the Data & Optimizer agent.
    
    This agent focuses on:
    1. Comprehensive data collection
    2. Sentiment analysis from multiple sources
    3. Historical performance analysis
    4. Strategy parameter optimization
    5. Team knowledge management
    """
    config = get_config()
    model_config = MODEL_CONFIG["data_optimizer"]
    
    # Initialize the LLM
    llm = ChatAnthropic(
        model=model_config["model"],
        temperature=model_config["temperature"],
        max_tokens=model_config["max_tokens"],
        anthropic_api_key=config.llm.anthropic_api_key,
    )
    
    data_optimizer = Agent(
        role="數據分析與策略優化師 (Data Analyst & Strategy Optimizer)",
        goal="""
        作為團隊的數據專家和策略優化師，你的目標是：
        1. 收集最新的市場數據、新聞和社交媒體輿情
        2. 整合多個數據源，提供全面的市場視角
        3. 分析過去交易信號的表現，識別成功和失敗模式
        4. 提出策略參數優化建議（如閾值調整、權重變化）
        5. 維護團隊知識庫，記錄哪些策略在什麼情況下表現最好
        
        你要為團隊提供數據驅動的洞察，幫助其他 agent 做出更好的決策。
        """,
        backstory="""
        你是一位數據科學家，擁有機器學習和量化金融背景，專注於預測市場分析 6 年。
        
        你的專長：
        - 數據工程：收集、清洗、整合多源數據
        - 輿情分析：NLP 分析新聞和社交媒體
        - 績效分析：回測、信號評估、風險歸因
        - 優化建議：參數調優、策略改進
        
        你的工作哲學：
        - "數據是決策的基礎"
        - "沒有衡量就沒有改進"
        - "過去的表現可以指導未來，但不能保證"
        - "保持客觀，讓數據說話"
        
        你是團隊的「情報官」，負責確保每個 agent 都有最新、最準確的資訊。
        你也是「績效教練」，追蹤每個策略的表現，提出改進建議。
        
        你特別擅長：
        - 識別數據中的模式和異常
        - 將複雜的分析結果轉化為可行動的建議
        - 發現策略之間的互補性和衝突
        
        在辯論中，你提供客觀的數據支持，不偏向任何特定策略，
        但會指出數據顯示的最佳行動方案。
        """,
        tools=[
            get_polymarket_data,
            get_historical_prices,
            calculate_statistics,
            search_x_sentiment,
            web_search_news,
            analyze_combined_sentiment,
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        memory=True,
    )
    
    return data_optimizer


# Data collection and analysis template
DATA_ANALYSIS_TEMPLATE = """
## 數據分析與優化報告

### 1. 市場數據摘要
- 市場 ID: {market_id}
- 市場問題: {market_question}
- 當前 YES 價格: {yes_price}
- 當前 NO 價格: {no_price}
- 24小時成交量: ${volume_24h}
- 總流動性: ${total_liquidity}

### 2. 新聞與輿情分析
#### 新聞摘要
{news_summary}

#### 社交媒體輿情
- X/Twitter 情緒分數: {x_sentiment} (-1 到 1)
- 情緒標籤: {sentiment_label}
- 關鍵話題: {key_topics}
- 影響力人士觀點: {influencer_views}

#### 綜合輿情評估
{combined_sentiment_assessment}

### 3. 歷史表現分析
#### 價格走勢
{price_trend_analysis}

#### 成交量模式
{volume_pattern_analysis}

#### 波動性分析
{volatility_analysis}

### 4. 策略表現回顧
| 策略 | 過去信號 | 準確率 | 平均收益 | 建議權重 |
|------|----------|--------|----------|----------|
| 動量 | {momentum_signals} | {momentum_accuracy}% | {momentum_return}% | {momentum_weight} |
| 均值回歸 | {reversion_signals} | {reversion_accuracy}% | {reversion_return}% | {reversion_weight} |
| 套利 | {arbitrage_signals} | {arbitrage_accuracy}% | {arbitrage_return}% | {arbitrage_weight} |

### 5. 優化建議
```json
{{
    "parameter_adjustments": [
        {parameter_adjustments}
    ],
    "strategy_recommendations": [
        {strategy_recommendations}
    ],
    "data_quality_issues": [
        {data_quality_issues}
    ],
    "confidence": {optimization_confidence}
}}
```

### 6. 團隊知識更新
{knowledge_updates}

### 7. 綜合建議
{overall_recommendation}
"""


# Strategy performance tracking
class StrategyPerformanceTracker:
    """Track and analyze strategy performance over time."""
    
    def __init__(self):
        self.signals_history = {
            "momentum": [],
            "mean_reversion": [],
            "arbitrage": [],
        }
        self.performance_metrics = {
            "momentum": {"wins": 0, "losses": 0, "total_return": 0.0},
            "mean_reversion": {"wins": 0, "losses": 0, "total_return": 0.0},
            "arbitrage": {"wins": 0, "losses": 0, "total_return": 0.0},
        }
    
    def record_signal(
        self,
        strategy: str,
        signal: str,
        confidence: float,
        market_id: str,
        price_at_signal: float
    ):
        """Record a trading signal for later analysis."""
        self.signals_history[strategy].append({
            "signal": signal,
            "confidence": confidence,
            "market_id": market_id,
            "price_at_signal": price_at_signal,
            "timestamp": None,  # Would use datetime.now() in production
            "outcome": None,  # To be updated when resolved
        })
    
    def update_outcome(
        self,
        strategy: str,
        signal_index: int,
        outcome_price: float
    ):
        """Update the outcome of a previous signal."""
        if signal_index < len(self.signals_history[strategy]):
            signal = self.signals_history[strategy][signal_index]
            initial_price = signal["price_at_signal"]
            
            # Calculate return based on signal direction
            if signal["signal"] == "BUY":
                ret = (outcome_price - initial_price) / initial_price
            elif signal["signal"] == "SELL":
                ret = (initial_price - outcome_price) / initial_price
            else:
                ret = 0
            
            signal["outcome"] = {
                "price": outcome_price,
                "return": ret,
                "is_win": ret > 0,
            }
            
            # Update metrics
            if ret > 0:
                self.performance_metrics[strategy]["wins"] += 1
            else:
                self.performance_metrics[strategy]["losses"] += 1
            self.performance_metrics[strategy]["total_return"] += ret
    
    def get_strategy_stats(self, strategy: str) -> dict:
        """Get performance statistics for a strategy."""
        metrics = self.performance_metrics[strategy]
        total = metrics["wins"] + metrics["losses"]
        
        return {
            "total_signals": total,
            "wins": metrics["wins"],
            "losses": metrics["losses"],
            "win_rate": metrics["wins"] / total * 100 if total > 0 else 0,
            "total_return": round(metrics["total_return"] * 100, 2),
            "avg_return": round(metrics["total_return"] / total * 100, 2) if total > 0 else 0,
        }
    
    def recommend_weight_adjustment(self) -> dict:
        """Recommend weight adjustments based on performance."""
        stats = {
            "momentum": self.get_strategy_stats("momentum"),
            "mean_reversion": self.get_strategy_stats("mean_reversion"),
            "arbitrage": self.get_strategy_stats("arbitrage"),
        }
        
        # Calculate recommended weights based on win rate and return
        total_score = 0
        scores = {}
        
        for strategy, s in stats.items():
            # Score = win_rate * 0.5 + (avg_return + 50) * 0.5
            # This balances win rate with return magnitude
            score = s["win_rate"] * 0.5 + (s["avg_return"] + 50) * 0.5
            scores[strategy] = max(0, score)
            total_score += scores[strategy]
        
        # Normalize to weights summing to 1
        if total_score > 0:
            weights = {k: round(v / total_score, 2) for k, v in scores.items()}
        else:
            weights = {"momentum": 0.33, "mean_reversion": 0.33, "arbitrage": 0.34}
        
        return {
            "current_stats": stats,
            "recommended_weights": weights,
            "adjustment_reason": self._generate_adjustment_reason(stats, weights),
        }
    
    def _generate_adjustment_reason(self, stats: dict, weights: dict) -> str:
        """Generate explanation for weight adjustment."""
        best_strategy = max(weights, key=weights.get)
        worst_strategy = min(weights, key=weights.get)
        
        reasons = []
        
        if stats[best_strategy]["win_rate"] > 60:
            reasons.append(f"{best_strategy} 策略表現最佳（勝率 {stats[best_strategy]['win_rate']:.1f}%），建議增加權重")
        
        if stats[worst_strategy]["win_rate"] < 40 and stats[worst_strategy]["total_signals"] > 5:
            reasons.append(f"{worst_strategy} 策略表現較差（勝率 {stats[worst_strategy]['win_rate']:.1f}%），建議降低權重")
        
        if not reasons:
            reasons.append("各策略表現相近，維持均衡權重")
        
        return "; ".join(reasons)


# Global performance tracker instance
performance_tracker = StrategyPerformanceTracker()


def generate_optimization_suggestions(
    market_conditions: str,
    recent_performance: dict,
    current_params: dict
) -> list:
    """
    Generate strategy optimization suggestions.
    
    Args:
        market_conditions: Description of current market conditions
        recent_performance: Recent performance metrics by strategy
        current_params: Current strategy parameters
    
    Returns:
        List of optimization suggestions
    """
    suggestions = []
    
    # Check momentum strategy
    if recent_performance.get("momentum", {}).get("win_rate", 50) < 40:
        suggestions.append({
            "strategy": "momentum",
            "parameter": "trend_threshold",
            "current_value": current_params.get("momentum_threshold", 0.02),
            "suggested_value": 0.03,
            "reason": "勝率偏低，建議提高趨勢確認閾值以減少假信號",
        })
    
    # Check mean reversion strategy
    if recent_performance.get("mean_reversion", {}).get("avg_holding_days", 5) > 7:
        suggestions.append({
            "strategy": "mean_reversion",
            "parameter": "z_score_threshold",
            "current_value": current_params.get("z_score_threshold", 2.0),
            "suggested_value": 2.5,
            "reason": "持倉時間過長，建議提高 z-score 閾值以選擇更極端的機會",
        })
    
    # Check arbitrage strategy
    if recent_performance.get("arbitrage", {}).get("slippage_cost", 0.01) > 0.015:
        suggestions.append({
            "strategy": "arbitrage",
            "parameter": "min_profit_threshold",
            "current_value": current_params.get("min_arb_profit", 0.02),
            "suggested_value": 0.025,
            "reason": "滑點成本高於預期，建議提高最低套利利潤閾值",
        })
    
    # General suggestions based on market conditions
    if "高波動" in market_conditions or "high volatility" in market_conditions.lower():
        suggestions.append({
            "strategy": "all",
            "parameter": "position_size_multiplier",
            "current_value": 1.0,
            "suggested_value": 0.8,
            "reason": "市場波動性高，建議降低倉位規模以控制風險",
        })
    
    return suggestions


def aggregate_market_intelligence(
    market_data: dict,
    sentiment_data: dict,
    news_data: dict
) -> dict:
    """
    Aggregate intelligence from multiple data sources.
    
    Returns:
        Comprehensive market intelligence summary
    """
    # Extract key metrics
    price_momentum = market_data.get("price_change_24h", 0)
    volume_trend = market_data.get("volume_change_24h", 0)
    social_sentiment = sentiment_data.get("overall_sentiment", 0)
    news_sentiment = news_data.get("average_sentiment", 0)
    
    # Calculate composite scores
    sentiment_score = (social_sentiment * 0.4 + news_sentiment * 0.6)
    momentum_score = (price_momentum * 50 + 50)  # Normalize to 0-100
    
    # Determine market regime
    if price_momentum > 0.03 and volume_trend > 0.1:
        regime = "STRONG_UPTREND"
    elif price_momentum < -0.03 and volume_trend > 0.1:
        regime = "STRONG_DOWNTREND"
    elif abs(price_momentum) < 0.01:
        regime = "CONSOLIDATION"
    else:
        regime = "MIXED"
    
    # Generate actionable insights
    insights = []
    
    if sentiment_score > 0.3 and price_momentum < 0:
        insights.append("情緒與價格背離 - 潛在反轉機會")
    
    if volume_trend > 0.2:
        insights.append("成交量顯著增加 - 市場活躍度提升")
    
    if abs(social_sentiment - news_sentiment) > 0.3:
        insights.append("社交媒體與新聞情緒分歧 - 建議謹慎")
    
    return {
        "market_regime": regime,
        "composite_sentiment": round(sentiment_score, 3),
        "momentum_score": round(momentum_score, 1),
        "key_insights": insights,
        "recommended_strategy_bias": _determine_strategy_bias(regime, sentiment_score),
        "confidence_level": _calculate_intelligence_confidence(
            len(insights), 
            abs(social_sentiment - news_sentiment)
        ),
    }


def _determine_strategy_bias(regime: str, sentiment: float) -> str:
    """Determine which strategy should be favored given market conditions."""
    if regime == "STRONG_UPTREND":
        return "MOMENTUM_LONG"
    elif regime == "STRONG_DOWNTREND":
        return "MOMENTUM_SHORT"
    elif regime == "CONSOLIDATION":
        if abs(sentiment) > 0.3:
            return "MEAN_REVERSION"
        else:
            return "ARBITRAGE"
    else:
        return "BALANCED"


def _calculate_intelligence_confidence(insight_count: int, sentiment_divergence: float) -> str:
    """Calculate confidence in the aggregated intelligence."""
    if insight_count >= 3 and sentiment_divergence < 0.2:
        return "HIGH"
    elif insight_count >= 2 or sentiment_divergence < 0.3:
        return "MEDIUM"
    else:
        return "LOW"
