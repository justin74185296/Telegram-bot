"""
Decision Tasks
==============

Tasks for final decision making and human consultation.
"""

from crewai import Task, Agent
from typing import Optional


def create_final_decision_task(
    supervisor_agent: Agent,
    market_id: str,
    market_question: str,
    all_analyses: str,
    debate_summary: str,
    portfolio_status: str,
) -> Task:
    """
    Create the final decision task for the supervisor.
    
    The supervisor synthesizes all information and makes the final trading recommendation.
    """
    return Task(
        description=f"""
        ## 最終交易決策

        ### 市場資訊
        - 市場 ID: {market_id}
        - 市場問題: {market_question}

        ### 所有分析摘要
        {all_analyses}

        ### 辯論總結
        {debate_summary}

        ### 當前投資組合狀態
        {portfolio_status}

        ### 你的任務
        作為首席交易監督官，你需要做出最終的交易決策。請：

        1. **綜合所有信號**
           - 權衡每個策略 agent 的信號和信心
           - 考慮辯論中達成的共識和未解決的分歧
           - 評估當前市場狀態

        2. **風險評估**
           - 計算建議交易佔投資組合的比例
           - 確保符合風險限制（單筆 ≤5%，總曝險 ≤20%）
           - 評估最壞情況的損失

        3. **做出最終決策**
           選擇以下之一：
           - BUY_YES: 買入 YES 合約
           - BUY_NO: 買入 NO 合約
           - SELL_YES: 賣出 YES 持倉
           - SELL_NO: 賣出 NO 持倉
           - HOLD: 維持現有持倉
           - WAIT: 暫不行動，等待更好機會

        4. **制定執行計劃**
           - 建議的交易規模
           - 建議的入場價格
           - 設定止損和止盈位
           - 預期持倉時間

        ### 決策原則
        - 保護本金是第一要務
        - 當不確定時，選擇較小的倉位或等待
        - 確保有清晰的退出策略
        - 如果分歧仍然很大（>40%），必須標記需要人類確認

        ### 輸出格式
        請以 JSON 格式輸出你的最終決策：
        ```json
        {{
            "decision_id": "唯一ID",
            "market_id": "{market_id}",
            "timestamp": "ISO格式時間",
            
            "signal_synthesis": {{
                "momentum_weight": 數字,
                "mean_reversion_weight": 數字,
                "arbitrage_weight": 數字,
                "weighted_confidence": 數字
            }},
            
            "final_decision": {{
                "action": "BUY_YES/BUY_NO/SELL_YES/SELL_NO/HOLD/WAIT",
                "confidence": 數字 (0-100),
                "position_size_shares": 數字,
                "position_size_usd": 數字,
                "position_percent_of_portfolio": 數字,
                "entry_price": 數字,
                "target_price": 數字,
                "stop_loss_price": 數字,
                "time_horizon": "SHORT/MEDIUM/LONG",
                "expected_return_percent": 數字,
                "max_loss_percent": 數字
            }},
            
            "risk_assessment": {{
                "single_trade_limit_check": "PASS/FAIL",
                "total_exposure_check": "PASS/FAIL",
                "risk_reward_ratio": 數字,
                "overall_risk_level": "LOW/MEDIUM/HIGH"
            }},
            
            "rationale": {{
                "primary_reasons": ["原因1", "原因2", "原因3"],
                "supporting_factors": ["因素1", "因素2"],
                "risk_factors": ["風險1", "風險2"],
                "dissenting_views_considered": "考慮過的反對意見"
            }},
            
            "execution_plan": {{
                "order_type": "LIMIT/MARKET",
                "urgency": "LOW/MEDIUM/HIGH",
                "split_orders": true/false,
                "special_instructions": "特殊說明"
            }},
            
            "human_review_required": true/false,
            "human_review_reason": "如果需要人類審核，說明原因",
            
            "simulation_output": "模擬下單：[動作] [數量] 股 @ [價格]"
        }}
        ```

        記住：這是模擬模式，所有下單都是模擬的，不會執行真實交易。
        """,
        expected_output="""
        一個完整的 JSON 格式最終交易決策，包含信號綜合、風險評估、執行計劃和詳細理由。
        """,
        agent=supervisor_agent,
    )


