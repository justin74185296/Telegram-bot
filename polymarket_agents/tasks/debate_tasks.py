"""
Debate Tasks
============

Tasks for the multi-round debate/discussion mechanism between agents.
"""

from crewai import Task, Agent
from typing import List, Optional


def create_debate_round_task(
    agent: Agent,
    market_id: str,
    round_number: int,
    previous_analyses: str,
    debate_history: str = "",
) -> Task:
    """
    Create a debate round task for an agent.
    
    Each agent reviews others' analyses and can agree, disagree, or provide new evidence.
    """
    agent_name = agent.role
    
    return Task(
        description=f"""
        ## 辯論第 {round_number} 輪 - {agent_name}

        ### 背景
        你正在參與一場關於市場 {market_id} 的團隊辯論。
        這是第 {round_number} 輪辯論。

        ### 之前的分析摘要
        {previous_analyses}

        ### 之前的辯論記錄
        {debate_history if debate_history else "（這是第一輪辯論）"}

        ### 你的任務
        作為 {agent_name}，請：

        1. **審視其他 agent 的分析**
           - 仔細閱讀每個 agent 的信號和理由
           - 識別你同意和不同意的點

        2. **表達你的立場**
           - 同意的點：說明為什麼，並補充支持證據
           - 不同意的點：明確指出，並提供反駁理由和數據
           - 新發現：如果有新的數據或觀點，請分享

        3. **更新你的信號（如需要）**
           - 如果其他 agent 提出了有說服力的論點，你可以調整你的信心分數
           - 如果你維持原立場，請解釋為什麼

        ### 辯論規則
        - 用數據和邏輯支持你的觀點
        - 尊重其他 agent 的專業領域
        - 如果被說服，可以改變立場
        - 清楚標明你的最終立場和信心分數

        ### 輸出格式
        請以 JSON 格式輸出你的辯論發言：
        ```json
        {{
            "agent": "{agent_name}",
            "round": {round_number},
            "responses_to_others": [
                {{
                    "to_agent": "agent名稱",
                    "stance": "AGREE/DISAGREE/PARTIALLY_AGREE",
                    "comment": "你的評論",
                    "evidence": "支持你觀點的數據或理由"
                }}
            ],
            "new_insights": "任何新的觀點或數據",
            "updated_signal": {{
                "action": "BUY_YES/BUY_NO/SELL_YES/SELL_NO/HOLD/WAIT",
                "confidence": 數字 (0-100),
                "change_from_previous": "如果改變了，說明原因"
            }},
            "key_argument": "你在這輪辯論中的核心論點",
            "open_questions": ["如果有任何疑問或需要更多資訊的點"]
        }}
        ```

        記住：好的辯論應該推進團隊對市場的理解，而不是為了辯論而辯論。
        """,
        expected_output=f"""
        一個完整的 JSON 格式辯論發言，包含對其他 agent 的回應、更新的信號和核心論點。
        """,
        agent=agent,
    )


def create_debate_summary_task(
    supervisor_agent: Agent,
    market_id: str,
    all_debate_rounds: str,
    round_count: int,
) -> Task:
    """
    Create a task for the supervisor to summarize the debate.
    
    The supervisor analyzes the debate and determines if more rounds are needed.
    """
    return Task(
        description=f"""
        ## 辯論總結與決策評估

        ### 市場
        - 市場 ID: {market_id}
        - 已完成辯論輪數: {round_count}

        ### 完整辯論記錄
        {all_debate_rounds}

        ### 你的任務
        作為首席交易監督官，請：

        1. **總結辯論**
           - 總結每個 agent 的最終立場和信心分數
           - 識別團隊的共識點和分歧點
           - 計算信心分數的分歧度（最高 - 最低）

        2. **評估是否需要更多辯論**
           - 分歧度 > 30%：需要再一輪辯論
           - 最多 4 輪辯論
           - 如果已經 4 輪但分歧仍大，標記需要人類介入

        3. **準備決策摘要**
           - 如果達成足夠共識，準備進入最終決策階段
           - 如果需要更多辯論，指出關鍵分歧點

        ### 分歧度計算
        分歧度 = (最高信心分數 - 最低信心分數)

        例如：
        - 動量：買入，信心 75%
        - 均值回歸：賣出，信心 60%
        - 套利：等待，信心 40%
        
        如果信號方向相反，分歧度自動設為 100%（需要人類介入）

        ### 輸出格式
        請以 JSON 格式輸出你的評估：
        ```json
        {{
            "debate_summary": {{
                "rounds_completed": {round_count},
                "agent_positions": [
                    {{
                        "agent": "agent名稱",
                        "final_action": "動作",
                        "final_confidence": 數字,
                        "key_argument": "核心論點"
                    }}
                ],
                "consensus_points": ["共識1", "共識2"],
                "disagreement_points": ["分歧1", "分歧2"]
            }},
            "divergence_analysis": {{
                "confidence_divergence": 數字,
                "signal_divergence": true/false,
                "overall_divergence_score": 數字 (0-100)
            }},
            "next_step": {{
                "action": "CONTINUE_DEBATE/PROCEED_TO_DECISION/REQUEST_HUMAN_INPUT",
                "reason": "原因",
                "focus_for_next_round": "如果繼續辯論，下一輪的焦點"
            }},
            "preliminary_assessment": {{
                "leaning_towards": "當前傾向的行動",
                "confidence_in_assessment": 數字,
                "key_risks": ["風險1", "風險2"]
            }}
        }}
        ```

        作為監督官，你的評估將決定是否繼續辯論或進入決策階段。
        """,
        expected_output="""
        一個完整的 JSON 格式辯論總結，包含各 agent 立場、分歧分析和下一步建議。
        """,
        agent=supervisor_agent,
    )


