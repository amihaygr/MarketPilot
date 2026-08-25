from datetime import date

import pytest

from marketpilot.batch.mariadb import publish_certified_partition
from marketpilot.streaming.mariadb_sink import MariaDbConfig


class FakeCursor:
    def __init__(self, watermark: tuple[str, str]) -> None:
        self.watermark = watermark

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, _sql: str, _parameters: object = None) -> None:
        return None

    def fetchone(self) -> tuple[str, str]:
        return self.watermark


class FakeConnection:
    def __init__(self, watermark: tuple[str, str]) -> None:
        self.fake_cursor = FakeCursor(watermark)
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


def test_certified_publication_rolls_back_when_quality_watermark_failed(monkeypatch) -> None:
    run_id = "76c538c2-21f1-4fc7-9353-fcfbced0fa22"
    connection = FakeConnection(("FAILED", run_id))
    monkeypatch.setattr("marketpilot.batch.mariadb._connect", lambda _config: connection)

    with pytest.raises(RuntimeError, match="DQ watermark"):
        publish_certified_partition(
            MariaDbConfig("mariadb", 3306, "marketpilot", "publisher", "secret"),
            run_id,
            date(2026, 8, 22),
            ("non_empty",),
        )

    assert connection.rolled_back
    assert not connection.committed
    assert connection.closed
