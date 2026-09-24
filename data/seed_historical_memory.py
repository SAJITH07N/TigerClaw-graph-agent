"""
Historical Case Memory Seeding Script.
Ingests 4 months of historical closed cases (confirmed fraud and cleared false positives)
into TigerGraph PriorCase vertices with semantic vector embeddings for TigerVector GraphRAG retrieval.
"""

import time
import random
from typing import List, Dict, Any, Optional
from graphrag.policy_store import generate_deterministic_embedding
from tigergraph.client import TigerGraphClient


HISTORICAL_CASE_TEMPLATES = [
    {
        "typology": "Account Takeover (ATO)",
        "fraud": True,
        "summaries": [
            "Customer credentials compromised via phishing. Suspect logged in from new Android emulator in foreign IP and transferred $4,200 via wire. Fast velocity burst within 30 minutes of password reset.",
            "Account takeover via SIM swap. Unauthorized user added new card and drained $3,850 across digital merchants in 2 hours.",
            "ATO incident with device fingerprint change to Linux headless browser. 5 rapid transfers of $950 each.",
        ],
    },
    {
        "typology": "Mule Ring / Shared Device Syndicate",
        "fraud": True,
        "summaries": [
            "Organized mule syndicate identified sharing device DEV-RING-889 across 6 distinct student accounts. Coordinated P2P deposits layered into crypto exchange accounts totaling $34,000.",
            "Shared device emulator cluster connecting 4 accounts. Rapid circular transactions to evade velocity checks, SAR filed under 31 CFR 1020.320.",
            "Mule ring operating across 5 proxy accounts with shared IP and card fan-out. Aggregate suspicious volume $48,500.",
        ],
    },
    {
        "typology": "Card Testing Burst / Micro-Charge",
        "fraud": True,
        "summaries": [
            "Automated card testing script fired 14 micro-charges ($1.00 to $4.99) within 80 seconds on card CARD-9921 across online gaming sites, followed by a $1,200 electronics purchase attempt.",
            "High frequency card testing burst. 8 rapid authorizations in 60 seconds with 50% decline rate.",
            "Micro-charge probing syndicate targeting digital gift cards before attempting luxury goods purchase.",
        ],
    },
    {
        "typology": "First-Party Bust-Out / Synthetic Identity",
        "fraud": True,
        "summaries": [
            "Synthetic identity nurtured over 8 months. Sudden $12,000 max credit line drawdown across cash advances followed by immediate phone disconnection and account abandonment.",
            "First party bust-out scheme with multiple max-limit loan draws in 48 hours across linked synthetic profiles.",
        ],
    },
    {
        "typology": "Legitimate Vacation / Seasonal Travel",
        "fraud": False,
        "summaries": [
            "Customer traveled to Paris for vacation. Flagged for foreign IP and $2,400 hotel charge, but customer verified transaction via two-factor SMS. Cleared as benign travel.",
            "Seasonal holiday shopping surge. High volume of luxury retail transactions on known family device. Customer confirmed identity via out-of-band call.",
            "Business travel flight and car rental booking. Transaction cleared following biometric step-up authentication.",
        ],
    },
]


def seed_historical_memory(tg_client: Optional[TigerGraphClient] = None, count: int = 100) -> int:
    """Seeds historical closed cases into the TigerGraph PriorCase knowledge layer."""
    client = tg_client or TigerGraphClient()
    seeded = 0
    now = int(time.time())
    four_months_seconds = 120 * 86400

    for i in range(1, count + 1):
        tmpl = random.choice(HISTORICAL_CASE_TEMPLATES)
        summary = random.choice(tmpl["summaries"]) + f" (Ref: INC-{i:04d})"
        case_id = f"PRIOR-CASE-{i:04d}"
        embedding = generate_deterministic_embedding(f"{tmpl['typology']} {summary}")
        ts = now - random.randint(1000, four_months_seconds)

        case_data = {
            "prior_case_id": case_id,
            "outcome": "confirmed_fraud" if tmpl["fraud"] else "cleared_false_positive",
            "confirmed_fraud": tmpl["fraud"],
            "fraud_type": tmpl["typology"],
            "summary": summary,
            "embedding": embedding,
            "closed_at": ts,
        }

        client.upsert_vertex("PriorCase", case_id, case_data)
        seeded += 1

    return seeded


if __name__ == "__main__":
    count = seed_historical_memory()
    print(f"Successfully seeded {count} historical cases into TigerGraph PriorCase memory.")
