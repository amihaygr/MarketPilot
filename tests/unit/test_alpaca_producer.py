import asyncio
import json
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

from marketpilot.contracts.market_bar import MarketBarV1
from marketpilot.core.settings import Settings
from services.market_producer.alpaca import AlpacaRunner, build_alpaca_bar, reconnect_delay


def settings() -> Settings:
    return Settings(
        kafka_bootstrap_servers="kafka:9092",
        market_bars_topic="market.bars.1m.v1",
        symbols=("AAPL",),
        market_bar_interval="1Min",
        synthetic_publish_seconds=60,
        market_data_source="alpaca",
        alpaca_data_feed="iex",
        alpaca_data_timeout_seconds=None,
        alpaca_reconnect_initial_seconds=1,
        alpaca_reconnect_max_seconds=8,
    )


def raw_bar(timestamp: datetime) -> SimpleNamespace:
    return SimpleNamespace(
        symbol="aapl",
        timestamp=timestamp,
        open=Decimal("200.00"),
        high=Decimal("201.00"),
        low=Decimal("199.50"),
        close=Decimal("200.50"),
        volume=1234,
    )


class FakeProducer:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def produce(self, _topic: str, **kwargs: object) -> None:
        self.events.append(json.loads(str(kwargs["value"])))

    def poll(self, _timeout: float) -> int:
        return 0

    def flush(self, _timeout: float | None = None) -> int:
        return 0


class FakeStream:
    def __init__(self, bar: SimpleNamespace, stop_event: object) -> None:
        self.bar = bar
        self.stop_event = stop_event
        self.handler = None

    def subscribe_bars(self, handler, *_symbols: str) -> None:  # type: ignore[no-untyped-def]
        self.handler = handler

    def run(self) -> None:
        asyncio.run(self.handler(self.bar))
        self.stop_event.set()

    def stop(self) -> None:
        self.stop_event.set()


def test_alpaca_bar_has_deterministic_contract_identity() -> None:
    timestamp = datetime(2026, 8, 24, 14, 30, 44, tzinfo=UTC)
    first = build_alpaca_bar(raw_bar(timestamp), settings())
    second = build_alpaca_bar(raw_bar(timestamp), settings())

    assert first == second
    assert first.source == "alpaca"
    assert first.event_time_utc == datetime(2026, 8, 24, 14, 30, tzinfo=UTC)
    assert MarketBarV1.from_event(first.to_event()) == first


def test_reconnect_delay_is_exponential_and_capped() -> None:
    assert [reconnect_delay(settings(), attempt) for attempt in range(1, 6)] == [1, 2, 4, 8, 8]


def test_runner_publishes_only_regular_session_bars() -> None:
    from threading import Event

    regular_stop = Event()
    regular_producer = FakeProducer()
    regular = raw_bar(datetime(2026, 8, 24, 14, 30, tzinfo=UTC))
    AlpacaRunner(
        settings(),
        regular_producer,
        stop_event=regular_stop,
        stream_factory=lambda _settings: FakeStream(regular, regular_stop),
    ).run()

    closed_stop = Event()
    closed_producer = FakeProducer()
    weekend = raw_bar(datetime(2026, 8, 22, 14, 30, tzinfo=UTC))
    AlpacaRunner(
        settings(),
        closed_producer,
        stop_event=closed_stop,
        stream_factory=lambda _settings: FakeStream(weekend, closed_stop),
    ).run()

    assert len(regular_producer.events) == 1
    assert closed_producer.events == []