def create_human_consultation_task(
    supervisor_agent: Agent,
    market_id: str,
    situation_summary: str,
    specific_questions: str,
    urgency_level: str = "MEDIUM",
) -> Task:
    """
    Create a task for requesting human input.
    
    This task formats the consultation request and prepares context for human review.
    """
    return Task(
        description=f"""
        ## 人類諮詢請求

        ### 情況
        市場 ID: {market_id}
        緊急程度: {urgency_level}

        ### 情況摘要
        {situation_summary}

        ### 你的任務
        作為首席交易監督官，你判定此情況需要人類介入。請準備一份清晰的諮詢請求：

        1. **說明為什麼需要人類介入**
           - 分歧太大？
           - 交易金額太大？
           - 有特殊情況？
           - 需要外部資訊？

        2. **準備具體問題**
           {specific_questions}

        3. **提供背景資訊**
           - 相關數據摘要
           - 各 agent 的觀點
           - 潛在風險

        4. **提供你的初步傾向**
           - 如果必須現在決定，你會怎麼做？
           - 這個傾向的信心有多高？

        ### 輸出格式
        請以友好、清晰的方式輸出諮詢請求：
        ```json
        {{
            "consultation_type": "DECISION_CONFIRMATION/ADDITIONAL_INFO/RISK_APPROVAL/STRATEGY_GUIDANCE",
            "urgency": "{urgency_level}",
            "market_id": "{market_id}",
            
            "situation_brief": "用 2-3 句話概述情況",
            
            "why_human_needed": "為什麼需要人類介入",
            
            "questions_for_human": [
                {{
                    "question": "具體問題",
                    "context": "問題背景",
                    "options": ["選項A", "選項B", "選項C"],
                    "agent_recommendation": "如果有的話，agent 的建議"
                }}
            ],
            
            "relevant_data": {{
                "current_price": 數字,
                "agent_signals": "摘要",
                "divergence_level": 數字,
                "proposed_trade_size": "金額和比例"
            }},
            
            "preliminary_inclination": {{
                "action": "傾向的動作",
                "confidence": 數字,
                "caveat": "但需要人類確認..."
            }},
            
            "time_sensitivity": "這個決策有多緊急？",
            
            "human_friendly_message": "
                🤔 人類，我需要你的意見！

                關於市場 [市場描述]，我們團隊遇到了 [情況]。

                具體問題是：[問題]

                你有什麼看法？有沒有我們沒考慮到的資訊？
            "
        }}
        ```

        記住：保持友好和清晰，讓人類能快速理解情況並提供有價值的輸入。
        """,
        expected_output="""
        一個格式清晰的人類諮詢請求，包含情況說明、具體問題和相關數據。
        """,
        agent=supervisor_agent,
    )


