"""
Unit tests for GraphRAG Policy Grounding and FinCEN SAR Filing Generator.
Validates 31 CFR § 1020.320 regulatory compliance, citations, and 4-part narrative structure.
"""

import pytest
from graphrag.policy_store import PolicyStore
from graphrag.typology_catalog import TypologyCatalog
from graphrag.sar_generator import SARGenerator


@pytest.fixture(scope="module")
def policy_store():
    return PolicyStore()


@pytest.fixture(scope="module")
def typology_catalog():
    return TypologyCatalog()


def test_policy_store_chunking_and_retrieval(policy_store):
    assert len(policy_store.policies) > 0

    # Query for ATO policies
    results = policy_store.search_policies("Account Takeover and password reset step-up auth", top_k=3)
    assert len(results) > 0
    top_chunk = results[0]
    assert "policy_id" in top_chunk
    assert "text_content" in top_chunk
    assert "clause_id" in top_chunk


def test_typology_catalog_matching(typology_catalog):
    typologies = typology_catalog.typologies
    assert len(typologies) >= 5

    # Match ATO indicators
    matched = typology_catalog.match_typology([
        "emulator_used",
        "new_device_fingerprint",
        "velocity_spike_post_login"
    ])
    assert len(matched) > 0
    assert matched[0]["typology_id"] == "TYP-ATO-001"
    assert matched[0]["name"] == "Account Takeover (ATO)"


def test_fincen_sar_generation():
    generator = SARGenerator()

    # Eligibility check
    assert generator.check_filing_eligibility(total_volume=14500.0, has_identified_suspect=True, is_syndicate=True) is True
    assert generator.check_filing_eligibility(total_volume=500.0, has_identified_suspect=False, is_syndicate=False) is False

    sar_filing = generator.generate_sar(
        case_id="CASE-BM-01",
        suspect_entities={
            "accounts": ["ACC-101", "ACC-102"],
            "cards": ["CARD-999"],
            "devices": ["DEV-555"],
            "addresses": ["ADDR-123"],
        },
        transaction_summary={
            "total_amount": 14500.0,
            "velocity_1h_count": 5,
            "velocity_1h_volume": 14500.0,
            "transactions": [{"txn_id": "TXN-101", "amount": 14500.0, "ts": 1700000000}],
        },
        graph_findings={
            "summary": "Coordinated transfers across 2 mule accounts linked by emulator DEV-555.",
            "max_pagerank_risk": 0.88,
            "community_size": 4,
        },
        typology_match={
            "typology_id": "TYP-MULE-002",
            "name": "Mule Ring / Shared Device Syndicate",
        },
        actions_taken=[
            {"action_type": "SUSPEND_ACCOUNT", "permission_level": "Tier-1 Analyst Approval", "status": "executed"}
        ]
    )

    assert sar_filing is not None
    assert sar_filing["sar_id"].startswith("SAR-")
    assert sar_filing["statutory_trigger"] == "31 CFR § 1020.320 / FinCEN Form 111"
    assert sar_filing["total_suspicious_volume"] == 14500.0

    narrative = sar_filing["narrative_sections"]
    assert "part_1_executive_summary" in narrative
    assert "part_2_graph_connectivity" in narrative
    assert "part_3_chronological_flow" in narrative
    assert "part_4_regulatory_conclusion" in narrative

    # Check 4-part narrative content
    assert "Mule Ring / Shared Device Syndicate" in narrative["part_1_executive_summary"]
    assert "DEV-555" in narrative["part_2_graph_connectivity"]
    assert "$14,500.00" in narrative["part_3_chronological_flow"]
    assert "31 U.S.C. 5318(g)" in narrative["part_4_regulatory_conclusion"]
