"""Deterministic Bronze keys shared by archive writers and barriers."""

from datetime import datetime
from typing import Any


def market_bar_bronze_key(
    event: dict[str, Any],
    topic: str,
    partition: int,
    offset: int,
) -> str:
    event_time = datetime.fromisoformat(str(event["event_time_utc"]))
    return (
        f"source={event['source']}/event=market_bar_1m/"
        f"year={event_time:%Y}/month={event_time:%m}/day={event_time:%d}/"
        f"symbol={event['symbol']}/topic={topic}/partition={partition}/offset={offset}.json"
    )
