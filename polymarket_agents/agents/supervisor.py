"""
Supervisor Agent
================

The team manager and final decision maker. Uses Claude Opus 4.5 (highest tier).
Responsible for:
- Receiving signals from all trading agents
- Moderating debates between agents
- Making final trading decisions
- Enforcing risk management rules
- Triggering human intervention when needed
"""

from crewai import Agent
from langchain_anthropic import ChatAnthropic

from ..config import MODEL_CONFIG, get_config
from ..tools.trading import (
    simulate_order,
    check_risk_limits,
    get_portfolio_status,
)


def create_supervisor_agent() -> Agent:
    """
    Create the Supervisor agent with highest-tier LLM.
    
    The Supervisor is the team manager responsible for:
    1. Synthesizing signals from all other agents
    2. Moderating debates and ensuring productive discussion
    3. Making final BUY/SELL/HOLD decisions
    4. Enforcing strict risk management
    5. Requesting human input when necessary
    """
    config = get_config()
    model_config = MODEL_CONFIG["supervisor"]
    
    # Initialize the LLM
    llm = ChatAnthropic(
        model=model_config["model"],
        temperature=model_config["temperature"],
        max_tokens=model_config["max_tokens"],
        anthropic_api_key=config.llm.anthropic_api_key,
    )
    
    supervisor = Agent(
        role="首席交易監督官 (Chief Trading Supervisor)",
        goal="""
        作為團隊的最高決策者，你的目標是：
        1. 綜合所有策略 agent 的信號和辯論，做出最優的交易決策
        2. 嚴格執行風險控制：單筆不超過總資金 5%，總曝險不超過 20%
        3. 當 agent 分歧超過 30% 時，主持額外辯論輪次
        4. 當分歧超過 40% 或涉及大額交易時，必須詢問人類意見
        5. 輸出清晰、有理有據的最終建議
        """,
        backstory="""
        你是一位擁有 20 年經驗的資深量化交易主管，曾在頂級對沖基金管理數十億美元的預測市場投資組合。
        
        你的專長包括：
        - 多策略信號整合與權重分配
        - 風險管理與資金控制
        - 團隊協調與衝突解決
        - 在不確定性中做出果斷決策
        
        你的交易哲學：
        - "保護本金是第一要務"
        - "當團隊意見分歧時，謹慎是美德"
        - "好的交易是等出來的，不是追出來的"
        - "永遠要有退出計劃"
        
        你特別擅長在壓力下保持冷靜，並能有效整合不同策略的觀點，做出平衡風險和收益的決策。
        當你不確定時，你會主動尋求更多資訊或人類專家的意見。
        """,
        tools=[
            simulate_order,
            check_risk_limits,
            get_portfolio_status,
        ],
        llm=llm,
        verbose=True,
        allow_delegation=True,
        memory=True,
    )
    
    return supervisor


# Supervisor's decision framework
SUPERVISOR_DECISION_TEMPLATE = """
## 監督官決策框架

### 1. 信號匯總
請匯總所有 agent 的建議：

| Agent | 建議 | 信心分數 | 主要理由 |
|-------|------|----------|----------|
| 動量交易員 | {momentum_signal} | {momentum_confidence}% | {momentum_reason} |
| 均值回歸交易員 | {mean_reversion_signal} | {mean_reversion_confidence}% | {mean_reversion_reason} |
| 套利交易員 | {arbitrage_signal} | {arbitrage_confidence}% | {arbitrage_reason} |
| 數據優化師 | {data_signal} | {data_confidence}% | {data_reason} |

### 2. 分歧分析
- 最高信心分數: {max_confidence}%
- 最低信心分數: {min_confidence}%
- 分歧程度: {divergence}%
- 需要額外辯論: {needs_debate}
- 需要人類介入: {needs_human}

### 3. 風險評估
- 建議交易金額: ${proposed_amount}
- 佔投資組合比例: {portfolio_percent}%
- 當前總曝險: {current_exposure}%
- 風險檢查結果: {risk_check_result}

### 4. 最終決策
**建議行動**: {final_action}
**建議規模**: {position_size}
**理由**: {final_rationale}

### 5. 人類確認（如需要）
{human_confirmation_request}
"""


def calculate_divergence(confidences: list) -> float:
    """Calculate divergence between agent opinions."""
    if not confidences:
        return 0.0
    return max(confidences) - min(confidences)


def needs_extra_debate(divergence: float, threshold: float = 30.0) -> bool:
    """Determine if extra debate round is needed."""
    return divergence > threshold


def needs_human_intervention(
    divergence: float,
    trade_percent: float,
    divergence_threshold: float = 40.0,
    trade_threshold: float = 4.0
) -> bool:
    """Determine if human intervention is required."""
    return divergence > divergence_threshold or trade_percent > trade_threshold
