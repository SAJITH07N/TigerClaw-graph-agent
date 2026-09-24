"""
Uncertainty Engine & Next-Best Action Decision Matrix.
Quantifies 4-pillar data completeness, signal conflict, composite confidence,
and maps (Risk x Confidence) to permission-gated next-best actions.
"""

from typing import Dict, List, Any, Tuple
import math


def calculate_uncertainty(
    trigger_data: Dict[str, Any],
    graph_evidence: Dict[str, Any],
    typology_match: Dict[str, Any],
    has_additional_evidence: bool = False,
) -> Dict[str, Any]:
    """
    Quantifies multi-pillar uncertainty across 4 dimensions:
    1. P_txn: Transaction history & velocity signals
    2. P_dev: Device and biometric identity signals
    3. P_behav: Account behavioral baseline stability
    4. P_prior: Historical case memory pattern match
    """
    # 1. P_txn Score (0.0 to 1.0)
    p_txn = 0.5
    if "velocity" in graph_evidence:
        p_txn += 0.3
    if float(trigger_data.get("amount", 0)) > 0:
        p_txn += 0.2
    p_txn = min(p_txn, 1.0)

    # 2. P_dev Score (0.0 to 1.0)
    dev_id = trigger_data.get("device_id")
    p_dev = 0.4 if dev_id and dev_id != "DEV-UNKNOWN" else 0.1
    if trigger_data.get("is_known_device") or trigger_data.get("is_emulator"):
        p_dev += 0.4
    if has_additional_evidence:
        p_dev += 0.2
    p_dev = min(p_dev, 1.0)

    # 3. P_behav Score (0.0 to 1.0)
    tenure = int(trigger_data.get("tenure_months", 12))
    p_behav = 0.5 if tenure > 6 else 0.3
    if "historical_avg_amount" in trigger_data or "historical_velocity" in trigger_data:
        p_behav += 0.3
    if has_additional_evidence:
        p_behav += 0.2
    p_behav = min(p_behav, 1.0)

    # 4. P_prior Score (0.0 to 1.0)
    prior_cases = graph_evidence.get("prior_cases", [])
    if prior_cases:
        top_sim = max(float(c.get("similarity_score", 0.0)) for c in prior_cases)
        p_prior = round(min(max(top_sim, 0.4), 1.0), 2)
    else:
        p_prior = 0.3

    # Multi-pillar weighted completeness
    w_txn, w_dev, w_behav, w_prior = 0.30, 0.30, 0.20, 0.20
    data_completeness = round(w_txn * p_txn + w_dev * p_dev + w_behav * p_behav + w_prior * p_prior, 4)

    # Signal conflict index: divergence between high transaction risk and benign device/tenure
    txn_risk = float(trigger_data.get("risk_score", 0.5))
    device_clean = 1.0 if trigger_data.get("is_known_device") else 0.0
    tenure_clean = 1.0 if tenure >= 24 else 0.0
    conflict_raw = abs(txn_risk - (device_clean * 0.5 + tenure_clean * 0.5))
    signal_conflict = round(min(max(conflict_raw, 0.0), 1.0), 4)

    # If additional evidence resolved the ambiguity, reduce conflict
    if has_additional_evidence:
        signal_conflict = round(signal_conflict * 0.25, 4)
        data_completeness = round(min(data_completeness + 0.20, 0.98), 4)

    # Composite confidence
    composite_confidence = round(data_completeness * (1.0 - 0.45 * signal_conflict), 4)

    # Derive Risk Level
    if txn_risk >= 0.85 or graph_evidence.get("device_ring", {}).get("is_mule_ring", False):
        risk_level = "critical"
    elif txn_risk >= 0.70 or graph_evidence.get("card_fanout", {}).get("is_anomalous_fanout", False):
        risk_level = "high"
    elif txn_risk >= 0.45:
        risk_level = "medium"
    else:
        risk_level = "low"

    # If legitimate typology confirmed with low conflict, adjust risk level
    if typology_match.get("name") == "Legitimate Vacation / Seasonal Travel" and trigger_data.get("stepup_verified"):
        risk_level = "low"

    return {
        "data_completeness": data_completeness,
        "signal_conflict": signal_conflict,
        "composite_confidence": composite_confidence,
        "risk_level": risk_level,
        "pillar_scores": {
            "p_txn": round(p_txn, 2),
            "p_dev": round(p_dev, 2),
            "p_behav": round(p_behav, 2),
            "p_prior": round(p_prior, 2),
        },
    }


def _safe_suffix(val: Any, n: int = 4) -> str:
    s = str(val or "UNKNOWN")
    return s[-n:] if len(s) >= n else s


