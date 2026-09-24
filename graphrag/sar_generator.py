"""
FinCEN Suspicious Activity Report (SAR) Generator (31 CFR § 1020.320).
Generates formal, regulatory-compliant 4-part SAR narratives and structured metadata.
"""

import time
from typing import Dict, Any, List, Optional


class SARGenerator:
    def __init__(self, institution_name: str = "First Global Bank, N.A.", bsa_id: str = "BSA-99482-TX"):
        self.institution_name = institution_name
        self.bsa_id = bsa_id

    def check_filing_eligibility(self, total_volume: float, has_identified_suspect: bool, is_syndicate: bool) -> bool:
        """
        Determines if a case triggers mandatory FinCEN filing under 31 CFR § 1020.320:
        1. >= $5,000 with identified suspect or mule ring
        2. >= $25,000 without identified suspect
        3. Identified multi-account syndicate or structuring
        """
        if total_volume >= 25000.0:
            return True
        if total_volume >= 5000.0 and (has_identified_suspect or is_syndicate):
            return True
        if is_syndicate and total_volume >= 2000.0:
            return True
        return False

    def generate_sar(
        self,
        case_id: str,
        suspect_entities: Dict[str, Any],
        transaction_summary: Dict[str, Any],
        graph_findings: Dict[str, Any],
        typology_match: Dict[str, Any],
        actions_taken: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generates a complete FinCEN-compliant SAR package."""
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        total_amount = float(transaction_summary.get("total_amount", 0.0))

        # Part 1: Executive Summary
        executive_summary = (
            f"SUSPICIOUS ACTIVITY REPORT - MANDATORY FILING UNDER 31 CFR § 1020.320.\n"
            f"Filing Institution: {self.institution_name} (BSA ID: {self.bsa_id}).\n"
            f"Case Identifier: {case_id}.\n"
            f"Total Suspicious Volume: ${total_amount:,.2f}.\n"
            f"Primary Suspect Account(s): {', '.join(suspect_entities.get('accounts', []))}.\n"
            f"Classification: {typology_match.get('name', 'Suspected Organized Fraud Syndicate')}.\n"
            f"Summary: Automated graph investigation identified coordinated suspicious activity involving "
            f"{len(suspect_entities.get('accounts', []))} account(s), {len(suspect_entities.get('cards', []))} card(s), "
            f"and device(s) {', '.join(suspect_entities.get('devices', []))} exhibiting anomalous velocity and shared infrastructure."
        )

        # Part 2: Entity & Graph Topology
        entity_graph_narrative = (
            f"SECTION II: ENTITY & IDENTITY GRAPH TOPOLOGY\n"
            f"- Identified Accounts: {', '.join(suspect_entities.get('accounts', []))}\n"
            f"- Associated Cards: {', '.join(suspect_entities.get('cards', []))}\n"
            f"- Hardware Device Fingerprints: {', '.join(suspect_entities.get('devices', []))}\n"
            f"- IP / Address Nodes: {', '.join(suspect_entities.get('addresses', []))}\n"
            f"- Graph Pattern Findings: {graph_findings.get('summary', 'Shared device ring and multi-account fanout.')}\n"
            f"- PageRank Risk Diffusion Score: {graph_findings.get('max_pagerank_risk', 'N/A')}\n"
            f"- Community Syndicate Size: {graph_findings.get('community_size', 1)} entities."
        )

        # Part 3: Chronological Transaction Flow
        txns_text = "\n".join([
            f"  * {t.get('txn_id', 'TXN')}: Amount ${float(t.get('amount', 0)):,.2f}, TS: {t.get('ts', 'N/A')}, "
            f"Merchant/Product: {t.get('product_cd', 'Online')}, Risk Score: {t.get('risk_score', 'N/A')}"
            for t in transaction_summary.get("transactions", [])
        ])
        chronological_flow = (
            f"SECTION III: CHRONOLOGICAL TRANSACTION FLOW & VELOCITY\n"
            f"Analysis of transaction timestamps indicates coordinated velocity bursts:\n"
            f"{txns_text if txns_text else '  * No individual transactions itemized.'}\n"
            f"- 1-Hour Velocity: {transaction_summary.get('velocity_1h_count', 0)} transactions, "
            f"${float(transaction_summary.get('velocity_1h_volume', 0)):,.2f}.\n"
            f"- Velocity Z-Score: {transaction_summary.get('velocity_zscore', 0.0)} vs. historical baseline."
        )

        # Part 4: Regulatory & Law Enforcement Conclusion
        actions_text = ", ".join([a.get("action_type", "action") for a in actions_taken])
        regulatory_conclusion = (
            f"SECTION IV: REGULATORY CONCLUSION & CONTAINMENT ACTIONS\n"
            f"The investigated pattern matches documented typology '{typology_match.get('name')}' "
            f"(Confidence: {typology_match.get('confidence', 0.0):.2%}). "
            f"Immediate preventative measures executed: [{actions_text}]. "
            f"This filing is maintained under 31 U.S.C. 5318(g) Safe Harbor and in compliance with Bank Secrecy Act records retention rules. "
            f"Case memory and evidence graph stored under TigerGraph Case Memory Node {case_id}."
        )

        full_narrative = f"{executive_summary}\n\n{entity_graph_narrative}\n\n{chronological_flow}\n\n{regulatory_conclusion}"

        narrative_dict = {
            "part_1_executive_summary": executive_summary,
            "part_2_graph_connectivity": entity_graph_narrative,
            "part_2_entity_graph": entity_graph_narrative,
            "part_3_chronological_flow": chronological_flow,
            "part_4_regulatory_conclusion": regulatory_conclusion,
        }

        return {
            "sar_id": f"SAR-{case_id}",
            "case_id": case_id,
            "filed_at": timestamp,
            "institution": self.institution_name,
            "filing_institution": self.institution_name,
            "bsa_id": self.bsa_id,
            "mandatory_filing": True,
            "statutory_trigger": "31 CFR § 1020.320 / FinCEN Form 111",
            "total_suspicious_amount": total_amount,
            "total_suspicious_volume": total_amount,
            "primary_subject_accounts": suspect_entities.get("accounts", []),
            "typology": typology_match.get("name"),
            "typology_id": typology_match.get("typology_id"),
            "four_part_narrative": narrative_dict,
            "narrative_sections": narrative_dict,
            "full_narrative_text": full_narrative,
            "status": "QUEUED_FOR_BSA_REVIEW",
        }
