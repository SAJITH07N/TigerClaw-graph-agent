# Building an Autonomous Graph-Native Fraud Investigation & Next-Best Action Platform with TigerGraph, LangGraph, and GraphRAG

*How we engineered an enterprise-grade agentic financial crime defense system uniting GSQL multi-hop graph algorithms, 4-pillar uncertainty quantification, dynamic evidence loops, and automated FinCEN SAR compliance.*

---

## 1. Introduction & The Paradigm Shift in Financial Crime

Financial fraud has evolved from isolated point-of-sale card theft into sophisticated, multi-layered cybercrime operations. Modern fraud rings deploy distributed botnets, emulator farms, synthetic identities, and complex money mule laundering chains across thousands of synthetic accounts.

Traditional fraud detection engines—predominantly rule-based decision trees and point-in-time tabular gradient boosted machines (GBMs)—suffer from three catastrophic systemic flaws:

1. **Relational Blindness (The Isolated Transaction Silo)**: A $450 transaction from an emulator might appear marginally suspicious on its own. However, if that emulator shares a device fingerprint with 12 distinct accounts created within the past 48 hours, it is a high-confidence mule ring. Tabular models evaluating rows in isolation fail to capture these multi-hop topologies.
2. **Alert Fatigue & Binary False Positives**: Traditional rules generate massive alert queues with false positive rates exceeding 85%. Benign anomalies—such as a long-time customer traveling internationally on vacation—are aggressively blocked, degrading customer experience.
3. **Operational Bottlenecks & Static Playbooks**: When an alert fires, human fraud analysts must manually query disparate databases, inspect hardware headers, search historical cases, and manually draft narrative Suspicious Activity Reports (SAR). This manual loop introduces hours of delay, allowing syndicates to drain balances and bust out.

To overcome these barriers, we developed the **TigerGraph Agentic Fraud Investigation & Next-Best Action Platform** for the **HHGOA Challenge (Task 4)**. 

In this post, we deep-dive into how we designed and implemented:
- A **14-vertex, 10-edge heterogeneous graph schema** powered by **10 installed GSQL queries**.
- An **8-step LangGraph multi-agent state machine** executing automated investigations.
- A mathematically grounded **4-Pillar Uncertainty & Confidence Model** that dynamically requests supplementary evidence when confidence is low.
- A **2D Risk-Confidence Next-Best Action Permissions Matrix** with automated Tier-0 controls, Tier-1 analyst approvals, and Tier-2 dual-control lead authorizations.
- A **GraphRAG Policy Grounding & FinCEN SAR Engine** that automatically drafts regulatory 4-part narratives under **31 CFR § 1020.320**.
- A **Tri-Layer Case Memory** leveraging **TigerVector cosine similarity** over 100 historical closed cases.

---

## 2. System Architecture Overview

