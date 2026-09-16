"""Local calibrated model training and auditable artifact helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from marketpilot.decision_intelligence.hybrid import ValidationMetrics, evaluate_promotion

FEATURE_NAMES = (
    "ema20_distance_pct",
    "ema50_distance_pct",
    "atr_pct",
    "rsi14",
    "macd_pct",
    "volume_ratio",
    "relative_strength_spy",
    "daily_trend",
    "hourly_trend",
    "five_minute_trend",
    "support_distance_pct",
    "resistance_distance_pct",
    "revenue_growth_pct",
    "eps_growth_pct",
    "fcf_growth_pct",
    "net_margin_pct",
    "debt_to_equity",
    "dilution_pct",
    "fundamental_age_days",
    "market_age_minutes",
    "rule_score",
)


@dataclass(frozen=True, slots=True)
class TrainingRow:
    snapshot_id: str
    symbol: str
    as_of_date: date
    features: tuple[float, ...]
    label: int
    realized_r: float


@dataclass(frozen=True, slots=True)
class TrainingResult:
    model_family: str
    activation_threshold: Decimal
    metrics: ValidationMetrics
    promotion_eligible: bool
    promotion_reasons: tuple[str, ...]
    test_probabilities: tuple[float, ...]
    test_labels: tuple[int, ...]


def feature_values(payload: dict[str, object]) -> tuple[float, ...]:
    values: list[float] = []
    for name in FEATURE_NAMES:
        raw = payload.get(name)
        values.append(float(raw) if raw is not None else 0.0)
    return tuple(values)


def expected_calibration_error(labels: Sequence[int], probabilities: Sequence[float]) -> float:
    if not labels:
        return 1.0
    total = len(labels)
    error = 0.0
    for start in range(10):
        low, high = start / 10, (start + 1) / 10
        indices = [
            index
            for index, probability in enumerate(probabilities)
            if low <= probability < high or (start == 9 and probability == 1)
        ]
        if indices:
            accuracy = sum(labels[index] for index in indices) / len(indices)
            confidence = sum(probabilities[index] for index in indices) / len(indices)
            error += len(indices) / total * abs(accuracy - confidence)
    return error


def train_walk_forward(rows: Sequence[TrainingRow]) -> tuple[Any, TrainingResult]:
    """Train calibrated baseline/challenger with expanding chronological folds."""
    try:
        import numpy as np
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.ensemble import HistGradientBoostingClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import average_precision_score, brier_score_loss
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as error:  # pragma: no cover - depends on optional runtime image
        raise RuntimeError("install MarketPilot with the ml optional dependency") from error

    ordered = sorted(rows, key=lambda row: (row.as_of_date, row.symbol, row.snapshot_id))
    if len(ordered) < 300 or len({row.label for row in ordered}) < 2:
        raise ValueError("at least 300 entered samples and both labels are required")
    dates = sorted({row.as_of_date for row in ordered})
    if (dates[-1] - dates[0]).days < 700:
        raise ValueError("training data must span approximately 24 months")

    fold_starts = [0.50, 0.625, 0.75, 0.875]
    candidates = {
        "LOGISTIC_REGRESSION": lambda: make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=2_000, class_weight="balanced")
        ),
        "HIST_GRADIENT_BOOSTING": lambda: HistGradientBoostingClassifier(
            max_depth=5,
            learning_rate=0.05,
            max_iter=250,
            l2_regularization=1.0,
            random_state=42,
        ),
    }
    candidate_outputs: dict[
        str, tuple[list[int], list[float], list[float], list[str], list[int]]
    ] = {}
    for family, factory in candidates.items():
        labels_out: list[int] = []
        probabilities_out: list[float] = []
        realized_r_out: list[float] = []
        symbols_out: list[str] = []
        fold_ids_out: list[int] = []
        for fold_id, fraction in enumerate(fold_starts):
            split = int(len(dates) * fraction)
            test_end = min(len(dates), split + max(1, int(len(dates) * 0.125)))
            train_dates, test_dates = set(dates[:split]), set(dates[split:test_end])
            train = [row for row in ordered if row.as_of_date in train_dates]
            test = [row for row in ordered if row.as_of_date in test_dates]
            if not test or len({row.label for row in train}) < 2:
                continue
            base = factory()
            calibrated = CalibratedClassifierCV(base, method="sigmoid", cv=3)
            calibrated.fit(
                np.asarray([row.features for row in train]), [row.label for row in train]
            )
            probabilities = calibrated.predict_proba(np.asarray([row.features for row in test]))[
                :, 1
            ]
            labels_out.extend(row.label for row in test)
            probabilities_out.extend(float(value) for value in probabilities)
            realized_r_out.extend(row.realized_r for row in test)
            symbols_out.extend(row.symbol for row in test)
            fold_ids_out.extend([fold_id] * len(test))
        if not labels_out:
            raise ValueError("walk-forward folds produced no out-of-sample observations")
        candidate_outputs[family] = (
            labels_out,
            probabilities_out,
            realized_r_out,
            symbols_out,
            fold_ids_out,
        )

    family = min(
        candidate_outputs,
        key=lambda name: brier_score_loss(candidate_outputs[name][0], candidate_outputs[name][1]),
    )
    labels, probabilities, realized, test_symbols, fold_ids = candidate_outputs[family]
    positive_rate = sum(labels) / len(labels)
    brier = brier_score_loss(labels, probabilities)
    baseline_brier = brier_score_loss(labels, [positive_rate] * len(labels))

    thresholds = [value / 100 for value in range(60, 86)]
    threshold = max(
        thresholds,
        key=lambda candidate: sum(
            (probability * 2 - (1 - probability))
            for probability in probabilities
            if probability >= candidate
        ),
    )
    selected_r = [
        value
        for value, probability in zip(realized, probabilities, strict=True)
        if probability >= threshold
    ]
    per_symbol_profit: dict[str, float] = {}
    for symbol, realized_r, probability in zip(test_symbols, realized, probabilities, strict=True):
        if probability >= threshold:
            per_symbol_profit[symbol] = per_symbol_profit.get(symbol, 0.0) + max(0, realized_r)
    total_profit = sum(per_symbol_profit.values())
    largest_share = (
        max(per_symbol_profit.values(), default=0) / total_profit if total_profit else 1.0
    )
    fold_means = []
    for fold_id in sorted(set(fold_ids)):
        fold_values = [
            realized_r
            for realized_r, probability, observation_fold in zip(
                realized, probabilities, fold_ids, strict=True
            )
            if observation_fold == fold_id and probability >= threshold
        ]
        fold_means.append(sum(fold_values) / len(fold_values) if fold_values else -1.0)
    metrics = ValidationMetrics(
        entered_samples=len(ordered),
        positive_samples=sum(row.label for row in ordered),
        symbol_count=len({row.symbol for row in ordered}),
        quarter_count=len(
            {(row.as_of_date.year, (row.as_of_date.month - 1) // 3) for row in ordered}
        ),
        brier_score=Decimal(str(round(brier, 8))),
        baseline_brier_score=Decimal(str(round(baseline_brier, 8))),
        pr_auc=Decimal(str(round(average_precision_score(labels, probabilities), 8))),
        positive_rate=Decimal(str(round(positive_rate, 8))),
        expected_calibration_error=Decimal(
            str(round(expected_calibration_error(labels, probabilities), 8))
        ),
        mean_realized_r=Decimal(str(round(sum(selected_r) / len(selected_r), 8)))
        if selected_r
        else Decimal("-1"),
        largest_symbol_profit_share=Decimal(str(round(largest_share, 8))),
        worst_fold_mean_r=Decimal(str(round(min(fold_means, default=-1.0), 8))),
    )
    promotion = evaluate_promotion(metrics)

    final_model = CalibratedClassifierCV(candidates[family](), method="sigmoid", cv=5)
    final_model.fit(np.asarray([row.features for row in ordered]), [row.label for row in ordered])
    result = TrainingResult(
        family,
        Decimal(str(threshold)),
        metrics,
        promotion.eligible,
        promotion.reasons,
        tuple(probabilities),
        tuple(labels),
    )
    return final_model, result


def artifact_manifest(
    *, model_version: str, result: TrainingResult, payload: bytes
) -> dict[str, object]:
    return {
        "model_version": model_version,
        "model_family": result.model_family,
        "feature_names": list(FEATURE_NAMES),
        "feature_schema_version": 2,
        "activation_threshold": str(result.activation_threshold),
        "promotion_eligible": result.promotion_eligible,
        "promotion_reasons": list(result.promotion_reasons),
        "metrics": {key: str(value) for key, value in asdict(result.metrics).items()},
        "artifact_sha256": hashlib.sha256(payload).hexdigest(),
    }


def dumps_manifest(manifest: dict[str, object]) -> bytes:
    return (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
