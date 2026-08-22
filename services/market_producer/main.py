"""Publish deterministic synthetic minute bars for the Phase 2 vertical slice."""

import json
import logging
import time
from datetime import UTC, datetime
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

from confluent_kafka import Producer

from marketpilot.contracts.market_bar import MarketBarV1
from marketpilot.core.settings import Settings

logger = logging.getLogger(__name__)


def build_synthetic_bar(symbol: str, event_time_utc: datetime, interval: str) -> MarketBarV1:
    minute = event_time_utc.replace(second=0, microsecond=0)
    seed = sum(ord(character) for character in symbol)
    open_price = Decimal(100 + seed % 400).quantize(Decimal("0.01"))
    return MarketBarV1(
        event_id=uuid5(NAMESPACE_URL, f"marketpilot:{symbol}:{minute.isoformat()}:{interval}"),
        symbol=symbol,
        event_time_utc=minute,
        interval=interval,
        open=open_price,
        high=open_price + Decimal("0.50"),
        low=open_price - Decimal("0.50"),
        close=open_price + Decimal("0.10"),
        volume=1000 + seed,
        source="synthetic",
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='{"level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
    )
    settings = Settings.from_env()
    producer = Producer(
        {"bootstrap.servers": settings.kafka_bootstrap_servers, "enable.idempotence": True}
    )
    try:
        while True:
            event_time = datetime.now(UTC)
            for symbol in settings.symbols:
                event = build_synthetic_bar(
                    symbol, event_time, settings.market_bar_interval
                ).to_event()
                producer.produce(
                    settings.market_bars_topic,
                    key=symbol,
                    value=json.dumps(event, separators=(",", ":")),
                )
            producer.flush(10)
            logger.info("published synthetic batch symbols=%d", len(settings.symbols))
            time.sleep(settings.synthetic_publish_seconds)
    finally:
        producer.flush(10)


if __name__ == "__main__":
    main()