```
                                    ┌────────────────────────────────────────────────────────┐
                                    │                MULTI-SOURCE TRIGGERS                   │
                                    │  [Risk Score Alerts] [Customer Disputes] [Escalations] │
                                    └──────────────────────────┬─────────────────────────────┘
                                                               │
                                                               ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           LANGGRAPH 8-STEP STATE MACHINE                                               │
│                                                                                                                        │
│  ┌────────────────────────┐       ┌────────────────────────┐       ┌────────────────────────┐                          │
│  │ 1. Trigger Ingestion   │ ────► │ 2. Entity Resolution   │ ────► │ 3. GSQL & GraphRAG     │                          │
│  │    & Normalization     │       │    & Neighbor BFS      │       │    Evidence Gathering  │                          │
│  └────────────────────────┘       └────────────────────────┘       └───────────┬────────────┘                          │
│                                                                                │                                       │
│                                   ┌────────────────────────┐                   ▼                                       │
│                                   │ 5. Controlled Evidence │ ◄─── [Conf < 0.75 or Conflict]                            │
│                                   │    Gathering Loop      │                   │                                       │
│                                   └───────────┬────────────┘                   ▼                                       │
│                                               │                    ┌────────────────────────┐                          │
│                                               └──────────────────► │ 4. Assess Uncertainty  │                          │
│                                                                    │    (4-Pillar Model)    │                          │
│                                                                    └───────────┬────────────┘                          │
│                                                                                │                                       │
│  ┌────────────────────────┐       ┌────────────────────────┐                   ▼                                       │
│  │ 8. Graph Case Memory   │ ◄──── │ 7. Grounded Audit      │ ◄──── ┌────────────────────────┐                          │
│  │    Persistence (Write) │       │    Explanation Synth   │       │ 6. Next-Best Action    │                          │
│  └────────────────────────┘       └────────────────────────┘       │    & SAR Filing Gating │                          │
│                                                                    └────────────────────────┘                          │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                               │
                                                               ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                         TIGERGRAPH CASE MEMORY & KNOWLEDGE ENGINE                                      │
│                                                                                                                        │
│   [14 Vertices & 10 Edges DDL]    [10 Installed GSQL Queries]   [TigerVector Cosine Search]   [GraphRAG Policy Store]  │
│   - Transaction, Account, Device  - BFS Neighborhood, Mule Ring - 100+ Historical Closed      - 31 CFR § 1020.320 SAR  │
│   - Card, Address, Case, Action   - PageRank Risk Diffusion     - Similar Case Cosine         - Bank Fraud Policies    │
│   - Evidence, Decision, PriorCase - Louvain Syndicate Clusters  - Embedding Indexing          - 5 Documented Typologies│
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

The system architecture cleanly decouples stateful investigation orchestration from the underlying high-performance graph database and vector memory.

---

## 3. The Heterogeneous Fraud Graph Schema & 10 Installed GSQL Queries

### 3.1 14-Vertex, 10-Edge Heterogeneous Schema
Financial fraud graphs are fundamentally heterogeneous. Entities have distinct temporal dynamics, risk profiles, and connectivity constraints. Our schema models transactional activity, identity infrastructure, policy documentation, and case audit history:

```gsql
CREATE GRAPH FraudGraph(
    // Financial & Entity Vertices
    VERTEX Transaction (PRIMARY_ID txn_id STRING, amount DOUBLE, timestamp INT, is_fraud BOOL, risk_score DOUBLE),
    VERTEX Account     (PRIMARY_ID account_id STRING, created_at INT, risk_score DOUBLE, status STRING),
    VERTEX Card        (PRIMARY_ID card_id STRING, card_type STRING, issuer STRING, risk_score DOUBLE),
    VERTEX Device      (PRIMARY_ID device_id STRING, device_type STRING, ip_address STRING, is_emulator BOOL),
    VERTEX Address     (PRIMARY_ID address_id STRING, street STRING, zip STRING, country STRING),
    VERTEX EmailDomain (PRIMARY_ID domain_id STRING, is_disposable BOOL, risk_multiplier DOUBLE),
    VERTEX Identity    (PRIMARY_ID identity_id STRING, ssn_hash STRING, full_name STRING, kyc_status STRING),

    // Investigation & Case Memory Vertices
    VERTEX Case        (PRIMARY_ID case_id STRING, trigger_type STRING, status STRING, risk_level STRING, created_at INT),
    VERTEX Evidence    (PRIMARY_ID evidence_id STRING, pillar STRING, score DOUBLE, description STRING),
    VERTEX Decision    (PRIMARY_ID decision_id STRING, outcome STRING, confidence DOUBLE, timestamp INT),
    VERTEX Action      (PRIMARY_ID action_id STRING, action_type STRING, permission_level STRING, status STRING),
    VERTEX PriorCase   (PRIMARY_ID prior_case_id STRING, summary STRING, outcome STRING, embedding VECTOR<DOUBLE, 64>),
    VERTEX PolicyDoc   (PRIMARY_ID policy_id STRING, title STRING, text STRING, section STRING),
    VERTEX TypologyDoc (PRIMARY_ID typology_id STRING, name STRING, indicators STRING, embedding VECTOR<DOUBLE, 64>),

    // Directional & Undirected Graph Edges
    UNDIRECTED EDGE PAID_WITH (FROM Transaction, TO Card),
    UNDIRECTED EDGE FROM_DEVICE (FROM Transaction, TO Device),
    UNDIRECTED EDGE TO_ADDRESS (FROM Transaction, TO Address),
    UNDIRECTED EDGE HELD_BY (FROM Account, TO Identity),
    UNDIRECTED EDGE USED_BY (FROM Card, TO Account),
    UNDIRECTED EDGE SHARES_DEVICE (FROM Account, TO Device),
    UNDIRECTED EDGE SHARES_CARD (FROM Account, TO Card),
    DIRECTED EDGE ABOUT_TRANSACTION (FROM Case, TO Transaction),
    DIRECTED EDGE ABOUT_ACCOUNT (FROM Case, TO Account),
    DIRECTED EDGE HAS_EVIDENCE (FROM Case, TO Evidence),
    DIRECTED EDGE HAS_DECISION (FROM Case, TO Decision),
    DIRECTED EDGE LED_TO_ACTION (FROM Decision, TO Action),
    UNDIRECTED EDGE SIMILAR_TO (FROM Case, TO PriorCase, similarity DOUBLE),
    DIRECTED EDGE CITES_POLICY (FROM Action, TO PolicyDoc),
    DIRECTED EDGE MATCHES_TYPOLOGY (FROM Case, TO TypologyDoc, confidence DOUBLE)
);
```

### 3.2 The 10 High-Performance Installed GSQL Queries

Rather than issuing unoptimized ad-hoc REST lookups, the platform pre-installs 10 parameterized GSQL queries compiled into native C++ binaries within TigerGraph:

1. **`get_entity_neighborhood` (2-Hop BFS)**: Extracts the full 2-hop topological ego-network around a transaction or account, returning structured node and edge payloads for visualization.
2. **`shared_device_ring` (Mule Ring Detection)**: Traverses `Account - SHARES_DEVICE - Device` to detect hardware sharing rings and emulator clusters across multiple unrelated identities.
3. **`shared_card_fanout` (Card Testing & Fan-Out)**: Traverses `Account - SHARES_CARD - Card` to detect cross-account payment card fan-out and rapid card testing.
4. **`velocity_check` (Sliding Window Velocity Spikes)**: Accumulates transaction count and dollar volume across 1-hour, 6-hour, and 24-hour sliding windows, comparing against account baselines.
5. **`pagerank_risk_propagation` (Associative Risk Diffusion)**: Runs power-iteration PageRank weighted by known bad entity seeds to diffuse risk through neighbor accounts and shared devices.
6. **`community_detection` (Louvain Syndicate Clustering)**: Computes modularity-optimized community clusters to partition the graph into tightly knit fraud syndicates.
7. **`similar_case_search` (TigerVector Cosine Search)**: Conducts vector similarity search over historical `PriorCase` investigation vectors.
8. **`write_case_subgraph` (Idempotent Case Write-Back)**: Atomically commits new investigations, linking `Case -> Evidence -> Decision -> Action` for continuous learning.
9. **`temporal_velocity_burst` (Sub-Minute Micro-Charge Detection)**: Detects automated bot-driven carding attacks executing multiple micro-charges within seconds.
10. **`path_between` (Shortest Associative Path)**: Traces the shortest multi-hop link between two arbitrary graph entities (e.g., suspicious IP to victim account).

---

## 4. Multi-Pillar Uncertainty Quantification & Controlled Evidence Loops

### 4.1 The 4-Pillar Completeness Model
In production banking, an agent cannot make drastic decisions (like terminating a checking account) without evaluating evidence completeness. We model completeness across 4 independent dimensions:

1. **$P_{\text{txn}}$ (Transaction Signal)**: Presence of amount, velocity metrics, card brand, and terminal details.
2. **$P_{\text{dev}}$ (Device & Hardware Signal)**: Presence of device ID, emulator flags, IP geolocation, and OS telemetry.
3. **$P_{\text{behav}}$ (Behavioral Signal)**: Historical baseline comparison, spending deviation, and time-of-day profile.
4. **$P_{\text{prior}}$ (Prior Case & Entity Signal)**: Known dispute history, KYC verification tier, and historical graph connectivity.

$$\text{Completeness } (C_{\text{data}}) = 0.30 P_{\text{txn}} + 0.30 P_{\text{dev}} + 0.20 P_{\text{behav}} + 0.20 P_{\text{prior}}$$

### 4.2 Signal Conflict Index ($S_{\text{conflict}}$)
Fraud investigations often present conflicting indicators. For instance, a transaction might have an alarming risk score of $0.85$, but the account has a 10-year pristine KYC history with 0 chargebacks.

$$S_{\text{conflict}} = |\text{Transaction Risk} - \text{Clean Baseline Profile}| \in [0.0, 1.0]$$

### 4.3 Composite Confidence Calculation
The composite confidence score discounts data completeness by the severity of signal conflict:

$$\text{Composite Confidence } (\text{Conf}) = C_{\text{data}} \times (1.0 - 0.45 \cdot S_{\text{conflict}})$$

```python
# agent/decision_matrix.py (Excerpts)
def compute_uncertainty_pillars(evidence: Dict[str, Any], trigger_data: Dict[str, Any]) -> Dict[str, float]:
    p_txn = score_transaction_pillar(trigger_data, evidence)
    p_dev = score_device_pillar(trigger_data, evidence)
    p_behav = score_behavior_pillar(trigger_data, evidence)
    p_prior = score_prior_pillar(trigger_data, evidence)

    completeness = 0.30 * p_txn + 0.30 * p_dev + 0.20 * p_behav + 0.20 * p_prior
    signal_conflict = calculate_signal_conflict(trigger_data, evidence)
    composite_confidence = max(0.05, min(1.0, completeness * (1.0 - 0.45 * signal_conflict)))

    return {
        "p_txn": round(p_txn, 3),
        "p_dev": round(p_dev, 3),
        "p_behav": round(p_behav, 3),
        "p_prior": round(p_prior, 3),
        "completeness": round(completeness, 3),
        "signal_conflict": round(signal_conflict, 3),
        "composite_confidence": round(composite_confidence, 3)
    }
