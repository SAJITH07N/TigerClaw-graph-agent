"""
Step 8: Update Memory Node.
Persists the completed investigation, evidence subgraph, decisions, and actions
into TigerGraph Tri-Layer Case Memory (Structural, Semantic, Community).
"""

import time
from typing import Dict, Any
from agent.state import AgentState
from tigergraph.client import TigerGraphClient
from graphrag.policy_store import generate_deterministic_embedding


def update_memory_node(state: AgentState, tg_client: TigerGraphClient) -> AgentState:
    """Step 8: Persists case subgraph into TigerGraph memory."""
    case_id = state.get("case_id", f"CASE-{int(time.time())}")
    trigger_data = state.get("trigger_data", {})
    uncertainty = state.get("uncertainty_metrics", {})
    typology = state.get("typology_matches", [{}])[0]
    actions = state.get("next_best_actions", [])
    explanation = state.get("final_explanation", "")

    # Build evidence records
    evidence_payload = []
    for step in state.get("step_history", []):
        evidence_payload.append({
            "evidence_id": f"EV-{case_id}-{step['step']}",
            "type": "investigation_step",
            "source": step["name"],
            "content": step["details"],
            "score_contribution": 0.2,
            "timestamp": step["timestamp"],
        })

    # Build decision records
    decisions_payload = [{
        "decision_id": f"DEC-{case_id}-01",
        "decision_type": "fraud_classification",
        "rationale": f"Classified as {typology.get('name')} with risk {uncertainty.get('risk_level')}.",
        "actor": "LangGraphFraudAgent",
        "timestamp": int(time.time()),
    }]

    # Build action records
    actions_payload = []
    for act in actions:
        actions_payload.append({
            "action_id": act.get("action_id"),
            "action_type": act.get("action_type"),
            "status": act.get("status"),
            "approval_route": act.get("approval_route"),
            "executed_at": int(time.time()),
        })

    summary_embedding = generate_deterministic_embedding(f"{typology.get('name')} {explanation[:200]}")

    payload = {
        "case_id": case_id,
        "status": "closed",
        "risk_level": uncertainty.get("risk_level", "medium"),
        "confidence_score": uncertainty.get("composite_confidence", 0.8),
        "fraud_type_hypothesis": typology.get("name", "Unknown"),
        "summary_embedding": summary_embedding,
        "evidence": evidence_payload,
        "decisions": decisions_payload,
        "actions_taken": actions_payload,
        "target_account_id": trigger_data.get("account_id"),
        "target_transaction_id": trigger_data.get("txn_id"),
        "findings": explanation[:300],
        "confirmed_fraud": uncertainty.get("risk_level") in ["critical", "high"],
    }

    # Write to TigerGraph
    write_result = tg_client.run_installed_query("write_case_subgraph", {"payload": payload})[0]

    history = state.get("step_history", [])
    history.append({
        "step": 10,
        "name": "Graph Case Memory Persistence",
        "timestamp": int(time.time()),
        "status": "completed",
        "details": f"Persisted case {case_id} ({write_result.get('evidence_count', 0)} evidence, {write_result.get('action_count', 0)} actions) to TigerGraph Case Memory.",
    })

    return {
        **state,
        "case_memory_id": case_id,
        "step_history": history,
    }
