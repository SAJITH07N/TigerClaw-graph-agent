"""
Step 1: Trigger Node.
Ingests and normalizes triggers (Risk Score Alerts, Customer Disputes, Analyst Escalations).
"""

import time
from typing import Dict, Any
from agent.state import AgentState


def trigger_node(state: AgentState) -> AgentState:
    """Step 1: Ingests trigger event and establishes case tracking baseline."""
    case_id = state.get("case_id") or f"CASE-{int(time.time())}"
    trigger_type = state.get("trigger_type", "risk_score_alert")
    trigger_data = state.get("trigger_data", {})

    history = state.get("step_history", [])
    history.append({
        "step": 1,
        "name": "Trigger Ingestion & Normalization",
        "timestamp": int(time.time()),
        "status": "completed",
        "details": f"Ingested {trigger_type} for txn {trigger_data.get('txn_id', 'N/A')}",
    })

    return {
        **state,
        "case_id": case_id,
        "trigger_type": trigger_type,
        "trigger_data": trigger_data,
        "step_history": history,
    }
