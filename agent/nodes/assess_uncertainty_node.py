"""
Step 4: Assess Uncertainty Node.
Quantifies 4-pillar data completeness, signal conflict, and composite confidence.
Determines whether a controlled evidence-gathering loop is required.
"""

import time
from typing import Dict, Any
from agent.state import AgentState
from agent.decision_matrix import calculate_uncertainty, determine_next_best_actions


def assess_uncertainty_node(state: AgentState) -> AgentState:
    """Step 4: Computes uncertainty metrics, initial actions before evidence, and evaluates evidence adequacy."""
    trigger_data = state.get("trigger_data", {})
    graph_evidence = state.get("graph_evidence", {})
    typology_matches = state.get("typology_matches", [{}])
    top_typology = typology_matches[0] if typology_matches else {}

    # Initial uncertainty calculation
    uncertainty = calculate_uncertainty(
        trigger_data=trigger_data,
        graph_evidence=graph_evidence,
        typology_match=top_typology,
        has_additional_evidence=False,
    )

    # Initial Next-Best Actions evaluated before any additional evidence is gathered
    actions_before = determine_next_best_actions(
        uncertainty=uncertainty,
        trigger_data=trigger_data,
        graph_evidence=graph_evidence,
        typology_match=top_typology,
    )

    # Check if confidence is below threshold (0.75) or signal conflict is high
    requires_gathering_loop = bool(
        uncertainty["composite_confidence"] < 0.75
        or uncertainty["signal_conflict"] > 0.35
        or trigger_data.get("requires_stepup", False)
    )

    trajectory = {
        "before_additional_evidence": uncertainty.copy(),
        "additional_evidence_gathered": [],
        "after_additional_evidence": {},
        "what_changed": "Baseline evidence assessed.",
    }

    history = state.get("step_history", [])
    history.append({
        "step": 5,
        "name": "Multi-Pillar Uncertainty Assessment",
        "timestamp": int(time.time()),
        "status": "completed",
        "details": f"Completeness: {uncertainty['data_completeness']:.2f}, Conflict: {uncertainty['signal_conflict']:.2f}, Conf: {uncertainty['composite_confidence']:.2f}, Loop Required: {requires_gathering_loop}",
    })

    return {
        **state,
        "uncertainty_metrics": uncertainty,
        "requires_gathering_loop": requires_gathering_loop,
        "evidence_trajectory": trajectory,
        "next_best_actions_before_evidence": actions_before,
        "step_history": history,
    }
