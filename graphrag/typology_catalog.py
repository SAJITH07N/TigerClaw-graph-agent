"""
Documented Fraud Typologies Catalog & Classifier.
Embeds and matches fraud typologies with graph pattern indicators.
"""

from typing import List, Dict, Any, Optional
from graphrag.policy_store import generate_deterministic_embedding
from tigergraph.client import TigerGraphClient


TYPOLOGIES = [
    {
        "typology_id": "TYP-ATO-001",
        "name": "Account Takeover (ATO)",
        "description": "Unauthorized account takeover via credential stuffing or SIM swapping, followed by rapid fund transfer.",
        "indicators": [
            "new_device_fingerprint",
            "emulator_used",
            "velocity_spike_post_login",
            "address_mismatch",
            "unusual_high_value_transaction",
        ],
    },
    {
        "typology_id": "TYP-MULE-002",
        "name": "Mule Ring / Shared Device Syndicate",
        "description": "Coordinated ring utilizing shared devices or proxies across multiple consumer accounts.",
        "indicators": [
            "shared_device_multiple_accounts",
            "cross_account_card_overlap",
            "high_community_density",
            "pagerank_risk_diffusion_high",
        ],
    },
    {
        "typology_id": "TYP-TEST-003",
        "name": "Card Testing Burst / Micro-Charge",
        "description": "Rapid automated micro-transactions (< $15.00) used by card-testing scripts to probe validity.",
        "indicators": [
            "burst_velocity_under_120s",
            "micro_charges_under_15",
            "high_frequency_merchant_retries",
            "card_fanout_across_devices",
        ],
    },
    {
        "typology_id": "TYP-BUST-004",
        "name": "First-Party Bust-Out / Synthetic Identity",
        "description": "Nurtured identity or synthetic profile accumulating credit followed by sudden total drawdown.",
        "indicators": [
            "sudden_credit_line_exhaustion",
            "historic_low_velocity_then_extreme_surge",
            "shared_address_with_delinquent_nodes",
        ],
    },
    {
        "typology_id": "TYP-LEGIT-005",
        "name": "Legitimate Vacation / Seasonal Travel",
        "description": "Benign out-of-pattern spending caused by holiday travel, seasonal shopping, or business trips.",
        "indicators": [
            "known_device_verified",
            "long_account_tenure",
            "clean_historical_dispute_record",
            "positive_customer_stepup_confirmation",
        ],
    },
]


class TypologyCatalog:
    def __init__(self, tg_client: Optional[TigerGraphClient] = None):
        self.tg_client = tg_client or TigerGraphClient()
        self.typologies: Dict[str, Dict[str, Any]] = {}
        self._initialize_catalog()

    def _initialize_catalog(self) -> None:
        for t in TYPOLOGIES:
            t_copy = t.copy()
            full_text = f"{t['name']} {t['description']} {' '.join(t['indicators'])}"
            t_copy["embedding"] = generate_deterministic_embedding(full_text)
            self.typologies[t["typology_id"]] = t_copy
            # Upsert into graph as TypologyDoc vertex
            self.tg_client.upsert_vertex("TypologyDoc", t["typology_id"], t_copy)

    def match_typology(self, observed_indicators: List[str], top_k: int = 2) -> List[Dict[str, Any]]:
        """Matches observed graph/transaction indicators against documented typologies."""
        obs_set = set(observed_indicators)
        matches = []

        for t_id, t_data in self.typologies.items():
            ind_set = set(t_data["indicators"])
            intersection = obs_set.intersection(ind_set)
            jaccard = len(intersection) / max(len(obs_set.union(ind_set)), 1)

            # Cosine similarity on indicator text
            obs_text = " ".join(observed_indicators)
            obs_vec = generate_deterministic_embedding(obs_text)
            dot = sum(a * b for a, b in zip(obs_vec, t_data["embedding"]))

            combined_score = 0.6 * jaccard + 0.4 * max(dot, 0.0)

            matches.append({
                "typology_id": t_id,
                "name": t_data["name"],
                "confidence": round(combined_score, 4),
                "matched_indicators": list(intersection),
                "description": t_data["description"],
            })

        matches.sort(key=lambda x: x["confidence"], reverse=True)
        return matches[:top_k]