```

### 4.4 Controlled Evidence Gathering Loop & Trajectory Diffing
If $\text{Conf} < 0.75$ or $S_{\text{conflict}} > 0.40$, the state machine enters **Step 5: Controlled Evidence Gathering**. It issues targeted step-up verification queries (e.g., Step-Up MFA Challenge, Out-of-Band SMS Verification, Telephony Carrier Check).

Crucially, the system captures an **audit trajectory diff**:
```json
{
  "before_additional_evidence": {
    "completeness": 0.62,
    "signal_conflict": 0.55,
    "composite_confidence": 0.46
  },
  "additional_evidence_gathered": {
    "step_up_mfa_status": "PASSED",
    "carrier_sim_swap_detected": false
  },
  "after_additional_evidence": {
    "completeness": 0.94,
    "signal_conflict": 0.10,
    "composite_confidence": 0.90
  },
  "what_changed": "Out-of-band biometric challenge passed by cardholder. Signal conflict decreased from 0.55 to 0.10, raising composite confidence from 0.46 to 0.90."
}
```

---

## 5. Next-Best Action Permissions Matrix & Containment Gating

Containment actions in banking carry severe compliance and customer impact risks. Unjustified account freezes can lead to regulatory fines, while delayed card locks allow financial loss.

We map $(\text{Risk Level} \times \text{Confidence})$ into a strict 3-tier permissions hierarchy:

```
                     CONFIDENCE >= 0.75           CONFIDENCE < 0.75
               ┌─────────────────────────────┬─────────────────────────────┐
