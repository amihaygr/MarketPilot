"""Pure Phase 9 analytics catalogue and validation rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

INDICATOR_SCHEMA_VERSION = 1
INDICATOR_VERSION = 1
SIGNAL_SCHEMA_VERSION = 1
SIGNAL_MODEL_VERSION = 1
INDICATOR_CODES = ("SMA_20", "RSI_14", "REALIZED_VOLATILITY_20", "VOLUME_RATIO_20")
SIGNAL_CODES = (
    "PRICE_CROSS_ABOVE_SMA20",
    "PRICE_CROSS_BELOW_SMA20",
    "RSI_CROSS_OVERSOLD",
    "RSI_CROSS_OVERBOUGHT",
    "VOLUME_SPIKE",
)


@dataclass(frozen=True, slots=True)
class AnalyticsScope:
    logical_date: date
    run_id: str
    lookback_days: int


def resolve_analytics_scope(
    logical_date_value: str,
    run_id: str,
    lookback_days: int = 10,
) -> AnalyticsScope:
    logical_date = date.fromisoformat(logical_date_value)
    UUID(run_id)
    if lookback_days < 1 or lookback_days > 31:
        raise ValueError("analytics lookback must be between 1 and 31 days")
    return AnalyticsScope(logical_date, run_id, lookback_days)


def signal_strength(signal_code: str, value: float) -> float:
    """Return a bounded, explainable score; it is not a trading recommendation."""
    if signal_code == "RSI_CROSS_OVERSOLD":
        score = (30.0 - value) / 30.0
    elif signal_code == "RSI_CROSS_OVERBOUGHT":
        score = (value - 70.0) / 30.0
    elif signal_code == "VOLUME_SPIKE":
        score = (value - 2.0) / 3.0
    else:
        score = abs(value) / 0.02
    return round(max(0.0, min(1.0, score)), 6)
