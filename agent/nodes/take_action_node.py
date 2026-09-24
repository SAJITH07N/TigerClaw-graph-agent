"""
Step 6: Take Action Node.
Maps uncertainty and risk to permission-gated Next-Best Actions (NBA),
evaluates FinCEN SAR filing eligibility, and executes actions.
"""

import time
from typing import Dict, Any, List
from agent.state import AgentState
from agent.decision_matrix import determine_next_best_actions
from agent.mock_actions import BankingActionExecutor
from graphrag.sar_generator import SARGenerator


def take_action_node(state: AgentState, sar_gen: SARGenerator) -> AgentState:
    """Step 6: Recommends, gates, and dispatches Next-Best Actions."""
    uncertainty = state.get("uncertainty_metrics", {})
    trigger_data = state.get("trigger_data", {})
    graph_evidence = state.get("graph_evidence", {})
    typology_matches = state.get("typology_matches", [{}])
    top_typology = typology_matches[0] if typology_matches else {}
    entities = state.get("entities", {})

    # 1. Determine Next-Best Actions from 2D Matrix
    raw_actions = determine_next_best_actions(
        uncertainty=uncertainty,
        trigger_data=trigger_data,
        graph_evidence=graph_evidence,
        typology_match=top_typology,
    )

    # 2. Execute / Gate Actions
    executed_actions = []
    for act in raw_actions:
        exec_res = BankingActionExecutor.execute_action(act)
        act["status"] = exec_res["status"]
        executed_actions.append(act)

    # 3. Evaluate FinCEN SAR Filing Eligibility (Only for High/Critical Risk)
    total_amount = float(trigger_data.get("amount", 0.0))
    risk_level = uncertainty.get("risk_level", "low")
    is_syndicate = bool(
        graph_evidence.get("device_ring", {}).get("is_mule_ring")
        or "linked_mule_accounts" in trigger_data
        or "fanout_accounts" in trigger_data
    )
    has_suspect = bool(entities.get("devices") or entities.get("accounts"))

    sar_filing = None
    if risk_level in ["high", "critical"] and sar_gen.check_filing_eligibility(total_amount, has_suspect, is_syndicate):
        sar_filing = sar_gen.generate_sar(
            case_id=state.get("case_id", "CASE-001"),
            suspect_entities=entities,
            transaction_summary={
                "total_amount": total_amount,
                "transactions": [trigger_data],
                "velocity_1h_count": graph_evidence.get("velocity", {}).get("velocity_1h_count", 1),
                "velocity_1h_volume": total_amount,
                "velocity_zscore": graph_evidence.get("velocity", {}).get("velocity_zscore", 0.0),
            },
            graph_findings={
                "summary": f"Detected typology {top_typology.get('name')}. Coordinated multi-entity graph patterns.",
                "max_pagerank_risk": "0.89",
                "community_size": len(entities.get("accounts", [1])),
            },
            typology_match=top_typology,
            actions_taken=executed_actions,
        )

    history = state.get("step_history", [])
    history.append({
        "step": 8,
        "name": "Next-Best Action Determination & Permissions Gating",
        "timestamp": int(time.time()),
        "status": "completed",
        "details": f"Generated {len(executed_actions)} actions. SAR Required: {sar_filing is not None}.",
    })

    return {
        **state,
        "next_best_actions": executed_actions,
        "next_best_actions_after_evidence": executed_actions,
        "sar_filing": sar_filing,
        "step_history": history,
    }
