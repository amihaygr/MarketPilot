from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pytest

from marketpilot.analytics.mariadb import publish_analytics_partition
from marketpilot.analytics.rules import (
    INDICATOR_CODES,
    SIGNAL_CODES,
    resolve_analytics_scope,
    signal_strength,
)
from marketpilot.streaming.mariadb_sink import MariaDbConfig


class FakeCursor:
    def __init__(self) -> None:
        self.executions: list[tuple[str, Any]] = []

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *_arguments: object) -> None:
        return None

    def execute(self, sql: str, parameters: Any = None) -> None:
        self.executions.append((sql, parameters))

    def executemany(self, sql: str, parameters: Any) -> None:
        self.executions.append((sql, list(parameters)))


class FakeConnection:
    def __init__(self) -> None:
        self.fake_cursor = FakeCursor()
        self.committed = False
        self.rolled_back = False

    def cursor(self) -> FakeCursor:
        return self.fake_cursor

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        return None


def test_analytics_scope_is_bounded_and_versioned_catalogues_are_unique() -> None:
    scope = resolve_analytics_scope(
        "2026-08-28",
        "5cb13061-4394-4e75-a788-9ef06c190bf2",
        10,
    )
    assert scope.logical_date == date(2026, 8, 28)
    assert scope.lookback_days == 10
    assert len(INDICATOR_CODES) == len(set(INDICATOR_CODES)) == 4
    assert len(SIGNAL_CODES) == len(set(SIGNAL_CODES)) == 5
    with pytest.raises(ValueError, match="between 1 and 31"):
        resolve_analytics_scope("2026-08-28", scope.run_id, 32)


@pytest.mark.parametrize(
    ("code", "value", "expected"),
    [
        ("RSI_CROSS_OVERSOLD", 15.0, 0.5),
        ("RSI_CROSS_OVERBOUGHT", 85.0, 0.5),
        ("VOLUME_SPIKE", 3.5, 0.5),
        ("PRICE_CROSS_ABOVE_SMA20", 0.01, 0.5),
        ("PRICE_CROSS_BELOW_SMA20", -0.03, 1.0),
    ],
)
def test_signal_strength_is_explainable_and_bounded(
    code: str,
    value: float,
    expected: float,
) -> None:
    assert signal_strength(code, value) == expected


def test_analytics_partition_is_replaced_atomically(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = FakeConnection()
    monkeypatch.setattr(
        "marketpilot.analytics.mariadb.pymysql.connect",
        lambda **_parameters: connection,
    )
    timestamp = datetime(2026, 8, 28, 14, 30, tzinfo=UTC)
    indicators = [
        {
            "symbol_id": 1,
            "event_time_utc": timestamp,
            "indicator_code": "RSI_14",
            "indicator_version": 1,
            "indicator_value": Decimal("42.5"),
            "lookback_bars": 14,
            "certification_status": "PROVISIONAL",
            "code_version": "test",
            "data_version": "market-analytics-v1",
            "schema_version": 1,
        }
    ]
    signals = [
        {
            "symbol_id": 1,
            "signal_time_utc": timestamp,
            "signal_code": "VOLUME_SPIKE",
            "model_version": 1,
            "direction": "WATCH",
            "strength": Decimal("0.25"),
            "explanation": "Volume crossed its configured threshold",
            "certification_status": "PROVISIONAL",
            "code_version": "test",
            "data_version": "market-signals-v1",
            "schema_version": 1,
        }
    ]
    result = publish_analytics_partition(
        MariaDbConfig("mariadb", 3306, "marketpilot", "publisher", "secret"),
        logical_date=date(2026, 8, 28),
        run_id="5cb13061-4394-4e75-a788-9ef06c190bf2",
        indicators=indicators,
        signals=signals,
    )

    assert result == (1, 1)
    assert connection.committed is True
    assert connection.rolled_back is False
    statements = "\n".join(sql for sql, _ in connection.fake_cursor.executions)
    assert statements.index("DELETE FROM fact_signal") < statements.index(
        "INSERT INTO fact_indicator_1m"
    )
    assert "market-analytics-publication" in statements
    assert "market_analytics_gold" in statements


def test_analytics_publication_rejects_invalid_rsi_before_database_connect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    def connect(**_parameters: Any) -> FakeConnection:
        nonlocal called
        called = True
        return FakeConnection()

    monkeypatch.setattr("marketpilot.analytics.mariadb.pymysql.connect", connect)
    with pytest.raises(ValueError, match="RSI value"):
        publish_analytics_partition(
            MariaDbConfig("mariadb", 3306, "marketpilot", "publisher", "secret"),
            logical_date=date(2026, 8, 28),
            run_id="5cb13061-4394-4e75-a788-9ef06c190bf2",
            indicators=[
                {
                    "symbol_id": 1,
                    "event_time_utc": datetime(2026, 8, 28, tzinfo=UTC),
                    "indicator_code": "RSI_14",
                    "indicator_version": 1,
                    "indicator_value": 101,
                }
            ],
            signals=[],
        )
    assert called is False
