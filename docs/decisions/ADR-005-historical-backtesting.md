# ADR-005: Local Historical Backtesting Boundary

- Status: Accepted
- Date: 2026-08-29

## Context

MarketPilot models versioned indicators and signals but does not yet measure how
an explicit historical strategy would have behaved. A backtest must be
reproducible, explainable, bounded, and protected from look-ahead bias. It must
not be presented as trade execution or financial advice.

## Decision

- Backtesting is a bounded Spark Batch application submitted by Airflow through
  `SparkSubmitOperator`.
- Only certified one-minute Gold bars are eligible input in the local phase.
- A signal calculated from bar `t` may affect returns starting with bar `t+1`.
- Strategy code, parameters, input range, costs, run ID, code version, data
  version, and schema version are persisted for every run.
- Full-resolution analytical output is written to MinIO as versioned Parquet.
- MariaDB Gold stores run metadata, application-ready summary metrics, and a
  bounded daily equity curve for the Backend API.
- Publication is idempotent by run ID and uses an explicit quality gate before a
  run becomes `PUBLISHED`.
- The initial strategy is a long-or-cash SMA crossover with explicit transaction
  cost and slippage assumptions and SPY as the comparison benchmark.
- The Web App reads backtest results only through the Backend API.

## Consequences

### Positive

- Results are repeatable and traceable to certified data and code versions.
- Next-bar application prevents the most direct form of look-ahead bias.
- Detailed output remains queryable and replayable without turning MariaDB into
  the only analytical store.
- The application receives small, bounded read models.

### Negative

- A fixed universe can still create survivorship bias.
- The MVP does not model dividends, splits, taxes, market impact, or order-book
  liquidity.
- IEX data and the available local history limit conclusions.
- Historical performance cannot establish future performance.

## Rejected alternatives

- Run the backtest in the browser. This would violate the API and compute
  boundaries and make runs difficult to reproduce.
- Execute trades from generated signals. MarketPilot is an engineering and
  analytics project, not a trading execution system.
- Store only aggregate metrics in MariaDB. This would remove the detailed audit
  trail required to reproduce and explain a result.
