"""
Typed AgentState Schema for LangGraph 8-Step Fraud Investigation Workflow.
"""

from typing import Dict, List, Any, Optional, TypedDict


class EvidencePillars(TypedDict):
    p_txn: float      # Transaction history & velocity
    p_dev: float      # Device & identity fingerprinting
    p_behav: float    # Account behavior vs baseline
    p_prior: float    # Prior case similarity


class UncertaintyMetrics(TypedDict):
    data_completeness: float    # C_data in [0.0, 1.0]
    signal_conflict: float      # S_conflict in [0.0, 1.0]
    composite_confidence: float # Conf in [0.0, 1.0]
    risk_level: str             # low, medium, high, critical
    pillar_scores: EvidencePillars


class ActionRecord(TypedDict):
    action_id: str
    action_type: str
    target_entity: str
    approval_route: str         # auto_executable, tier1_analyst, tier2_approval
    rationale: str
    policy_citation: str
    status: str                 # executed, pending_approval, cancelled


class EvidenceTrajectory(TypedDict):
    before_additional_evidence: Dict[str, Any]
    additional_evidence_gathered: List[Dict[str, Any]]
    after_additional_evidence: Dict[str, Any]
    what_changed: str


class AgentState(TypedDict, total=False):
    case_id: str
    trigger_type: str           # risk_score_alert, customer_dispute, analyst_escalation
    trigger_data: Dict[str, Any]
    entities: Dict[str, Any]
    graph_evidence: Dict[str, Any]
    policy_citations: List[Dict[str, Any]]
    typology_matches: List[Dict[str, Any]]
    uncertainty_metrics: UncertaintyMetrics
    evidence_trajectory: EvidenceTrajectory
    next_best_actions_before_evidence: List[ActionRecord]
    next_best_actions_after_evidence: List[ActionRecord]
    next_best_actions: List[ActionRecord]
    sar_filing: Optional[Dict[str, Any]]
    final_explanation: str
    case_memory_id: str
    step_history: List[Dict[str, Any]]
    requires_gathering_loop: bool
    counterfactual_analysis: Dict[str, Any]
    typology_deep_dive: Dict[str, Any]
    circular_routing_evidence: Dict[str, Any]
    merchant_collusion_evidence: Dict[str, Any]