def create_post_decision_review_task(
    data_optimizer_agent: Agent,
    decision_record: str,
    outcome: Optional[str] = None,
) -> Task:
    """
    Create a task for post-decision review and learning.
    
    This task helps the system learn from past decisions.
    """
    return Task(
        description=f"""
        ## 決策後回顧與學習

        ### 決策記錄
        {decision_record}

        ### 結果（如果有）
        {outcome if outcome else "尚未知道最終結果"}

        ### 你的任務
        作為數據分析與策略優化師，請進行決策後回顧：

        1. **分析決策過程**
           - 各 agent 的信號是否合理？
           - 辯論過程是否有效？
           - 最終決策是否符合風險規則？

        2. **識別改進機會**
           - 有哪些信息被遺漏了？
           - 哪些分析可以做得更好？
           - 辯論中有哪些有價值的觀點？

        3. **更新策略參數建議**
           - 基於這次經驗，是否需要調整參數？
           - 各策略的權重是否需要調整？

        4. **記錄經驗教訓**
           - 這次決策的關鍵學習是什麼？
           - 有什麼應該在未來避免或重複的？

        ### 輸出格式
        ```json
        {{
            "review_id": "唯一ID",
            "decision_reviewed": "決策摘要",
            
            "process_analysis": {{
                "signal_quality": "HIGH/MEDIUM/LOW",
                "debate_effectiveness": "HIGH/MEDIUM/LOW",
                "risk_compliance": "YES/NO",
                "issues_identified": ["問題1", "問題2"]
            }},
            
            "improvement_opportunities": [
                {{
                    "area": "改進領域",
                    "current_state": "當前狀態",
                    "suggested_improvement": "建議改進",
                    "priority": "HIGH/MEDIUM/LOW"
                }}
            ],
            
            "parameter_adjustments": [
                {{
                    "parameter": "參數名",
                    "current_value": "當前值",
                    "suggested_value": "建議值",
                    "reason": "原因"
                }}
            ],
            
            "lessons_learned": [
                {{
                    "lesson": "經驗教訓",
                    "applies_to": "適用情況",
                    "action_item": "行動項目"
                }}
            ],
            
            "knowledge_update": {{
                "new_patterns_identified": ["模式1"],
                "strategy_performance_update": "更新內容",
                "market_regime_observations": "觀察"
            }}
        }}
        ```

        這個回顧將幫助團隊持續改進決策質量。
        """,
        expected_output="""
        一個完整的決策後回顧報告，包含過程分析、改進機會和經驗教訓。
        """,
        agent=data_optimizer_agent,
    )


# Helper functions for decision formatting

def format_decision_for_display(decision: dict) -> str:
    """
    Format a decision dictionary for human-readable display.
    """
    action = decision.get("final_decision", {}).get("action", "UNKNOWN")
    confidence = decision.get("final_decision", {}).get("confidence", 0)
    size_usd = decision.get("final_decision", {}).get("position_size_usd", 0)
    entry_price = decision.get("final_decision", {}).get("entry_price", 0)
    
    action_emoji = {
        "BUY_YES": "📈 買入 YES",
        "BUY_NO": "📉 買入 NO",
        "SELL_YES": "💰 賣出 YES",
        "SELL_NO": "💰 賣出 NO",
        "HOLD": "⏸️ 持有",
        "WAIT": "⏳ 等待",
    }.get(action, f"❓ {action}")
    
    display = f"""
╔══════════════════════════════════════════════════════════════╗
║                     🎯 最終交易決策                          ║
╠══════════════════════════════════════════════════════════════╣
║  行動: {action_emoji:<50} ║
║  信心: {confidence}%{' ' * (49 - len(str(confidence)))} ║
║  規模: ${size_usd:.2f}{' ' * (48 - len(f'{size_usd:.2f}'))} ║
║  入場價: {entry_price:.4f}{' ' * (47 - len(f'{entry_price:.4f}'))} ║
╠══════════════════════════════════════════════════════════════╣
║  主要理由:                                                   ║
"""
    
    for i, reason in enumerate(decision.get("rationale", {}).get("primary_reasons", [])[:3], 1):
        display += f"║  {i}. {reason[:55]:<55} ║\n"
    
    display += "╚══════════════════════════════════════════════════════════════╝"
    
    return display


def generate_simulation_output(decision: dict) -> str:
    """
    Generate the simulation order output string.
    """
    action = decision.get("final_decision", {}).get("action", "HOLD")
    shares = decision.get("final_decision", {}).get("position_size_shares", 0)
    price = decision.get("final_decision", {}).get("entry_price", 0)
    market_id = decision.get("market_id", "unknown")
    
    if action in ["HOLD", "WAIT"]:
        return f"模擬結果：{action} - 不執行交易"
    
    side = "買入" if "BUY" in action else "賣出"
    contract = "YES" if "YES" in action else "NO"
    
    return f"""
{'='*60}
🎮 模擬下單 (SIMULATED ORDER)
{'='*60}
市場: {market_id}
動作: {side} {contract}
數量: {shares:.2f} 股
價格: ${price:.4f}
總值: ${shares * price:.2f}
狀態: ✅ 模擬成功（未執行真實交易）
{'='*60}
"""
