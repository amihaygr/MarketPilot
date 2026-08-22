import json
from datetime import UTC, datetime

import pytest

from services.market_producer.main import build_synthetic_bar
from services.raw_archive_sink.main import bronze_key, parse_record, quarantine_key


def test_valid_record_has_deterministic_bronze_key() -> None:
    event = build_synthetic_bar("SPY", datetime(2026, 8, 22, 14, 30, tzinfo=UTC), "1Min").to_event()
    parsed = parse_record(json.dumps(event).encode())
    assert bronze_key(parsed, "market.bars.1m.v1", 2, 42) == (
        "source=synthetic/event=market_bar_1m/year=2026/month=08/day=22/"
        "symbol=SPY/topic=market.bars.1m.v1/partition=2/offset=42.json"
    )


def test_invalid_record_is_rejected() -> None:
    with pytest.raises(ValueError, match="JSON object"):
        parse_record(b"[]")


def test_quarantine_key_is_offset_idempotent() -> None:
    assert quarantine_key("topic", 1, 9) == "quarantine/topic=topic/partition=1/offset=9.json"
