# Hybrid model training runbook

## Safety boundary

This workflow produces research probabilities, not orders or guaranteed returns. Never change a
registry row to `ACTIVE` merely because a chart looks attractive. Promotion requires all automated
gates, 20 new live certified v2 sessions and a recorded human review.

## Prerequisites

1. Acquire 24 months through `historical_market_backfill` in windows of at most 31 calendar days.
2. Confirm every requested session passed the ADR-010 IEX gates (35% per symbol,
   80% across the universe) and is `CERTIFIED` in Gold.
3. Run the daily Decision Intelligence calculation and label evaluation for the eligible snapshots.
4. Verify that SEC facts used by each snapshot were filed no later than its `as_of_utc` timestamp.

## Train a Preview model

Trigger the manual Airflow DAG `hybrid_model_training` with a unique immutable `model_version`.
The bounded task trains both candidates, calibrates them with sigmoid calibration, evaluates four
chronological walk-forward windows, writes the selected artifact plus manifest to the
`marketpilot-models` MinIO bucket and registers it as `PREVIEW`.

The DAG fails closed when there are fewer than 300 entered examples, only one label class or less
than approximately 24 months of observations. Failure does not affect v1 recommendations.

## Review

Read `/api/v1/decision-model/status` and inspect the stored metrics by symbol and quarter. Confirm
the Brier, PR-AUC, ECE, realized R, concentration and fold-stability gates. The Opportunity Center
must label all predictions `PREVIEW` until an explicit promotion process is implemented and run.

## Recovery

If an artifact is absent, has a mismatched checksum or cannot be deserialized, the daily scorer
publishes `FALLBACK` and leaves deterministic v1 output in control. Restore the immutable artifact
from MinIO or train a new version; never overwrite an existing version in place.
