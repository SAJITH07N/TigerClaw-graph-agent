"""
Step 2: Investigate Node.
Performs entity resolution and 2-hop BFS graph extraction using TigerGraph get_entity_neighborhood.
"""

import time
from typing import Dict, Any
from agent.state import AgentState
from tigergraph.client import TigerGraphClient


def investigate_node(state: AgentState, tg_client: TigerGraphClient) -> AgentState:
    """Step 2: Resolves entities and extracts graph neighborhood."""
    trigger_data = state.get("trigger_data", {})
    txn_id = trigger_data.get("txn_id", "")
    account_id = trigger_data.get("account_id", "")
    card_id = trigger_data.get("card_id", "")
    device_id = trigger_data.get("device_id", "")

    # Extract 2-hop neighborhood around transaction or account
    start_id = txn_id if txn_id else account_id
    start_type = "Transaction" if txn_id else "Account"

    neighborhood = tg_client.run_installed_query(
        "get_entity_neighborhood",
        {"start_id": start_id, "start_type": start_type, "max_hops": 2},
    )[0]

    entities = {
        "accounts": [account_id] if account_id else [],
        "cards": [card_id] if card_id else [],
        "devices": [device_id] if device_id and device_id != "DEV-UNKNOWN" else [],
        "transactions": [txn_id] if txn_id else [],
        "addresses": [trigger_data.get("addr1")] if trigger_data.get("addr1") else [],
    }

    # Add any extra linked accounts/devices found in trigger_data
    if "linked_mule_accounts" in trigger_data:
        for acc in trigger_data["linked_mule_accounts"]:
            if acc not in entities["accounts"]:
                entities["accounts"].append(acc)
    if "fanout_accounts" in trigger_data:
        for acc in trigger_data["fanout_accounts"]:
            if acc not in entities["accounts"]:
                entities["accounts"].append(acc)

    history = state.get("step_history", [])
    history.append({
        "step": 2,
        "name": "Entity Resolution & Neighborhood BFS",
        "timestamp": int(time.time()),
        "status": "completed",
        "details": f"Extracted {neighborhood.get('node_count', 0)} nodes and {neighborhood.get('edge_count', 0)} edges.",
    })

    return {
        **state,
        "entities": entities,
        "graph_evidence": {"neighborhood": neighborhood},
        "step_history": history,
    }
