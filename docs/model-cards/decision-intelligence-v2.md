# Model card — Decision Intelligence v2 Hybrid

## Intended use

Rank fixed-universe swing-trade research scenarios. The prediction is conditional on a valid entry
into the deterministic Buy Zone and estimates whether Target 1 is reached before Stop within ten
XNYS sessions.

## Models

- Transparent baseline: calibrated Logistic Regression.
- Non-linear challenger: calibrated Histogram Gradient Boosting.
- Selection: lower out-of-sample Brier score, subject to every promotion gate in ADR-009.

## Data and leakage controls

Training accepts certified market features and SEC facts known at snapshot time. SPY is a relative
market feature, not a target security. `NO_ENTRY` observations are reported separately and excluded
from success training. Same-bar target/stop ambiguity is conservatively a Stop.

## Limitations

IEX is a partial free feed. The fixed universe creates survivorship risk. Price returns currently
exclude dividend cash flows. The model does not know intrabar event order, analyst forecasts,
order-book liquidity, taxes or market impact. A calibrated probability is not a promise of profit.

## Release state

The first release is `PREVIEW`. Deterministic v1 rules remain in control until walk-forward gates,
20 new live v2 Shadow sessions and human approval are all complete. Artifact or schema failures
must produce `FALLBACK` without reusing an old probability.
