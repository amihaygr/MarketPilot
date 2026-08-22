from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from marketpilot.contracts.market_bar import MarketBarV1


def make_bar(**overrides: object) -> MarketBarV1:
    values = {
        "event_id": uuid4(),
        "symbol": "SPY",
        "event_time_utc": datetime(2026, 8, 21, 14, 30, tzinfo=UTC),
        "interval": "1Min",
        "open": Decimal("640.10"),
        "high": Decimal("641.00"),
        "low": Decimal("639.80"),
        "close": Decimal("640.50"),
        "volume": 1200,
    }
    values.update(overrides)
    return MarketBarV1(**values)  # type: ignore[arg-type]


def test_valid_bar_serializes_versioned_event() -> None:
    event = make_bar().to_event()
    assert event["schema_version"] == 1
    assert event["symbol"] == "SPY"
    assert event["event_time_utc"].endswith("+00:00")


def test_invalid_ohlc_is_rejected() -> None:
    with pytest.raises(ValueError, match="high"):
        make_bar(high=Decimal("639.00")).validate()


def test_serialized_event_round_trip() -> None:
    bar = make_bar()
    restored = MarketBarV1.from_event(bar.to_event())
    assert restored == bar


def test_unknown_schema_version_is_rejected() -> None:
    event = make_bar().to_event()
    event["schema_version"] = 2
    with pytest.raises(ValueError, match="schema_version"):
        MarketBarV1.from_event(event)