def determine_next_best_actions(
    uncertainty: Dict[str, Any],
    trigger_data: Dict[str, Any],
    graph_evidence: Dict[str, Any],
    typology_match: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Evaluates the 2D Risk x Confidence decision matrix and routes actions through permission tiers.
    """
    risk = uncertainty["risk_level"]
    conf = uncertainty["composite_confidence"]
    card_id = trigger_data.get("card_id", "CARD-UNKNOWN")
    account_id = trigger_data.get("account_id", "ACC-UNKNOWN")
    amount = float(trigger_data.get("amount", 0.0))
    actions: List[Dict[str, Any]] = []

    c_suf = _safe_suffix(card_id)
    a_suf = _safe_suffix(account_id)

    if risk == "critical":
        # Critical Risk: Immediate containment
        actions.append({
            "action_id": f"ACT-LOCK-{c_suf}",
            "action_type": "temporary_card_lock",
            "target_entity": card_id,
            "approval_route": "auto_executable",
            "permission_level": "Tier-0 Automated",
            "rationale": "High-risk anomaly / syndicate pattern detected. Autonomous lock executed to prevent fund drain.",
            "policy_citation": "POL-FRM-2026 Clause 1.1",
            "status": "executed",
        })
        actions.append({
            "action_id": f"ACT-FREEZE-{a_suf}",
            "action_type": "freeze_account_credits_debits",
            "target_entity": account_id,
            "approval_route": "tier1_analyst",
            "permission_level": "Tier-1 Fraud Analyst",
            "rationale": f"Critical risk score ({risk}) with multi-entity syndicate involvement. Freezing account.",
            "policy_citation": "POL-FRM-2026 Clause 1.2",
            "status": "pending_approval" if conf < 0.90 else "executed",
        })
        if amount >= 2500.0:
            actions.append({
                "action_id": f"ACT-REVOKE-{c_suf}",
                "action_type": "permanent_card_revocation_reissue",
                "target_entity": card_id,
                "approval_route": "tier2_approval",
                "permission_level": "Tier-2 Dual-Control Lead",
                "rationale": f"High value unauthorized exposure (${amount:,.2f}). Requiring Tier-2 card revocation.",
                "policy_citation": "POL-FRM-2026 Clause 1.2",
                "status": "pending_approval",
            })
    elif risk == "high":
        actions.append({
            "action_id": f"ACT-SMS-{a_suf}",
            "action_type": "out_of_band_sms_verification",
            "target_entity": account_id,
            "approval_route": "auto_executable",
            "permission_level": "Tier-0 Automated",
            "rationale": "High risk pattern detected. Dispatched out-of-band verification challenge.",
            "policy_citation": "POL-FRM-2026 Clause 2.3",
            "status": "executed",
        })
        actions.append({
            "action_id": f"ACT-LOCK-{c_suf}",
            "action_type": "temporary_card_lock",
            "target_entity": card_id,
            "approval_route": "auto_executable",
            "permission_level": "Tier-0 Automated",
            "rationale": "Temporary lock pending customer verification of anomalous transaction.",
            "policy_citation": "POL-FRM-2026 Clause 1.1",
            "status": "executed",
        })
    elif risk == "medium":
        actions.append({
            "action_id": f"ACT-STEPUP-{a_suf}",
            "action_type": "stepup_mfa_challenge",
            "target_entity": account_id,
            "approval_route": "auto_executable",
            "permission_level": "Tier-0 Automated",
            "rationale": "Medium uncertainty / unrecognized device. Step-up MFA challenge initiated.",
            "policy_citation": "POL-FRM-2026 Clause 2.2",
            "status": "executed",
        })
        actions.append({
            "action_id": f"ACT-MONITOR-{a_suf}",
            "action_type": "enhanced_velocity_monitoring",
            "target_entity": account_id,
            "approval_route": "auto_executable",
            "permission_level": "Tier-0 Automated",
            "rationale": "Account placed on 48-hour enhanced velocity watch.",
            "policy_citation": "POL-FRM-2026 Clause 2.1",
            "status": "executed",
        })
    else:  # low risk / legitimate false positive
        actions.append({
            "action_id": f"ACT-CLEAR-{a_suf}",
            "action_type": "clear_transaction_alert",
            "target_entity": account_id,
            "approval_route": "auto_executable",
            "permission_level": "Tier-0 Automated",
            "rationale": "Legitimate customer behavior verified via device history / step-up auth. Alert cleared.",
            "policy_citation": "POL-FRM-2026 Clause 1.1",
            "status": "executed",
        })

    return actions
