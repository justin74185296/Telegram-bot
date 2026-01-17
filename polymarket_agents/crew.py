"""
Polymarket Trading Crew
=======================

Main orchestration module that assembles the trading agent crew
and manages the analysis → debate → decision workflow.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from crewai import Crew, Process

from .config import get_config, SystemConfig
from .agents import (
    create_supervisor_agent,
    create_momentum_trader_agent,
    create_mean_reversion_trader_agent,
    create_arbitrage_trader_agent,
    create_data_optimizer_agent,
)
from .tasks.analysis_tasks import (
    create_data_collection_task,
    create_momentum_analysis_task,
    create_mean_reversion_analysis_task,
    create_arbitrage_analysis_task,
)
from .tasks.debate_tasks import (
    create_debate_round_task,
    create_debate_summary_task,
    calculate_debate_divergence,
    should_continue_debate,
)
from .tasks.decision_tasks import (
    create_final_decision_task,
    create_human_consultation_task,
    format_decision_for_display,
    generate_simulation_output,
)
from .tools.trading import get_portfolio_status
from .utils.helpers import (
    setup_logging,
    parse_json_response,
    print_banner,
    print_section,
    Timer,
)


class PolymarketTradingCrew:
    """
    Main trading crew orchestrator.
    
    This class manages the complete trading analysis workflow:
    1. Data collection
    2. Individual strategy analysis
    3. Multi-round debate
    4. Final decision
    5. Human consultation (if needed)
    """
    
    def __init__(self, config: Optional[SystemConfig] = None):
        """Initialize the trading crew."""
        self.config = config or get_config()
        self.logger = setup_logging(self.config.log_level)
        
        # Initialize agents
        self.logger.info("Initializing trading agents...")
        self.supervisor = create_supervisor_agent()
        self.momentum_trader = create_momentum_trader_agent()
        self.mean_reversion_trader = create_mean_reversion_trader_agent()
        self.arbitrage_trader = create_arbitrage_trader_agent()
        self.data_optimizer = create_data_optimizer_agent()
        
        # Trading agents (excluding supervisor and data optimizer)
        self.trading_agents = [
            self.momentum_trader,
            self.mean_reversion_trader,
            self.arbitrage_trader,
        ]
        
        # All agents
        self.all_agents = [
            self.supervisor,
            self.momentum_trader,
            self.mean_reversion_trader,
            self.arbitrage_trader,
            self.data_optimizer,
        ]
        
        # State tracking
        self.current_market_id: Optional[str] = None
        self.analysis_results: Dict[str, Any] = {}
        self.debate_history: List[Dict[str, Any]] = []
        self.final_decision: Optional[Dict[str, Any]] = None
        
        self.logger.info("Trading crew initialized successfully!")
    
    def analyze_market(
        self,
        market_id: str,
        market_question: str = "",
        max_debate_rounds: int = 4,
        min_debate_rounds: int = 2,
    ) -> Dict[str, Any]:
        """
        Run complete market analysis workflow.
        
        Args:
            market_id: The Polymarket market ID to analyze
            market_question: Human-readable market question
            max_debate_rounds: Maximum debate rounds (default: 4)
            min_debate_rounds: Minimum debate rounds (default: 2)
        
        Returns:
            Complete analysis result including final decision
        """
        print_banner(f"POLYMARKET TRADING ANALYSIS", "═", 70)
        print(f"📊 市場: {market_id}")
        print(f"❓ 問題: {market_question or '(未提供)'}")
        print(f"⏰ 開始時間: {datetime.now().isoformat()}")
        print("═" * 70)
        
        self.current_market_id = market_id
        self.analysis_results = {}
        self.debate_history = []
        
        with Timer("Complete Analysis"):
            # Phase 1: Data Collection
            print_section("第一階段：數據收集")
            data_result = self._run_data_collection(market_id, market_question)
            
            # Phase 2: Individual Analysis
            print_section("第二階段：策略分析")
            analysis_results = self._run_strategy_analyses(market_id, data_result)
            
            # Phase 3: Debate
            print_section("第三階段：團隊辯論")
            debate_result = self._run_debate_rounds(
                market_id,
                analysis_results,
                max_rounds=max_debate_rounds,
                min_rounds=min_debate_rounds,
            )
            
            # Phase 4: Final Decision
            print_section("第四階段：最終決策")
            decision = self._make_final_decision(
                market_id,
                market_question,
                analysis_results,
                debate_result,
            )
            
            self.final_decision = decision
        
        # Display results
        self._display_results(decision)
        
        return {
            "market_id": market_id,
            "market_question": market_question,
            "timestamp": datetime.now().isoformat(),
            "data_collection": data_result,
            "strategy_analyses": analysis_results,
            "debate_summary": debate_result,
            "final_decision": decision,
            "simulation_mode": True,
        }
    
    def _run_data_collection(
        self,
        market_id: str,
        market_question: str,
    ) -> Dict[str, Any]:
        """Run data collection task."""
        print("🔍 收集市場數據、新聞和輿情...")
        
        task = create_data_collection_task(
            data_optimizer_agent=self.data_optimizer,
            market_id=market_id,
            market_question=market_question,
        )
        
        crew = Crew(
            agents=[self.data_optimizer],
            tasks=[task],
            verbose=self.config.verbose,
        )
        
        result = crew.kickoff()
        parsed = parse_json_response(str(result)) or {"raw_result": str(result)}
        
        self.analysis_results["data_collection"] = parsed
        print("✅ 數據收集完成")
        
        return parsed
    
    def _run_strategy_analyses(
        self,
        market_id: str,
        data_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run individual strategy analysis tasks."""
        results = {}
        
        # Create analysis tasks
        tasks = [
            ("momentum", create_momentum_analysis_task(
                self.momentum_trader, market_id
            )),
            ("mean_reversion", create_mean_reversion_analysis_task(
                self.mean_reversion_trader, market_id
            )),
            ("arbitrage", create_arbitrage_analysis_task(
                self.arbitrage_trader, market_id
            )),
        ]
        
        for strategy_name, task in tasks:
            print(f"📈 運行 {strategy_name} 策略分析...")
            
            crew = Crew(
                agents=[task.agent],
                tasks=[task],
                verbose=self.config.verbose,
            )
            
            result = crew.kickoff()
            parsed = parse_json_response(str(result)) or {"raw_result": str(result)}
            results[strategy_name] = parsed
            
            # Extract signal info for display
            signal = parsed.get("signal", {})
            action = signal.get("action", "UNKNOWN")
            confidence = signal.get("confidence", 0)
            print(f"   ➡️ 信號: {action}, 信心: {confidence}%")
        
        self.analysis_results["strategies"] = results
        print("✅ 所有策略分析完成")
        
        return results
    
    def _run_debate_rounds(
        self,
        market_id: str,
        analysis_results: Dict[str, Any],
        max_rounds: int = 4,
        min_rounds: int = 2,
    ) -> Dict[str, Any]:
        """Run multi-round debate between agents."""
        print(f"🎯 開始辯論 (最少 {min_rounds} 輪, 最多 {max_rounds} 輪)")
        
        # Prepare initial analyses for debate
        previous_analyses = json.dumps(analysis_results, indent=2, ensure_ascii=False)
        debate_history_str = ""
        all_rounds = []
        
        for round_num in range(1, max_rounds + 1):
            print(f"\n📢 辯論第 {round_num} 輪")
            
            round_results = {}
            
            # Each trading agent participates in debate
            for agent in self.trading_agents:
                print(f"   💬 {agent.role} 發言中...")
                
                task = create_debate_round_task(
                    agent=agent,
                    market_id=market_id,
                    round_number=round_num,
                    previous_analyses=previous_analyses,
                    debate_history=debate_history_str,
                )
                
                crew = Crew(
                    agents=[agent],
                    tasks=[task],
                    verbose=self.config.verbose,
                )
                
                result = crew.kickoff()
                parsed = parse_json_response(str(result)) or {"raw_result": str(result)}
                round_results[agent.role] = parsed
            
            all_rounds.append(round_results)
            
            # Update debate history for next round
            debate_history_str += f"\n--- 第 {round_num} 輪 ---\n"
            debate_history_str += json.dumps(round_results, indent=2, ensure_ascii=False)
            
            # Check if we should continue debate (after minimum rounds)
            if round_num >= min_rounds:
                # Extract signals for divergence calculation
                signals = []
                for agent_role, result in round_results.items():
                    signal = result.get("updated_signal", {})
                    signals.append({
                        "agent": agent_role,
                        "action": signal.get("action", "HOLD"),
                        "confidence": signal.get("confidence", 50),
                    })
                
                divergence = calculate_debate_divergence(signals)
                decision = should_continue_debate(
                    divergence["overall_divergence"],
                    round_num,
                    max_rounds,
                    self.config.risk.disagreement_threshold,
                )
                
                print(f"   📊 分歧度: {divergence['overall_divergence']:.1f}%")
                
                if not decision["continue"]:
                    print(f"   ✅ {decision['reason']}")
                    break
                else:
                    print(f"   ⚠️ {decision['reason']}")
        
        # Supervisor summarizes debate
        print("\n👔 監督官總結辯論...")
        
        summary_task = create_debate_summary_task(
            supervisor_agent=self.supervisor,
            market_id=market_id,
            all_debate_rounds=debate_history_str,
            round_count=len(all_rounds),
        )
        
        summary_crew = Crew(
            agents=[self.supervisor],
            tasks=[summary_task],
            verbose=self.config.verbose,
        )
        
        summary_result = summary_crew.kickoff()
        summary_parsed = parse_json_response(str(summary_result)) or {"raw_result": str(summary_result)}
        
        self.debate_history = all_rounds
        
        return {
            "total_rounds": len(all_rounds),
            "rounds": all_rounds,
            "summary": summary_parsed,
        }
    
    def _make_final_decision(
        self,
        market_id: str,
        market_question: str,
        analysis_results: Dict[str, Any],
        debate_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Make final trading decision."""
        print("🎯 監督官做出最終決策...")
        
        # Get portfolio status
        portfolio_status = get_portfolio_status()
        
        # Prepare all analyses summary
        all_analyses = json.dumps(analysis_results, indent=2, ensure_ascii=False)
        debate_summary = json.dumps(debate_result.get("summary", {}), indent=2, ensure_ascii=False)
        
        # Check if human consultation is needed
        summary = debate_result.get("summary", {})
        next_step = summary.get("next_step", {}).get("action", "PROCEED_TO_DECISION")
        
        if next_step == "REQUEST_HUMAN_INPUT":
            print("⚠️ 需要人類介入！")
            return self._request_human_input(market_id, analysis_results, debate_result)
        
        # Create final decision task
        decision_task = create_final_decision_task(
            supervisor_agent=self.supervisor,
            market_id=market_id,
            market_question=market_question,
            all_analyses=all_analyses,
            debate_summary=debate_summary,
            portfolio_status=portfolio_status,
        )
        
        decision_crew = Crew(
            agents=[self.supervisor],
            tasks=[decision_task],
            verbose=self.config.verbose,
        )
        
        result = decision_crew.kickoff()
        decision = parse_json_response(str(result)) or {"raw_result": str(result)}
        
        # Check if human review is required
        if decision.get("human_review_required", False):
            print("⚠️ 決策需要人類審核！")
            decision["human_review_pending"] = True
        
        return decision
    
    def _request_human_input(
        self,
        market_id: str,
        analysis_results: Dict[str, Any],
        debate_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Request human input when needed."""
        situation_summary = f"""
        市場 {market_id} 的分析顯示團隊存在重大分歧。
        
        策略信號摘要:
        - 動量策略: {analysis_results.get('momentum', {}).get('signal', {}).get('action', 'N/A')}
        - 均值回歸: {analysis_results.get('mean_reversion', {}).get('signal', {}).get('action', 'N/A')}
        - 套利策略: {analysis_results.get('arbitrage', {}).get('signal', {}).get('action', 'N/A')}
        
        辯論總結:
        {json.dumps(debate_result.get('summary', {}), indent=2, ensure_ascii=False)[:500]}
        """
        
        specific_questions = """
        1. 你對這個市場有什麼額外的資訊或看法？
        2. 你傾向於哪個策略的觀點？
        3. 你是否允許在這個市場進行交易？
        """
        
        task = create_human_consultation_task(
            supervisor_agent=self.supervisor,
            market_id=market_id,
            situation_summary=situation_summary,
            specific_questions=specific_questions,
            urgency_level="MEDIUM",
        )
        
        crew = Crew(
            agents=[self.supervisor],
            tasks=[task],
            verbose=self.config.verbose,
        )
        
        result = crew.kickoff()
        consultation = parse_json_response(str(result)) or {"raw_result": str(result)}
        
        # Print human-friendly message
        human_msg = consultation.get("human_friendly_message", "需要人類輸入")
        print("\n" + "=" * 60)
        print(human_msg)
        print("=" * 60 + "\n")
        
        return {
            "status": "AWAITING_HUMAN_INPUT",
            "consultation_request": consultation,
            "preliminary_analyses": analysis_results,
            "debate_summary": debate_result,
        }
    
    def _display_results(self, decision: Dict[str, Any]):
        """Display the final results."""
        print("\n" + "═" * 70)
        
        if decision.get("status") == "AWAITING_HUMAN_INPUT":
            print("⏳ 狀態: 等待人類輸入")
            return
        
        # Display formatted decision
        print(format_decision_for_display(decision))
        
        # Display simulation output
        print(generate_simulation_output(decision))
        
        # Final summary
        print("\n📋 分析完成！這是模擬模式，未執行真實交易。")
        print("═" * 70)
    
    def provide_human_input(
        self,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Provide human input to continue the analysis.
        
        Args:
            input_data: Human's responses to the consultation questions
        
        Returns:
            Updated decision after incorporating human input
        """
        if not self.current_market_id:
            return {"error": "No pending analysis to provide input for"}
        
        print_section("處理人類輸入")
        print(f"收到輸入: {json.dumps(input_data, indent=2, ensure_ascii=False)}")
        
        # Re-run final decision with human guidance
        # This is a simplified implementation
        # In production, you would incorporate the human input more thoroughly
        
        return {
            "status": "HUMAN_INPUT_RECEIVED",
            "input": input_data,
            "message": "感謝您的輸入！系統將根據您的指導重新評估。",
        }


def create_crew() -> PolymarketTradingCrew:
    """Factory function to create a new trading crew."""
    return PolymarketTradingCrew()


# Convenience function for quick analysis
def analyze(market_id: str, question: str = "") -> Dict[str, Any]:
    """
    Quick analysis function.
    
    Args:
        market_id: Market to analyze
        question: Optional market question
    
    Returns:
        Analysis results
    """
    crew = create_crew()
    return crew.analyze_market(market_id, question)
