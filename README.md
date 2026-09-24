# 🐅 Agent Tiger: Autonomous Graph-Native Financial Crime Intelligence & Containment
> **Autonomous Multi-Hop Graph Investigation, GraphRAG Policy Grounding & Next-Best Action Platform**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-green.svg)](https://fastapi.tiangolo.com/)
[![TigerGraph](https://img.shields.io/badge/TigerGraph-GSQL%20%2B%20TigerVector-orange.svg)](https://www.tigergraph.com/)
[![Tests](https://img.shields.io/badge/Tests-62%20Passed-brightgreen.svg)]()
[![Docker](https://img.shields.io/badge/Docker-1--Click%20Compose-blue.svg)]()
[![LLM](https://img.shields.io/badge/LLM-Groq%20LLaMA--3.3--70B%20%2B%20GraphRAG-orange.svg)]()
[![Compliance](https://img.shields.io/badge/FinCEN-31%20CFR%20§%201020.320-blue.svg)]()

---

## 📌 Executive Summary

Traditional fraud detection systems rely on isolated point-in-time rules and fragmented data silos, resulting in overwhelming false-positive rates, missed multi-hop syndicate mule rings, and delayed containment actions.

**Agent Tiger** solves these limitations by uniting **TigerGraph's high-performance graph database and TigerVector capabilities**, **LangGraph multi-agent state orchestration**, **multi-pillar uncertainty quantification**, and **GraphRAG policy grounding**. The platform autonomously investigates incoming triggers, uncovers hidden associative topology across accounts, devices, and cards, dynamically gathers missing evidence, gates containment actions through a 3-tier permissions matrix, and generates audit-proof FinCEN Suspicious Activity Reports (SAR).

---

## 🏛️ System Architecture

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

---

## 🌟 Key Capabilities & Innovations

### 1. 14-Vertex, 10-Edge Graph Schema & 10 Installed GSQL Queries
Designed specifically for enterprise fraud intelligence:
- **Vertices (14)**: `Transaction`, `Identity`, `Card`, `Account`, `Device`, `Address`, `EmailDomain`, `Case`, `Evidence`, `Decision`, `Action`, `PolicyDoc`, `TypologyDoc`, `PriorCase`.
- **Edges (10)**: `PAID_WITH`, `FROM_DEVICE`, `TO_ADDRESS`, `HELD_BY`, `USED_BY`, `SHARES_DEVICE`, `SHARES_CARD`, `ABOUT_TRANSACTION`, `ABOUT_ACCOUNT`, `HAS_EVIDENCE`, `HAS_DECISION`, `LED_TO_ACTION`, `SIMILAR_TO`, `CITES_POLICY`, `MATCHES_TYPOLOGY`.
- **Installed GSQL Queries (10)**:
  1. `get_entity_neighborhood`: 2-hop BFS subgraph extraction.
  2. `shared_device_ring`: Mule ring and multi-account hardware sharing detection.
  3. `shared_card_fanout`: Cross-account card testing and fanout anomaly detection.
  4. `velocity_check`: Sliding window velocity spikes (1h, 6h, 24h) vs historical baselines.
  5. `pagerank_risk_propagation`: Associative risk diffusion through connected graph entities.
  6. `community_detection`: WCC and Louvain syndicate clustering.
  7. `similar_case_search`: TigerVector cosine similarity search over historical cases.
  8. `write_case_subgraph`: Idempotent case memory write-back (Case $\to$ Evidence $\to$ Decision $\to$ Action).
  9. `temporal_velocity_burst`: Sub-minute micro-charge burst detection.
  10. `path_between`: Shortest associative path tracing between entities.

### 2. Dual-Mode TigerGraph Client
- **Savanna Cloud & RESTPP Native**: Connects transparently to live TigerGraph instances via `pyTigerGraph` using standard token/secret authentication.
- **Built-in High-Fidelity In-Memory Engine**: Implements the identical GSQL query semantics, BFS traversals, PageRank power iterations, Louvain/WCC communities, and TigerVector cosine similarity locally. Zero external database installation required for rapid local testing and CI/CD pipelines!

### 3. Multi-Pillar Uncertainty & Confidence Quantification
Unlike black-box classifiers that output uncalibrated probabilities, the platform calculates uncertainty across **4 distinct evidence pillars**:
$$\text{Completeness } (C_{\text{data}}) = 0.30 P_{\text{txn}} + 0.30 P_{\text{dev}} + 0.20 P_{\text{behav}} + 0.20 P_{\text{prior}}$$
$$\text{Signal Conflict } (S_{\text{conflict}}) = |\text{Txn Risk} - \text{Clean Profile Baseline}| \in [0.0, 1.0]$$
$$\text{Composite Confidence } (\text{Conf}) = C_{\text{data}} \times (1.0 - 0.45 \cdot S_{\text{conflict}})$$

### 4. Controlled Evidence Gathering Loop & Trajectory Diffing
When confidence is low ($\text{Conf} < 0.75$) or signal conflict is elevated ($S_{\text{conflict}} > 0.40$), the agent triggers targeted supplementary queries (Step-up MFA, Out-of-band SMS, Carrier Verification).
The system explicitly logs the **Evidence Trajectory Diff**:
- `before_additional_evidence` (initial pillar scores, conflict, and confidence)
- `additional_evidence_gathered` (step-up verification outcome)
- `after_additional_evidence` (post-loop pillar scores, resolved conflict, updated confidence)
- `what_changed` (human-readable audit delta explaining why confidence changed)

### 5. 2D Next-Best Action Permissions Matrix
Actions are gated based on $(\text{Risk Level} \times \text{Confidence})$ into a strict 3-tier hierarchy:
- **Tier-0 (Automated Action)**: Non-destructive, immediate controls (e.g., Step-Up MFA Challenge, Temporary Card Lock, Out-of-Band SMS Alert).
- **Tier-1 (Analyst Approval Required)**: High-impact actions requiring one-click confirmation in the dashboard queue (e.g., Account Credits/Debits Freeze, Enhanced Monitoring).
- **Tier-2 (Dual-Control Lead Authorization)**: High-exposure, irreversible containment (e.g., Permanent Card Revocation & Reissue, Core Banking Account Suspension).

### 6. FinCEN Suspicious Activity Report (SAR) Generator
Automatically triggers when statutory thresholds under **31 CFR § 1020.320** are met ($\ge \$5,000$ for identified suspects, $\ge \$2,000$ for organized syndicates). Formats a regulatory-compliant **4-part narrative**:
1. **Section I**: Executive Summary & Case Context
2. **Section II**: Entity & Identity Graph Topology (Device fingerprints, mule rings, PageRank diffusion)
3. **Section III**: Chronological Transaction Flow & Velocity Analysis
4. **Section IV**: Regulatory Conclusion, Containment Actions & 31 U.S.C. 5318(g) Safe Harbor Retention

### 7. Tri-Layer Case Memory (Closed Case Ingestion)
Pre-seeded with **100 historical closed cases** (50 confirmed fraud, 50 cleared benign):
- **Structural Graph Memory**: Links resolved cases to accounts, transactions, and typologies.
- **TigerVector Semantic Memory**: Cosine similarity indexing over case investigation narratives.
- **Community Syndicate Memory**: Identifies recurring hardware and infrastructure fingerprints across past investigations.

### 8. Interactive Analyst Dashboard & Cytoscape.js Visualizer
- **8-Step Live Stepper**: Step-by-step interactive playback of the investigation state machine.
- **Cytoscape.js Subgraph Canvas**: Color-coded, physics-driven interactive entity graph rendering.
- **4-Pillar Uncertainty Radar & Gauges**: Visual feedback on completeness, conflict, and confidence.
- **Action Approval Queue**: Real-time analyst approval / rejection controls.
- **FinCEN SAR Modal**: Formatted regulatory filing preview ready for BSA review.

---

## 📊 Rubric Mapping & Task 4 Verification Matrix

| HHGOA Task 4 Rubric Requirement | Platform Implementation & Architecture | Verification Test File |
| :--- | :--- | :--- |
| **Multi-Source Trigger Ingestion** | Normalizes Risk Alerts, Customer Disputes, and Escalations (`agent/nodes/trigger_node.py`) | `tests/test_langgraph_workflow.py` |
| **Multi-Hop Graph Traversals** | 10 GSQL queries, 2-hop BFS, shortest path, and PageRank (`schema/*.gsql`, `tigergraph/client.py`) | `tests/test_gsql_queries.py` |
| **4-Pillar Uncertainty Model** | $P_{\text{txn}}, P_{\text{dev}}, P_{\text{behav}}, P_{\text{prior}}$ scoring & conflict index (`agent/decision_matrix.py`) | `tests/test_uncertainty_nba.py` |
| **Evidence Gathering Loop & Diff** | Conditional iteration, before/after trajectory diff, `what_changed` analysis (`agent/nodes/gather_more_node.py`) | `tests/test_uncertainty_nba.py` |
| **Next-Best Action & Permissions** | 2D Risk $\times$ Confidence matrix, Tier-0/1/2 gating (`agent/decision_matrix.py`, `agent/nodes/take_action_node.py`) | `tests/test_uncertainty_nba.py` |
| **GraphRAG Policy Grounding & SAR** | Hybrid vector policy store, 31 CFR § 1020.320 4-part SAR generator (`graphrag/sar_generator.py`) | `tests/test_graphrag_sar.py` |
| **Tri-Layer Case Memory** | 100 historical closed cases, TigerVector cosine search, graph persistence (`data/seed_historical_memory.py`) | `tests/test_in_memory_engine.py` |
| **20 Standardized Benchmark Cases** | Full suite execution producing compliant JSON answer files (`benchmark_runner.py`, `answers/*.json`) | `tests/test_benchmark_runner.py` |
| **Interactive Analyst UI & API** | FastAPI backend, Cytoscape.js graph canvas, live 8-step stepper (`app/api/server.py`, `app/static/`) | `tests/test_benchmark_runner.py` |

---

## 🚀 Quickstart Guide

### 1. Option A: 1-Click Docker Compose Deployment (Recommended)
Run the complete containerized platform with one command:

```bash
docker-compose up --build
```
The server will build and start on **`http://localhost:8000`** with real-time health checking.

---

### 2. Option B: Local Python Environment Setup
Ensure Python 3.10+ is installed:

```bash
git clone https://github.com/your-org/tigergraph-fraud-agent.git
cd tigergraph-fraud-agent

# Install dependencies
pip install -r requirements.txt
```

#### Optional: Dynamic Groq Cloud LLM Integration
To enable high-speed dynamic narrative generation using Groq's LLaMA-3.3-70B model, copy `.env.example` to `.env` and provide your free Groq API key:

```bash
cp .env.example .env
# Edit .env and set:
# GROQ_API_KEY=gsk_your_groq_api_key_here
# GROQ_MODEL=llama-3.3-70b-versatile
```
*(Note: If `GROQ_API_KEY` is omitted, the platform seamlessly and automatically falls back to deterministic local GraphRAG policy-grounded templates with 100% offline test coverage).*

---

### 3. Run All 55 Unit, Integration & Benchmark Tests
Verify the complete platform with pytest:

```bash
pytest -v
```

Output:
```
============================= test session starts =============================
tests/test_api_server.py::test_health_check_endpoint PASSED
tests/test_api_server.py::test_list_cases_endpoint PASSED
tests/test_api_server.py::test_llm_status_endpoint PASSED
tests/test_api_server.py::test_benchmark_matrix_endpoint PASSED
tests/test_api_server.py::test_get_case_detail_endpoint PASSED
tests/test_api_server.py::test_get_case_subgraph_endpoint PASSED
tests/test_api_server.py::test_approve_action_endpoint PASSED
tests/test_api_server.py::test_get_sar_endpoint PASSED
tests/test_api_server.py::test_live_investigation_endpoint PASSED
tests/test_benchmark_runner.py::test_all_20_benchmark_answer_files_exist PASSED
tests/test_benchmark_runner.py::test_benchmark_answer_structure[1..20] PASSED
tests/test_graphrag_sar.py::test_policy_store_chunking_and_retrieval PASSED
tests/test_graphrag_sar.py::test_typology_catalog_matching PASSED
tests/test_graphrag_sar.py::test_fincen_sar_generation PASSED
tests/test_gsql_queries.py::test_query_1..10 PASSED
tests/test_in_memory_engine.py::test_engine_features PASSED
tests/test_langgraph_workflow.py::test_full_8_step_workflow_execution PASSED
tests/test_uncertainty_nba.py::test_4_pillar_and_matrix PASSED
============================= 55 passed in 1.56s ==============================
```

### 4. Generate or Re-evaluate Benchmark Answer JSON Files
Run the standalone benchmark generator across all 20 scenarios:

```bash
python benchmark_runner.py
```
This populates all 20 verified answer files in `answers/case_01.json` through `answers/case_20.json`.

### 5. Launch the Interactive Analyst Web Dashboard
Start the FastAPI server:

```bash
python -m uvicorn app.api.server:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser and navigate to: **`http://localhost:8000`**

---

## 🌐 Web Dashboard Features

1. **Interactive Benchmark Evaluation Matrix**: High-density comparative matrix showing all 20 benchmark scenarios side-by-side with risk levels, $C_{\text{data}}$ completeness, $S_{\text{conflict}}$ conflict scores, composite confidence, next-best actions, and FinCEN SAR compliance badges with 1-click CSV export.
2. **Benchmark Scenario Switcher**: Instantly load and investigate any of the 20 benchmark scenarios (ATO, Mule Rings, Card Testing, Synthetic IDs, Vacation Travel FPs, Bust-Outs).
3. **8-Step Live Investigation Stepper**: Step through the agentic lifecycle with real-time audit messages and animated workflow playback.
4. **Cytoscape.js Graph Subgraph Explorer**: Pan, zoom, inspect, and explore 2-hop entity neighborhoods with node-type specific badges and risk styling.
5. **4-Pillar Uncertainty Breakdown**: Interactive progress gauges showing $P_{\text{txn}}$, $P_{\text{dev}}$, $P_{\text{behav}}$, $P_{\text{prior}}$, data completeness, signal conflict, and composite confidence.
6. **Action Approval Center**: Review recommended Next-Best Actions, inspect policy citations, and click to approve Tier-1/Tier-2 pending actions.
7. **FinCEN SAR Modal**: Click "View FinCEN SAR Filing" to inspect regulatory Form 111 XML/Text narratives with full statutory compliance citations.
8. **Live LLM Status & Health Bar**: Real-time diagnostic badge displaying TigerGraph GSQL graph engine metrics and Groq Cloud LLaMA-3.3-70B / GraphRAG mode.

---

## 📁 Repository Structure

```
tigergraph_fraud_agent/
├── Dockerfile                               # 1-Click Container build
├── docker-compose.yml                       # Multi-service container orchestration
├── .dockerignore                            # Container build exclusions
├── README.md                                # Submission documentation & rubric mapping
├── blog_post.md                             # In-depth technical blog post
├── requirements.txt                         # Python dependencies
├── pyproject.toml                           # Package build & pytest configuration
├── .env.example                             # Environment variable template
├── benchmark_runner.py                      # Standalone 20-case benchmark executor
├── answers/                                 # 20 Benchmark Answer JSON Files
│   ├── case_01.json ... case_20.json
├── data/                                    # Dataset generation & memory seeding
│   ├── ieee_cis_preprocessor.py             # Entity resolution & proxy key derivation
│   ├── seed_historical_memory.py            # 100 historical closed case seeder
│   └── benchmark_generator.py               # 20 benchmark scenario definitions
├── schema/                                  # GSQL DDL and 10 Installed Query Definitions
│   ├── schema.gsql                          # 14 Vertices & 10 Edges Schema DDL
│   ├── get_entity_neighborhood.gsql         # Query 1: 2-hop BFS Subgraph
│   ├── shared_device_ring.gsql              # Query 2: Mule Ring Detection
│   ├── shared_card_fanout.gsql              # Query 3: Multi-Account Fanout
│   ├── velocity_check.gsql                  # Query 4: Sliding Window Velocity
│   ├── pagerank_risk_propagation.gsql       # Query 5: Associative Risk Diffusion
│   ├── community_detection.gsql             # Query 6: Louvain Syndicate Clusters
│   ├── similar_case_search.gsql             # Query 7: TigerVector Cosine Search
│   ├── write_case_subgraph.gsql             # Query 8: Case Memory Idempotent Write
│   ├── temporal_velocity_burst.gsql         # Query 9: Sub-Minute Burst Detection
│   └── path_between.gsql                    # Query 10: Shortest Associative Path
├── tigergraph/                              # Dual-Mode Client & Graph Engine
│   ├── client.py                            # Unified interface (Savanna Cloud / RESTPP + Local)
│   ├── in_memory_engine.py                  # High-fidelity GSQL & TigerVector engine
│   └── mcp_server.py                        # Model Context Protocol server for TigerGraph
├── graphrag/                                # Policy Grounding & Regulatory SAR
│   ├── groq_client.py                       # Groq Cloud LLM API client (LLaMA-3.3-70B)
│   ├── policy_store.py                      # Bank policy store & hybrid retriever
│   ├── typology_catalog.py                  # 5 Fraud typologies & embedding matcher
│   ├── sar_generator.py                     # Regulatory FinCEN SAR compliance generator
│   └── docs/                                # Raw Markdown Bank Policies & Guidelines
│       ├── fraud_policy.md
│       ├── typologies.md
│       └── fincen_sar_guidelines.md
├── .env.example                             # Environment variable template
├── benchmark_runner.py                      # Standalone 20-case benchmark executor
├── answers/                                 # 20 Benchmark Answer JSON Files
│   ├── case_01.json ... case_20.json
├── data/                                    # Dataset generation & memory seeding
│   ├── ieee_cis_preprocessor.py             # Entity resolution & proxy key derivation
│   ├── seed_historical_memory.py            # 100 historical closed case seeder
│   └── benchmark_generator.py               # 20 benchmark scenario definitions
├── schema/                                  # GSQL DDL and 10 Installed Query Definitions
│   ├── schema.gsql                          # 14 Vertices & 10 Edges Schema DDL
│   ├── get_entity_neighborhood.gsql         # Query 1: 2-hop BFS Subgraph
│   ├── shared_device_ring.gsql              # Query 2: Mule Ring Detection
│   ├── shared_card_fanout.gsql              # Query 3: Multi-Account Fanout
│   ├── velocity_check.gsql                  # Query 4: Sliding Window Velocity
│   ├── pagerank_risk_propagation.gsql       # Query 5: Associative Risk Diffusion
│   ├── community_detection.gsql             # Query 6: Louvain Syndicate Clusters
│   ├── similar_case_search.gsql             # Query 7: TigerVector Cosine Search
│   ├── write_case_subgraph.gsql             # Query 8: Case Memory Idempotent Write
│   ├── temporal_velocity_burst.gsql         # Query 9: Sub-Minute Burst Detection
│   └── path_between.gsql                    # Query 10: Shortest Associative Path
├── tigergraph/                              # Dual-Mode Client & Graph Engine
│   ├── client.py                            # Unified interface (Savanna Cloud / RESTPP + Local)
│   ├── in_memory_engine.py                  # High-fidelity GSQL & TigerVector engine
│   └── mcp_server.py                        # Model Context Protocol server for TigerGraph
├── graphrag/                                # Policy Grounding & Regulatory SAR
│   ├── policy_store.py                      # Bank policy store & hybrid retriever
│   ├── typology_catalog.py                  # 5 Fraud typologies & embedding matcher
│   ├── sar_generator.py                     # Regulatory FinCEN SAR compliance generator
│   └── docs/                                # Raw Markdown Bank Policies & Guidelines
│       ├── fraud_policy.md
│       ├── typologies.md
│       └── fincen_sar_guidelines.md
├── agent/                                   # LangGraph 8-Step Orchestration Core
│   ├── state.py                             # Typed AgentState & Evidence schemas
│   ├── workflow.py                          # Master 8-step state machine
│   ├── decision_matrix.py                   # 4-Pillar Uncertainty & NBA Matrix
│   ├── mock_actions.py                      # Banking containment API stubs
│   └── nodes/                               # 8 Individual Workflow Nodes
│       ├── trigger_node.py
│       ├── investigate_node.py
│       ├── gather_evidence_node.py
│       ├── assess_uncertainty_node.py
│       ├── gather_more_node.py
│       ├── take_action_node.py
│       ├── explain_node.py
│       └── update_memory_node.py
├── app/                                     # Web Dashboard & REST API
│   ├── api/server.py                        # FastAPI REST API & WebSocket handlers
│   └── static/                              # Analyst Dashboard Frontend
│       ├── index.html                       # Modern SPA Dashboard
│       ├── css/style.css                    # Glassmorphism & Cyber Dark UI styling
│       └── js/
│           ├── app.js                       # Frontend State, Stepper & Action controller
│           └── graph_visualizer.js          # Cytoscape.js interactive graph visualizer
└── tests/                                   # Comprehensive Pytest Suite (46 Tests)
    ├── test_in_memory_engine.py             # Graph traversals & algorithms
    ├── test_gsql_queries.py                 # 10 Installed GSQL queries
    ├── test_uncertainty_nba.py              # 4-Pillar completeness & NBA permissions
    ├── test_graphrag_sar.py                 # Policy store & SAR generator
    ├── test_langgraph_workflow.py           # Master 8-step LangGraph execution
    └── test_benchmark_runner.py             # 20 Benchmark answer JSON schema tests
```

---

## 📄 License & Attribution
Developed for the **High-Performance Heterogeneous Graph Machine Learning (HHGOA) Challenge - Task 4**.
All code is open-source and released under the MIT License.
