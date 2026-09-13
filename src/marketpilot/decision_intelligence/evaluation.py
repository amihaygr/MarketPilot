"""Leakage-safe recommendation outcome evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    observed_close: Decimal
    observed_high: Decimal
    observed_low: Decimal
    realized_return_pct: Decimal
    max_favorable_excursion_pct: Decimal
    max_adverse_excursion_pct: Decimal
    target_1_hit: bool
    target_2_hit: bool
    stop_hit: bool
    outcome: str


def evaluate_path(
    *,
    entry: Decimal,
    target_1: Decimal,
    target_2: Decimal,
    stop: Decimal,
    bars: list[dict[str, object]],
) -> EvaluationResult:
    if entry <= 0 or not bars:
        raise ValueError("entry must be positive and bars must not be empty")
    highs = [Decimal(str(row["high_price"])) for row in bars]
    lows = [Decimal(str(row["low_price"])) for row in bars]
    close = Decimal(str(bars[-1]["close_price"]))
    high, low = max(highs), min(lows)
    target_1_hit = high >= target_1
    target_2_hit = high >= target_2
    stop_hit = low <= stop
    if stop_hit and (target_1_hit or target_2_hit):
        outcome = "STOP"  # Conservative when intrabar ordering is unknowable.
    elif target_2_hit:
        outcome = "TARGET_2"
    elif target_1_hit:
        outcome = "TARGET_1"
    elif stop_hit:
        outcome = "STOP"
    else:
        outcome = "OPEN"
    return EvaluationResult(
        observed_close=close,
        observed_high=high,
        observed_low=low,
        realized_return_pct=(close / entry - 1) * 100,
        max_favorable_excursion_pct=(high / entry - 1) * 100,
        max_adverse_excursion_pct=(low / entry - 1) * 100,
        target_1_hit=target_1_hit,
        target_2_hit=target_2_hit,
        stop_hit=stop_hit,
        outcome=outcome,
    )
