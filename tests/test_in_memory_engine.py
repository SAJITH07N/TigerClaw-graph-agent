"""
Unit tests for TigerGraph high-fidelity in-memory graph and vector engine.
Tests BFS neighborhood queries, PageRank risk diffusion, Louvain/WCC communities,
sliding window velocity checks, and TigerVector cosine similarity.
"""

import pytest
import numpy as np
from tigergraph.in_memory_engine import TigerGraphInMemoryEngine


@pytest.fixture
def engine():
    eng = TigerGraphInMemoryEngine()
    # Add vertices
    eng.upsert_vertex("Account", "acc_101", {"account_holder_name": "Alice Smith", "risk_score": 0.1})
    eng.upsert_vertex("Account", "acc_102", {"account_holder_name": "Bob Jones", "risk_score": 0.2})
    eng.upsert_vertex("Account", "acc_103", {"account_holder_name": "Charlie Brown", "risk_score": 0.8})
    eng.upsert_vertex("Device", "dev_555", {"device_fingerprint": "fp_emu_x86", "risk_score": 0.9})
    eng.upsert_vertex("Card", "card_999", {"card_pan_masked": "411111******1111", "risk_score": 0.3})
    eng.upsert_vertex("Transaction", "txn_001", {"amount": 500.0, "timestamp": 1700000000, "risk_score": 0.85})

    # Add edges
    eng.upsert_edge("HELD_BY", "Card", "card_999", "Account", "acc_101", {})
    eng.upsert_edge("USED_BY", "Device", "dev_555", "Account", "acc_101", {})
    eng.upsert_edge("USED_BY", "Device", "dev_555", "Account", "acc_102", {})
    eng.upsert_edge("USED_BY", "Device", "dev_555", "Account", "acc_103", {})
    eng.upsert_edge("SHARES_DEVICE", "Account", "acc_101", "Account", "acc_102", {"shared_device_id": "dev_555"})
    eng.upsert_edge("SHARES_DEVICE", "Account", "acc_102", "Account", "acc_103", {"shared_device_id": "dev_555"})
    eng.upsert_edge("PAID_WITH", "Transaction", "txn_001", "Card", "card_999", {})
    eng.upsert_edge("FROM_DEVICE", "Transaction", "txn_001", "Device", "dev_555", {})

    return eng


def test_vertex_and_edge_counts(engine):
    assert engine.get_vertex_count() == 6
    assert engine.get_edge_count() >= 8


def test_get_entity_neighborhood_bfs(engine):
    res = engine.get_entity_neighborhood(start_id="txn_001", start_type="Transaction", max_hops=2)
    nodes = {n["id"]: n for n in res.get("nodes", [])}
    edges = res.get("edges", [])

    assert "txn_001" in nodes
    assert "dev_555" in nodes
    assert "card_999" in nodes
    assert "acc_101" in nodes
    assert len(edges) >= 3


def test_shared_device_ring(engine):
    res = engine.shared_device_ring(device_id="dev_555")
    assert res.get("shared_device_id") == "dev_555"
    assert res.get("associated_accounts_count") >= 3
    account_ids = res.get("associated_accounts", [])
    assert "acc_101" in account_ids
    assert "acc_102" in account_ids
    assert "acc_103" in account_ids


def test_shared_card_fanout(engine):
    # Link card to multiple accounts
    engine.upsert_edge("HELD_BY", "Card", "card_999", "Account", "acc_102", {})
    res = engine.shared_card_fanout(card_id="card_999")
    assert res.get("card_id") == "card_999"
    assert res.get("associated_accounts_count") >= 1


def test_pagerank_risk_propagation(engine):
    pr_scores = engine.pagerank_risk_propagation(damping=0.85, max_iter=20)
    assert isinstance(pr_scores, dict)
    assert len(pr_scores) > 0


def test_community_detection(engine):
    communities = engine.community_detection(min_size=2)
    assert isinstance(communities, (list, dict))
    assert len(communities) > 0


def test_velocity_check(engine):
    base_ts = 1700000000
    for i in range(5):
        txn_id = f"txn_vel_{i}"
        engine.upsert_vertex("Transaction", txn_id, {"amount": 100.0 * (i + 1), "timestamp": base_ts + i * 60, "risk_score": 0.5})
        engine.upsert_edge("PAID_WITH", "Transaction", txn_id, "Card", "card_999", {})

    vel = engine.velocity_check(account_id="acc_101", current_ts=base_ts + 300)
    assert "velocity_1h" in vel
    assert "velocity_24h" in vel


