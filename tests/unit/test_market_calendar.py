from datetime import UTC, date, datetime

import pytest

from marketpilot.batch.market_calendar import (
    expected_xnys_market_minutes,
    is_xnys_regular_market_minute,
)


def test_xnys_calendar_handles_regular_session() -> None:
    assert expected_xnys_market_minutes(date(2026, 8, 24)) == 390


def test_xnys_calendar_handles_early_close() -> None:
    assert expected_xnys_market_minutes(date(2026, 11, 27)) == 210


def test_xnys_calendar_rejects_weekend() -> None:
    assert expected_xnys_market_minutes(date(2026, 8, 22)) == 0


def test_xnys_minute_gate_rejects_extended_hours_and_naive_time() -> None:
    assert is_xnys_regular_market_minute(datetime(2026, 8, 24, 14, 30, tzinfo=UTC))
    assert not is_xnys_regular_market_minute(datetime(2026, 8, 24, 23, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        is_xnys_regular_market_minute(datetime(2026, 8, 24, 14, 30))
