#!/usr/bin/env python3
"""
Example Run Script
==================

This script demonstrates a complete simulation run of the Polymarket
Multi-Agent Trading System with sample inputs and expected outputs.

Run this file to see the system in action with mock data.
"""

import json
import os
import sys
from datetime import datetime

# Ensure we can import the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the API key for demonstration
os.environ.setdefault("ANTHROPIC_API_KEY", "demo-key-for-testing")


def print_section(title: str, char: str = "─"):
    """Print a section header."""
    print(f"\n{char * 60}")
    print(f"📌 {title}")
    print(f"{char * 60}")


def demonstrate_mock_tools():
    """Demonstrate the mock tools functionality."""
    print_section("工具演示 - Mock Tools Demo")
    
    from polymarket_agents.tools.market_data import (
        get_polymarket_data,
        get_orderbook,
        get_historical_prices,
        calculate_statistics,
    )
    from polymarket_agents.tools.sentiment import (
        search_x_sentiment,
        web_search_news,
    )
    from polymarket_agents.tools.trading import (
        simulate_order,
        calculate_position_size,
        check_risk_limits,
        analyze_arbitrage_opportunity,
    )
    
    market_id = "will-bitcoin-reach-100k-2025"
    
    # 1. Market Data
    print("\n1️⃣ 獲取市場數據...")
    market_data = get_polymarket_data.run(market_id=market_id)
    print(f"市場數據:\n{market_data[:500]}...")
    
    # 2. Statistics
    print("\n2️⃣ 計算統計指標...")
    stats = calculate_statistics.run(market_id=market_id)
    print(f"統計數據:\n{stats[:500]}...")
    
    # 3. Sentiment
    print("\n3️⃣ 搜索輿情...")
    sentiment = search_x_sentiment.run(event_keywords="bitcoin")
    print(f"輿情數據:\n{sentiment[:500]}...")
    
    # 4. Risk Check
    print("\n4️⃣ 風險檢查...")
    risk_check = check_risk_limits.run(proposed_trade_value=300.0, side="BUY_YES")
    print(f"風險評估:\n{risk_check[:500]}...")
    
    # 5. Simulated Order
    print("\n5️⃣ 模擬下單...")
    order_result = simulate_order.run(
        market_id=market_id,
        side="BUY_YES",
        quantity=100,
        price=0.67,
        reason="動量策略信號 - 強勁上漲趨勢"
    )
    print(f"模擬訂單結果:\n{order_result[:500]}...")


