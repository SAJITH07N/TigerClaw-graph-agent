"""
Unified Dual-Mode TigerGraph Client.
Provides a single Python API whether running against TigerGraph Savanna Cloud,
Local Docker TigerGraph RESTPP endpoints, or the built-in TigerGraph In-Memory Graph Engine.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from tigergraph.in_memory_engine import TigerGraphInMemoryEngine

logger = logging.getLogger(__name__)


class TigerGraphClient:
    def __init__(
        self,
        host: Optional[str] = None,
        graph_name: str = "FraudInvestigationGraph",
        username: Optional[str] = None,
        password: Optional[str] = None,
        secret: Optional[str] = None,
        token: Optional[str] = None,
        force_in_memory: bool = False,
    ):
        self.host = host or os.getenv("TG_HOST")
        self.graph_name = graph_name or os.getenv("TG_GRAPH_NAME", "FraudInvestigationGraph")
        self.username = username or os.getenv("TG_USERNAME", "tigergraph")
        self.password = password or os.getenv("TG_PASSWORD", "tigergraph")
        self.secret = secret or os.getenv("TG_SECRET")
        self.token = token or os.getenv("TG_TOKEN")
        self.use_live = False
        self.tg_conn = None
        self.engine = TigerGraphInMemoryEngine(graph_name=self.graph_name)

        if not force_in_memory and self.host:
            try:
                import pyTigerGraph as tg
                self.tg_conn = tg.TigerGraphConnection(
                    host=self.host,
                    graphname=self.graph_name,
                    username=self.username,
                    password=self.password,
                    secret=self.secret,
                    apiToken=self.token,
                )
                if self.secret and not self.token:
                    self.token = self.tg_conn.getToken(self.secret)[0]
                self.tg_conn.getVertexTypes()
                self.use_live = True
                logger.info("Connected to live TigerGraph server at %s", self.host)
            except Exception as e:
                logger.warning("Could not connect to live TigerGraph instance (%s). Falling back to In-Memory Engine.", e)
                self.use_live = False
        else:
            self.use_live = False

    def upsert_vertex(self, vertex_type: str, primary_id: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        if self.use_live and self.tg_conn:
            try:
                self.tg_conn.upsertVertex(vertex_type, primary_id, attributes)
                return
            except Exception as e:
                logger.warning("Live TigerGraph upsert failed: %s. Using in-memory engine.", e)
        self.engine.upsert_vertex(vertex_type, primary_id, attributes)

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
        if self.use_live and self.tg_conn:
            try:
                self.tg_conn.upsertEdge(from_type, from_id, edge_type, to_type, to_id, attributes)
                return
            except Exception as e:
                logger.warning("Live TigerGraph edge upsert failed: %s. Using in-memory engine.", e)
        self.engine.upsert_edge(edge_type, from_type, from_id, to_type, to_id, attributes, is_directed)

    def get_vertex(self, vertex_type: str, primary_id: str) -> Optional[Dict[str, Any]]:
        if self.use_live and self.tg_conn:
            try:
                res = self.tg_conn.getVerticesById(vertex_type, primary_id)
                if res:
                    return res[0].get("attributes", {})
            except Exception:
                pass
        return self.engine.get_vertex(vertex_type, primary_id)

    def run_installed_query(self, query_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        params = params or {}
        if self.use_live and self.tg_conn:
            try:
                return self.tg_conn.runInstalledQuery(query_name, params)
            except Exception as e:
                logger.warning("Failed running installed query %s on live TigerGraph: %s. Emulating.", query_name, e)

        # In-memory execution dispatcher (returns unnested structures)
        if query_name == "get_entity_neighborhood":
            return [self.engine.get_entity_neighborhood(
                start_id=params.get("start_id", ""),
                start_type=params.get("start_type", "Transaction"),
                max_hops=int(params.get("max_hops", 2)),
            )]
        elif query_name == "shared_device_ring":
            return [self.engine.shared_device_ring(device_id=params.get("device_id", ""))]
        elif query_name == "shared_card_fanout":
            return [self.engine.shared_card_fanout(
                card_id=params.get("card_id", ""),
                time_window_seconds=int(params.get("time_window_seconds", 86400)),
            )]
        elif query_name == "velocity_check":
            return [self.engine.velocity_check(
                account_id=params.get("account_id", ""),
                current_ts=params.get("current_ts"),
            )]
        elif query_name == "temporal_velocity_burst":
            return [self.engine.temporal_velocity_burst(
                card_id=params.get("card_id", ""),
                burst_window_seconds=int(params.get("burst_window_seconds", 120)),
                count_threshold=int(params.get("count_threshold", 3)),
            )]
        elif query_name == "pagerank_risk_propagation":
            return self.engine.pagerank_risk_propagation(
                max_iter=int(params.get("max_iter", 20)),
                damping=float(params.get("damping", 0.85)),
            )
        elif query_name == "community_detection":
            return self.engine.community_detection(min_size=int(params.get("min_size", 2)))
        elif query_name == "similar_case_search":
            return self.engine.similar_case_search(
                query_vector=params.get("query_vector", []),
                top_k=int(params.get("top_k", 5)),
            )
        elif query_name == "path_between":
            return self.engine.path_between(
                source_id=params.get("source_id", ""),
                target_id=params.get("target_id", ""),
                source_type=params.get("source_type", "Account"),
                target_type=params.get("target_type", "Device"),
            )
        elif query_name == "write_case_subgraph":
            return [self.engine.write_case_subgraph(case_payload=params.get("payload", {}))]
        elif query_name == "circular_fund_routing":
            return [self.engine.circular_fund_routing(
                start_account_id=params.get("start_account_id", params.get("account_id", "")),
                max_depth=int(params.get("max_depth", 4)),
                time_window_seconds=int(params.get("time_window_seconds", 86400)),
            )]
        elif query_name == "merchant_collusion_ring":
            return [self.engine.merchant_collusion_ring(
                merchant_id=params.get("merchant_id", ""),
                min_accounts=int(params.get("min_accounts", 2)),
            )]
        else:
            raise ValueError(f"Unknown query name: {query_name}")
