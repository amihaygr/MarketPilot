from datetime import date

from marketpilot.batch.market_calendar import expected_xnys_market_minutes


def test_xnys_calendar_handles_regular_session() -> None:
    assert expected_xnys_market_minutes(date(2026, 8, 24)) == 390


def test_xnys_calendar_handles_early_close() -> None:
    assert expected_xnys_market_minutes(date(2026, 11, 27)) == 210


def test_xnys_calendar_rejects_weekend() -> None:
    assert expected_xnys_market_minutes(date(2026, 8, 22)) == 0
