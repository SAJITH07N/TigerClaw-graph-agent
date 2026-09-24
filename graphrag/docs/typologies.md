# Documented Fraud Typologies Catalog (TYP-2026)

## Typology 1: Account Takeover (ATO)
- **ID**: `TYP-ATO-001`
- **Definition**: Unauthorized takeover of an established customer account following credential stuffing or SIM swapping.
- **Key Indicators**:
  - Sudden new device ID / emulator login with no prior history.
  - High velocity of high-value transactions within 1 hour of device change.
  - Password or address change within 24 hours prior to transaction.
  - Distinct IP address geographically distant from customer's home ZIP code.

## Typology 2: Mule Ring / Shared Device Syndicate
- **ID**: `TYP-MULE-002`
- **Definition**: Coordinated syndicate using shared hardware or device emulators to route stolen funds across multiple proxy accounts.
- **Key Indicators**:
  - Single device ID linked to 2 or more distinct customer accounts (`shared_device_ring >= 2`).
  - Rapid circular or fan-in fund transfers between connected accounts.
  - High Louvain / WCC community density score.
  - Associative PageRank risk diffusion score $> 0.65$.

## Typology 3: Card Testing Burst / Micro-Charge Syndicate
- **ID**: `TYP-TEST-003`
- **Definition**: Automated testing of stolen card batches using rapid micro-transactions ($< \$15.00$) at online merchants prior to large cash-outs.
- **Key Indicators**:
  - $\ge 3$ transactions on the same card within 120 seconds (`temporal_velocity_burst`).
  - Transaction amounts $< \$15.00$ followed by escalating amounts.
  - High decline / authorization retry rate across digital merchants.

## Typology 4: First-Party Bust-Out / Synthetic Identity
- **ID**: `TYP-BUST-004`
- **Definition**: Account opened with synthetic or altered identity elements, nurtured over months to increase credit limit, followed by maximum sudden drawdown and abandonment.
- **Key Indicators**:
  - Account tenure $> 6$ months with sudden $500\%+$ velocity surge.
  - Maximum credit line utilization within 48 hours.
  - Address shared with known delinquent accounts or PO Box proxy.

## Typology 5: Legitimate Vacation / Seasonal Travel (False Positive)
- **ID**: `TYP-LEGIT-005`
- **Definition**: Benign customer purchasing high-value airline, hotel, or retail items during genuine travel.
- **Key Indicators**:
  - Known customer device ID and consistent browser fingerprint.
  - Prior airline ticket purchase or travel advisory on record.
  - Clean account history (tenure $> 12$ months, zero past disputes).
  - Out-of-band Step-up SMS confirmed by customer.
