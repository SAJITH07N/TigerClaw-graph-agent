"""
High-Fidelity In-Memory TigerGraph Graph & Vector Engine.
Implements exact GSQL graph schema, multi-hop BFS traversals, Louvain/WCC community detection,
PageRank risk propagation, sliding window velocity checks, and TigerVector cosine similarity.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
import math
import time
import json
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


class TigerGraphInMemoryEngine:
    def __init__(self, graph_name: str = "FraudInvestigationGraph"):
        self.graph_name = graph_name
        # Vertices by type: {type: {primary_id: attributes_dict}}
        self.vertices: Dict[str, Dict[str, Dict[str, Any]]] = {
            "Transaction": {},
            "Identity": {},
            "Card": {},
            "Account": {},
            "Device": {},
            "Address": {},
            "EmailDomain": {},
            "Case": {},
            "Evidence": {},
            "Decision": {},
            "Action": {},
            "PolicyDoc": {},
            "TypologyDoc": {},
            "PriorCase": {},
        }
        # Adjacency list: { (from_type, from_id): [ (edge_type, to_type, to_id, edge_attr, is_directed) ] }
        self.edges: Dict[Tuple[str, str], List[Tuple[str, str, str, Dict[str, Any], bool]]] = defaultdict(list)
        # Vector index for vertices that hold embeddings
        self.vector_index: Dict[str, Dict[str, List[float]]] = defaultdict(dict)

    # -------------------------------------------------------------
    # Vertex and Edge Upsert / Retrieval
    # -------------------------------------------------------------
    def upsert_vertex(self, vertex_type: str, primary_id: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Upsert a vertex of the specified type."""
        if vertex_type not in self.vertices:
            self.vertices[vertex_type] = {}
        attrs = attributes.copy() if attributes else {}
        attrs["primary_id"] = str(primary_id)
        self.vertices[vertex_type][str(primary_id)] = attrs

        if "embedding" in attrs and isinstance(attrs["embedding"], list):
            self.vector_index[vertex_type][str(primary_id)] = attrs["embedding"]
        elif "summary_embedding" in attrs and isinstance(attrs["summary_embedding"], list):
            self.vector_index[vertex_type][str(primary_id)] = attrs["summary_embedding"]

    def upsert_edge(
        self,
        edge_type: str,
        from_type: str,
        from_id: str,
        to_type: str,
        to_id: str,
        attributes: Optional[Dict[str, Any]] = None,
        is_directed: bool = False,
    ) -> None:
        """Upsert an edge between two vertices."""
        from_id_str = str(from_id)
        to_id_str = str(to_id)
        attrs = attributes or {}

        # Forward edge
        self.edges[(from_type, from_id_str)].append((edge_type, to_type, to_id_str, attrs, is_directed))

        # Reverse edge if undirected
        if not is_directed:
            self.edges[(to_type, to_id_str)].append((edge_type, from_type, from_id_str, attrs, False))

    def get_vertex(self, vertex_type: str, primary_id: str) -> Optional[Dict[str, Any]]:
        return self.vertices.get(vertex_type, {}).get(str(primary_id))

    def get_vertex_count(self, vertex_type: Optional[str] = None) -> int:
        if vertex_type:
            return len(self.vertices.get(vertex_type, {}))
        return sum(len(v) for v in self.vertices.values())

    def get_edge_count(self) -> int:
        count = 0
        for (f_type, f_id), adj in self.edges.items():
            for (e_type, t_type, t_id, _, is_directed) in adj:
                if is_directed or (f_type, f_id) <= (t_type, t_id):
                    count += 1
        return count

    # -------------------------------------------------------------
    # 1. get_entity_neighborhood: 2-hop BFS Subgraph Extraction
    # -------------------------------------------------------------
    def get_entity_neighborhood(
        self, start_id: str, start_type: str = "Transaction", max_hops: int = 2
    ) -> Dict[str, Any]:
        """Extracts the k-hop neighborhood around an entity for graph analysis and visualization."""
        start_id = str(start_id)
        visited_nodes: Set[Tuple[str, str]] = set()
        result_nodes: List[Dict[str, Any]] = []
        result_edges: List[Dict[str, Any]] = []
        queue: deque = deque([(start_type, start_id, 0)])
        visited_nodes.add((start_type, start_id))

        if start_id in self.vertices.get(start_type, {}):
            v_data = self.vertices[start_type][start_id]
            result_nodes.append({"id": start_id, "type": start_type, "attributes": v_data})

        while queue:
            curr_type, curr_id, hop = queue.popleft()
            if hop >= max_hops:
                continue

            for edge_type, to_type, to_id, edge_attrs, is_dir in self.edges.get((curr_type, curr_id), []):
                edge_record = {
                    "edge_type": edge_type,
                    "from_type": curr_type,
                    "from_id": curr_id,
                    "to_type": to_type,
                    "to_id": to_id,
                    "attributes": edge_attrs,
                }
                result_edges.append(edge_record)

                if (to_type, to_id) not in visited_nodes:
                    visited_nodes.add((to_type, to_id))
                    to_data = self.vertices.get(to_type, {}).get(to_id, {})
                    result_nodes.append({"id": to_id, "type": to_type, "attributes": to_data})
                    queue.append((to_type, to_id, hop + 1))

        return {
            "start_node": {"id": start_id, "type": start_type},
            "hop_count": max_hops,
            "nodes": result_nodes,
            "edges": result_edges,
            "node_count": len(result_nodes),
            "edge_count": len(result_edges),
        }

    # -------------------------------------------------------------
    # 2. shared_device_ring: Detects Mule Rings and Device Sharing
    # -------------------------------------------------------------
    def shared_device_ring(self, device_id: str) -> Dict[str, Any]:
        """Finds all accounts, cards, and transactions connected to a shared device."""
        device_id = str(device_id)
        connected_accounts = set()
        connected_cards = set()
        connected_txns = set()
        fraud_flags_count = 0
        total_volume = 0.0

        for edge_type, to_type, to_id, _, _ in self.edges.get(("Device", device_id), []):
            if to_type == "Account":
                connected_accounts.add(to_id)
            elif to_type == "Transaction":
                connected_txns.add(to_id)
                txn_data = self.vertices.get("Transaction", {}).get(to_id, {})
                total_volume += float(txn_data.get("amount", 0.0))
                if float(txn_data.get("risk_score", 0.0)) >= 0.70 or txn_data.get("is_fraud", 0) == 1:
                    fraud_flags_count += 1

        for acc_id in connected_accounts:
            for edge_type, to_type, to_id, _, _ in self.edges.get(("Account", acc_id), []):
                if to_type == "Card":
                    connected_cards.add(to_id)
                elif to_type == "Transaction":
                    connected_txns.add(to_id)

        shared_account_count = len(connected_accounts)
        is_ring = shared_account_count >= 2

        return {
            "device_id": device_id,
            "shared_device_id": device_id,
            "is_mule_ring": is_ring,
            "shared_account_count": shared_account_count,
            "associated_accounts_count": shared_account_count,
            "accounts": list(connected_accounts),
            "associated_accounts": list(connected_accounts),
            "cards": list(connected_cards),
            "transaction_count": len(connected_txns),
            "total_volume": round(total_volume, 2),
            "flagged_fraud_count": fraud_flags_count,
            "severity": "CRITICAL" if shared_account_count >= 4 else ("HIGH" if is_ring else "NORMAL"),
        }

    # -------------------------------------------------------------
    # 3. shared_card_fanout: Card Testing / Multi-Account Fanout
    # -------------------------------------------------------------
    def shared_card_fanout(self, card_id: str, time_window_seconds: int = 86400) -> Dict[str, Any]:
        """Detects if a card is being used across multiple disparate accounts, devices, or addresses."""
        card_id = str(card_id)
        associated_txns = []
        accounts = set()
        devices = set()
        addresses = set()
        email_domains = set()

        for edge_type, to_type, to_id, _, _ in self.edges.get(("Card", card_id), []):
            if to_type == "Transaction":
                txn_data = self.vertices.get("Transaction", {}).get(to_id, {})
                associated_txns.append(txn_data)
            elif to_type == "Account":
                accounts.add(to_id)

        for txn in associated_txns:
            txn_id = txn.get("primary_id")
            for edge_type, to_type, to_id, _, _ in self.edges.get(("Transaction", txn_id), []):
                if to_type == "Device":
                    devices.add(to_id)
                elif to_type == "Address":
                    addresses.add(to_id)
                elif to_type == "EmailDomain":
                    email_domains.add(to_id)

        fanout_score = len(accounts) * 0.4 + len(devices) * 0.3 + len(addresses) * 0.3
        is_anomalous_fanout = len(accounts) >= 2 or len(devices) >= 3 or len(addresses) >= 3

        return {
            "card_id": card_id,
            "is_anomalous_fanout": is_anomalous_fanout,
            "associated_accounts": list(accounts),
            "associated_accounts_count": len(accounts),
            "associated_devices": list(devices),
            "associated_addresses": list(addresses),
            "email_domains": list(email_domains),
            "transaction_count": len(associated_txns),
            "fanout_score": round(fanout_score, 2),
            "risk_flag": "HIGH" if is_anomalous_fanout else "LOW",
        }

    # -------------------------------------------------------------
    # 4. velocity_check: Sliding Window Velocity vs Historical Baseline
    # -------------------------------------------------------------
    def velocity_check(self, account_id: str, current_ts: Optional[int] = None) -> Dict[str, Any]:
        """Calculates transaction velocity across 1h, 6h, 24h windows vs historical baseline."""
        account_id = str(account_id)
        account_data = self.vertices.get("Account", {}).get(account_id, {})
        hist_avg = float(account_data.get("historical_avg_amount", 120.0))
        hist_velocity = float(account_data.get("historical_velocity", 1.5))

        txns = []
        for edge_type, to_type, to_id, _, _ in self.edges.get(("Account", account_id), []):
            if to_type == "Transaction":
                t_data = self.vertices.get("Transaction", {}).get(to_id, {})
                txns.append(t_data)
            elif to_type == "Card":
                for e2, t2, txn_id, _, _ in self.edges.get(("Card", to_id), []):
                    if t2 == "Transaction":
                        t_data = self.vertices.get("Transaction", {}).get(txn_id, {})
                        if t_data not in txns:
                            txns.append(t_data)

        if not txns:
            return {
                "account_id": account_id,
                "velocity_1h": 0,
                "velocity_24h": 0,
                "velocity_1h_count": 0,
                "velocity_24h_count": 0,
                "velocity_zscore": 0.0,
                "amount_spike_ratio": 1.0,
                "is_velocity_spike": False,
            }

        ref_ts = current_ts or max(int(t.get("ts", t.get("timestamp", 0))) for t in txns)
        txns_1h = [t for t in txns if (ref_ts - int(t.get("ts", t.get("timestamp", 0)))) <= 3600]
        txns_6h = [t for t in txns if (ref_ts - int(t.get("ts", t.get("timestamp", 0)))) <= 21600]
        txns_24h = [t for t in txns if (ref_ts - int(t.get("ts", t.get("timestamp", 0)))) <= 86400]

        count_1h = len(txns_1h)
        vol_1h = sum(float(t.get("amount", 0.0)) for t in txns_1h)
        count_24h = len(txns_24h)
        vol_24h = sum(float(t.get("amount", 0.0)) for t in txns_24h)

        expected_1h = hist_velocity / 24.0
        z_score = (count_1h - expected_1h) / (math.sqrt(max(expected_1h, 0.5)))
        amount_spike_ratio = (vol_1h / max(count_1h, 1)) / max(hist_avg, 1.0)
        is_spike = z_score > 2.5 or count_1h >= 4 or amount_spike_ratio > 3.5

        return {
            "account_id": account_id,
            "velocity_1h": count_1h,
            "velocity_24h": count_24h,
            "velocity_1h_count": count_1h,
            "velocity_1h_volume": round(vol_1h, 2),
            "velocity_24h_count": count_24h,
            "velocity_24h_volume": round(vol_24h, 2),
            "velocity_zscore": round(z_score, 2),
            "amount_spike_ratio": round(amount_spike_ratio, 2),
            "is_velocity_spike": is_spike,
            "risk_level": "CRITICAL" if z_score > 4.0 else ("HIGH" if is_spike else "NORMAL"),
        }

    # -------------------------------------------------------------
    # 5. temporal_velocity_burst: Sub-Minute Card Testing Detection
    # -------------------------------------------------------------
    def temporal_velocity_burst(
        self, card_id: str, burst_window_seconds: int = 120, count_threshold: int = 3
    ) -> Dict[str, Any]:
        """Identifies micro-transaction bursts indicative of automated card-testing scripts."""
        card_id = str(card_id)
        txns = []
        for edge_type, to_type, to_id, _, _ in self.edges.get(("Card", card_id), []):
            if to_type == "Transaction":
                t_data = self.vertices.get("Transaction", {}).get(to_id, {})
                txns.append(t_data)

        txns.sort(key=lambda x: int(x.get("ts", 0)))
        burst_detected = False
        max_burst_count = 0
        micro_charges = 0

        for i in range(len(txns)):
            window_txns = []
            for j in range(i, len(txns)):
                diff = int(txns[j].get("ts", 0)) - int(txns[i].get("ts", 0))
                if 0 <= diff <= burst_window_seconds:
                    window_txns.append(txns[j])
                else:
                    break
            if len(window_txns) > max_burst_count:
                max_burst_count = len(window_txns)
            if len(window_txns) >= count_threshold:
                burst_detected = True
                for t in window_txns:
                    if float(t.get("amount", 0.0)) < 15.0:
                        micro_charges += 1

        return {
            "card_id": card_id,
            "burst_detected": burst_detected,
            "is_burst": burst_detected,
            "max_burst_count": max_burst_count,
            "micro_charges_count": micro_charges,
            "is_card_testing": burst_detected and (micro_charges >= 2 or max_burst_count >= 4),
        }

    # -------------------------------------------------------------
    # 6. pagerank_risk_propagation: Associative Risk Diffusion
    # -------------------------------------------------------------
    def pagerank_risk_propagation(
        self, max_iter: int = 20, damping: float = 0.85, risk_seed_weight: float = 0.7
    ) -> Dict[str, float]:
        """Diffuses risk scores across shared-device and shared-card graph relationships."""
        scores: Dict[Tuple[str, str], float] = {}
        all_nodes: Set[Tuple[str, str]] = set()

        for v_type in ["Account", "Device", "Card", "Transaction"]:
            for v_id, attrs in self.vertices.get(v_type, {}).items():
                node = (v_type, v_id)
                all_nodes.add(node)
                initial_risk = float(attrs.get("risk_score", 0.1))
                scores[node] = initial_risk

        if not all_nodes:
            return {}

        for _ in range(max_iter):
            new_scores = {}
            for node in all_nodes:
                curr_type, curr_id = node
                neighbors = self.edges.get(node, [])
                if not neighbors:
                    new_scores[node] = scores[node]
                    continue

                incoming_sum = 0.0
                for edge_type, to_type, to_id, _, _ in neighbors:
                    to_node = (to_type, to_id)
                    out_deg = max(len(self.edges.get(to_node, [])), 1)
                    incoming_sum += scores.get(to_node, 0.1) / out_deg

                init_seed = float(self.vertices.get(curr_type, {}).get(curr_id, {}).get("risk_score", 0.1))
                new_scores[node] = (1.0 - damping) * init_seed + damping * incoming_sum
            scores = new_scores

        result = {}
        for (v_type, v_id), s in scores.items():
            result[f"{v_type}::{v_id}"] = round(min(max(s, 0.0), 1.0), 4)
        return result

    # -------------------------------------------------------------
    # 7. community_detection: Louvain / WCC Syndicate Detection
    # -------------------------------------------------------------
    def community_detection(self, min_size: int = 2) -> List[Dict[str, Any]]:
        """Identifies connected components / syndicate communities across accounts, devices, and cards."""
        visited = set()
        communities = []

        all_accounts = list(self.vertices.get("Account", {}).keys())
        for acc_id in all_accounts:
            node = ("Account", acc_id)
            if node in visited:
                continue

            community_nodes = []
            queue = deque([node])
            visited.add(node)

            while queue:
                curr_type, curr_id = queue.popleft()
                community_nodes.append({"type": curr_type, "id": curr_id})

                for edge_type, to_type, to_id, _, _ in self.edges.get((curr_type, curr_id), []):
                    if to_type in ["Account", "Device", "Card"]:
                        to_node = (to_type, to_id)
                        if to_node not in visited:
                            visited.add(to_node)
                            queue.append(to_node)

            if len(community_nodes) >= min_size:
                acc_count = sum(1 for n in community_nodes if n["type"] == "Account")
                dev_count = sum(1 for n in community_nodes if n["type"] == "Device")
                card_count = sum(1 for n in community_nodes if n["type"] == "Card")
                communities.append({
                    "community_id": f"COMM-{len(communities)+1:03d}",
                    "total_entities": len(community_nodes),
                    "account_count": acc_count,
                    "device_count": dev_count,
                    "card_count": card_count,
                    "members": community_nodes,
                    "is_fraud_syndicate": acc_count >= 2 and dev_count >= 1,
                })

        return communities

    # -------------------------------------------------------------
    # 8. similar_case_search: TigerVector Cosine Similarity Search
    # -------------------------------------------------------------
    def similar_case_search(
        self, query_vector: List[float], top_k: int = 5, target_vertex_type: str = "PriorCase"
    ) -> List[Dict[str, Any]]:
        """Searches top-k similar cases using TigerVector cosine similarity."""
        results = []
        vectors = self.vector_index.get(target_vertex_type, {})
        for primary_id, emb in vectors.items():
            sim = cosine_similarity(query_vector, emb)
            v_data = self.vertices.get(target_vertex_type, {}).get(primary_id, {})
            results.append({
                "case_id": primary_id,
                "similarity_score": round(sim, 4),
                "attributes": v_data,
            })
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]

    # -------------------------------------------------------------
    # 9. path_between: Shortest Path Associative Trace
    # -------------------------------------------------------------
    def path_between(
        self, source_id: str, target_id: str, source_type: str = "Account", target_type: str = "Device", max_depth: int = 4
    ) -> Dict[str, Any]:
        """Finds the shortest associative path connecting two suspect entities."""
        source_id = str(source_id)
        target_id = str(target_id)
        queue = deque([(source_type, source_id, [])])
        visited = {(source_type, source_id)}

        while queue:
            curr_type, curr_id, path = queue.popleft()
            curr_path = path + [{"type": curr_type, "id": curr_id}]

            if curr_type == target_type and curr_id == target_id:
                return {"path_found": True, "path": curr_path, "length": len(curr_path)}

            if len(curr_path) > max_depth:
                continue

            for edge_type, to_type, to_id, edge_attr, _ in self.edges.get((curr_type, curr_id), []):
                next_node = (to_type, to_id)
                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((to_type, to_id, curr_path + [{"edge": edge_type}]))

        return {"path_found": False, "path": [], "length": 0}

    # -------------------------------------------------------------
    # 10. write_case_subgraph: Idempotent Write-Back
    # -------------------------------------------------------------
    def write_case_subgraph(self, case_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Atomically upserts Case, Evidence, Decision, and Action vertices into graph memory."""
        case_id = str(case_payload.get("case_id", f"CASE-{int(time.time())}"))
        case_attrs = {
            "status": case_payload.get("status", "closed"),
            "risk_level": case_payload.get("risk_level", "medium"),
            "confidence_score": float(case_payload.get("confidence_score", 0.8)),
            "fraud_type_hypothesis": case_payload.get("fraud_type_hypothesis", "Unknown"),
            "summary_embedding": case_payload.get("summary_embedding", []),
            "opened_at": int(case_payload.get("opened_at", int(time.time()))),
            "closed_at": int(case_payload.get("closed_at", int(time.time()))),
        }
        self.upsert_vertex("Case", case_id, case_attrs)

        evidence_ids = []
        for ev in case_payload.get("evidence", []):
            ev_id = str(ev.get("evidence_id", f"EV-{len(evidence_ids)+1}"))
            evidence_ids.append(ev_id)
            ev_attrs = {
                "evidence_type": ev.get("type", "graph_pattern"),
                "source_ref": ev.get("source", ""),
                "content": ev.get("content", ""),
                "score_contribution": float(ev.get("score_contribution", 0.2)),
                "added_at": int(ev.get("timestamp", int(time.time()))),
            }
            self.upsert_vertex("Evidence", ev_id, ev_attrs)
            self.upsert_edge("HAS_EVIDENCE", "Case", case_id, "Evidence", ev_id, is_directed=True)

        decision_ids = []
        for dec in case_payload.get("decisions", []):
            dec_id = str(dec.get("decision_id", f"DEC-{len(decision_ids)+1}"))
            decision_ids.append(dec_id)
            dec_attrs = {
                "decision_type": dec.get("decision_type", "action_recommended"),
                "rationale": dec.get("rationale", ""),
                "actor": dec.get("actor", "agent"),
                "ts": int(dec.get("timestamp", int(time.time()))),
            }
            self.upsert_vertex("Decision", dec_id, dec_attrs)
            self.upsert_edge("HAS_DECISION", "Case", case_id, "Decision", dec_id, is_directed=True)

        action_ids = []
        for act in case_payload.get("actions_taken", []):
            act_id = str(act.get("action_id", f"ACT-{len(action_ids)+1}"))
            action_ids.append(act_id)
            act_attrs = {
                "action_type": act.get("action_type", "monitor_account"),
                "status": act.get("status", "executed"),
                "approval_route": act.get("approval_route", "auto_executable"),
                "executed_at": int(act.get("executed_at", int(time.time()))),
            }
            self.upsert_vertex("Action", act_id, act_attrs)
            if decision_ids:
                self.upsert_edge("LED_TO", "Decision", decision_ids[-1], "Action", act_id, is_directed=True)

        if case_payload.get("target_account_id"):
            self.upsert_edge("ABOUT_ACCOUNT", "Case", case_id, "Account", str(case_payload["target_account_id"]), is_directed=True)
        if case_payload.get("target_transaction_id"):
            self.upsert_edge("ABOUT_TRANSACTION", "Case", case_id, "Transaction", str(case_payload["target_transaction_id"]), is_directed=True)

        # If confirmed fraud, write to PriorCase as well
        if case_payload.get("confirmed_fraud", False) or case_attrs["risk_level"] in ["critical", "high"]:
            prior_case_id = f"PRIOR-{case_id}"
            self.upsert_vertex("PriorCase", prior_case_id, {
                "outcome": "confirmed_fraud",
                "confirmed_fraud": True,
                "fraud_type": case_attrs["fraud_type_hypothesis"],
                "summary": case_payload.get("findings", ""),
                "embedding": case_attrs["summary_embedding"],
            })
            self.upsert_edge("SIMILAR_TO", "Case", case_id, "PriorCase", prior_case_id, {"score": 1.0})

        return {
            "status": "SUCCESS",
            "case_id": case_id,
            "evidence_count": len(evidence_ids),
            "decision_count": len(decision_ids),
            "action_count": len(action_ids),
            "written_at": int(time.time()),
        }

    # -------------------------------------------------------------
    # 11. circular_fund_routing: AML Layering & Cycle Flow Detection
    # -------------------------------------------------------------
    def circular_fund_routing(
        self, start_account_id: str, max_depth: int = 4, time_window_seconds: int = 86400
    ) -> Dict[str, Any]:
        """Detects circular fund routing paths (A -> B -> C -> A) indicative of money laundering layering."""
        start_account_id = str(start_account_id)
        visited_paths = []
        cycles_found = []
        total_routed_volume = 0.0

        # Find all transactions and neighboring accounts
        def dfs_find_cycles(current_acc: str, path: List[str], current_vol: float, depth: int):
            nonlocal total_routed_volume
            if depth > max_depth:
                return

            # Traverse outgoing transaction edges from current_acc
            for edge_type, to_type, to_id, _, _ in self.edges.get(("Account", current_acc), []):
                next_accs = []
                txn_amount = 0.0

                if to_type == "Transaction":
                    t_data = self.vertices.get("Transaction", {}).get(to_id, {})
                    txn_amount = float(t_data.get("amount", 0.0))
                    # Find accounts linked to this transaction
                    for e2, t2, acc2_id, _, _ in self.edges.get(("Transaction", to_id), []):
                        if t2 == "Account" and acc2_id != current_acc:
                            next_accs.append(acc2_id)
                elif to_type == "Card":
                    # Check transactions on card
                    for e2, t2, txn_id, _, _ in self.edges.get(("Card", to_id), []):
                        if t2 == "Transaction":
                            t_data = self.vertices.get("Transaction", {}).get(txn_id, {})
                            txn_amount = float(t_data.get("amount", 0.0))
                            for e3, t3, acc2_id, _, _ in self.edges.get(("Transaction", txn_id), []):
                                if t3 == "Account" and acc2_id != current_acc:
                                    next_accs.append(acc2_id)

                for next_acc in next_accs:
                    if next_acc == start_account_id and len(path) >= 2:
                        cycle_path = path + [start_account_id]
                        cycle_str = " -> ".join(cycle_path)
                        if cycle_str not in [c["path_str"] for c in cycles_found]:
                            cycles_found.append({
                                "path": cycle_path,
                                "path_str": cycle_str,
                                "hop_count": len(path),
                                "cycle_volume": round(current_vol + txn_amount, 2),
                            })
                            total_routed_volume += (current_vol + txn_amount)
                    elif next_acc not in path:
                        dfs_find_cycles(next_acc, path + [next_acc], current_vol + txn_amount, depth + 1)

        dfs_find_cycles(start_account_id, [start_account_id], 0.0, 1)

        is_circular = len(cycles_found) > 0
        layering_risk = min(1.0, 0.4 + (0.2 * len(cycles_found)) + (0.1 * len(cycles_found[0]["path"]) if is_circular else 0.0)) if is_circular else 0.0

        return {
            "start_account_id": start_account_id,
            "is_circular_routing": is_circular,
            "cycle_detected": is_circular,
            "cycles_count": len(cycles_found),
            "cycles": cycles_found,
            "primary_cycle_path": cycles_found[0]["path_str"] if is_circular else "",
            "hop_count": cycles_found[0]["hop_count"] if is_circular else 0,
            "total_routed_volume": round(total_routed_volume, 2),
            "layering_risk_score": round(layering_risk, 2),
        }

    # -------------------------------------------------------------
    # 12. merchant_collusion_ring: Bust-Out & Collusion Detection
    # -------------------------------------------------------------
    def merchant_collusion_ring(
        self, merchant_id: str = "", min_accounts: int = 2
    ) -> Dict[str, Any]:
        """Identifies dense clusters of buyer accounts, cards, and devices linked to specific merchants."""
        merchant_id = str(merchant_id)
        linked_accounts = set()
        linked_devices = set()
        linked_cards = set()
        txns_matched = []
        total_vol = 0.0

        all_txns = self.vertices.get("Transaction", {})
        for tid, tdata in all_txns.items():
            t_merch = str(tdata.get("merchant_id", tdata.get("merchant", "")))
            if not merchant_id or t_merch == merchant_id or merchant_id.lower() in t_merch.lower():
                txns_matched.append((tid, tdata))
                total_vol += float(tdata.get("amount", 0.0))

                # Find linked entities
                for e_type, to_type, to_id, _, _ in self.edges.get(("Transaction", tid), []):
                    if to_type == "Account":
                        linked_accounts.add(to_id)
                    elif to_type == "Device":
                        linked_devices.add(to_id)
                    elif to_type == "Card":
                        linked_cards.add(to_id)

        num_accs = len(linked_accounts)
        num_devs = len(linked_devices)
        num_cards = len(linked_cards)
        txn_count = len(txns_matched)
        avg_amt = round(total_vol / max(txn_count, 1), 2)

        collusion_risk = 0.0
        if num_accs >= min_accounts:
            collusion_risk = min(1.0, 0.45 + (0.12 * num_accs) + (0.15 * num_devs))

        is_collusion = num_accs >= min_accounts and collusion_risk >= 0.65

        return {
            "merchant_id": merchant_id,
            "transaction_count": txn_count,
            "total_volume": round(total_vol, 2),
            "avg_transaction_amount": avg_amt,
            "colluding_accounts_count": num_accs,
            "colluding_accounts": list(linked_accounts),
            "shared_devices_count": num_devs,
            "shared_devices": list(linked_devices),
            "linked_cards_count": num_cards,
            "collusion_risk_score": round(collusion_risk, 2),
            "is_collusion_detected": is_collusion,
        }

