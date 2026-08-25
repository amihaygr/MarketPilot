"""Resilient Alpaca minute-bar stream normalized to MarketBarV1."""

import logging
import os
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from threading import Event
from typing import Any, Protocol
from uuid import NAMESPACE_URL, uuid5

from marketpilot.batch.market_calendar import is_xnys_regular_market_minute
from marketpilot.contracts.market_bar import MarketBarV1
from marketpilot.core.settings import Settings
from services.market_producer.publishing import ProducerLike, publish_event

logger = logging.getLogger(__name__)


class AlpacaBarLike(Protocol):
    symbol: str
    timestamp: datetime
    open: Any
    high: Any
    low: Any
    close: Any
    volume: int


class StockStreamLike(Protocol):
    def subscribe_bars(self, handler: Callable[..., Any], *symbols: str) -> None: ...

    def run(self) -> None: ...

    def stop(self) -> None: ...


StreamFactory = Callable[[Settings], StockStreamLike]


def default_stream_factory(settings: Settings) -> StockStreamLike:
    """Create the official SDK client lazily so synthetic mode needs no credentials."""
    from alpaca.data.enums import DataFeed
    from alpaca.data.live import StockDataStream

    return StockDataStream(
        os.environ["ALPACA_API_KEY"],
        os.environ["ALPACA_API_SECRET"],
        feed=DataFeed(settings.alpaca_data_feed),
        data_timeout=settings.alpaca_data_timeout_seconds,
        websocket_params={"ping_interval": 10, "ping_timeout": 30, "max_queue": 1024},
    )


def build_alpaca_bar(bar: AlpacaBarLike, settings: Settings) -> MarketBarV1:
    timestamp = bar.timestamp
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("Alpaca bar timestamp must be timezone-aware")
    minute = timestamp.astimezone(UTC).replace(second=0, microsecond=0)
    symbol = str(bar.symbol).upper()
    event_id = uuid5(
        NAMESPACE_URL,
        f"marketpilot:alpaca:{settings.alpaca_data_feed}:{symbol}:"
        f"{minute.isoformat()}:{settings.market_bar_interval}",
    )
    return MarketBarV1(
        event_id=event_id,
        symbol=symbol,
        event_time_utc=minute,
        interval=settings.market_bar_interval,
        open=Decimal(str(bar.open)),
        high=Decimal(str(bar.high)),
        low=Decimal(str(bar.low)),
        close=Decimal(str(bar.close)),
        volume=int(bar.volume),
        source="alpaca",
    )


def reconnect_delay(settings: Settings, failure_number: int) -> float:
    return min(
        settings.alpaca_reconnect_initial_seconds * (2 ** max(0, failure_number - 1)),
        settings.alpaca_reconnect_max_seconds,
    )


class AlpacaRunner:
    def __init__(
        self,
        settings: Settings,
        producer: ProducerLike,
        *,
        stop_event: Event | None = None,
        stream_factory: StreamFactory = default_stream_factory,
    ) -> None:
        self.settings = settings
        self.producer = producer
        self.stop_event = stop_event or Event()
        self.stream_factory = stream_factory
        self.current_stream: StockStreamLike | None = None

    def stop(self) -> None:
        self.stop_event.set()
        if self.current_stream is not None:
            self.current_stream.stop()

    def run(self) -> None:
        consecutive_failures = 0
        while not self.stop_event.is_set():
            received_bar = False
            try:
                stream = self.stream_factory(self.settings)
                self.current_stream = stream

                async def on_bar(raw_bar: AlpacaBarLike) -> None:
                    nonlocal received_bar
                    bar = build_alpaca_bar(raw_bar, self.settings)
                    if not is_xnys_regular_market_minute(bar.event_time_utc):
                        logger.info(
                            "ignored Alpaca bar outside regular session symbol=%s timestamp=%s",
                            bar.symbol,
                            bar.event_time_utc.isoformat(),
                        )
                        return
                    publish_event(
                        self.producer,
                        self.settings.market_bars_topic,
                        bar.to_event(),
                    )
                    received_bar = True

                stream.subscribe_bars(on_bar, *self.settings.symbols)
                logger.info(
                    "starting Alpaca stream feed=%s symbols=%d",
                    self.settings.alpaca_data_feed,
                    len(self.settings.symbols),
                )
                stream.run()
                if not self.stop_event.is_set():
                    raise RuntimeError("Alpaca stream stopped unexpectedly")
            except Exception:
                if self.stop_event.is_set():
                    break
                consecutive_failures = 1 if received_bar else consecutive_failures + 1
                delay = reconnect_delay(self.settings, consecutive_failures)
                logger.exception(
                    "Alpaca stream failed; reconnecting attempt=%d delay_seconds=%s",
                    consecutive_failures,
                    delay,
                )
                self.stop_event.wait(delay)
            finally:
                self.current_stream = None
                self.producer.flush(10)