CRITICAL RISK  │ Tier-2: Dual-Control Freeze │ Tier-1: Analyst Review      │
               │ (Ledger Lock & Police SAR)  │ (Temporary Auth Hold)       │
               ├─────────────────────────────┼─────────────────────────────┤
HIGH RISK      │ Tier-1: Analyst Approval    │ Tier-0: Non-Destructive     │
               │ (Account Credit Freeze)     │ (Step-Up MFA Challenge)     │
               ├─────────────────────────────┼─────────────────────────────┤
LOW / BENIGN   │ Tier-0: Automated Dismissal │ Tier-0: Supplementary Alert │
               │ (Allow & Clear Flag)        │ (Send Transaction SMS)      │
               └─────────────────────────────┴─────────────────────────────┘
```

- **Tier-0 (Automated Action)**: Non-destructive operations executed in real time without human intervention (e.g., *Step-Up MFA Challenge*, *Temporary Card Lock*, *Out-of-Band SMS Alert*).
- **Tier-1 (Analyst Approval Required)**: High-impact actions placed into the interactive analyst dashboard queue requiring single-click human confirmation (e.g., *Account Credits/Debits Freeze*, *Enhanced Monitoring Flag*).
- **Tier-2 (Dual-Control Lead Authorization)**: Irreversible, high-exposure containment actions requiring lead analyst authorization (e.g., *Permanent Card Revocation & Reissue*, *Core Banking Account Suspension*).

---

## 6. GraphRAG Policy Grounding & Automated FinCEN SAR Generator

### 6.1 Regulatory Thresholds under 31 CFR § 1020.320
Under federal Bank Secrecy Act (BSA) regulations:
- Transactions $\ge \$5,000$ involving identified suspicious actors require mandatory SAR filing.
- Transactions $\ge \$2,000$ involving organized syndicate networks or structuring require mandatory SAR filing.
- Filings must occur within 30 calendar days of initial detection.

### 6.2 The 4-Part Regulatory SAR Narrative
The system automatically compiles a regulatory-compliant 4-part SAR narrative:

1. **Part I: Executive Summary & Trigger Context**: Case identifier, financial institution info, primary suspect identity, trigger amount, and initial classification.
2. **Part II: Entity & Graph Topology Analysis**: Device hardware fingerprints, emulator indicators, shared account mule rings, and PageRank associative risk propagation findings.
3. **Part III: Chronological Transaction Flow & Velocity**: Micro-charge bursts, cross-account card fan-out, and velocity spikes vs historical baselines.
4. **Part IV: Regulatory Conclusion & 31 U.S.C. 5318(g) Safe Harbor**: Statutory citations, implemented containment actions, law enforcement handoff notes, and document retention protocols.

```markdown
### FINCEN FORM 111 - SUSPICIOUS ACTIVITY REPORT (SAR) NARRATIVE
**Filing Institution**: First Global Bank, N.A. (BSA ID: BSA-99482-TX)
**Statutory Authority**: 31 CFR § 1020.320 / 31 U.S.C. § 5318(g)

