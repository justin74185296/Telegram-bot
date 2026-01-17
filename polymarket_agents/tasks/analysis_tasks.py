"""
Analysis Tasks
==============

Tasks for market analysis by each specialized agent.
"""

from crewai import Task, Agent
from typing import Optional


def create_data_collection_task(
    data_optimizer_agent: Agent,
    market_id: str,
    market_question: str,
) -> Task:
    """
    Create the data collection and initial analysis task.
    
    This task runs first to gather all relevant data for the team.
    """
    return Task(
        description=f"""
        ## 數據收集與初步分析任務

        ### 目標市場
        - 市場 ID: {market_id}
        - 市場問題: {market_question}

        ### 你的任務
        1. **收集市場數據**
           - 使用 get_polymarket_data 工具獲取當前價格、成交量等數據
           - 使用 get_historical_prices 工具獲取 30 天歷史價格
           - 使用 calculate_statistics 工具計算統計指標

        2. **收集輿情數據**
           - 使用 search_x_sentiment 工具搜索相關的 X/Twitter 輿情
           - 使用 web_search_news 工具搜索相關新聞
           - 使用 analyze_combined_sentiment 整合輿情分析

        3. **整理數據報告**
           - 整合所有數據來源
           - 標記數據質量和可靠性
           - 提供初步的市場情況評估

        ### 輸出格式
        請以 JSON 格式輸出你的分析結果：
        ```json
        {{
            "market_id": "{market_id}",
            "timestamp": "ISO格式時間",
            "market_data": {{
                "yes_price": 數字,
                "no_price": 數字,
                "price_change_24h": 數字,
                "volume_24h": 數字,
                "liquidity": 數字
            }},
            "statistics": {{
                "mean_30d": 數字,
                "std_dev": 數字,
                "z_score": 數字,
                "trend_direction": "BULLISH/BEARISH/NEUTRAL"
            }},
            "sentiment": {{
                "social_sentiment": 數字 (-1 到 1),
                "news_sentiment": 數字 (-1 到 1),
                "combined_sentiment": 數字,
                "sentiment_label": "標籤"
            }},
            "key_news": ["新聞1", "新聞2"],
            "initial_assessment": "你的初步評估",
            "data_quality": "HIGH/MEDIUM/LOW",
            "confidence": 數字 (0-100)
        }}
        ```

        請確保數據準確完整，這將作為團隊後續分析的基礎。
        """,
        expected_output="""
        一個完整的 JSON 格式數據報告，包含市場數據、統計指標、輿情分析和初步評估。
        """,
        agent=data_optimizer_agent,
    )


def create_momentum_analysis_task(
    momentum_agent: Agent,
    market_id: str,
    context_tasks: Optional[list] = None,
) -> Task:
    """
    Create the momentum analysis task.
    
    This task analyzes price trends and momentum indicators.
    """
    return Task(
        description=f"""
        ## 動量分析任務

        ### 目標市場
        - 市場 ID: {market_id}

        ### 你的任務
        作為動量策略交易員，請分析以下內容：

        1. **趨勢識別**
           - 分析短期趨勢（7日）和中期趨勢（21日）
           - 判斷趨勢強度和持續性
           - 識別趨勢轉折信號

        2. **動量指標計算**
           - 計算價格變化率 (ROC)
           - 分析價格加速度
           - 評估動量是否在增強或減弱

        3. **成交量確認**
           - 分析成交量變化是否確認價格趨勢
           - 識別量價背離信號

        4. **生成交易信號**
           - 基於你的分析，給出買/賣/持有建議
           - 提供 0-100 的信心分數
           - 詳細解釋你的理由

        ### 輸出格式
        請以 JSON 格式輸出你的分析：
        ```json
        {{
            "agent": "momentum_trader",
            "market_id": "{market_id}",
            "analysis": {{
                "short_term_trend": "BULLISH/BEARISH/NEUTRAL",
                "medium_term_trend": "BULLISH/BEARISH/NEUTRAL",
                "trend_strength": 數字 (1-10),
                "momentum_score": 數字 (0-100),
                "volume_confirmation": true/false
            }},
            "signal": {{
                "action": "BUY_YES/BUY_NO/SELL_YES/SELL_NO/HOLD/WAIT",
                "confidence": 數字 (0-100),
                "entry_price": 數字,
                "target_price": 數字,
                "stop_loss": 數字,
                "time_horizon": "SHORT/MEDIUM/LONG"
            }},
            "rationale": "詳細解釋你的分析邏輯和交易理由",
            "risk_factors": ["風險1", "風險2"],
            "debate_position": "你在辯論中要捍衛的立場摘要"
        }}
        ```

        記住：你需要在接下來的辯論中捍衛你的觀點，所以請準備好數據支持。
        """,
        expected_output="""
        一個完整的 JSON 格式動量分析報告，包含趨勢分析、動量指標、交易信號和辯論立場。
        """,
        agent=momentum_agent,
        context=context_tasks or [],
    )


