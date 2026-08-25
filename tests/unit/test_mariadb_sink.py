from datetime import UTC, datetime
from decimal import Decimal

import pytest

from marketpilot.streaming import mariadb_sink
from marketpilot.streaming.mariadb_sink import MariaDbConfig


class FakeCursor:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, list[tuple[object, ...]]]] = []

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def executemany(self, sql: str, parameters: list[tuple[object, ...]]) -> None:
        if self.fail:
            raise RuntimeError("database unavailable")
        self.calls.append((sql, parameters))


class FakeConnection:
    def __init__(self, fail: bool = False) -> None:
        self.fake_cursor = FakeCursor(fail=fail)
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self) -> FakeCursor:
        return self.fake_cursor

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


def sample_row() -> dict[str, object]:
    return {
        "event_id": "f2e20fef-cf15-5da8-9a14-a022f98a2aec",
        "symbol": "AAPL",
        "event_time_utc": datetime(2026, 8, 25, 14, 40, tzinfo=UTC),
        "interval": "1Min",
        "open": Decimal("386.00"),
        "high": Decimal("386.50"),
        "low": Decimal("385.50"),
        "close": Decimal("386.10"),
        "volume": 1286,
        "source": "synthetic",
        "schema_version": 1,
        "ingested_at_utc": datetime(2026, 8, 25, 14, 40, 1, tzinfo=UTC),
        "kafka_topic": "market.bars.1m.v1",
        "kafka_partition": 0,
        "kafka_offset": 42,
        "pipeline_run_id": "ca0ab638-e697-5c4e-bbb2-5bcd6200df70",
        "code_version": "test",
        "data_version": "market-bar-v1",
    }


def config() -> MariaDbConfig:
    return MariaDbConfig("mariadb", 3306, "marketpilot", "ingest", "secret")


def test_market_bar_parameters_preserve_lineage_and_utc() -> None:
    parameters = mariadb_sink.market_bar_parameters(sample_row())

    assert parameters[0] == datetime(2026, 8, 25, 14, 40)
    assert parameters[7] == "f2e20fef-cf15-5da8-9a14-a022f98a2aec"
    assert parameters[10:13] == ("market.bars.1m.v1", 0, 42)
    assert parameters[-1] == "AAPL"


def test_partition_write_commits_symbols_and_idempotent_upsert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection()
    monkeypatch.setattr(mariadb_sink.pymysql, "connect", lambda **_kwargs: connection)

    mariadb_sink.upsert_market_bar_partition([sample_row()], config())

    assert connection.committed
    assert connection.closed
    assert len(connection.fake_cursor.calls) == 2
    assert connection.fake_cursor.calls[0][1] == [("AAPL",)]
    assert "ON DUPLICATE KEY UPDATE" in connection.fake_cursor.calls[1][0]
    assert "certification_status = 'PROVISIONAL'" in connection.fake_cursor.calls[1][0]


def test_partition_write_rolls_back_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = FakeConnection(fail=True)
    monkeypatch.setattr(mariadb_sink.pymysql, "connect", lambda **_kwargs: connection)

    with pytest.raises(RuntimeError, match="database unavailable"):
        mariadb_sink.upsert_market_bar_partition([sample_row()], config())

    assert connection.rolled_back
    assert connection.closed
    assert not connection.committed


def test_empty_partition_does_not_connect(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected_connect(**_kwargs: object) -> None:
        raise AssertionError("empty partitions must not open a database connection")

    monkeypatch.setattr(mariadb_sink.pymysql, "connect", unexpected_connect)

    mariadb_sink.upsert_market_bar_partition([], config())
