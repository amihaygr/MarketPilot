# ADR-009: Hybrid Decision Intelligence

- Status: Accepted
- Date: 2026-09-16

## Context

The deterministic Phase 14 rules provide explainable levels and risk controls, but their score and
confidence are not calibrated probabilities. The existing SMA backtest does not validate whether a
published Buy Zone reaches Target 1 before Stop.

## Decision

- The deterministic rules remain authoritative for levels, freshness, portfolio risk and hard gates.
- A calibrated probability model estimates whether Target 1 is reached before Stop within ten XNYS
  sessions, conditional on a valid entry into the published Buy Zone.
- Recommendations with no valid entry are labelled `NO_ENTRY`, not losses. A bar touching both Stop
  and a target is conservatively labelled Stop.
- Training uses only point-in-time, certified inputs. SEC facts filed after the feature timestamp and
  future market observations are forbidden.
- Logistic Regression is the baseline and Histogram Gradient Boosting is the challenger. Both use
  sigmoid probability calibration and chronological walk-forward validation.
- Model artifacts and datasets are versioned in MinIO; registry, metrics, predictions and lineage are
  stored in MariaDB.
- A model remains `PREVIEW` until all automatic validation gates pass, 20 new live certified sessions
  accumulate for its own version and a human records approval. `v1` remains the fallback.
- The system never submits an order and never presents probability as a guaranteed return.

## Consequences

The product gains measurable probabilities and out-of-sample evidence while preserving explainable
risk controls. It also gains model lifecycle, calibration and drift responsibilities. Free IEX data
limits market coverage and must remain visible in the UI.
