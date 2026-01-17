"""
Polymarket Trading Tasks Module
===============================

This module contains task definitions for the trading crew,
including the debate/discussion mechanism and structured outputs.
"""

from .analysis_tasks import (
    create_data_collection_task,
    create_momentum_analysis_task,
    create_mean_reversion_analysis_task,
    create_arbitrage_analysis_task,
)
from .debate_tasks import (
    create_debate_round_task,
    create_debate_summary_task,
)
from .decision_tasks import (
    create_final_decision_task,
    create_human_consultation_task,
)

__all__ = [
    "create_data_collection_task",
    "create_momentum_analysis_task",
    "create_mean_reversion_analysis_task",
    "create_arbitrage_analysis_task",
    "create_debate_round_task",
    "create_debate_summary_task",
    "create_final_decision_task",
    "create_human_consultation_task",
]
