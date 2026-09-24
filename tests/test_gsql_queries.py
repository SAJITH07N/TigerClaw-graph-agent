"""
Tests for the 10 installed GSQL queries executed via TigerGraphClient.
Verifies parameters, graph execution, and payload return structures.
"""

import pytest
from tigergraph.client import TigerGraphClient
from benchmark_runner import setup_benchmark_graph


@pytest.fixture(scope="module")
def tg_client():
    client = TigerGraphClient()
    setup_benchmark_graph(client)
    return client


def test_query_1_get_entity_neighborhood(tg_client):
    res = tg_client.run_installed_query(
        "get_entity_neighborhood",
        {"start_id": "ACC-USER-101", "start_type": "Account", "max_hops": 2}
    )
    assert len(res) > 0
    subgraph = res[0]
    assert "nodes" in subgraph
    assert "edges" in subgraph
    assert any(n["id"] == "ACC-USER-101" for n in subgraph["nodes"])


def test_query_2_shared_device_ring(tg_client):
    res = tg_client.run_installed_query(
        "shared_device_ring",
        {"device_id": "DEV-MULE-SHARED-99"}
    )
    assert len(res) > 0
    ring = res[0]
    assert ring.get("shared_device_id") == "DEV-MULE-SHARED-99"
    assert ring.get("associated_accounts_count", 0) >= 1


def test_query_3_shared_card_fanout(tg_client):
    res = tg_client.run_installed_query(
        "shared_card_fanout",
        {"card_id": "CARD-4000-03"}
    )
    assert len(res) > 0
    fanout = res[0]
    assert fanout.get("card_id") == "CARD-4000-03"


def test_query_4_velocity_check(tg_client):
    res = tg_client.run_installed_query(
        "velocity_check",
        {"account_id": "ACC-USER-101"}
    )
    assert len(res) > 0
    vel = res[0]
    assert "velocity_1h" in vel
    assert "velocity_24h" in vel


def test_query_5_pagerank_risk_propagation(tg_client):
    res = tg_client.run_installed_query(
        "pagerank_risk_propagation",
        {"damping": 0.85, "max_iter": 15}
    )
    assert isinstance(res, dict)
    assert len(res) > 0


def test_query_6_community_detection(tg_client):
    res = tg_client.run_installed_query(
        "community_detection",
        {"min_size": 2}
    )
    assert isinstance(res, (list, dict))
    assert len(res) > 0


def test_query_7_similar_case_search(tg_client):
    test_vec = [0.1] * 16
    res = tg_client.run_installed_query(
        "similar_case_search",
        {"query_vector": test_vec, "top_k": 5}
    )
    assert isinstance(res, list)
    assert len(res) > 0
    assert "case_id" in res[0]
    assert "similarity_score" in res[0]


def test_query_8_write_case_subgraph(tg_client):
    res = tg_client.run_installed_query(
        "write_case_subgraph",
        {
            "payload": {
                "case_id": "TEST-CASE-WRITE",
                "title": "Unit Test Case Subgraph",
                "status": "CLOSED",
                "decision": "CONFIRMED_FRAUD",
                "typology_id": "TYP-ATO-001",
                "embedding": [0.05] * 16,
                "associated_accounts": ["ACC-USER-101"]
            }
        }
    )
    assert len(res) > 0
    assert res[0].get("status") == "SUCCESS"


def test_query_9_temporal_velocity_burst(tg_client):
    res = tg_client.run_installed_query(
        "temporal_velocity_burst",
        {"card_id": "CARD-4000-03"}
    )
    assert len(res) > 0
    burst = res[0]
    assert "is_burst" in burst


def test_query_10_path_between(tg_client):
    res = tg_client.run_installed_query(
        "path_between",
        {"source_id": "ACC-USER-101", "target_id": "DEV-EMULATOR-01", "source_type": "Account", "target_type": "Device"}
    )
    assert isinstance(res, dict)
    assert "path_found" in res


def test_query_11_circular_fund_routing(tg_client):
    res = tg_client.run_installed_query(
        "circular_fund_routing",
        {"start_account_id": "ACC-USER-101", "max_depth": 4}
    )
    assert len(res) > 0
    routing = res[0]
    assert "start_account_id" in routing
    assert "is_circular_routing" in routing
    assert "layering_risk_score" in routing


def test_query_12_merchant_collusion_ring(tg_client):
    res = tg_client.run_installed_query(
        "merchant_collusion_ring",
        {"merchant_id": "MERCH-ELEC-99", "min_accounts": 1}
    )
    assert len(res) > 0
    collusion = res[0]
    assert "merchant_id" in collusion
    assert "colluding_accounts_count" in collusion
    assert "collusion_risk_score" in collusion
    assert "is_collusion_detected" in collusion