def create_mean_reversion_analysis_task(
    mean_reversion_agent: Agent,
    market_id: str,
    context_tasks: Optional[list] = None,
) -> Task:
    """
    Create the mean reversion analysis task.
    
    This task analyzes statistical deviations and reversion opportunities.
    """
    return Task(
        description=f"""
        ## 均值回歸分析任務

        ### 目標市場
        - 市場 ID: {market_id}

        ### 你的任務
        作為均值回歸策略交易員，請分析以下內容：

        1. **統計分析**
           - 計算價格的 30 日均值和標準差
           - 計算當前價格的 z-score
           - 分析價格在歷史範圍中的位置

        2. **超買/超賣判斷**
           - z-score > 2.0 表示超買
           - z-score < -2.0 表示超賣
           - 評估回歸的可能性和幅度

        3. **回歸預期**
           - 預估回歸目標價格
           - 評估回歸所需時間
           - 計算風險回報比

        4. **生成交易信號**
           - 如果超買，建議做空/賣出
           - 如果超賣，建議做多/買入
           - 提供 0-100 的信心分數
           - 用統計數據支持你的建議

        ### 輸出格式
        請以 JSON 格式輸出你的分析：
        ```json
        {{
            "agent": "mean_reversion_trader",
            "market_id": "{market_id}",
            "analysis": {{
                "mean_30d": 數字,
                "std_dev_30d": 數字,
                "current_z_score": 數字,
                "percentile_rank": 數字 (0-100),
                "overbought_oversold": "OVERBOUGHT/OVERSOLD/NEUTRAL",
                "reversion_potential": "HIGH/MEDIUM/LOW"
            }},
            "signal": {{
                "action": "BUY_YES/BUY_NO/SELL_YES/SELL_NO/HOLD/WAIT",
                "confidence": 數字 (0-100),
                "entry_price": 數字,
                "target_price": 數字,
                "stop_loss": 數字,
                "expected_holding_period": "天數"
            }},
            "statistical_evidence": {{
                "z_score_interpretation": "解釋",
                "historical_reversion_rate": "歷史上類似情況的回歸概率",
                "confidence_interval": "95% 置信區間"
            }},
            "rationale": "詳細解釋你的統計分析和交易理由",
            "risk_factors": ["風險1", "風險2"],
            "debate_position": "你在辯論中要捍衛的立場摘要"
        }}
        ```

        注意：你的觀點可能與動量交易員相反，這是正常的。請準備好在辯論中用數據捍衛你的立場。
        """,
        expected_output="""
        一個完整的 JSON 格式均值回歸分析報告，包含統計分析、超買超賣判斷、交易信號和辯論立場。
        """,
        agent=mean_reversion_agent,
        context=context_tasks or [],
    )


def create_arbitrage_analysis_task(
    arbitrage_agent: Agent,
    market_id: str,
    context_tasks: Optional[list] = None,
) -> Task:
    """
    Create the arbitrage analysis task.
    
    This task analyzes arbitrage opportunities.
    """
    return Task(
        description=f"""
        ## 套利分析任務

        ### 目標市場
        - 市場 ID: {market_id}

        ### 你的任務
        作為套利策略交易員，請分析以下內容：

        1. **價格一致性分析**
           - 檢查 YES + NO 價格是否等於 1.0
           - 計算偏離度和潛在套利空間
           - 評估這個偏離是否足以覆蓋交易成本

        2. **流動性評估**
           - 使用 get_orderbook 分析買賣盤深度
           - 評估執行大額交易的可行性
           - 估算滑點成本

        3. **套利機會計算**
           - 計算理論利潤
           - 扣除預估滑點和手續費
           - 計算淨套利收益

        4. **生成套利建議**
           - 如果有套利機會，詳細說明執行策略
           - 如果沒有，說明原因
           - 提供風險評估

        ### 輸出格式
        請以 JSON 格式輸出你的分析：
        ```json
        {{
            "agent": "arbitrage_trader",
            "market_id": "{market_id}",
            "price_analysis": {{
                "yes_price": 數字,
                "no_price": 數字,
                "price_sum": 數字,
                "deviation_from_unity": 數字,
                "deviation_percent": 數字
            }},
            "arbitrage_opportunity": {{
                "exists": true/false,
                "type": "UNDERPRICED/OVERPRICED/NONE",
                "gross_profit_per_unit": 數字,
                "estimated_slippage": 數字,
                "estimated_fees": 數字,
                "net_profit_per_unit": 數字
            }},
            "liquidity_assessment": {{
                "yes_side_liquidity": 數字,
                "no_side_liquidity": 數字,
                "max_executable_size": 數字,
                "liquidity_grade": "EXCELLENT/GOOD/FAIR/POOR"
            }},
            "signal": {{
                "action": "EXECUTE_ARBITRAGE/NO_OPPORTUNITY/WAIT",
                "confidence": 數字 (0-100),
                "recommended_size": 數字,
                "expected_profit": 數字,
                "execution_strategy": "說明"
            }},
            "rationale": "詳細解釋你的分析",
            "risk_factors": ["風險1", "風險2"],
            "debate_position": "你在辯論中要捍衛的立場摘要"
        }}
        ```

        套利應該是「近乎無風險」的，如果風險較高，請明確指出。
        """,
        expected_output="""
        一個完整的 JSON 格式套利分析報告，包含價格分析、套利機會評估、流動性分析和執行建議。
        """,
        agent=arbitrage_agent,
        context=context_tasks or [],
    )
