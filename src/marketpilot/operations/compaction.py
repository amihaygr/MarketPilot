"""Pure Silver compaction validation policy."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DatasetMetrics:
    row_count: int
    distinct_business_keys: int
    logical_hash_xor: int
    logical_hash_sum: int
    schema_fields: tuple[tuple[str, str, bool], ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def validate_compaction(before: DatasetMetrics, after: DatasetMetrics) -> None:
    if before.row_count < 1:
        raise ValueError("source partition is empty")
    if before != after:
        raise ValueError("compaction changed rows, business keys, logical hash, or schema")


def compaction_dates(through_date: date, lookback_days: int, run_id: str) -> tuple[date, ...]:
    UUID(run_id)
    if lookback_days < 1 or lookback_days > 31:
        raise ValueError("compaction lookback must be between 1 and 31 days")
    start = through_date - timedelta(days=lookback_days - 1)
    return tuple(start + timedelta(days=offset) for offset in range(lookback_days))
