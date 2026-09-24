"""
Step 3: Gather Evidence Node.
Executes multi-query GSQL algorithms (rings, fan-out, velocity, PageRank, community)
and retrieves GraphRAG policy grounding & historical case similarity.
"""

import time
from typing import Dict, Any, List
from agent.state import AgentState
from tigergraph.client import TigerGraphClient
from graphrag.policy_store import PolicyStore, generate_deterministic_embedding
from graphrag.typology_catalog import TypologyCatalog


def gather_evidence_node(
    state: AgentState,
    tg_client: TigerGraphClient,
    policy_store: PolicyStore,
    typology_catalog: TypologyCatalog,
) -> AgentState:
    """Step 3: Gathers graph and semantic evidence across all algorithms and knowledge sources."""
    trigger_data = state.get("trigger_data", {})
    device_id = trigger_data.get("device_id", "")
    card_id = trigger_data.get("card_id", "")
    account_id = trigger_data.get("account_id", "")

    graph_evidence = state.get("graph_evidence", {})

    # 1. Device Ring Query
    device_ring = tg_client.run_installed_query("shared_device_ring", {"device_id": device_id})[0]
    graph_evidence["device_ring"] = device_ring

    # 2. Card Fan-Out Query
    card_fanout = tg_client.run_installed_query("shared_card_fanout", {"card_id": card_id, "time_window_seconds": 86400})[0]
    graph_evidence["card_fanout"] = card_fanout

    # 3. Velocity Check Query
    velocity = tg_client.run_installed_query("velocity_check", {"account_id": account_id})[0]
    graph_evidence["velocity"] = velocity

    # 4. Temporal Micro-Burst Query
    burst = tg_client.run_installed_query("temporal_velocity_burst", {"card_id": card_id, "burst_window_seconds": 120, "count_threshold": 3})[0]
    graph_evidence["temporal_burst"] = burst

    # 5. PageRank Risk Propagation
    pagerank_scores = tg_client.run_installed_query("pagerank_risk_propagation", {"max_iter": 10, "damping": 0.85})
    graph_evidence["pagerank_scores"] = pagerank_scores

    # 6. Community Detection
    communities = tg_client.run_installed_query("community_detection", {"min_size": 2})
    graph_evidence["communities"] = communities

    # 7. Semantic Vector Search over PriorCases
    case_query = f"{trigger_data.get('dispute_reason', '')} {device_id} {trigger_data.get('amount', 0)}"
    q_vec = generate_deterministic_embedding(case_query)
    prior_cases = tg_client.run_installed_query("similar_case_search", {"query_vector": q_vec, "top_k": 3})
    graph_evidence["prior_cases"] = prior_cases

    # 8. Circular Fund Routing / Layering Query
    circular_res = tg_client.run_installed_query("circular_fund_routing", {"start_account_id": account_id, "max_depth": 4})[0]
    graph_evidence["circular_routing"] = circular_res

    # 9. Merchant Collusion Ring Query
    merchant_id = trigger_data.get("merchant_id", trigger_data.get("merchant", ""))
    merchant_res = tg_client.run_installed_query("merchant_collusion_ring", {"merchant_id": merchant_id, "min_accounts": 2})[0]
    graph_evidence["merchant_collusion"] = merchant_res

    # 10. Observed Indicators for Typology Matching
    observed_indicators = []

    # Check for Legitimate Travel / Benign Spending
    if trigger_data.get("stepup_verified") or (trigger_data.get("is_known_device") and float(trigger_data.get("risk_score", 0.5)) < 0.45):
        observed_indicators.append("known_device_verified")
        observed_indicators.append("positive_customer_stepup_confirmation")
        if int(trigger_data.get("tenure_months", 12)) >= 24:
            observed_indicators.append("long_account_tenure")
            observed_indicators.append("clean_historical_dispute_record")

    # Check for Mule Ring / Shared Device Syndicate
    elif (
        device_ring.get("is_mule_ring")
        or "linked_mule_accounts" in trigger_data
        or "fanout_accounts" in trigger_data
        or card_fanout.get("is_anomalous_fanout")
    ):
        observed_indicators.append("shared_device_multiple_accounts")
        observed_indicators.append("high_community_density")
        observed_indicators.append("cross_account_card_overlap")
        observed_indicators.append("pagerank_risk_diffusion_high")
        if trigger_data.get("is_emulator") or "emulator" in device_id.lower():
            observed_indicators.append("emulator_used")

    # Check for Card Testing / Micro-Burst
    elif (
        trigger_data.get("is_burst")
        or burst.get("is_card_testing")
        or (float(trigger_data.get("amount", 0)) < 15.0 and float(trigger_data.get("risk_score", 0.5)) > 0.6)
    ):
        observed_indicators.append("burst_velocity_under_120s")
        observed_indicators.append("micro_charges_under_15")
        observed_indicators.append("high_frequency_merchant_retries")
        observed_indicators.append("card_fanout_across_devices")

    # Check for Synthetic ID / Bust-Out
    elif (
        float(trigger_data.get("amount", 0)) >= 10000.0
        and int(trigger_data.get("tenure_months", 12)) <= 10
        and float(trigger_data.get("risk_score", 0.5)) >= 0.8
    ):
        observed_indicators.append("sudden_credit_line_exhaustion")
        observed_indicators.append("historic_low_velocity_then_extreme_surge")
        observed_indicators.append("shared_address_with_delinquent_nodes")

    # Default to Account Takeover (ATO) for high-risk single-account compromises
    else:
        observed_indicators.append("new_device_fingerprint")
        observed_indicators.append("velocity_spike_post_login")
        observed_indicators.append("unusual_high_value_transaction")
        if trigger_data.get("is_emulator") or "emulator" in device_id.lower():
            observed_indicators.append("emulator_used")
        if trigger_data.get("dispute_reason"):
            observed_indicators.append("address_mismatch")

    typology_matches = typology_catalog.match_typology(observed_indicators, top_k=2)

    # 9. GraphRAG Policy Search
    policy_query = f"containment action for {typology_matches[0]['name'] if typology_matches else 'fraud'} amount {trigger_data.get('amount')}"
    policy_citations = policy_store.search_policies(policy_query, top_k=3)

    history = state.get("step_history", [])
    history.append({
        "step": 3,
        "name": "Multi-Query GSQL & GraphRAG Evidence Gathering",
        "timestamp": int(time.time()),
        "status": "completed",
        "details": f"Ran 9 GSQL queries (including Circular Routing & Merchant Collusion). Matched top typology: {typology_matches[0]['name'] if typology_matches else 'N/A'}.",
    })

    return {
        **state,
        "graph_evidence": graph_evidence,
        "circular_routing_evidence": circular_res,
        "merchant_collusion_evidence": merchant_res,
        "typology_matches": typology_matches,
        "policy_citations": policy_citations,
        "step_history": history,
    }
