# ADR-008: Stateful Decision Intelligence with Batch Authority

- Status: Accepted
- Date: 2026-09-13

## Context

MarketPilot needs explainable swing-trade decision support without becoming an execution system.
Recommendations combine multi-timeframe market features, SEC fundamentals and manual portfolio risk.

## Decision

- Every output is a research scenario: buy zone, invalidation stop, two targets and risk sizing.
- Spark Structured Streaming may publish a stateful `PROVISIONAL` result after a closed 15-minute bar.
- The post-market Spark Batch pipeline recomputes and publishes the authoritative `CERTIFIED` result.
- Inputs, formula/model version, timestamps, data/feed status, lineage and Hebrew explanations are retained.
- IEX lowers confidence. Market data older than 30 minutes during trading, or fundamentals older than
  150 days, blocks an entry recommendation.
- The first 20 completed market sessions are Shadow Mode. Results are recorded and evaluated but
  `actionable=false` regardless of the displayed scenario.
- Portfolio state is manual. Maximum planned risk is 2% per trade, 20% symbol exposure and 6% total
  open risk. The system never submits orders or accesses Alpaca balances.
- Elastic remains optional under ADR-006 and is not required by this phase.

## Consequences

The recommendation is reproducible and auditable, but delayed fundamentals and partial free market
feeds can suppress it. Promotion from Shadow Mode requires walk-forward evidence and a separate,
documented decision; strong historical returns alone are insufficient.
