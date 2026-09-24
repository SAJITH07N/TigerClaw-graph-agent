"""
Step: Adversarial Counterfactual Check Node.
Evaluates competing benign vs fraudulent hypotheses to protect against false positives
and ensure calibrated risk assessment prior to action execution.
"""

import time
from typing import Dict, Any, List
from agent.state import AgentState


def counterfactual_node(state: AgentState) -> AgentState:
    """Evaluates alternative hypotheses (benign explanations) against observed graph evidence."""
    trigger_data = state.get("trigger_data", {})
    graph_evidence = state.get("graph_evidence", {})
    uncertainty = state.get("uncertainty_metrics", {})
    typology_matches = state.get("typology_matches", [{}])
    top_typology = typology_matches[0] if typology_matches else {}

    amount = float(trigger_data.get("amount", 0.0))
    risk_score = float(trigger_data.get("risk_score", 0.5))
    tenure_months = int(trigger_data.get("tenure_months", 12))
    is_known_device = bool(trigger_data.get("is_known_device", False))
    stepup_verified = bool(trigger_data.get("stepup_verified", False))

    device_ring = graph_evidence.get("device_ring", {})
    card_fanout = graph_evidence.get("card_fanout", {})
    temporal_burst = graph_evidence.get("temporal_burst", {})
    circular_routing = graph_evidence.get("circular_routing", {})
    merchant_collusion = graph_evidence.get("merchant_collusion", {})

    hypotheses: List[Dict[str, Any]] = []

    # Hypothesis 1: Legitimate High-Value Purchase / Authorized Travel
    h1_plausibility = 0.1
    if is_known_device:
        h1_plausibility += 0.35
    if stepup_verified:
        h1_plausibility += 0.45
    if tenure_months >= 24:
        h1_plausibility += 0.15
    if device_ring.get("is_mule_ring") or card_fanout.get("is_anomalous_fanout"):
        h1_plausibility = max(0.05, h1_plausibility - 0.40)
    hypotheses.append({
        "hypothesis": "Authorized Cardholder / Legitimate Travel Activity",
        "plausibility": round(min(1.0, h1_plausibility), 2),
        "supporting_factors": [
            f"Account tenure: {tenure_months} months",
            f"Known device status: {is_known_device}",
            f"Step-up verification status: {stepup_verified}",
        ],
    })

    # Hypothesis 2: Shared Household Device / Authorized Delegate
    h2_plausibility = 0.05
    if device_ring.get("associated_accounts_count", 0) in [1, 2] and not device_ring.get("is_mule_ring"):
        h2_plausibility += 0.35
    if tenure_months >= 12:
        h2_plausibility += 0.15
    if device_ring.get("is_mule_ring") or "mule" in str(trigger_data.get("device_id", "")).lower():
        h2_plausibility = 0.02
    hypotheses.append({
        "hypothesis": "Shared Household Device or Authorized Family Delegate",
        "plausibility": round(min(1.0, h2_plausibility), 2),
        "supporting_factors": [
            f"Device account count: {device_ring.get('associated_accounts_count', 1)}",
            f"Mule ring detected: {device_ring.get('is_mule_ring', False)}",
        ],
    })

    # Hypothesis 3: Merchant Promotional Surge / Benign High Velocity
    h3_plausibility = 0.05
    if temporal_burst.get("burst_detected") and not temporal_burst.get("is_card_testing"):
        h3_plausibility += 0.30
    if not temporal_burst.get("burst_detected"):
        h3_plausibility += 0.10
    hypotheses.append({
        "hypothesis": "Merchant Flash Sale / Benign Velocity Spike",
        "plausibility": round(min(1.0, h3_plausibility), 2),
        "supporting_factors": [
            f"Card testing indicators: {temporal_burst.get('is_card_testing', False)}",
            f"Micro-charges count: {temporal_burst.get('micro_charges_count', 0)}",
        ],
    })

    # Sort hypotheses by plausibility
    hypotheses.sort(key=lambda h: h["plausibility"], reverse=True)
    strongest = hypotheses[0]

    # Calculate overall fraud vs benign probability
    syndicate_signals = (
        (1.0 if device_ring.get("is_mule_ring") else 0.0)
        + (1.0 if card_fanout.get("is_anomalous_fanout") else 0.0)
        + (1.0 if temporal_burst.get("is_card_testing") else 0.0)
        + (1.0 if circular_routing.get("is_circular_routing") else 0.0)
        + (1.0 if merchant_collusion.get("is_collusion_detected") else 0.0)
    )

    if stepup_verified or (is_known_device and risk_score < 0.45):
        fraud_vs_benign_conf = 0.15
        false_positive_risk = 0.85
        recommendation = "DISMISS_AS_BENIGN"
    elif syndicate_signals >= 2 or risk_score >= 0.80:
        fraud_vs_benign_conf = min(0.98, 0.75 + (0.08 * syndicate_signals))
        false_positive_risk = round(1.0 - fraud_vs_benign_conf, 2)
        recommendation = "CONFIRM_CONTAINMENT"
    elif uncertainty.get("composite_confidence", 0.5) < 0.70:
        fraud_vs_benign_conf = 0.55
        false_positive_risk = 0.45
        recommendation = "REQUIRE_STEPUP"
    else:
        fraud_vs_benign_conf = round(risk_score, 2)
        false_positive_risk = round(1.0 - risk_score, 2)
        recommendation = "CONFIRM_CONTAINMENT" if risk_score >= 0.70 else "MONITOR"

    counterfactual_result = {
        "strongest_counterfactual": strongest["hypothesis"],
        "strongest_counterfactual_plausibility": strongest["plausibility"],
        "hypotheses_evaluated": hypotheses,
        "fraud_vs_benign_confidence": fraud_vs_benign_conf,
        "false_positive_risk": false_positive_risk,
        "recommendation": recommendation,
        "adversarial_audit_note": (
            f"Adversarial analysis evaluated {len(hypotheses)} benign hypotheses. "
            f"Leading counterfactual: '{strongest['hypothesis']}' (plausibility {strongest['plausibility']}). "
            f"Fraud confidence calibrated at {fraud_vs_benign_conf:.2f} with false-positive risk of {false_positive_risk:.2f}. "
            f"Recommendation: {recommendation}."
        ),
    }

    history = state.get("step_history", [])
    history.append({
        "step": 7,
        "name": "Adversarial Counterfactual Check",
        "timestamp": int(time.time()),
        "status": "completed",
        "details": f"Top counterfactual: {strongest['hypothesis']} ({strongest['plausibility']:.2f}). Fraud Conf: {fraud_vs_benign_conf:.2f}. Rec: {recommendation}.",
    })

    return {
        **state,
        "counterfactual_analysis": counterfactual_result,
        "step_history": history,
    }