def demonstrate_sample_workflow():
    """Demonstrate the expected workflow output."""
    print_section("工作流程演示 - Workflow Demo")
    
    # Sample analysis results
    sample_data_collection = {
        "market_id": "will-bitcoin-reach-100k-2025",
        "timestamp": datetime.now().isoformat(),
        "market_data": {
            "yes_price": 0.67,
            "no_price": 0.33,
            "price_change_24h": 0.05,
            "volume_24h": 210000,
            "liquidity": 2500000
        },
        "statistics": {
            "mean_30d": 0.62,
            "std_dev": 0.08,
            "z_score": 0.625,
            "trend_direction": "BULLISH"
        },
        "sentiment": {
            "social_sentiment": 0.65,
            "news_sentiment": 0.55,
            "combined_sentiment": 0.59,
            "sentiment_label": "MODERATELY_BULLISH"
        },
        "key_news": [
            "Bitcoin ETF Sees Record Inflows",
            "Analysts Predict New ATH Before Halving"
        ],
        "initial_assessment": "市場呈現溫和看漲趨勢，輿情偏正面",
        "data_quality": "HIGH",
        "confidence": 75
    }
    
    sample_momentum_analysis = {
        "agent": "momentum_trader",
        "market_id": "will-bitcoin-reach-100k-2025",
        "analysis": {
            "short_term_trend": "BULLISH",
            "medium_term_trend": "BULLISH",
            "trend_strength": 7,
            "momentum_score": 72,
            "volume_confirmation": True
        },
        "signal": {
            "action": "BUY_YES",
            "confidence": 75,
            "entry_price": 0.67,
            "target_price": 0.75,
            "stop_loss": 0.60,
            "time_horizon": "MEDIUM"
        },
        "rationale": "價格呈現明顯上升趨勢，7日和21日均呈看漲。成交量增加確認趨勢有效。社交媒體情緒偏正面支持上漲動能。",
        "risk_factors": ["價格已高於均值，回調風險存在", "需關注套利交易員的意見"],
        "debate_position": "強烈建議買入 YES，趨勢明確且有量價配合"
    }
    
    sample_mean_reversion_analysis = {
        "agent": "mean_reversion_trader",
        "market_id": "will-bitcoin-reach-100k-2025",
        "analysis": {
            "mean_30d": 0.62,
            "std_dev_30d": 0.08,
            "current_z_score": 0.625,
            "percentile_rank": 73,
            "overbought_oversold": "NEUTRAL",
            "reversion_potential": "LOW"
        },
        "signal": {
            "action": "HOLD",
            "confidence": 55,
            "entry_price": None,
            "target_price": 0.62,
            "stop_loss": None,
            "expected_holding_period": "N/A"
        },
        "statistical_evidence": {
            "z_score_interpretation": "價格略高於均值但未達超買區域",
            "historical_reversion_rate": "60% of similar situations reverted within 2 weeks",
            "confidence_interval": "95% CI: [0.54, 0.70]"
        },
        "rationale": "Z-score 為 0.625，未達到超買閾值 (2.0)。雖然價格高於均值，但不足以觸發賣出信號。建議觀望，等待更極端的情況。",
        "risk_factors": ["如果趨勢持續，可能錯過機會", "均值本身可能因基本面改變而上移"],
        "debate_position": "不建議現在交易，回歸信號不足。但不反對動量策略的小倉位操作。"
    }
    
    sample_arbitrage_analysis = {
        "agent": "arbitrage_trader",
        "market_id": "will-bitcoin-reach-100k-2025",
        "price_analysis": {
            "yes_price": 0.67,
            "no_price": 0.33,
            "price_sum": 1.00,
            "deviation_from_unity": 0.00,
            "deviation_percent": 0.0
        },
        "arbitrage_opportunity": {
            "exists": False,
            "type": "NONE",
            "gross_profit_per_unit": 0,
            "estimated_slippage": 0.02,
            "estimated_fees": 0.002,
            "net_profit_per_unit": 0
        },
        "liquidity_assessment": {
            "yes_side_liquidity": 25000,
            "no_side_liquidity": 18000,
            "max_executable_size": 18000,
            "liquidity_grade": "GOOD"
        },
        "signal": {
            "action": "NO_OPPORTUNITY",
            "confidence": 90,
            "recommended_size": 0,
            "expected_profit": 0,
            "execution_strategy": "無套利機會，價格定價高效"
        },
        "rationale": "YES + NO = 1.00，市場定價完美。無套利空間。流動性良好，如有方向性觀點可正常交易。",
        "risk_factors": ["無套利風險，但也無無風險收益"],
        "debate_position": "無套利機會。如團隊有方向性共識，可支持該方向的交易。"
    }
    
    sample_final_decision = {
        "decision_id": f"DEC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "market_id": "will-bitcoin-reach-100k-2025",
        "timestamp": datetime.now().isoformat(),
        "signal_synthesis": {
            "momentum_weight": 0.45,
            "mean_reversion_weight": 0.30,
            "arbitrage_weight": 0.25,
            "weighted_confidence": 68
        },
        "final_decision": {
            "action": "BUY_YES",
            "confidence": 68,
            "position_size_shares": 150,
            "position_size_usd": 100.50,
            "position_percent_of_portfolio": 1.0,
            "entry_price": 0.67,
            "target_price": 0.75,
            "stop_loss_price": 0.60,
            "time_horizon": "MEDIUM",
            "expected_return_percent": 11.9,
            "max_loss_percent": 10.4
        },
        "risk_assessment": {
            "single_trade_limit_check": "PASS",
            "total_exposure_check": "PASS",
            "risk_reward_ratio": 1.14,
            "overall_risk_level": "LOW"
        },
        "rationale": {
            "primary_reasons": [
                "動量策略顯示強勁上漲趨勢 (信心 75%)",
                "輿情分析偏向正面 (綜合情緒 0.59)",
                "成交量增加確認趨勢"
            ],
            "supporting_factors": [
                "均值回歸策略未發出反向信號",
                "流動性良好，執行風險低"
            ],
            "risk_factors": [
                "價格已高於 30 日均值",
                "Z-score 雖未超買但正在上升"
            ],
            "dissenting_views_considered": "均值回歸策略建議觀望，但未強烈反對。考慮後決定採用較小倉位。"
        },
        "execution_plan": {
            "order_type": "LIMIT",
            "urgency": "LOW",
            "split_orders": False,
            "special_instructions": "設定止損在 $0.60，如觸及立即平倉"
        },
        "human_review_required": False,
        "simulation_output": "模擬下單：買入 YES 150 股 @ $0.67"
    }
    
    # Print sample outputs
    print("\n📊 第一階段：數據收集結果")
    print(json.dumps(sample_data_collection, indent=2, ensure_ascii=False))
    
    print("\n📈 第二階段：策略分析")
    print("\n動量策略分析:")
    print(json.dumps(sample_momentum_analysis, indent=2, ensure_ascii=False))
    
    print("\n均值回歸策略分析:")
    print(json.dumps(sample_mean_reversion_analysis, indent=2, ensure_ascii=False))
    
    print("\n套利策略分析:")
    print(json.dumps(sample_arbitrage_analysis, indent=2, ensure_ascii=False))
    
    print("\n🎯 第四階段：最終決策")
    print(json.dumps(sample_final_decision, indent=2, ensure_ascii=False))
    
    # Print formatted decision
    print("\n" + "═" * 70)
    print("""
╔══════════════════════════════════════════════════════════════╗
║                     🎯 最終交易決策                          ║
╠══════════════════════════════════════════════════════════════╣
║  行動: 📈 買入 YES                                           ║
║  信心: 68%                                                   ║
║  規模: $100.50                                               ║
║  入場價: 0.6700                                              ║
╠══════════════════════════════════════════════════════════════╣
║  主要理由:                                                   ║
║  1. 動量策略顯示強勁上漲趨勢 (信心 75%)                      ║
║  2. 輿情分析偏向正面 (綜合情緒 0.59)                         ║
║  3. 成交量增加確認趨勢                                       ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    print("""
============================================================
🎮 模擬下單 (SIMULATED ORDER)
============================================================
市場: will-bitcoin-reach-100k-2025
動作: 買入 YES
數量: 150.00 股
價格: $0.6700
總值: $100.50
狀態: ✅ 模擬成功（未執行真實交易）
============================================================
    """)


def show_architecture():
    """Display the system architecture."""
    print_section("系統架構 - System Architecture")
    
    architecture = """
┌─────────────────────────────────────────────────────────────────────────────┐
│                    POLYMARKET 多代理交易系統架構                            │
│                    Multi-Agent Trading System Architecture                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              輸入層 (Input Layer)                            │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐               │
│  │  市場 ID      │    │  市場問題     │    │  人類輸入     │               │
│  │  Market ID    │    │  Question     │    │  Human Input  │               │
│  └───────┬───────┘    └───────┬───────┘    └───────┬───────┘               │
└──────────┼────────────────────┼────────────────────┼────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          數據收集層 (Data Layer)                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   🔍 數據優化師 (Data Optimizer)                    │   │
│  │                        Claude Sonnet 4.5                            │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │ Polymarket   │  │ X/Twitter    │  │ News         │             │   │
│  │  │ API 數據     │  │ 輿情         │  │ 新聞         │             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          策略分析層 (Strategy Layer)                         │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │ 📈 動量交易員   │  │ 📊 均值回歸     │  │ ⚖️ 套利交易員   │            │
│  │  Momentum       │  │  Mean Reversion │  │  Arbitrage      │            │
│  │  Sonnet 4.5     │  │  Sonnet 4.5     │  │  Sonnet 4.5     │            │
│  │                 │  │                 │  │                 │            │
│  │ • 趨勢識別     │  │ • Z-Score 計算  │  │ • 價格一致性   │            │
│  │ • 動量指標     │  │ • 超買/超賣    │  │ • 流動性評估   │            │
│  │ • 成交量分析   │  │ • 回歸預測     │  │ • 套利計算     │            │
│  │                 │  │                 │  │                 │            │
│  │ 輸出: 買/賣信號 │  │ 輸出: 反向信號 │  │ 輸出: 套利機會 │            │
│  │ 信心: 0-100    │  │ 信心: 0-100    │  │ 信心: 0-100    │            │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │
└───────────┼────────────────────┼────────────────────┼────────────────────────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            辯論層 (Debate Layer)                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        🗣️ 多輪辯論機制                              │   │
│  │                                                                     │   │
│  │    第 1 輪  ──►  第 2 輪  ──►  第 3 輪  ──►  第 4 輪 (最多)       │   │
│  │      │           │           │           │                         │   │
│  │      ▼           ▼           ▼           ▼                         │   │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐                   │   │
│  │  │ 發言   │  │ 反駁   │  │ 補充   │  │ 總結   │                   │   │
│  │  │ 同意   │  │ 質疑   │  │ 證據   │  │ 共識   │                   │   │
│  │  └────────┘  └────────┘  └────────┘  └────────┘                   │   │
│  │                                                                     │   │
│  │  分歧度 > 30%: 繼續辯論 │ 分歧度 > 40%: 請求人類介入              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           決策層 (Decision Layer)                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    👔 監督官 (Supervisor)                           │   │
│  │                      Claude Opus 4.5                                │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │   │
│  │  │ 信號綜合   │  │ 風險控制   │  │ 最終決策   │                │   │
│  │  │ 權重分配   │  │ ≤5% 單筆   │  │ 買/賣/持有 │                │   │
│  │  │            │  │ ≤20% 總額  │  │            │                │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                │   │
│  │                                                                     │   │
│  │  ┌───────────────────────────────────────────────────────────────┐ │   │
│  │  │  如需要 ──► 🤔 人類介入請求 (Human-in-the-Loop)              │ │   │
│  │  │            "人類，你怎麼看這個價差？有額外資訊嗎？"          │ │   │
│  │  └───────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           輸出層 (Output Layer)                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      🎮 模擬執行 (Simulation)                       │   │
│  │                                                                     │   │
│  │    模擬下單：買入 YES 150 股 @ $0.67                               │   │
│  │                                                                     │   │
│  │    • 不執行真實交易                                                │   │
│  │    • 記錄決策理由                                                  │   │
│  │    • 追蹤模擬績效                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              工具層 (Tools)                                  │
│                                                                             │
│  市場數據工具              輿情分析工具              交易工具               │
│  ├─ get_polymarket_data    ├─ search_x_sentiment    ├─ simulate_order      │
│  ├─ get_orderbook          ├─ web_search_news       ├─ calculate_position  │
│  ├─ get_historical_prices  └─ analyze_combined      ├─ check_risk_limits   │
│  └─ calculate_statistics      _sentiment            └─ analyze_arbitrage   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
    """
    print(architecture)


def main():
    """Main demonstration function."""
    print("\n" + "═" * 70)
    print("   🎯 POLYMARKET 多代理交易系統 - 範例運行")
    print("   Multi-Agent Trading System - Example Run")
    print("═" * 70)
    
    print("""
    
這個範例展示了系統的完整工作流程和預期輸出。
由於需要真實的 Anthropic API Key 來運行完整系統，
這裡我們展示 mock 數據和預期的輸出格式。

要運行真實系統，請：
1. 設置環境變數：export ANTHROPIC_API_KEY='your-key'
2. 運行：python -m polymarket_agents.main --interactive

    """)
    
    # Show architecture
    show_architecture()
    
    # Demonstrate mock tools
    demonstrate_mock_tools()
    
    # Demonstrate sample workflow
    demonstrate_sample_workflow()
    
    print("\n" + "═" * 70)
    print("   ✅ 範例運行完成！")
    print("═" * 70)


if __name__ == "__main__":
    main()
