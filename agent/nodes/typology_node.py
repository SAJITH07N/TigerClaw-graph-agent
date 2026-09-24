"""
Step: Specialized Typology Deep-Dive Node.
Executes multi-specialist graph intelligence to map complex associative indicators
to formal financial crime typologies (ATO, Mule Rings, Card Testing, Synthetic ID, AML Layering, Merchant Collusion).
"""

import time
from typing import Dict, Any, List
from agent.state import AgentState


def typology_node(state: AgentState) -> AgentState:
    """Performs deep-dive typology analysis using multi-query graph indicators."""
    trigger_data = state.get("trigger_data", {})
    graph_evidence = state.get("graph_evidence", {})
    typology_matches = state.get("typology_matches", [])

    device_ring = graph_evidence.get("device_ring", {})
    card_fanout = graph_evidence.get("card_fanout", {})
    velocity = graph_evidence.get("velocity", {})
    temporal_burst = graph_evidence.get("temporal_burst", {})
    circular_routing = graph_evidence.get("circular_routing", {})
    merchant_collusion = graph_evidence.get("merchant_collusion", {})

    amount = float(trigger_data.get("amount", 0.0))
    risk_score = float(trigger_data.get("risk_score", 0.5))
    tenure_months = int(trigger_data.get("tenure_months", 12))
    device_id = str(trigger_data.get("device_id", ""))

    scored_typologies: List[Dict[str, Any]] = []

    # 1. ATO Deep-Dive
    ato_score = 0.0
    if not trigger_data.get("is_known_device", True):
        ato_score += 0.35
    if trigger_data.get("is_emulator") or "emulator" in device_id.lower():
        ato_score += 0.35
    if velocity.get("is_velocity_spike") or risk_score >= 0.70:
        ato_score += 0.25
    scored_typologies.append({
        "typology_id": "TYP-ATO-001",
        "name": "Account Takeover & Device Spoofing",
        "score": round(min(1.0, ato_score), 2),
        "fincen_category": "Cyber-Enabled Identity Theft",
        "gsql_proof": [
            f"Emulator status: {trigger_data.get('is_emulator', False)}",
            f"Velocity Z-Score: {velocity.get('velocity_zscore', 0.0)}",
        ],
    })

    # 2. Mule Ring Deep-Dive
    mule_score = 0.0
    if device_ring.get("is_mule_ring"):
        mule_score += 0.55
    if card_fanout.get("is_anomalous_fanout"):
        mule_score += 0.30
    if "linked_mule_accounts" in trigger_data or "fanout_accounts" in trigger_data:
        mule_score += 0.20
    scored_typologies.append({
        "typology_id": "TYP-MULE-002",
        "name": "Money Mule Syndicate & Hardware Sharing Ring",
        "score": round(min(1.0, mule_score), 2),
        "fincen_category": "Coordinated Mule Account Network",
        "gsql_proof": [
            f"Associated accounts: {device_ring.get('associated_accounts_count', 1)}",
            f"Shared cards count: {card_fanout.get('associated_accounts_count', 1)}",
        ],
    })

    # 3. Card Testing Deep-Dive
    testing_score = 0.0
    if temporal_burst.get("is_card_testing") or trigger_data.get("is_burst"):
        testing_score += 0.60
    if temporal_burst.get("micro_charges_count", 0) >= 2 or amount < 15.0:
        testing_score += 0.30
    scored_typologies.append({
        "typology_id": "TYP-TEST-003",
        "name": "Automated Micro-Charge Card Testing Script",
        "score": round(min(1.0, testing_score), 2),
        "fincen_category": "Automated Script / Card Testing Attack",
        "gsql_proof": [
            f"Burst detected: {temporal_burst.get('burst_detected', False)}",
            f"Micro-charges: {temporal_burst.get('micro_charges_count', 0)}",
        ],
    })

    # 4. Circular Fund Routing / Layering Deep-Dive
    aml_score = 0.0
    if circular_routing.get("is_circular_routing"):
        aml_score += 0.65
        aml_score += min(0.30, 0.10 * circular_routing.get("cycles_count", 1))
    scored_typologies.append({
        "typology_id": "TYP-AML-005",
        "name": "Circular Fund Routing & AML Layering",
        "score": round(min(1.0, aml_score), 2),
        "fincen_category": "Money Laundering: Layering / Circular Flow",
        "gsql_proof": [
            f"Cycles detected: {circular_routing.get('cycles_count', 0)}",
            f"Total routed volume: ${circular_routing.get('total_routed_volume', 0.0):,.2f}",
        ],
    })

    # 5. Merchant Collusion Deep-Dive
    collusion_score = 0.0
    if merchant_collusion.get("is_collusion_detected"):
        collusion_score += 0.60
    if merchant_collusion.get("colluding_accounts_count", 0) >= 2:
        collusion_score += 0.30
    scored_typologies.append({
        "typology_id": "TYP-COLLUDE-006",
        "name": "Merchant Collusion & Coordinated Bust-Out",
        "score": round(min(1.0, collusion_score), 2),
        "fincen_category": "Merchant Fraud & Coordinated Default",
        "gsql_proof": [
            f"Colluding accounts: {merchant_collusion.get('colluding_accounts_count', 0)}",
            f"Collusion risk: {merchant_collusion.get('collusion_risk_score', 0.0)}",
        ],
    })

    # Sort typologies by score
    scored_typologies.sort(key=lambda t: t["score"], reverse=True)
    lead_typology = scored_typologies[0] if scored_typologies else {}

    typology_deep_dive = {
        "lead_typology": lead_typology,
        "all_typologies": scored_typologies,
        "fincen_sar_applicable": lead_typology.get("score", 0.0) >= 0.70,
        "investigation_summary": (
            f"Specialized typology analysis identified [{lead_typology.get('name', 'General Fraud')}] "
            f"as the primary pattern (score: {lead_typology.get('score', 0.0):.2f}). "
            f"FinCEN classification: {lead_typology.get('fincen_category', 'Suspicious Activity')}."
        ),
    }

    history = state.get("step_history", [])
    history.append({
        "step": 4,
        "name": "Specialized Typology Deep-Dive Analysis",
        "timestamp": int(time.time()),
        "status": "completed",
        "details": typology_deep_dive["investigation_summary"],
    })

    return {
        **state,
        "typology_deep_dive": typology_deep_dive,
        "step_history": history,
    }
