"""
Benchmark Evaluation Runner.
Executes the 8-step agent workflow across all 20 benchmark scenarios
and produces standardized answer JSON files in answers/case_01.json .. case_20.json.
"""

import os
import json
import logging
from typing import Dict, Any, List
from tigergraph.client import TigerGraphClient
from data.seed_historical_memory import seed_historical_memory
from data.ieee_cis_preprocessor import IEEECISPreprocessor
from data.benchmark_generator import BENCHMARK_CASES
from agent.workflow import FraudInvestigationWorkflow

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def setup_benchmark_graph(tg_client: TigerGraphClient) -> None:
    """Pre-populates the graph with historical closed cases and preprocessed benchmark entities."""
    logger.info("Seeding historical closed cases memory...")
    seed_historical_memory(tg_client, count=100)

    preprocessor = IEEECISPreprocessor(tg_client)
    logger.info("Ingesting benchmark case entities into graph...")
    for bm in BENCHMARK_CASES:
        t_data = bm["trigger_data"]
        rec = {
            "TransactionID": t_data.get("txn_id"),
            "TransactionAmt": t_data.get("amount", 100.0),
            "TransactionDT": 1000000 + bm["case_num"] * 3600,
            "ProductCD": "W",
            "account_id": t_data.get("account_id"),
            "card_id": t_data.get("card_id"),
            "risk_score": t_data.get("risk_score", 0.5),
            "is_fraud": 1 if bm.get("expected_risk_level") in ["critical", "high"] else 0,
            "card1": t_data.get("card_id", "4000").split("-")[-1],
            "card2": "150",
            "addr1": t_data.get("addr1", "90210"),
            "p_emaildomain": t_data.get("p_emaildomain", "gmail.com"),
            "DeviceInfo": t_data.get("device_id", "DEV-01"),
            "tenure_months": t_data.get("tenure_months", 12),
            "historical_avg_amount": t_data.get("historical_avg_amount", 120.0),
            "historical_velocity": 1.5,
            "is_emulator": t_data.get("is_emulator", False),
        }
        preprocessor.process_transaction_record(rec)

        # Synthesize extra mule ring / fanout edges if present
        if "linked_mule_accounts" in t_data:
            dev_id = t_data.get("device_id")
            for acc in t_data["linked_mule_accounts"]:
                tg_client.upsert_vertex("Account", acc, {
                    "account_holder_name": f"Mule Account {acc[-3:]}",
                    "tenure_months": 3,
                    "historical_avg_amount": 80.0,
                    "risk_score": 0.85,
                })
                tg_client.upsert_edge("USED_BY", "Device", dev_id, "Account", acc)
                tg_client.upsert_edge("SHARES_DEVICE", "Account", acc, "Device", dev_id, {"weight": 1.0})

        if "fanout_accounts" in t_data:
            card_id = t_data.get("card_id")
            for acc in t_data["fanout_accounts"]:
                tg_client.upsert_vertex("Account", acc, {
                    "account_holder_name": f"Proxy Account {acc[-3:]}",
                    "tenure_months": 2,
                    "risk_score": 0.80,
                })
                tg_client.upsert_edge("HELD_BY", "Card", card_id, "Account", acc)
                tg_client.upsert_edge("SHARES_CARD", "Account", acc, "Card", card_id, {"weight": 1.0})


def run_benchmark(output_dir: str = "answers") -> List[Dict[str, Any]]:
    """Runs all 20 benchmark cases through the LangGraph workflow and saves answer JSONs."""
    os.makedirs(output_dir, exist_ok=True)
    tg_client = TigerGraphClient()
    setup_benchmark_graph(tg_client)

    workflow = FraudInvestigationWorkflow(tg_client=tg_client)
    results = []

    for bm in BENCHMARK_CASES:
        case_num = bm["case_num"]
        case_id = bm["case_id"]
        logger.info("Running Benchmark Case %02d: %s", case_num, bm["title"])

        initial_state = {
            "case_id": case_id,
            "trigger_type": bm["trigger_type"],
            "trigger_data": bm["trigger_data"],
            "step_history": [],
        }

        final_state = workflow.run_investigation(initial_state)

        # Standardized Answer JSON schema
        answer_payload = {
            "case_id": case_id,
            "benchmark_index": case_num,
            "case_title": bm["title"],
            "trigger": {
                "type": bm["trigger_type"],
                "data": bm["trigger_data"],
            },
            "investigation_results": {
                "top_typology_match": final_state.get("typology_matches", [{}])[0],
                "risk_level": final_state.get("uncertainty_metrics", {}).get("risk_level"),
                "composite_confidence": final_state.get("uncertainty_metrics", {}).get("composite_confidence"),
                "data_completeness": final_state.get("uncertainty_metrics", {}).get("data_completeness"),
                "signal_conflict": final_state.get("uncertainty_metrics", {}).get("signal_conflict"),
                "evidence_pillars": final_state.get("uncertainty_metrics", {}).get("pillar_scores"),
            },
            "evidence_trajectory": final_state.get("evidence_trajectory"),
            "next_best_actions_before_evidence": final_state.get("next_best_actions_before_evidence", []),
            "next_best_actions_after_evidence": final_state.get("next_best_actions_after_evidence", final_state.get("next_best_actions", [])),
            "next_best_actions": final_state.get("next_best_actions"),
            "sar_filing": final_state.get("sar_filing"),
            "grounded_explanation": final_state.get("final_explanation"),
            "case_memory_id": final_state.get("case_memory_id"),
            "audit_steps": final_state.get("step_history"),
        }

        fname = f"case_{case_num:02d}.json"
        fpath = os.path.join(output_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(answer_payload, f, indent=2)

        results.append(answer_payload)
        logger.info("Saved %s -> Typology: %s | Risk: %s | Actions: %d | SAR: %s",
                    fname,
                    answer_payload["investigation_results"]["top_typology_match"].get("name"),
                    answer_payload["investigation_results"]["risk_level"],
                    len(answer_payload["next_best_actions"]),
                    answer_payload["sar_filing"] is not None)

    return results


if __name__ == "__main__":
    results = run_benchmark()
    print(f"\nSuccessfully executed all {len(results)} benchmark cases. Answer JSON files generated in /answers/")
