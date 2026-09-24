"""
Step 7: Explain Node.
Synthesizes audit-ready, grounded explanations combining graph topology,
uncertainty metrics, policy citations, and action rationale.
Supports dynamic Groq LLM synthesis with seamless local GraphRAG fallback.
"""

import time
from typing import Dict, Any
from agent.state import AgentState
from graphrag.groq_client import GroqClient

_GROQ_CLIENT = GroqClient()


def explain_node(state: AgentState) -> AgentState:
    """Step 7: Synthesizes fully grounded explanation narrative."""
    case_id = state.get("case_id", "CASE")
    typology = state.get("typology_matches", [{}])[0]
    uncertainty = state.get("uncertainty_metrics", {})
    trajectory = state.get("evidence_trajectory", {})
    actions = state.get("next_best_actions", [])
    policies = state.get("policy_citations", [])
    sar = state.get("sar_filing")
    entities = state.get("entities", {})

    # Attempt dynamic synthesis via Groq if available
    llm_context = {
        "case_id": case_id,
        "typology_name": typology.get("name", "Unknown Typology"),
        "risk_level": uncertainty.get("risk_level", "medium"),
        "composite_confidence": uncertainty.get("composite_confidence", 0.0),
        "entities": entities,
        "actions": actions,
        "has_sar": sar is not None,
        "what_changed": trajectory.get("what_changed", "Initial multi-hop traversal complete."),
    }
    groq_narrative = _GROQ_CLIENT.generate_investigation_narrative(llm_context)

    lines = []
    lines.append(f"# FRAUD INVESTIGATION AUDIT REPORT - {case_id}")
    lines.append(f"**Primary Finding**: Classified as **{typology.get('name', 'Unknown Typology')}** (Typology ID: `{typology.get('typology_id', 'N/A')}`).")
    lines.append(f"**Risk Level**: `{uncertainty.get('risk_level', 'medium').upper()}` | **Composite Confidence**: `{uncertainty.get('composite_confidence', 0.0):.2%}` | **Data Completeness**: `{uncertainty.get('data_completeness', 0.0):.2%}`.")
    lines.append("")

    if groq_narrative:
        lines.append("## 🤖 Executive Intelligence Summary (Groq LLaMA-3.3-70B)")
        lines.append(groq_narrative)
        lines.append("")

    lines.append("## 1. Graph Evidence & Entity Topology")
    lines.append(f"- **Target Accounts**: {', '.join(entities.get('accounts', []))}")
    lines.append(f"- **Associated Cards**: {', '.join(entities.get('cards', []))}")
    lines.append(f"- **Hardware Devices**: {', '.join(entities.get('devices', []))}")
    lines.append(f"- **Graph Indicators**: {', '.join(typology.get('matched_indicators', []))}")
    lines.append("")

    lines.append("## 2. Uncertainty & Evidence Trajectory")
    lines.append(f"- **Pillar Completeness**: Txn: {uncertainty.get('pillar_scores',{}).get('p_txn',0):.2f}, Dev: {uncertainty.get('pillar_scores',{}).get('p_dev',0):.2f}, Behav: {uncertainty.get('pillar_scores',{}).get('p_behav',0):.2f}, Prior Cases: {uncertainty.get('pillar_scores',{}).get('p_prior',0):.2f}")
    lines.append(f"- **Evidence Trajectory Delta**: {trajectory.get('what_changed', 'Initial assessment complete.')}")
    lines.append("")

    counterfactual = state.get("counterfactual_analysis")
    if counterfactual:
        lines.append("## 3. Adversarial Counterfactual Analysis")
        lines.append(f"- **Strongest Benign Counterfactual**: {counterfactual.get('strongest_counterfactual', 'None')} (Plausibility: {counterfactual.get('strongest_counterfactual_plausibility', 0.0):.2%})")
        lines.append(f"- **Fraud vs. Benign Confidence**: {counterfactual.get('fraud_vs_benign_confidence', 0.0):.2%} | **False-Positive Risk**: {counterfactual.get('false_positive_risk', 0.0):.2%}")
        lines.append(f"- **Adversarial Recommendation**: `{counterfactual.get('recommendation', 'CONFIRM_CONTAINMENT')}`")
        lines.append("")

    lines.append("## 4. Policy-Grounded Next-Best Actions")
    for act in actions:
        lines.append(f"- **[{act.get('permission_level')}] {act.get('action_type')}** ({act.get('status')}): {act.get('rationale')} *(Ref: {act.get('policy_citation')})*")
    lines.append("")

    if sar:
        lines.append("## 5. Regulatory FinCEN SAR Filing")
        lines.append(f"- **SAR ID**: `{sar.get('sar_id')}` | **Status**: `{sar.get('status')}` | **Suspicious Volume**: `${sar.get('total_suspicious_amount', 0):,.2f}`")
        lines.append(f"- **Filing Mandate**: 31 CFR § 1020.320")
    else:
        lines.append("## 5. Regulatory FinCEN SAR Filing")
        lines.append("- **Status**: Below regulatory thresholds or cleared benign activity. No SAR required.")

    full_explanation = "\n".join(lines)

    history = state.get("step_history", [])
    history.append({
        "step": 9,
        "name": "Grounded Explanation Synthesis",
        "timestamp": int(time.time()),
        "status": "completed",
        "details": f"Synthesized audit report ({'Groq LLM Dynamic' if groq_narrative else 'Deterministic GraphRAG Grounded'}) with {len(actions)} actions and policy grounding.",
    })

    return {
        **state,
        "final_explanation": full_explanation,
        "step_history": history,
    }

