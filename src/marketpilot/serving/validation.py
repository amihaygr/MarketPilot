"""Bounded query validation shared by API routes and unit tests."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta


class QueryRangeError(ValueError):
    """Raised when a requested serving range is invalid or unbounded."""


def market_time_range(
    start_utc: datetime | None,
    end_utc: datetime | None,
    *,
    now_utc: datetime,
    max_days: int,
) -> tuple[datetime, datetime]:
    end = _aware_utc(end_utc or now_utc, "end_utc")
    start = _aware_utc(start_utc or end - timedelta(days=7), "start_utc")
    if start >= end:
        raise QueryRangeError("start_utc must be earlier than end_utc")
    if end - start > timedelta(days=max_days):
        raise QueryRangeError(f"market-bar range cannot exceed {max_days} days")
    return start, end


def filing_date_range(
    start_date: date | None,
    end_date: date | None,
    *,
    today: date,
    max_days: int,
) -> tuple[date, date]:
    end = end_date or today
    start = start_date or end - timedelta(days=365)
    if start > end:
        raise QueryRangeError("start_date must not be after end_date")
    if end - start > timedelta(days=max_days):
        raise QueryRangeError(f"filing range cannot exceed {max_days} days")
    return start, end


def utc_day_bounds(value: date) -> tuple[datetime, datetime]:
    start = datetime.combine(value, time.min, tzinfo=UTC)
    return start, start + timedelta(days=1)


def _aware_utc(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise QueryRangeError(f"{name} must include a timezone offset")
    return value.astimezone(UTC)
