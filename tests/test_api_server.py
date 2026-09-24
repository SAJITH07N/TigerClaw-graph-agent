"""
FastAPI Server Endpoints Test Suite.
Tests health checks, case listings, subgraphs, approvals, SAR endpoints, and batch runner.
"""

import pytest
from fastapi.testclient import TestClient
from app.api.server import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "vertex_count" in data
    assert "edge_count" in data
    assert data["vertex_count"] > 0


def test_list_cases_endpoint():
    response = client.get("/api/cases")
    assert response.status_code == 200
    cases = response.json()
    assert isinstance(cases, list)
    assert len(cases) >= 20
    first_case = cases[0]
    assert "case_id" in first_case
    assert "case_title" in first_case
    assert "risk_level" in first_case


def test_get_case_detail_endpoint():
    response = client.get("/api/cases/CASE-BM-01")
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "CASE-BM-01"
    assert "investigation_results" in data
    assert "next_best_actions" in data
    assert "evidence_trajectory" in data


def test_get_case_subgraph_endpoint():
    response = client.get("/api/cases/CASE-BM-01/subgraph")
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "CASE-BM-01"
    assert "elements" in data
    assert isinstance(data["elements"], list)
    assert len(data["elements"]) > 0


def test_approve_action_endpoint():
    payload = {
        "action_id": "ACT-FREEZE-0101",
        "decision": "approve",
        "analyst_notes": "Confirmed mule syndicate linkage via shared device cluster."
    }
    response = client.post("/api/actions/ACT-FREEZE-0101/approve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["action_id"] == "ACT-FREEZE-0101"
    assert data["status"] == "executed"
    assert data["decision"] == "approve"


def test_get_sar_endpoint():
    # CASE-BM-02 is a Mule Ring with $8,200 volume, triggering mandatory FinCEN SAR filing
    response = client.get("/api/sar/CASE-BM-02")
    assert response.status_code == 200
    data = response.json()
    assert "institution" in data or "filing_institution" in data
    assert "narrative_sections" in data or "four_part_narrative" in data
    assert "mandatory_filing" in data


def test_llm_status_endpoint():
    response = client.get("/api/llm/status")
    assert response.status_code == 200
    data = response.json()
    assert "provider" in data
    assert "model" in data
    assert "configured" in data
    assert "mode" in data


def test_benchmark_matrix_endpoint():
    response = client.get("/api/benchmark/matrix")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "cases" in data
    assert data["summary"]["total_cases"] >= 20
    assert len(data["cases"]) >= 20
    first = data["cases"][0]
    assert "data_completeness" in first
    assert "signal_conflict" in first
    assert "confidence" in first


def test_live_investigation_endpoint():
    response = client.post("/api/cases/CASE-BM-01/investigate")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "result" in data
    assert data["result"]["case_id"] == "CASE-BM-01"
