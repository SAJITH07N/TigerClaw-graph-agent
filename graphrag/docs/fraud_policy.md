# Bank Fraud Risk Management & Next-Best Action Policy (POL-FRM-2026)

## 1. Governance & Authorization Thresholds
- **Clause 1.1 (Autonomous Action Threshold)**: The automated Agentic Fraud System is authorized to execute low-impact containment actions (Temporary Card Lock, Step-Up MFA Challenge, Out-of-Band SMS Verification) autonomously when Confidence $\ge 0.75$ and Risk Level is HIGH or CRITICAL.
- **Clause 1.2 (Dual-Control Tier 2 Approval)**: Complete Account Suspension, Merchant-Wide Card Revocation, and Transaction Chargeback Reversal exceeding $2,500.00 REQUIRE explicit Tier-2 Fraud Analyst approval.
- **Clause 1.3 (Customer Contact Protocol)**: In cases of suspected Account Takeover (ATO), outbound customer communication must be routed through verified out-of-band channels (SMS/Push to phone on record) before permanent account closure.

## 2. Evidence Gathering & Step-Up Authorization Rules
- **Clause 2.1 (Multi-Pillar Evidence Completeness)**: An investigation cannot be closed with definitive action (Clear or Block) if Data Completeness ($C_{\text{data}}$) is below $0.70$, unless an active high-velocity loss is in progress.
- **Clause 2.2 (Step-Up Authentication Trigger)**: If new device fingerprint is detected without historical account linkage ($P_{\text{dev}} = 0$) and transaction amount $> \$500.00$, initiate Step-Up Biometric / OTP Challenge immediately.
- **Clause 2.3 (Cardholder Verification Trigger)**: If Card Testing micro-charge bursts or anomalous card fan-out is detected, send immediate Push Notification / SMS to verify the physical presence of the card.

## 3. FinCEN Suspicious Activity Report (SAR) Filing Mandate
- **Clause 3.1 (Mandatory Filing Threshold)**: In accordance with 31 CFR § 1020.320, a SAR must be generated and queued for BSA/AML Officer review whenever:
  - Aggregate suspect transaction volume $\ge \$5,000.00$ with identified suspect / mule ring, OR
  - Aggregate suspect transaction volume $\ge \$25,000.00$ regardless of suspect identification, OR
  - Structuring / Card testing syndicates operating across multiple accounts are confirmed.
- **Clause 3.2 (SAR Narrative Structure)**: Every SAR narrative must document:
  1. *Who*: All primary identities, accounts, card numbers, and device fingerprints.
  2. *What*: Typology hypothesis and graph pattern summary (e.g. 5 accounts sharing emulator device).
  3. *When & Where*: Timestamps, IP locations, merchant categories.
  4. *Why & How*: Detailed graph traversal findings, PageRank risk score propagation, and uncertainty metrics.