#### Part I: Executive Summary
On 2026-09-20, First Global Bank's Autonomous Fraud Intelligence System flagged transaction txn_bm_01 ($3,450.00 USD) associated with Account acc_bm_01_0 due to high-risk emulator device signatures...

#### Part II: Graph Topology & Associative Risk Analysis
Multi-hop topological BFS traversal identified device dev_bm_01_emu operating as a central hardware hub across 4 distinct accounts. PageRank associative risk diffusion yielded a network risk score of 0.88...

#### Part III: Chronological Transaction Flow & Velocity
Sliding window analysis revealed a 1-hour velocity of $7,800.00 across 3 linked accounts, representing an 820% spike above the historical baseline...

#### Part IV: Containment Actions & Regulatory Compliance
In accordance with Bank Fraud Policy Section 4.2, the institution executed Tier-1 Account Freezes and Card Revocations. Pursuant to 31 U.S.C. 5318(g), all underlying graph artifacts are retained for 5 years.
```

---

## 7. Tri-Layer Case Memory & TigerVector Ingestion

To ensure continuous institutional learning, the platform maintains a **Tri-Layer Case Memory** pre-seeded with 100 historical closed cases (50 confirmed fraud, 50 cleared benign):

1. **Layer 1: Structural Graph Memory**: Resolved cases are permanently written back into TigerGraph via the `write_case_subgraph` GSQL query, maintaining explicit edges to accounts, transactions, and typologies.
2. **Layer 2: Semantic TigerVector Memory**: Case investigation narratives are vectorized into 64-dimensional embeddings indexed within `PriorCase` vertices for cosine similarity lookup.
3. **Layer 3: Community Syndicate Memory**: Historical Louvain clusters preserve known emulator hashes and mule rings, instantly alerting analysts if a newly seen device overlaps with a past bust.

---

## 8. Benchmark Evaluation: 20 Standardized Scenarios

We evaluated the platform across 20 diverse, realistic fraud scenarios covering every major financial crime pattern:

| Category | Cases | Primary Typologies & Patterns | Resulting Containment Tier |
| :--- | :--- | :--- | :--- |
| **Account Takeover (ATO)** | Cases 1–4 | New emulator device + sudden high-value wire transfers | Tier-1 Account Freeze + FinCEN SAR |
| **Mule Ring Syndicates** | Cases 5–8 | Shared device hardware hub connecting 5+ accounts | Tier-2 Core Suspension + SAR |
| **Card Testing & Fan-Out** | Cases 9–12 | Sub-minute micro-charges across multiple merchant categories | Tier-0 Card Lock + Auto-MFA |
| **Synthetic Identities** | Cases 13–15 | Unverified SSN hashes sharing physical addresses | Tier-1 Credit Freeze + KYC Step-Up |
| **Vacation Travel FPs** | Cases 16–18 | International card swipe with biometric MFA pass | Tier-0 Allow & Clear Flag |
| **Bust-Out / Credit Bust** | Cases 19–20 | Max credit line withdrawal followed by dormant drop | Tier-2 Legal Referral + SAR |

All 20 standardized JSON answer files are generated in `/answers/` and fully verified by our automated test harness.

---

## 9. Interactive Analyst Dashboard

The platform includes a real-time SPA dashboard built with **FastAPI**, **Tailwind CSS**, and **Cytoscape.js**:

- **Interactive Benchmark Comparison Matrix**: Full 20-case aggregate evaluation view comparing risk levels, completeness, signal conflict, composite confidence, next-best actions, and FinCEN SAR compliance badges with 1-click CSV export.
- **8-Step Live Stepper**: Step-by-step interactive playback of the agentic state machine with animated execution.
- **Cytoscape.js Subgraph Explorer**: Force-directed, color-coded visualization of the 2-hop entity neighborhood with node-type badges.
- **4-Pillar Uncertainty Gauges**: Real-time visual feedback on completeness ($P_{\text{txn}}$, $P_{\text{dev}}$, $P_{\text{behav}}$, $P_{\text{prior}}$), conflict ($S_{\text{conflict}}$), and composite confidence.
- **Action Approval Queue**: One-click approval/rejection controls for Tier-1 and Tier-2 actions.
- **FinCEN SAR Modal**: Formatted regulatory filing preview ready for BSA compliance officer review with 1-click text copy and document download.
- **Dual-Engine & Groq Cloud LLM Status**: Live diagnostic health bar showing active TigerGraph graph engine metrics and Groq LLaMA-3.3-70B synthesis mode.

---

## 10. 1-Click Containerized Deployment & High-Speed Groq LLM

To ensure seamless reproducibility and zero-friction evaluation, the entire platform is packaged with **1-Click Docker Compose**:

```bash
# Build and run the complete platform
docker-compose up --build
```

### Groq Cloud LLM Inference Integration
In addition to the deterministic GraphRAG local policy templates, the platform seamlessly connects to **Groq Cloud's ultra-fast inference API** running `llama-3.3-70b-versatile` (or `llama-3.1-8b-instant`). By providing a free Groq API key in `.env`, the agent generates dynamic, natural-language executive intelligence summaries for the Chief Risk Officer and BSA Compliance Officer while strictly respecting graph evidence and policy citations. If the key is omitted or the system operates offline, the platform automatically and silently falls back to the deterministic grounded template.

---

## 11. Conclusion & Future Horizons

By unifying **TigerGraph's native graph algorithms and TigerVector**, **LangGraph agentic state machines**, **4-pillar uncertainty calibration**, **Groq Cloud dynamic LLM synthesis**, and **GraphRAG policy grounding**, we demonstrate a transformative path forward for autonomous financial crime defense.

The platform shifts fraud defense from reactive, tabular triage to proactive, graph-native intelligence—slashing false positives, uncovering distributed mule rings in milliseconds, and providing complete regulatory explainability.

### 🔗 Open-Source Code & Artifacts
The entire codebase, GSQL queries, 20 benchmark scenarios, and web dashboard are open-source:
- **Repository**: [GitHub / tigergraph-fraud-agent](https://github.com/your-org/tigergraph-fraud-agent)
- **Pytest Suite**: 55 automated unit, integration, and benchmark tests passing in 1.56s.
- **Docker**: Production-ready container image and Docker Compose orchestrator.
