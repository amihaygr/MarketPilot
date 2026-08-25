"""Run the configured long-lived synthetic or Alpaca market-data producer."""

import logging
import signal
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from threading import Event
from uuid import NAMESPACE_URL, uuid5

from confluent_kafka import Producer

from marketpilot.contracts.market_bar import MarketBarV1
from marketpilot.core.settings import Settings
from services.market_producer.publishing import publish_event

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


def run_synthetic(settings: Settings, producer: Producer, stop_event: Event) -> None:
    while not stop_event.is_set():
        event_time = datetime.now(UTC)
        for symbol in settings.symbols:
            event = build_synthetic_bar(symbol, event_time, settings.market_bar_interval).to_event()
            publish_event(producer, settings.market_bars_topic, event)
        producer.flush(10)
        logger.info("published synthetic batch symbols=%d", len(settings.symbols))
        stop_event.wait(settings.synthetic_publish_seconds)


def install_signal_handlers(stop: Callable[[], None]) -> None:
    def handle_signal(_signum: int, _frame: object) -> None:
        logger.info("market producer shutdown requested")
        stop()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='{"level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
    )
    settings = Settings.from_env()
    producer = Producer(
        {"bootstrap.servers": settings.kafka_bootstrap_servers, "enable.idempotence": True}
    )
    stop_event = Event()
    try:
        if settings.market_data_source == "synthetic":
            install_signal_handlers(stop_event.set)
            run_synthetic(settings, producer, stop_event)
        else:
            from services.market_producer.alpaca import AlpacaRunner

            runner = AlpacaRunner(settings, producer, stop_event=stop_event)
            install_signal_handlers(runner.stop)
            runner.run()
    finally:
        producer.flush(10)


if __name__ == "__main__":
    main()
