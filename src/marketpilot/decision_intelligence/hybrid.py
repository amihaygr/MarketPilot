"""Versioned Hybrid Decision Intelligence contracts and release gates."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

HYBRID_MODEL_VERSION = "decision-intelligence-v2-hybrid"
FEATURE_SCHEMA_VERSION = 2
MINIMUM_ACTION_PROBABILITY = Decimal("0.60")

ModelStatus = Literal["PREVIEW", "ACTIVE", "FALLBACK"]
EntryOutcome = Literal["TARGET_1", "TARGET_2", "STOP", "EXPIRED", "NO_ENTRY"]


@dataclass(frozen=True, slots=True)
class PriceBar:
    event_time_utc: datetime
    high: Decimal
    low: Decimal
    close: Decimal


@dataclass(frozen=True, slots=True)
class RecommendationLabel:
    entry_filled: bool
    entry_time_utc: datetime | None
    entry_price: Decimal | None
    outcome: EntryOutcome
    target_before_stop: int | None
    observed_close: Decimal | None
    observed_high: Decimal | None
    observed_low: Decimal | None


@dataclass(frozen=True, slots=True)
class ValidationMetrics:
    entered_samples: int
    positive_samples: int
    symbol_count: int
    quarter_count: int
    brier_score: Decimal
    baseline_brier_score: Decimal
    pr_auc: Decimal
    positive_rate: Decimal
    expected_calibration_error: Decimal
    mean_realized_r: Decimal
    largest_symbol_profit_share: Decimal
    worst_fold_mean_r: Decimal


@dataclass(frozen=True, slots=True)
class PromotionDecision:
    eligible: bool
    reasons: tuple[str, ...]


def label_recommendation_path(
    *,
    zone_low: Decimal,
    zone_high: Decimal,
    stop: Decimal,
    target_1: Decimal,
    target_2: Decimal,
    entry_window_bars: Sequence[PriceBar],
    outcome_bars: Sequence[PriceBar],
) -> RecommendationLabel:
    """Label a recommendation only after the market offered a valid entry.

    A bar touching both stop and a target is conservatively labelled STOP because
    one-minute OHLC data cannot establish intrabar ordering.
    """
    entry_bar = next(
        (bar for bar in entry_window_bars if bar.low <= zone_high and bar.high >= zone_low),
        None,
    )
    if entry_bar is None:
        return RecommendationLabel(False, None, None, "NO_ENTRY", None, None, None, None)

    entry_price = min(zone_high, max(zone_low, entry_bar.close))
    eligible = [bar for bar in outcome_bars if bar.event_time_utc > entry_bar.event_time_utc]
    if not eligible:
        return RecommendationLabel(
            True,
            entry_bar.event_time_utc,
            entry_price,
            "EXPIRED",
            0,
            entry_bar.close,
            entry_bar.high,
            entry_bar.low,
        )

    observed_high = max(bar.high for bar in eligible)
    observed_low = min(bar.low for bar in eligible)
    for bar in eligible:
        stop_hit = bar.low <= stop
        target_1_hit = bar.high >= target_1
        target_2_hit = bar.high >= target_2
        if stop_hit:
            outcome: EntryOutcome = "STOP"
            success = 0
            break
        if target_2_hit:
            outcome = "TARGET_2"
            success = 1
            break
        if target_1_hit:
            outcome = "TARGET_1"
            success = 1
            break
    else:
        outcome = "EXPIRED"
        success = 0

    return RecommendationLabel(
        True,
        entry_bar.event_time_utc,
        entry_price,
        outcome,
        success,
        eligible[-1].close,
        observed_high,
        observed_low,
    )


def expected_r(
    success_probability: Decimal,
    *,
    reward_r: Decimal = Decimal("2"),
    loss_r: Decimal = Decimal("1"),
    friction_r: Decimal = Decimal("0"),
) -> Decimal:
    if not Decimal("0") <= success_probability <= Decimal("1"):
        raise ValueError("success_probability must be between zero and one")
    return (
        success_probability * reward_r - (Decimal("1") - success_probability) * loss_r - friction_r
    ).quantize(Decimal("0.0001"))


def decision_feature_payload(data: object, decision: object) -> dict[str, float | int | str | None]:
    """Create scale-safe, JSON-ready features from a point-in-time v1 snapshot."""
    price = Decimal(data.price)
    pct = lambda value: float((Decimal(value) / price - 1) * 100)  # noqa: E731
    fundamentals_time = data.fundamentals_as_of_utc
    as_of = data.as_of_utc
    market_time = data.market_data_time_utc
    return {
        "ema20_distance_pct": pct(data.ema20),
        "ema50_distance_pct": pct(data.ema50),
        "atr_pct": float(Decimal(data.atr14) / price * 100),
        "rsi14": float(data.rsi14),
        "macd_pct": float(Decimal(data.macd_histogram) / price * 100),
        "volume_ratio": float(data.volume_ratio),
        "relative_strength_spy": float(data.relative_strength_spy),
        "daily_trend": int(data.daily_trend),
        "hourly_trend": int(data.hourly_trend),
        "five_minute_trend": int(data.five_minute_trend),
        "support_distance_pct": pct(data.support),
        "resistance_distance_pct": pct(data.resistance_1),
        "revenue_growth_pct": _optional_float(data.revenue_growth_pct),
        "eps_growth_pct": _optional_float(data.eps_growth_pct),
        "fcf_growth_pct": _optional_float(data.fcf_growth_pct),
        "net_margin_pct": _optional_float(data.net_margin_pct),
        "debt_to_equity": _optional_float(data.debt_to_equity),
        "dilution_pct": _optional_float(data.dilution_pct),
        "fundamental_age_days": (as_of - fundamentals_time).days if fundamentals_time else None,
        "market_age_minutes": max(0, int((as_of - market_time).total_seconds() // 60)),
        "rule_score": float(decision.opportunity_score),
    }


def _optional_float(value: object | None) -> float | None:
    return float(value) if value is not None else None


def evaluate_promotion(metrics: ValidationMetrics) -> PromotionDecision:
    reasons: list[str] = []
    if metrics.entered_samples < 300:
        reasons.append("fewer than 300 entered samples")
    if metrics.positive_samples < 50:
        reasons.append("fewer than 50 positive samples")
    if metrics.symbol_count < 8:
        reasons.append("fewer than 8 symbols")
    if metrics.quarter_count < 4:
        reasons.append("fewer than 4 calendar quarters")
    required_brier = metrics.baseline_brier_score * Decimal("0.95")
    if metrics.brier_score > required_brier:
        reasons.append("Brier score does not beat the base-rate baseline by 5%")
    if metrics.pr_auc <= metrics.positive_rate:
        reasons.append("PR-AUC does not beat positive-rate prevalence")
    if metrics.expected_calibration_error > Decimal("0.08"):
        reasons.append("expected calibration error exceeds 0.08")
    if metrics.mean_realized_r <= 0:
        reasons.append("mean realized R is not positive")
    if metrics.largest_symbol_profit_share > Decimal("0.25"):
        reasons.append("one symbol contributes more than 25% of profit")
    if metrics.worst_fold_mean_r < Decimal("-0.25"):
        reasons.append("a walk-forward fold is materially unstable")
    return PromotionDecision(not reasons, tuple(reasons))


def hybrid_action(
    *,
    rules_action: str,
    model_status: ModelStatus,
    success_probability: Decimal | None,
    activation_threshold: Decimal,
    price: Decimal,
    zone_low: Decimal,
    zone_high: Decimal,
) -> str:
    """Apply probability only after promotion; PREVIEW/FALLBACK preserve v1."""
    if model_status != "ACTIVE" or success_probability is None:
        return rules_action
    threshold = max(MINIMUM_ACTION_PROBABILITY, activation_threshold)
    if rules_action in {"INSUFFICIENT DATA", "AVOID"}:
        return rules_action
    if success_probability < threshold:
        return "WAIT"
    if zone_low <= price <= zone_high:
        return "BUY ZONE"
    if price > zone_high:
        return "WATCH BREAKOUT"
    return "WAIT"
