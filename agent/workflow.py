"""
Agent Tiger Multi-Agent Investigation Workflow.
Coordinates state transitions, GSQL graph algorithms, typology specialization,
adversarial counterfactual analysis, conditional evidence loops, and graph memory.
"""

from typing import Dict, Any, Optional
from agent.state import AgentState
from tigergraph.client import TigerGraphClient
from graphrag.policy_store import PolicyStore
from graphrag.typology_catalog import TypologyCatalog
from graphrag.sar_generator import SARGenerator

from agent.nodes.trigger_node import trigger_node
from agent.nodes.investigate_node import investigate_node
from agent.nodes.gather_evidence_node import gather_evidence_node
from agent.nodes.typology_node import typology_node
from agent.nodes.assess_uncertainty_node import assess_uncertainty_node
from agent.nodes.gather_more_node import gather_more_node
from agent.nodes.counterfactual_node import counterfactual_node
from agent.nodes.take_action_node import take_action_node
from agent.nodes.explain_node import explain_node
from agent.nodes.update_memory_node import update_memory_node


class FraudInvestigationWorkflow:
    def __init__(
        self,
        tg_client: Optional[TigerGraphClient] = None,
        policy_store: Optional[PolicyStore] = None,
        typology_catalog: Optional[TypologyCatalog] = None,
        sar_generator: Optional[SARGenerator] = None,
    ):
        self.tg_client = tg_client or TigerGraphClient()
        self.policy_store = policy_store or PolicyStore(self.tg_client)
        self.typology_catalog = typology_catalog or TypologyCatalog(self.tg_client)
        self.sar_generator = sar_generator or SARGenerator()

    def run_investigation(self, initial_state: AgentState) -> AgentState:
        """
        Executes the full 10-step Agent Tiger investigation pipeline:
        Step 1: Trigger Ingestion & Normalization
        Step 2: Entity Resolution & Neighborhood BFS
        Step 3: Multi-Query GSQL & GraphRAG Evidence Gathering
        Step 4: Specialized Typology Deep-Dive Analysis
        Step 5: Multi-Pillar Uncertainty Assessment
        [Conditional Step 6]: Controlled Evidence Gathering Loop (if confidence < 0.75 or conflict high)
        Step 7: Adversarial Counterfactual Reasoning
        Step 8: Next-Best Action Determination & Permissions Gating
        Step 9: Grounded Explanation Synthesis
        Step 10: Graph Case Memory Persistence
        """
        state = initial_state.copy()

        # Step 1: Trigger
        state = trigger_node(state)

        # Step 2: Investigate
        state = investigate_node(state, self.tg_client)

        # Step 3: Gather Evidence (9 GSQL queries + Policy RAG)
        state = gather_evidence_node(state, self.tg_client, self.policy_store, self.typology_catalog)

        # Step 4: Specialized Typology Deep-Dive
        state = typology_node(state)

        # Step 5: Assess Uncertainty
        state = assess_uncertainty_node(state)

        # Conditional Step 6: Controlled Evidence Loop
        if state.get("requires_gathering_loop", False):
            state = gather_more_node(state)

        # Step 7: Adversarial Counterfactual Check
        state = counterfactual_node(state)

        # Step 8: Take Action & FinCEN SAR
        state = take_action_node(state, self.sar_generator)

        # Step 9: Explain
        state = explain_node(state)

        # Step 10: Update Graph Memory
        state = update_memory_node(state, self.tg_client)

        state["audit_steps"] = state.get("step_history", [])
        state["grounded_explanation"] = state.get("final_explanation", "")

        return state

