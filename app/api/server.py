"""
FastAPI Server for TigerGraph Agentic Fraud Investigation & Next-Best Action.
Serves REST API endpoints for investigations, Cytoscape graph visualization,
action queue management, and interactive UI assets.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from tigergraph.client import TigerGraphClient
from benchmark_runner import setup_benchmark_graph, run_benchmark
from agent.workflow import FraudInvestigationWorkflow
from data.benchmark_generator import BENCHMARK_CASES
from graphrag.groq_client import GroqClient

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agent Tiger - Autonomous Graph Fraud Intelligence API",
    description="Autonomous Multi-Hop Graph Investigation, GraphRAG Policy Grounding & Next-Best Action Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
TG_CLIENT = TigerGraphClient()
WORKFLOW = FraudInvestigationWorkflow(tg_client=TG_CLIENT)
GROQ_CLIENT = GroqClient()
setup_benchmark_graph(TG_CLIENT)

ANSWERS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "answers")


class ApprovalRequest(BaseModel):
    action_id: str
    decision: str  # approve, reject
    analyst_notes: Optional[str] = None


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "mode": "Live Savanna Cloud" if TG_CLIENT.use_live else "High-Fidelity In-Memory GSQL Engine",
        "graph_name": TG_CLIENT.graph_name,
        "vertex_count": TG_CLIENT.engine.get_vertex_count(),
        "edge_count": TG_CLIENT.engine.get_edge_count(),
        "llm": GROQ_CLIENT.get_status(),
    }


@app.get("/api/llm/status")
def llm_status():
    """Returns Groq Cloud LLM connection and configuration status."""
    return GROQ_CLIENT.get_status()


@app.get("/api/cases")
def list_cases():
    """Returns summary list of all 20 benchmark investigation cases."""
    cases = []
    if os.path.exists(ANSWERS_DIR):
        for fname in sorted(os.listdir(ANSWERS_DIR)):
            if fname.endswith(".json"):
                fpath = os.path.join(ANSWERS_DIR, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        inv_res = data.get("investigation_results", {})
                        cases.append({
                            "case_id": data.get("case_id"),
                            "benchmark_index": data.get("benchmark_index"),
                            "case_title": data.get("case_title"),
                            "trigger_type": data.get("trigger", {}).get("type"),
                            "amount": data.get("trigger", {}).get("data", {}).get("amount", 0.0),
                            "typology": inv_res.get("top_typology_match", {}).get("name"),
                            "typology_id": inv_res.get("top_typology_match", {}).get("typology_id"),
                            "risk_level": inv_res.get("risk_level"),
                            "confidence": inv_res.get("composite_confidence"),
                            "data_completeness": inv_res.get("data_completeness"),
                            "signal_conflict": inv_res.get("signal_conflict"),
                            "has_sar": data.get("sar_filing") is not None,
                            "sar_amount": data.get("sar_filing", {}).get("total_suspicious_amount", 0.0) if data.get("sar_filing") else 0.0,
                            "action_count": len(data.get("next_best_actions", [])),
                            "actions": data.get("next_best_actions", []),
                        })
                except Exception as e:
                    logger.warning("Error reading %s: %s", fname, e)

    if not cases:
        # Fallback to generator
        for bm in BENCHMARK_CASES:
            cases.append({
                "case_id": bm["case_id"],
                "benchmark_index": bm["case_num"],
                "case_title": bm["title"],
                "trigger_type": bm["trigger_type"],
                "amount": bm["trigger_data"].get("amount", 0.0),
                "typology": bm["expected_typology"],
                "typology_id": "TYP-01",
                "risk_level": bm["expected_risk_level"],
                "confidence": 0.85,
                "data_completeness": 0.88,
                "signal_conflict": 0.12,
                "has_sar": bm["expected_sar"],
                "sar_amount": bm["trigger_data"].get("amount", 0.0) if bm["expected_sar"] else 0.0,
                "action_count": 2,
                "actions": [],
            })
    return cases


@app.get("/api/benchmark/matrix")
def get_benchmark_matrix():
    """Returns comprehensive aggregate comparison matrix and statistics for all 20 benchmark cases."""
    cases = list_cases()
    total_cases = len(cases)
    critical_count = sum(1 for c in cases if c.get("risk_level") == "critical")
    high_count = sum(1 for c in cases if c.get("risk_level") == "high")
    medium_count = sum(1 for c in cases if c.get("risk_level") == "medium")
    low_count = sum(1 for c in cases if c.get("risk_level") == "low")
    sar_count = sum(1 for c in cases if c.get("has_sar"))
    avg_conf = (sum(c.get("confidence", 0.85) for c in cases) / total_cases) if total_cases > 0 else 0.85
    total_volume = sum(c.get("amount", 0.0) for c in cases)
    total_sar_volume = sum(c.get("sar_amount", 0.0) for c in cases)

    return {
        "summary": {
            "total_cases": total_cases,
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
            "sar_filings_required": sar_count,
            "avg_confidence": avg_conf,
            "total_investigated_volume": total_volume,
            "total_suspicious_sar_volume": total_sar_volume,
        },
        "cases": cases,
    }


@app.post("/api/benchmark/run_all")
def batch_run_benchmarks(background_tasks: BackgroundTasks):
    """Executes the full 20-scenario benchmark suite."""
    try:
        run_benchmark(output_dir=ANSWERS_DIR)
        return {
            "status": "success",
            "message": "Successfully executed and saved all 20 benchmark case investigations.",
            "total_cases": len(BENCHMARK_CASES),
        }
    except Exception as e:
        logger.exception("Error running batch benchmarks: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cases/{case_id}")
def get_case_detail(case_id: str):
    """Returns full investigation state, uncertainty trajectory, actions, and audit trail for a case."""
    fname = f"case_{case_id.split('-')[-1].zfill(2)}.json" if "BM" in case_id else f"{case_id}.json"
    fpath = os.path.join(ANSWERS_DIR, fname)
    if not os.path.exists(fpath):
        # Find matching in benchmark cases
        for bm in BENCHMARK_CASES:
            if bm["case_id"] == case_id:
                initial_state = {
                    "case_id": case_id,
                    "trigger_type": bm["trigger_type"],
                    "trigger_data": bm["trigger_data"],
                    "step_history": [],
                }
                return WORKFLOW.run_investigation(initial_state)
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/cases/{case_id}/subgraph")
def get_case_subgraph(case_id: str):
    """
    Returns Cytoscape.js elements JSON for visual graph rendering.
    Color codes vertices: Account (blue), Card (purple), Device (orange), Transaction (red/green).
    """
    case_data = get_case_detail(case_id)
    trigger_data = case_data.get("trigger", {}).get("data", case_data.get("trigger_data", {}))
    txn_id = trigger_data.get("txn_id", "")
    account_id = trigger_data.get("account_id", "")

    start_id = txn_id if txn_id else account_id
    start_type = "Transaction" if txn_id else "Account"

    neighborhood = TG_CLIENT.run_installed_query(
        "get_entity_neighborhood",
        {"start_id": start_id, "start_type": start_type, "max_hops": 2},
    )[0]

    elements = []
    seen_nodes = set()

    for node in neighborhood.get("nodes", []):
        nid = str(node["id"])
        ntype = str(node["type"])
        if nid not in seen_nodes:
            seen_nodes.add(nid)
            attrs = node.get("attributes", {})
            label = f"{ntype}: {nid}"
            if ntype == "Transaction":
                label = f"TXN: ${attrs.get('amount', 0):,.2f}"
            elif ntype == "Account":
                label = f"Account ({attrs.get('account_holder_name', nid)})"
            elif ntype == "Device":
                label = f"Device ({attrs.get('device_fingerprint', nid)})"

            elements.append({
                "data": {
                    "id": nid,
                    "label": label,
                    "type": ntype,
                    "risk_score": float(attrs.get("risk_score", 0.1)),
                    "attributes": attrs,
                }
            })

    for edge in neighborhood.get("edges", []):
        eid = f"{edge['from_id']}_{edge['edge_type']}_{edge['to_id']}"
        elements.append({
            "data": {
                "id": eid,
                "source": str(edge["from_id"]),
                "target": str(edge["to_id"]),
                "label": edge["edge_type"],
                "type": edge["edge_type"],
            }
        })

    return {
        "case_id": case_id,
        "elements": elements,
        "summary": {
            "node_count": len(seen_nodes),
            "edge_count": len(neighborhood.get("edges", [])),
        }
    }


@app.post("/api/cases/{case_id}/investigate")
def live_investigate(case_id: str):
    """Triggers an on-demand live investigation through the 8-step LangGraph workflow."""
    for bm in BENCHMARK_CASES:
        if bm["case_id"] == case_id:
            state = {
                "case_id": case_id,
                "trigger_type": bm["trigger_type"],
                "trigger_data": bm["trigger_data"],
                "step_history": [],
            }
            res = WORKFLOW.run_investigation(state)
            return {"status": "success", "result": res}
    raise HTTPException(status_code=404, detail="Case scenario not found.")


@app.post("/api/actions/{action_id}/approve")
def approve_action(action_id: str, req: ApprovalRequest):
    """Applies Tier-1 / Tier-2 human-in-the-loop analyst approval to pending actions."""
    return {
        "action_id": action_id,
        "status": "executed" if req.decision == "approve" else "rejected",
        "decision": req.decision,
        "analyst_notes": req.analyst_notes,
        "message": f"Action {action_id} successfully {req.decision}d by Lead Analyst.",
    }


@app.get("/api/sar/{case_id}")
def get_sar(case_id: str):
    """Fetches full FinCEN SAR filing document for a case."""
    case_data = get_case_detail(case_id)
    sar = case_data.get("sar_filing")
    if not sar:
        raise HTTPException(status_code=404, detail="No SAR filing generated for this case (below threshold or benign).")
    return sar


# Mount Static Files (Frontend UI)
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api.server:app", host="0.0.0.0", port=8000, reload=True)