def create_focused_debate_task(
    agents: List[Agent],
    market_id: str,
    focus_topic: str,
    round_number: int,
) -> List[Task]:
    """
    Create focused debate tasks when there's a specific disagreement to resolve.
    
    Returns a list of tasks, one for each agent.
    """
    tasks = []
    
    for agent in agents:
        task = Task(
            description=f"""
            ## 焦點辯論 - 第 {round_number} 輪

            ### 辯論焦點
            {focus_topic}

            ### 市場
            {market_id}

            ### 你的任務
            作為 {agent.role}，請針對以下焦點問題發表你的專業意見：

            **焦點問題：{focus_topic}**

            請從你的專業角度分析這個問題，提供：
            1. 你的立場和判斷
            2. 支持你立場的數據或分析
            3. 潛在的風險或反對意見
            4. 你的信心水平

            ### 輸出格式
            ```json
            {{
                "agent": "{agent.role}",
                "focus_topic": "{focus_topic}",
                "position": "你的立場",
                "supporting_evidence": ["證據1", "證據2"],
                "counterarguments_considered": ["反對意見1"],
                "confidence": 數字 (0-100),
                "conclusion": "簡短結論"
            }}
            ```
            """,
            expected_output=f"""
            針對焦點問題 "{focus_topic}" 的專業分析和立場聲明。
            """,
            agent=agent,
        )
        tasks.append(task)
    
    return tasks


def calculate_debate_divergence(agent_signals: List[dict]) -> dict:
    """
    Calculate divergence metrics from agent signals.
    
    Args:
        agent_signals: List of signal dictionaries from each agent
    
    Returns:
        Divergence analysis dictionary
    """
    if not agent_signals:
        return {"error": "No signals provided"}
    
    # Extract confidences
    confidences = [s.get("confidence", 50) for s in agent_signals]
    
    # Extract actions
    actions = [s.get("action", "HOLD") for s in agent_signals]
    
    # Calculate confidence divergence
    confidence_divergence = max(confidences) - min(confidences)
    
    # Check if actions are conflicting
    buy_actions = {"BUY_YES", "BUY_NO"}
    sell_actions = {"SELL_YES", "SELL_NO"}
    
    has_buy = any(a in buy_actions for a in actions)
    has_sell = any(a in sell_actions for a in actions)
    signal_conflict = has_buy and has_sell
    
    # Calculate overall divergence
    if signal_conflict:
        overall_divergence = 100  # Max divergence if conflicting signals
    else:
        overall_divergence = confidence_divergence
    
    return {
        "confidence_divergence": confidence_divergence,
        "signal_conflict": signal_conflict,
        "overall_divergence": overall_divergence,
        "needs_more_debate": overall_divergence > 30,
        "needs_human_input": overall_divergence > 40 or signal_conflict,
        "agent_confidences": {
            s.get("agent", f"agent_{i}"): s.get("confidence", 50)
            for i, s in enumerate(agent_signals)
        },
        "agent_actions": {
            s.get("agent", f"agent_{i}"): s.get("action", "HOLD")
            for i, s in enumerate(agent_signals)
        },
    }


def should_continue_debate(
    divergence_score: float,
    current_round: int,
    max_rounds: int = 4,
    divergence_threshold: float = 30.0,
) -> dict:
    """
    Determine if debate should continue based on divergence and round count.
    
    Returns:
        Dictionary with decision and reasoning
    """
    if current_round >= max_rounds:
        return {
            "continue": False,
            "reason": f"已達到最大辯論輪數 ({max_rounds} 輪)",
            "next_action": "PROCEED_TO_DECISION" if divergence_score <= 40 else "REQUEST_HUMAN_INPUT",
        }
    
    if divergence_score <= divergence_threshold:
        return {
            "continue": False,
            "reason": f"分歧度 ({divergence_score:.1f}%) 低於閾值 ({divergence_threshold}%)，達成足夠共識",
            "next_action": "PROCEED_TO_DECISION",
        }
    
    return {
        "continue": True,
        "reason": f"分歧度 ({divergence_score:.1f}%) 仍高於閾值，需要繼續辯論",
        "next_action": "CONTINUE_DEBATE",
        "rounds_remaining": max_rounds - current_round,
    }
