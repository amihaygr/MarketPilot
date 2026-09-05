"""Normalize Alpaca bar models into the canonical MarketBarV1 contract."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Protocol
from uuid import NAMESPACE_URL, uuid5

from marketpilot.contracts.market_bar import MarketBarV1


class AlpacaBarLike(Protocol):
    symbol: str
    timestamp: datetime
    open: Any
    high: Any
    low: Any
    close: Any
    volume: int


def build_alpaca_market_bar(
    bar: AlpacaBarLike,
    *,
    feed: str,
    interval: str = "1Min",
) -> MarketBarV1:
    """Create one deterministic canonical event shared by live and historical paths."""
    timestamp = bar.timestamp
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("Alpaca bar timestamp must be timezone-aware")
    minute = timestamp.astimezone(UTC).replace(second=0, microsecond=0)
    symbol = str(bar.symbol).upper()
    event_id = uuid5(
        NAMESPACE_URL,
        f"marketpilot:alpaca:{feed}:{symbol}:{minute.isoformat()}:{interval}",
    )
    return MarketBarV1(
        event_id=event_id,
        symbol=symbol,
        event_time_utc=minute,
        interval=interval,
        open=Decimal(str(bar.open)),
        high=Decimal(str(bar.high)),
        low=Decimal(str(bar.low)),
        close=Decimal(str(bar.close)),
        volume=int(bar.volume),
        source="alpaca",
    )
