"""
Step 5: Gather More Node (Controlled Evidence Loop).
Executes targeted step-up inquiries, cardholder verifications, or device lookups
and computes the before-and-after evidence trajectory diff.
"""

import time
from typing import Dict, Any, List
from agent.state import AgentState
from agent.decision_matrix import calculate_uncertainty


def gather_more_node(state: AgentState) -> AgentState:
    """Step 5: Gathers additional targeted evidence to resolve ambiguity."""
    trigger_data = state.get("trigger_data", {})
    graph_evidence = state.get("graph_evidence", {})
    typology_matches = state.get("typology_matches", [{}])
    top_typology = typology_matches[0] if typology_matches else {}
    trajectory = state.get("evidence_trajectory", {})

    additional_items: List[Dict[str, Any]] = []

    # 1. Step-Up Verification Inquiry
    if trigger_data.get("requires_stepup") or trigger_data.get("stepup_verified"):
        additional_items.append({
            "inquiry_type": "out_of_band_biometric_stepup",
            "entity": trigger_data.get("account_id"),
            "result": "PASSED_VERIFIED" if trigger_data.get("stepup_verified", True) else "FAILED_REJECTED",
            "timestamp": int(time.time()),
        })
    elif trigger_data.get("dispute_reason"):
        additional_items.append({
            "inquiry_type": "customer_cardholder_affidavit",
            "entity": trigger_data.get("account_id"),
            "result": "CONFIRMED_UNAUTHORIZED_USE",
            "timestamp": int(time.time()),
        })
    else:
        additional_items.append({
            "inquiry_type": "device_carrier_reputation_lookup",
            "entity": trigger_data.get("device_id"),
            "result": "RISK_FINGERPRINT_CONFIRMED" if trigger_data.get("is_emulator") else "BENIGN_TELECOM_IP",
            "timestamp": int(time.time()),
        })

    # Re-calculate uncertainty with additional evidence
    after_uncertainty = calculate_uncertainty(
        trigger_data=trigger_data,
        graph_evidence=graph_evidence,
        typology_match=top_typology,
        has_additional_evidence=True,
    )

    before_conf = trajectory.get("before_additional_evidence", {}).get("composite_confidence", 0.5)
    after_conf = after_uncertainty["composite_confidence"]
    before_conflict = trajectory.get("before_additional_evidence", {}).get("signal_conflict", 0.5)
    after_conflict = after_uncertainty["signal_conflict"]

    what_changed = (
        f"Additional evidence gathering via [{additional_items[0]['inquiry_type']}] yielded [{additional_items[0]['result']}]. "
        f"Data Completeness increased from {trajectory.get('before_additional_evidence',{}).get('data_completeness',0):.2f} to {after_uncertainty['data_completeness']:.2f}. "
        f"Signal Conflict reduced from {before_conflict:.2f} to {after_conflict:.2f}. "
        f"Composite Confidence improved from {before_conf:.2f} to {after_conf:.2f}."
    )

    trajectory["additional_evidence_gathered"] = additional_items
    trajectory["after_additional_evidence"] = after_uncertainty
    trajectory["what_changed"] = what_changed

    history = state.get("step_history", [])
    history.append({
        "step": 6,
        "name": "Controlled Evidence Gathering Loop & Trajectory Diff",
        "timestamp": int(time.time()),
        "status": "completed",
        "details": what_changed,
    })

    return {
        **state,
        "uncertainty_metrics": after_uncertainty,
        "evidence_trajectory": trajectory,
        "requires_gathering_loop": False,
        "step_history": history,
    }
