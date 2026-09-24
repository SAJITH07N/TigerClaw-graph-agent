"""
Advanced Agent Tiger tests for Counterfactual reasoning, Typology Deep-Dive,
Circular Fund Routing, and Merchant Collusion detection.
"""

import pytest
from tigergraph.client import TigerGraphClient
from agent.workflow import FraudInvestigationWorkflow
from agent.nodes.counterfactual_node import counterfactual_node
from agent.nodes.typology_node import typology_node
from benchmark_runner import setup_benchmark_graph


@pytest.fixture(scope="module")
def tg_client():
    client = TigerGraphClient()
    setup_benchmark_graph(client)
    return client


def test_adversarial_counterfactual_benign_travel():
    state = {
        "case_id": "TEST-BENIGN-001",
        "trigger_data": {
            "amount": 2500.0,
            "risk_score": 0.35,
            "tenure_months": 36,
            "is_known_device": True,
            "stepup_verified": True,
        },
        "graph_evidence": {
            "device_ring": {"is_mule_ring": False, "associated_accounts_count": 1},
            "card_fanout": {"is_anomalous_fanout": False},
            "temporal_burst": {"burst_detected": False},
        },
        "uncertainty_metrics": {
            "composite_confidence": 0.85,
            "risk_level": "low",
        },
        "step_history": [],
    }

    res = counterfactual_node(state)
    cf = res["counterfactual_analysis"]

    assert cf["recommendation"] == "DISMISS_AS_BENIGN"
    assert cf["false_positive_risk"] >= 0.70
    assert cf["fraud_vs_benign_confidence"] <= 0.30
    assert "Authorized Cardholder" in cf["strongest_counterfactual"]


def test_adversarial_counterfactual_mule_syndicate():
    state = {
        "case_id": "TEST-SYNDICATE-001",
        "trigger_data": {
            "amount": 12000.0,
            "risk_score": 0.95,
            "tenure_months": 2,
            "is_known_device": False,
            "stepup_verified": False,
            "device_id": "DEV-MULE-SHARED-99",
        },
        "graph_evidence": {
            "device_ring": {"is_mule_ring": True, "associated_accounts_count": 8},
            "card_fanout": {"is_anomalous_fanout": True, "associated_accounts_count": 5},
            "temporal_burst": {"is_card_testing": True},
            "circular_routing": {"is_circular_routing": True},
            "merchant_collusion": {"is_collusion_detected": True},
        },
        "uncertainty_metrics": {
            "composite_confidence": 0.92,
            "risk_level": "critical",
        },
        "step_history": [],
    }

    res = counterfactual_node(state)
    cf = res["counterfactual_analysis"]

    assert cf["recommendation"] == "CONFIRM_CONTAINMENT"
    assert cf["fraud_vs_benign_confidence"] >= 0.90
    assert cf["false_positive_risk"] <= 0.10


def test_typology_deep_dive_aml_circular():
    state = {
        "trigger_data": {"amount": 8500.0, "risk_score": 0.85, "tenure_months": 6},
        "graph_evidence": {
            "circular_routing": {
                "is_circular_routing": True,
                "cycles_count": 3,
                "total_routed_volume": 25500.0,
            },
            "device_ring": {"is_mule_ring": False},
            "card_fanout": {"is_anomalous_fanout": False},
            "velocity": {"velocity_zscore": 1.2},
            "temporal_burst": {"is_card_testing": False},
            "merchant_collusion": {"is_collusion_detected": False},
        },
        "step_history": [],
    }

    res = typology_node(state)
    tdd = res["typology_deep_dive"]

    assert tdd["lead_typology"]["typology_id"] == "TYP-AML-005"
    assert tdd["lead_typology"]["score"] >= 0.70
    assert "Circular Fund Routing" in tdd["lead_typology"]["name"]
