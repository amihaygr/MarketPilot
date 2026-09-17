"""Plan resumable bounded windows for long historical acquisition."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta

from marketpilot.batch.market_calendar import expected_xnys_market_minutes


@dataclass(frozen=True, slots=True)
class HistoricalWindow:
    """One Airflow-compatible historical acquisition window."""

    start_date: date
    end_date: date

    @property
    def run_id(self) -> str:
        return f"phase15_24m__{self.start_date.isoformat()}__{self.end_date.isoformat()}"


def rolling_month_start(end_date: date, months: int) -> date:
    """Return the inclusive first day of a rolling ``months``-month interval."""
    if months < 1 or months > 60:
        raise ValueError("months must be in [1, 60]")
    month_index = end_date.year * 12 + end_date.month - 1 - months
    year, zero_based_month = divmod(month_index, 12)
    month = zero_based_month + 1
    shifted_day = min(end_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, shifted_day) + timedelta(days=1)


def plan_historical_windows(
    start_date: date,
    end_date: date,
    *,
    maximum_calendar_days: int = 31,
) -> tuple[HistoricalWindow, ...]:
    """Split an inclusive range into chronological windows containing XNYS sessions."""
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")
    if maximum_calendar_days < 1 or maximum_calendar_days > 31:
        raise ValueError("maximum_calendar_days must be in [1, 31]")

    windows: list[HistoricalWindow] = []
    cursor = start_date
    while cursor <= end_date:
        window_end = min(cursor + timedelta(days=maximum_calendar_days - 1), end_date)
        if any(
            expected_xnys_market_minutes(cursor + timedelta(days=offset)) > 0
            for offset in range((window_end - cursor).days + 1)
        ):
            windows.append(HistoricalWindow(cursor, window_end))
        cursor = window_end + timedelta(days=1)
    return tuple(windows)
