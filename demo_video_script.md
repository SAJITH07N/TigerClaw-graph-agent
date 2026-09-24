# 🎬 3–5 Minute Demo Video Script & Storyboard
> **Project**: TigerGraph Agentic Fraud Investigation & Next-Best Action Platform  
> **Target Duration**: 4 Minutes 15 Seconds (255 Seconds)  
> **Target Audience**: TigerGraph Hackathon Judges, Financial Crime Analysts, AI Engineers

---

## ⏱️ Scene Breakdown & Voiceover

### 🕒 Scene 1: Introduction & The Core Problem (0:00 – 0:40)
- **Visual**: Title screen showing Neo-Bauhaus logo, architecture diagram with LangGraph state machine + TigerGraph Knowledge Engine.
- **Voiceover (Speaker)**:
  > *"Welcome to our demonstration of the TigerGraph Agentic Fraud Investigation & Next-Best Action Platform for the HHGOA Hackathon. Fraud teams at modern financial institutions are overwhelmed by fragmented data silos, slow manual investigations, and high false positives. Money moves in seconds, but legacy fraud reviews take days. Today, we show how combining TigerGraph's graph-native knowledge engine, LangGraph multi-agent orchestration, multi-pillar uncertainty quantification, and GraphRAG transforms financial crime containment into an autonomous, defensible, and audit-ready process."*

---

### 🕒 Scene 2: Platform Architecture & Live Graph Canvas (0:40 – 1:30)
- **Visual**: Screen recording of the live Neo-Bauhaus Dark UI at `http://127.0.0.1:8000`. Show the left sidebar case selector, top telemetry status bar, Cytoscape graph canvas, 8-step stepper, and 4-pillar uncertainty meters.
- **Voiceover (Speaker)**:
  > *"Our system is powered by a 14-vertex, 10-edge TigerGraph schema and 10 pre-installed GSQL queries. In our analyst UI, entity types are encoded with crisp geometric semantics: Red diamonds for high-risk transactions, Blue squares for accounts, Purple ellipses for cards, Yellow hexagons for devices, and Green triangles for physical addresses. Clicking any entity highlights its multi-hop neighborhood and displays real-time telemetry."*
- **Action on Screen**:
  - Click on an Account node. Show the neighborhood highlighting and the floating yellow inspector badge displaying emulator detection and risk metrics.

---

### 🕒 Scene 3: Investigating Benchmark Case 01 - Moving from Uncertainty to Defensible Action (1:30 – 2:35)
- **Visual**: Select **CASE-BM-01 (Account Takeover via Android Emulator)**. Click **"Run Full Investigation (8 Steps)"**. Watch the 8-step stepper animate with active blue pulsing and green checkmarks.
- **Voiceover (Speaker)**:
  > *"Let's investigate Benchmark Case 01. The agent is triggered by a machine learning risk alert for a $3,450 transfer. 
  > In Step 1 and 2, it normalizes the trigger and executes a 2-hop BFS neighborhood traversal in TigerGraph.
  > In Step 3, it runs GSQL queries including `shared_device_ring` and `velocity_check`, identifying an Android emulator footprint.
  > In Step 4, our 4-pillar uncertainty model evaluates Transaction Velocity, Device Fingerprint, Account Baseline, and Prior Case Memory similarity. Initially, because the transaction amount diverges from the customer's historical baseline, Signal Conflict is elevated at 0.88, and Composite Confidence is only 0.44.
  > In Step 5, recognizing this uncertainty, the agent triggers a controlled, policy-approved inquiry—performing an out-of-band carrier reputation check. The response confirms the risk fingerprint. Watch how the evidence trajectory updates: Data Completeness surges to 98%, Signal Conflict drops to 0.22, and Confidence climbs to 88%!"*

---

### 🕒 Scene 4: Policy-Grounded Next-Best Actions & Tiered Governance (2:35 – 3:20)
- **Visual**: Scroll to the **Next-Best Action Approval Queue** and the **Regulatory Compliance (FinCEN SAR)** panel.
- **Voiceover (Speaker)**:
  > *"In Step 6, the agent maps the risk and confidence to our 3-tier governance matrix:
  > Tier-0 Automated actions—like a temporary card lock—are executed immediately to halt fund drain.
  > Tier-1 actions—like freezing account credits and debits—are routed to the Fraud Analyst with automated policy citation `POL-FRM-2026 Clause 1.2`.
  > High-exposure actions over $2,500 require Tier-2 Dual-Control Lead approval. 
  > Notice the 'Before vs. After' trajectory: before additional evidence, the account freeze was held in pending status; once confidence crossed the threshold, the action became defensible for immediate execution."*
- **Action on Screen**:
  - Click the **"Approve & Execute"** button on the pending Tier-2 card revocation action. Show the status turn to green `EXECUTED` with a toast notification.

---

### 🕒 Scene 5: FinCEN SAR Generation & 20-Case Benchmark Matrix (3:20 – 4:00)
- **Visual**: Switch to **CASE-BM-02 (Mule Ring Syndicate)**. Click **"View FinCEN SAR Filing"** modal. Show the structured XML/JSON Suspicious Activity Report (Form 111 / 31 CFR § 1020.320). Then click **"View 20-Case Benchmark Evaluation Matrix"**.
- **Voiceover (Speaker)**:
  > *"For cases meeting federal thresholds, our GraphRAG engine automatically drafts a compliant FinCEN Suspicious Activity Report with suspect identification, transaction narratives, and graph topology citations.
  > Finally, here is our 20-Case Benchmark Evaluation Matrix. Our agent was tested across 20 diverse scenarios—including Account Takeovers, Coordinated Mule Rings, Automated Card Testing, Synthetic Identity Bust-Outs, and Legitimate European Travel. The agent achieved 100% classification precision and correctly differentiated benign behavior without unnecessary account locks."*

---

### 🕒 Scene 6: Conclusion & Open Source Repository (4:00 – 4:15)
- **Visual**: Show GitHub repository page, terminal running 55 passing pytest tests, and closing summary card.
- **Voiceover (Speaker)**:
  > *"The entire platform is open-source, containerized with 1-click Docker Compose, and ships with 55 unit and integration tests. Thank you to the TigerGraph team for organizing this hackathon!"*

---
