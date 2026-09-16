"""Checksum-verified hybrid artifact loading and explainable scoring."""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from marketpilot.decision_intelligence.hybrid import expected_r
from marketpilot.decision_intelligence.modeling import FEATURE_NAMES, feature_values


@dataclass(frozen=True, slots=True)
class HybridScore:
    probability: Decimal
    expected_r: Decimal
    positive_drivers: tuple[str, ...]
    negative_drivers: tuple[str, ...]


def load_artifact(payload: bytes, expected_sha256: str) -> dict[str, Any]:
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise ValueError("hybrid model artifact checksum mismatch")
    try:
        import joblib
    except ImportError as error:  # pragma: no cover
        raise RuntimeError("joblib is required to load the hybrid model") from error
    artifact = joblib.load(io.BytesIO(payload))
    if (
        not isinstance(artifact, dict)
        or not {"model", "feature_names", "medians"} <= artifact.keys()
    ):
        raise ValueError("hybrid model artifact has an invalid schema")
    if list(artifact["feature_names"]) != list(FEATURE_NAMES):
        raise ValueError("hybrid model feature schema does not match the scorer")
    if len(artifact["medians"]) != len(artifact["feature_names"]):
        raise ValueError("hybrid model medians do not match the feature schema")
    return artifact


def score_payload(artifact: dict[str, Any], payload: dict[str, object]) -> HybridScore:
    vector = list(feature_values(payload))
    model = artifact["model"]
    probability = float(model.predict_proba([vector])[0][1])
    impacts: list[tuple[str, float]] = []
    for index, name in enumerate(artifact["feature_names"]):
        ablated = list(vector)
        ablated[index] = float(artifact["medians"][index])
        ablated_probability = float(model.predict_proba([ablated])[0][1])
        impacts.append((str(name), probability - ablated_probability))
    positives = tuple(
        name for name, value in sorted(impacts, key=lambda item: item[1], reverse=True) if value > 0
    )[:3]
    negatives = tuple(
        name for name, value in sorted(impacts, key=lambda item: item[1]) if value < 0
    )[:3]
    decimal_probability = Decimal(str(round(probability, 7)))
    return HybridScore(decimal_probability, expected_r(decimal_probability), positives, negatives)
