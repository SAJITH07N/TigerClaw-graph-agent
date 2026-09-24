"""
TigerGraph Model Context Protocol (MCP) Server Adapter.
Exposes standard TigerGraph MCP tool endpoints for LLM agent integration.
"""

from typing import Dict, Any, List, Optional
from tigergraph.client import TigerGraphClient


class TigerGraphMCPServer:
    def __init__(self, client: Optional[TigerGraphClient] = None):
        self.client = client or TigerGraphClient()

    def get_graph_schema(self) -> Dict[str, Any]:
        """Returns the DDL schema definition of the graph."""
        return {
            "graph_name": self.client.graph_name,
            "vertex_types": [
                "Transaction", "Identity", "Card", "Account", "Device",
                "Address", "EmailDomain", "Case", "Evidence", "Decision",
                "Action", "PolicyDoc", "TypologyDoc", "PriorCase"
            ],
            "edge_types": [
                "PAID_WITH", "FROM_DEVICE", "TO_ADDRESS", "HELD_BY",
                "USED_BY", "SHARES_DEVICE", "SHARES_CARD", "ABOUT_ACCOUNT",
                "ABOUT_TRANSACTION", "HAS_EVIDENCE", "HAS_DECISION", "LED_TO",
                "SIMILAR_TO", "CITES", "MATCHES_TYPOLOGY"
            ]
        }

    def get_node(self, vertex_type: str, primary_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific node by vertex type and primary ID."""
        return self.client.get_vertex(vertex_type, primary_id)

    def run_installed_query(self, query_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Runs one of the 10 installed GSQL queries."""
        return self.client.run_installed_query(query_name, params or {})

    def search_top_k_similarity(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Vector similarity search over historical cases using TigerVector."""
        return self.client.run_installed_query("similar_case_search", {"query_vector": query_vector, "top_k": top_k})
