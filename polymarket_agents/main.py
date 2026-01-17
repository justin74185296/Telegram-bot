#!/usr/bin/env python3
"""
Polymarket Multi-Agent Trading System
=====================================

Main entry point for running the trading analysis system.

Usage:
    python -m polymarket_agents.main --market <market_id> [--question <question>]
    
Example:
    python -m polymarket_agents.main --market "will-bitcoin-reach-100k-2025" --question "Will Bitcoin reach $100,000 by end of 2025?"
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from polymarket_agents.crew import PolymarketTradingCrew, create_crew
from polymarket_agents.config import get_config, validate_config
from polymarket_agents.tools.market_data import get_available_markets


def print_welcome():
    """Print welcome banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║     🎯 POLYMARKET 多代理交易分析系統 (Multi-Agent Trading System)      ║
║                                                                          ║
║     團隊成員:                                                            ║
║     👔 監督官 (Supervisor) - Claude Opus 4.5                            ║
║     📈 動量交易員 (Momentum Trader) - Claude Sonnet 4.5                 ║
║     📊 均值回歸交易員 (Mean Reversion Trader) - Claude Sonnet 4.5       ║
║     ⚖️  套利交易員 (Arbitrage Trader) - Claude Sonnet 4.5               ║
║     🔍 數據優化師 (Data Optimizer) - Claude Sonnet 4.5                  ║
║                                                                          ║
║     ⚠️  模擬模式 - 不執行真實交易                                       ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_available_markets():
    """Print list of available mock markets."""
    markets = get_available_markets()
    print("\n📋 可用的模擬市場:")
    print("-" * 60)
    for market_id in markets:
        print(f"  • {market_id}")
    print("-" * 60)
    print()


def run_analysis(
    market_id: str,
    market_question: str = "",
    verbose: bool = True,
    save_output: bool = True,
) -> dict:
    """
    Run the complete trading analysis.
    
    Args:
        market_id: Market to analyze
        market_question: Optional market question
        verbose: Whether to print verbose output
        save_output: Whether to save output to file
    
    Returns:
        Analysis results dictionary
    """
    # Validate configuration
    if not validate_config():
        print("❌ 配置驗證失敗。請設置 ANTHROPIC_API_KEY 環境變數。")
        print("   export ANTHROPIC_API_KEY='your-api-key'")
        return {"error": "Configuration validation failed"}
    
    # Create and run crew
    crew = create_crew()
    
    try:
        results = crew.analyze_market(
            market_id=market_id,
            market_question=market_question,
        )
        
        # Save results if requested
        if save_output:
            output_filename = f"analysis_{market_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n💾 結果已保存至: {output_filename}")
        
        return results
        
    except Exception as e:
        print(f"\n❌ 分析過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def interactive_mode():
    """Run in interactive mode, prompting user for input."""
    print_welcome()
    print_available_markets()
    
    while True:
        print("\n" + "=" * 60)
        market_id = input("請輸入市場 ID (或 'quit' 退出): ").strip()
        
        if market_id.lower() in ['quit', 'exit', 'q']:
            print("\n👋 感謝使用！再見！")
            break
        
        if not market_id:
            print("❌ 請輸入有效的市場 ID")
            continue
        
        question = input("請輸入市場問題 (可選，按 Enter 跳過): ").strip()
        
        print("\n🚀 開始分析...")
        results = run_analysis(market_id, question)
        
        if "error" not in results:
            print("\n✅ 分析完成！")
            
            # Ask if user wants to continue
            continue_choice = input("\n是否繼續分析其他市場？(y/n): ").strip().lower()
            if continue_choice != 'y':
                print("\n👋 感謝使用！再見！")
                break


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Polymarket Multi-Agent Trading Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a specific market
  python -m polymarket_agents.main --market "will-bitcoin-reach-100k-2025"
  
  # With market question
  python -m polymarket_agents.main --market "will-bitcoin-reach-100k-2025" \\
      --question "Will Bitcoin reach $100,000 by end of 2025?"
  
  # Interactive mode
  python -m polymarket_agents.main --interactive
  
  # List available mock markets
  python -m polymarket_agents.main --list-markets
        """
    )
    
    parser.add_argument(
        "--market", "-m",
        type=str,
        help="Market ID to analyze"
    )
    
    parser.add_argument(
        "--question", "-q",
        type=str,
        default="",
        help="Market question (optional)"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    
    parser.add_argument(
        "--list-markets", "-l",
        action="store_true",
        help="List available mock markets"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=True,
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save output to file"
    )
    
    args = parser.parse_args()
    
    # List markets mode
    if args.list_markets:
        print_available_markets()
        return
    
    # Interactive mode
    if args.interactive or (not args.market and not args.list_markets):
        interactive_mode()
        return
    
    # Single analysis mode
    if args.market:
        print_welcome()
        run_analysis(
            market_id=args.market,
            market_question=args.question,
            verbose=args.verbose,
            save_output=not args.no_save,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
