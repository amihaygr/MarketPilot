"""Versioned canonical contract for a one-minute market bar."""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class MarketBarV1:
    event_id: UUID
    symbol: str
    event_time_utc: datetime
    interval: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    source: str = "alpaca"
    schema_version: int = 1

    def validate(self) -> None:
        if self.event_time_utc.tzinfo is None or self.event_time_utc.utcoffset() is None:
            raise ValueError("event_time_utc must be timezone-aware")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be greater than or equal to OHLC values")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be less than or equal to OHLC values")
        if self.volume < 0:
            raise ValueError("volume must be non-negative")
        if not self.symbol or self.symbol != self.symbol.upper():
            raise ValueError("symbol must be non-empty uppercase text")

    def to_event(self, ingested_at_utc: datetime | None = None) -> dict[str, Any]:
        self.validate()
        ingested_at = ingested_at_utc or datetime.now(UTC)
        payload = asdict(self)
        payload.update(
            {
                "event_id": str(self.event_id),
                "event_time_utc": self.event_time_utc.isoformat(),
                "ingested_at_utc": ingested_at.isoformat(),
                "open": str(self.open),
                "high": str(self.high),
                "low": str(self.low),
                "close": str(self.close),
            }
        )
        return payload

    @classmethod
    def from_event(cls, event: dict[str, Any]) -> "MarketBarV1":
        """Parse and validate a serialized V1 event."""
        if event.get("schema_version") != 1:
            raise ValueError("schema_version must be 1")
        bar = cls(
            event_id=UUID(str(event["event_id"])),
            symbol=str(event["symbol"]),
            event_time_utc=datetime.fromisoformat(str(event["event_time_utc"])),
            interval=str(event["interval"]),
            open=Decimal(str(event["open"])),
            high=Decimal(str(event["high"])),
            low=Decimal(str(event["low"])),
            close=Decimal(str(event["close"])),
            volume=int(event["volume"]),
            source=str(event["source"]),
            schema_version=int(event["schema_version"]),
        )
        bar.validate()
        return bar
