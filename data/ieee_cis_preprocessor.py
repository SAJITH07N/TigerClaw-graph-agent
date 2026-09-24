"""
IEEE-CIS Fraud Dataset Preprocessor & Multi-Attribute Entity Resolver.
Resolves synthetic Account proxies from card features, addresses, and email domains.
Synthesizes SHARES_DEVICE and SHARES_CARD graph topology.
"""

import hashlib
import json
from typing import Dict, List, Any, Optional
from tigergraph.client import TigerGraphClient


def compute_account_proxy_key(row: Dict[str, Any]) -> str:
    """
    Constructs deterministic Account Proxy Key from (card1..card6, addr1, P_emaildomain).
    """
    if row.get("account_id"):
        return str(row.get("account_id"))
    card_str = f"{row.get('card1','')}-{row.get('card2','')}-{row.get('card3','')}-{row.get('card4','')}-{row.get('card5','')}-{row.get('card6','')}"
    addr1 = str(row.get("addr1", "NONE"))
    p_email = str(row.get("p_emaildomain", "NONE")).lower()
    raw = f"{card_str}|{addr1}|{p_email}"
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"ACC-{h}"


class IEEECISPreprocessor:
    def __init__(self, tg_client: Optional[TigerGraphClient] = None):
        self.tg_client = tg_client or TigerGraphClient()

    def process_transaction_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingests a single IEEE-CIS transaction record into the TigerGraph graph.
        Creates vertices (Transaction, Account, Card, Device, Address, EmailDomain) and edges.
        """
        txn_id = str(record.get("TransactionID") or record.get("txn_id"))
        amount = float(record.get("TransactionAmt") or record.get("amount", 100.0))
        ts = int(record.get("TransactionDT") or record.get("ts", 1000000))
        product_cd = str(record.get("ProductCD") or record.get("product_cd", "W"))
        risk_score = float(record.get("risk_score", 0.15))
        is_fraud = int(record.get("isFraud") or record.get("is_fraud", 0))

        # 1. Upsert Transaction Vertex
        self.tg_client.upsert_vertex("Transaction", txn_id, {
            "amount": amount,
            "ts": ts,
            "product_cd": product_cd,
            "risk_score": risk_score,
            "is_fraud": is_fraud,
            "addr1": str(record.get("addr1", "")),
            "addr2": str(record.get("addr2", "")),
            "p_emaildomain": str(record.get("P_emaildomain", record.get("p_emaildomain", ""))),
            "r_emaildomain": str(record.get("R_emaildomain", record.get("r_emaildomain", ""))),
        })

        # 2. Upsert Card Vertex
        card_id = record.get("card_id") or f"CARD-{record.get('card1', '0')}-{record.get('card2', '0')}"
        self.tg_client.upsert_vertex("Card", card_id, {
            "card1": str(record.get("card1", "")),
            "card2": str(record.get("card2", "")),
            "card3": str(record.get("card3", "")),
            "card4": str(record.get("card4", "")),
            "card5": str(record.get("card5", "")),
            "card6": str(record.get("card6", "")),
        })
        self.tg_client.upsert_edge("PAID_WITH", "Transaction", txn_id, "Card", card_id)

        # 3. Derive & Upsert Account Vertex
        account_id = compute_account_proxy_key(record)
        self.tg_client.upsert_vertex("Account", account_id, {
            "account_holder_name": f"Account Holder {account_id[-4:]}",
            "tenure_months": int(record.get("tenure_months", 12)),
            "historical_avg_amount": float(record.get("historical_avg_amount", 120.0)),
            "historical_velocity": float(record.get("historical_velocity", 1.5)),
            "kyc_status": "verified",
            "risk_score": risk_score,
        })
        self.tg_client.upsert_edge("HELD_BY", "Card", card_id, "Account", account_id)
        self.tg_client.upsert_edge("SHARES_CARD", "Account", account_id, "Card", card_id, {"weight": 1.0})

        # 4. Upsert Device Vertex (if present)
        device_id = str(record.get("DeviceInfo") or record.get("device_id", "DEV-UNKNOWN"))
        if device_id != "DEV-UNKNOWN":
            self.tg_client.upsert_vertex("Device", device_id, {
                "device_fingerprint": device_id,
                "device_type": str(record.get("DeviceType", "desktop")),
                "is_emulator": bool("emulator" in device_id.lower() or record.get("is_emulator", False)),
                "risk_score": 0.8 if "emulator" in device_id.lower() else 0.1,
            })
            self.tg_client.upsert_edge("FROM_DEVICE", "Transaction", txn_id, "Device", device_id)
            self.tg_client.upsert_edge("USED_BY", "Device", device_id, "Account", account_id)
            self.tg_client.upsert_edge("SHARES_DEVICE", "Account", account_id, "Device", device_id, {"weight": 1.0})

        # 5. Upsert Address Vertex (if present)
        addr1 = str(record.get("addr1", ""))
        if addr1:
            addr_id = f"ADDR-{addr1}"
            self.tg_client.upsert_vertex("Address", addr_id, {"zip_code": addr1, "country": "US"})
            self.tg_client.upsert_edge("TO_ADDRESS", "Transaction", txn_id, "Address", addr_id)

        # 6. Upsert Email Domain (if present)
        email_dom = str(record.get("P_emaildomain", record.get("p_emaildomain", "")))
        if email_dom:
            is_disp = any(d in email_dom.lower() for d in ["temp", "disposable", "guerrillamail", "mailinator"])
            self.tg_client.upsert_vertex("EmailDomain", email_dom, {"is_disposable": is_disp})

        return {
            "txn_id": txn_id,
            "account_id": account_id,
            "card_id": card_id,
            "device_id": device_id,
        }
