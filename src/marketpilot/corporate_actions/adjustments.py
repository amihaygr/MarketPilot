"""Deterministic split adjustment for analytical OHLCV history."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any


def adjust_bars_for_splits(
    rows: list[dict[str, Any]], actions: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Return split-adjusted copies while preserving immutable raw Gold rows."""
    splits: list[tuple[date, Decimal]] = []
    for action in actions:
        if action.get("action_type") not in {"forward_splits", "reverse_splits"}:
            continue
        old_rate = Decimal(str(action.get("old_rate") or 0))
        new_rate = Decimal(str(action.get("new_rate") or 0))
        ex_date = action.get("ex_date")
        if isinstance(ex_date, datetime):
            ex_date = ex_date.date()
        if isinstance(ex_date, date) and old_rate > 0 and new_rate > 0:
            splits.append((ex_date, old_rate / new_rate))

    adjusted: list[dict[str, Any]] = []
    for source in rows:
        row = dict(source)
        timestamp = row.get("event_time_utc")
        if not isinstance(timestamp, datetime):
            adjusted.append(row)
            continue
        price_factor = Decimal(1)
        for ex_date, factor in splits:
            if timestamp.date() < ex_date:
                price_factor *= factor
        if price_factor != 1:
            for field in ("open_price", "high_price", "low_price", "close_price"):
                row[field] = Decimal(str(row[field])) * price_factor
            row["volume"] = int(Decimal(str(row["volume"])) / price_factor)
        adjusted.append(row)
    return adjusted
