from datetime import UTC, date, datetime, timedelta

import pytest

from marketpilot.serving.settings import ServingSettings
from marketpilot.serving.validation import QueryRangeError, filing_date_range, market_time_range


def test_serving_settings_require_explicit_database_identity() -> None:
    values = {
        "MARIADB_HOST": "mariadb",
        "MARIADB_DATABASE": "marketpilot",
        "MARIADB_APP_USER": "marketpilot_app",
        "MARIADB_APP_PASSWORD": "secret",
        "API_CORS_ORIGINS": "http://localhost:3000, https://example.test",
    }
    settings = ServingSettings.from_environ(values)

    assert settings.mariadb_port == 3306
    assert settings.cors_origins == ("http://localhost:3000", "https://example.test")
    assert settings.max_market_range_days == 31
    assert settings.max_filing_range_days == 3660


def test_market_range_defaults_to_seven_aware_utc_days() -> None:
    now = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)

    start, end = market_time_range(None, None, now_utc=now, max_days=31)

    assert end == now
    assert start == now - timedelta(days=7)


def test_market_range_rejects_naive_and_unbounded_values() -> None:
    now = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)
    with pytest.raises(QueryRangeError, match="timezone"):
        market_time_range(datetime(2026, 8, 20), now, now_utc=now, max_days=31)
    with pytest.raises(QueryRangeError, match="cannot exceed 31"):
        market_time_range(now - timedelta(days=32), now, now_utc=now, max_days=31)


def test_filing_range_is_bounded_and_ordered() -> None:
    today = date(2026, 8, 26)
    assert filing_date_range(None, None, today=today, max_days=3660) == (
        date(2025, 8, 26),
        today,
    )
    with pytest.raises(QueryRangeError, match="must not be after"):
        filing_date_range(today, today - timedelta(days=1), today=today, max_days=3660)
