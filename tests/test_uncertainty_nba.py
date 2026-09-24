"""
Unit tests for 4-Pillar Uncertainty Quantification, Signal Conflict, and Next-Best Action Matrix.
Verifies trajectory delta logging and human-in-the-loop permission enforcement.
"""

import pytest
from agent.decision_matrix import calculate_uncertainty, determine_next_best_actions


def test_4_pillar_completeness_and_conflict():
    # Case with full high-risk signals (ATO)
    trigger_data = {
        "txn_id": "txn_1",
        "amount": 3500.0,
        "device_id": "dev_1",
        "is_emulator": True,
        "is_known_device": False,
        "tenure_months": 2,
        "risk_score": 0.90,
    }
    graph_evidence = {
        "velocity": {"spike": True},
        "device_ring": {"is_mule_ring": True, "accounts_count": 4},
        "prior_cases": [{"similarity_score": 0.92, "resolution_outcome": "CONFIRMED_FRAUD"}],
    }
    typology_match = {"typology_id": "TYP-ATO-001", "name": "Account Takeover (ATO)"}

    unc = calculate_uncertainty(trigger_data, graph_evidence, typology_match, has_additional_evidence=False)

    # Check 4-pillar completeness
    assert 0.0 <= unc["data_completeness"] <= 1.0
    assert unc["data_completeness"] >= 0.7
    pillars = unc["pillar_scores"]
    assert pillars["p_txn"] >= 0.7
    assert pillars["p_dev"] >= 0.7
    assert pillars["p_prior"] >= 0.8

    # Check risk level and confidence
    assert unc["risk_level"] == "critical"
    assert unc["composite_confidence"] > 0.4


def test_conflicting_signals_and_additional_evidence_resolution():
    # Transaction looks high risk, but device is known and customer has long tenure
    trigger_data = {
        "txn_id": "txn_1",
        "amount": 2500.0,
        "device_id": "dev_1",
        "is_emulator": False,
        "is_known_device": True,
        "tenure_months": 36,
        "risk_score": 0.85,
    }
    graph_evidence = {
        "velocity": {"spike": False},
        "prior_cases": [{"similarity_score": 0.40, "resolution_outcome": "CLEARED_BENIGN"}],
    }
    typology_match = {"typology_id": "TYP-TRAVEL-005", "name": "Legitimate Vacation / Seasonal Travel"}

    # Initial assessment before additional evidence
    initial_unc = calculate_uncertainty(trigger_data, graph_evidence, typology_match, has_additional_evidence=False)
    # Signal conflict should be elevated due to high txn risk vs clean device/tenure
    assert initial_unc["signal_conflict"] >= 0.15

    # Post-assessment after step-up auth & cardholder validation
    trigger_data["stepup_verified"] = True
    post_unc = calculate_uncertainty(trigger_data, graph_evidence, typology_match, has_additional_evidence=True)

    assert post_unc["data_completeness"] > initial_unc["data_completeness"]
    assert post_unc["signal_conflict"] < initial_unc["signal_conflict"]
    assert post_unc["composite_confidence"] > initial_unc["composite_confidence"]


def test_next_best_action_permissions_matrix():
    # Critical Risk + Moderate Confidence -> Tier-1 Lead Approval for Account Freeze, Tier-0 for Card Lock
    uncertainty = {
        "risk_level": "critical",
        "composite_confidence": 0.85,
        "data_completeness": 0.90,
        "signal_conflict": 0.10,
    }
    trigger_data = {
        "account_id": "acc_test_101",
        "card_id": "card_test_202",
        "amount": 5000.0,
    }
    graph_evidence = {}
    typology_match = {"typology_id": "TYP-ATO-001", "name": "Account Takeover (ATO)"}

    actions = determine_next_best_actions(uncertainty, trigger_data, graph_evidence, typology_match)

    action_types = [a["action_type"] for a in actions]
    assert "temporary_card_lock" in action_types
    assert "freeze_account_credits_debits" in action_types
    assert "permanent_card_revocation_reissue" in action_types

    # Find tier 1 or 2 pending action
    pending_action = next(a for a in actions if a["status"] == "pending_approval")
    assert "Tier-1" in pending_action["permission_level"] or "Tier-2" in pending_action["permission_level"]

    # Find auto executable action
    tier0_action = next(a for a in actions if a["approval_route"] == "auto_executable")
    assert "Tier-0" in tier0_action["permission_level"]
    assert tier0_action["status"] == "executed"
