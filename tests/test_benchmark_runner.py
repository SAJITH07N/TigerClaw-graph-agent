"""
Validation tests for all 20 standardized Benchmark Answer JSON files in answers/.
Ensures complete compliance with the HHGOA Task 4 submission rubric and schema specifications.
"""

import os
import json
import pytest
from data.benchmark_generator import BENCHMARK_CASES

ANSWERS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "answers")


def test_all_20_benchmark_answer_files_exist():
    assert os.path.exists(ANSWERS_DIR), f"Answers directory {ANSWERS_DIR} does not exist."
    for i in range(1, 21):
        fname = f"case_{i:02d}.json"
        fpath = os.path.join(ANSWERS_DIR, fname)
        assert os.path.isfile(fpath), f"Missing benchmark answer file: {fname}"


@pytest.mark.parametrize("case_num", list(range(1, 21)))
def test_benchmark_answer_structure(case_num):
    fname = f"case_{case_num:02d}.json"
    fpath = os.path.join(ANSWERS_DIR, fname)

    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Top level keys
    required_keys = [
        "case_id",
        "benchmark_index",
        "case_title",
        "trigger",
        "audit_steps",
        "investigation_results",
        "evidence_trajectory",
        "next_best_actions",
        "grounded_explanation",
    ]
    for k in required_keys:
        assert k in data, f"Key '{k}' missing from {fname}"

    assert data["benchmark_index"] == case_num
    assert data["case_id"] == f"CASE-BM-{case_num:02d}"

    # 2. Audit steps
    assert len(data["audit_steps"]) >= 7

    # 3. Investigation results & 4-Pillar metrics
    inv = data["investigation_results"]
    assert "evidence_pillars" in inv
    assert "data_completeness" in inv
    assert "signal_conflict" in inv
    assert "composite_confidence" in inv
    assert "risk_level" in inv
    assert "top_typology_match" in inv

    pillars = inv["evidence_pillars"]
    assert "p_txn" in pillars
    assert "p_dev" in pillars
    assert "p_behav" in pillars
    assert "p_prior" in pillars

    # 4. Evidence Trajectory Diff
    traj = data["evidence_trajectory"]
    assert "before_additional_evidence" in traj
    assert "after_additional_evidence" in traj
    assert "what_changed" in traj
    assert len(traj["what_changed"]) > 0

    # 5. Next Best Actions
    actions = data["next_best_actions"]
    assert len(actions) > 0
    for act in actions:
        assert "action_id" in act
        assert "action_type" in act
        assert "permission_level" in act
        assert "policy_citation" in act
        assert "rationale" in act
        assert "status" in act

    # 6. FinCEN SAR Filing validation based on benchmark generator expectations
    expected_case = next(bm for bm in BENCHMARK_CASES if bm["case_num"] == case_num)
    if expected_case.get("expected_sar"):
        assert data.get("sar_filing") is not None, f"Expected FinCEN SAR filing for case {case_num}"
        sar = data["sar_filing"]
        assert "sar_id" in sar
        assert "narrative_sections" in sar
        narrative = sar["narrative_sections"]
        assert "part_1_executive_summary" in narrative
        assert "part_2_graph_connectivity" in narrative
        assert "part_3_chronological_flow" in narrative
        assert "part_4_regulatory_conclusion" in narrative
    else:
        assert data.get("sar_filing") is None, f"Expected no SAR filing for case {case_num}"