def test_tigervector_cosine_similarity(engine):
    v1 = [0.9, 0.1, 0.0, 0.0]
    v2 = [0.85, 0.15, 0.0, 0.0]
    v3 = [0.0, 0.0, 0.9, 0.1]

    engine.upsert_vertex("PriorCase", "CASE-HIST-01", {
        "case_title": "Historical ATO",
        "typology_id": "TYP-ATO-001",
        "embedding": v1,
        "resolution_outcome": "CONFIRMED_FRAUD",
    })
    engine.upsert_vertex("PriorCase", "CASE-HIST-02", {
        "case_title": "Historical Mule Ring",
        "typology_id": "TYP-MULE-002",
        "embedding": v3,
        "resolution_outcome": "CONFIRMED_FRAUD",
    })

    top_matches = engine.similar_case_search(query_vector=v2, top_k=2)
    assert len(top_matches) == 2
    assert top_matches[0]["case_id"] == "CASE-HIST-01"
    assert top_matches[0]["similarity_score"] > 0.95
    assert top_matches[1]["case_id"] == "CASE-HIST-02"
    assert top_matches[1]["similarity_score"] < 0.2


def test_circular_fund_routing_in_memory(engine):
    # Setup circular account structure: acc_c1 -> txn_c1 -> acc_c2 -> txn_c2 -> acc_c1
    engine.upsert_vertex("Account", "acc_c1", {"account_number": "C1"})
    engine.upsert_vertex("Account", "acc_c2", {"account_number": "C2"})
    engine.upsert_vertex("Transaction", "txn_c1", {"amount": 5000.0, "timestamp": 1700000000})
    engine.upsert_vertex("Transaction", "txn_c2", {"amount": 4900.0, "timestamp": 1700000100})

    engine.upsert_edge("ABOUT_ACCOUNT", "Transaction", "txn_c1", "Account", "acc_c1")
    engine.upsert_edge("ABOUT_ACCOUNT", "Transaction", "txn_c1", "Account", "acc_c2")
    engine.upsert_edge("ABOUT_ACCOUNT", "Transaction", "txn_c2", "Account", "acc_c2")
    engine.upsert_edge("ABOUT_ACCOUNT", "Transaction", "txn_c2", "Account", "acc_c1")

    engine.upsert_edge("PAID_WITH", "Account", "acc_c1", "Transaction", "txn_c1")
    engine.upsert_edge("PAID_WITH", "Account", "acc_c2", "Transaction", "txn_c2")

    res = engine.circular_fund_routing(start_account_id="acc_c1", max_depth=4)
    assert "is_circular_routing" in res
    assert "start_account_id" in res
    assert res["start_account_id"] == "acc_c1"


def test_merchant_collusion_ring_in_memory(engine):
    engine.upsert_vertex("Account", "acc_m1", {})
    engine.upsert_vertex("Account", "acc_m2", {})
    engine.upsert_vertex("Device", "dev_m1", {})
    engine.upsert_vertex("Transaction", "txn_m1", {"amount": 250.0, "merchant_id": "MERCH_COLLUDE_01"})
    engine.upsert_vertex("Transaction", "txn_m2", {"amount": 350.0, "merchant_id": "MERCH_COLLUDE_01"})

    engine.upsert_edge("ABOUT_ACCOUNT", "Transaction", "txn_m1", "Account", "acc_m1")
    engine.upsert_edge("ABOUT_ACCOUNT", "Transaction", "txn_m2", "Account", "acc_m2")
    engine.upsert_edge("FROM_DEVICE", "Transaction", "txn_m1", "Device", "dev_m1")
    engine.upsert_edge("FROM_DEVICE", "Transaction", "txn_m2", "Device", "dev_m1")

    res = engine.merchant_collusion_ring(merchant_id="MERCH_COLLUDE_01", min_accounts=2)
    assert res["merchant_id"] == "MERCH_COLLUDE_01"
    assert res["colluding_accounts_count"] >= 2
    assert res["collusion_risk_score"] >= 0.65
    assert res["is_collusion_detected"] is True

