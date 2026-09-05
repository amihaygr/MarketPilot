"""Fetch, transport, and verify one bounded Alpaca historical market session."""

import json
import logging
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID

import boto3
from botocore.exceptions import ClientError
from confluent_kafka import Producer

from marketpilot.batch.market_calendar import (
    is_xnys_regular_market_minute,
    xnys_session_bounds,
)
from marketpilot.bronze.keys import market_bar_bronze_key
from marketpilot.contracts.market_bar import MarketBarV1
from marketpilot.historical.archive import (
    archive_source_page,
    read_manifest,
    write_manifest,
)
from marketpilot.historical.client import AlpacaHistoricalClient, HistoricalPage
from marketpilot.historical.settings import HistoricalSettings
from marketpilot.sources.alpaca import build_alpaca_market_bar

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RawHistoricalBar:
    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


@dataclass(frozen=True, slots=True)
class KafkaPosition:
    topic: str
    partition: int
    offset: int
    event: dict[str, Any]


class KafkaMessageLike(Protocol):
    def topic(self) -> str: ...

    def partition(self) -> int: ...

    def offset(self) -> int: ...


class ProducerLike(Protocol):
    def produce(self, topic: str, **kwargs: Any) -> None: ...

    def poll(self, timeout: float) -> int: ...

    def flush(self, timeout: float | None = None) -> int: ...


def parse_historical_pages(
    pages: list[HistoricalPage],
    *,
    requested_symbols: tuple[str, ...],
    feed: str,
) -> tuple[MarketBarV1, ...]:
    """Validate API pages and return one deterministic event per business key."""
    requested = set(requested_symbols)
    events: dict[tuple[str, datetime], MarketBarV1] = {}
    for page in pages:
        bars_by_symbol = page.decoded["bars"]
        for raw_symbol, raw_bars in bars_by_symbol.items():
            symbol = str(raw_symbol).upper()
            if symbol not in requested:
                raise ValueError(f"Alpaca returned an unrequested symbol: {symbol}")
            if not isinstance(raw_bars, list):
                raise ValueError("Alpaca bars entries must be arrays")
            for payload in raw_bars:
                if not isinstance(payload, dict):
                    raise ValueError("Alpaca bar must be a JSON object")
                timestamp = datetime.fromisoformat(str(payload["t"]).replace("Z", "+00:00"))
                raw = RawHistoricalBar(
                    symbol=symbol,
                    timestamp=timestamp,
                    open=Decimal(str(payload["o"])),
                    high=Decimal(str(payload["h"])),
                    low=Decimal(str(payload["l"])),
                    close=Decimal(str(payload["c"])),
                    volume=int(payload["v"]),
                )
                event = build_alpaca_market_bar(raw, feed=feed)
                if not is_xnys_regular_market_minute(event.event_time_utc):
                    continue
                key = (event.symbol, event.event_time_utc)
                previous = events.get(key)
                if previous is not None and previous != event:
                    raise ValueError(
                        f"conflicting Alpaca bar for {event.symbol} {event.event_time_utc}"
                    )
                events[key] = event
    return tuple(sorted(events.values(), key=lambda event: (event.symbol, event.event_time_utc)))


def publish_historical_events(
    producer: ProducerLike,
    *,
    topic: str,
    events: tuple[MarketBarV1, ...],
    ingested_at_utc: datetime,
) -> tuple[KafkaPosition, ...]:
    positions: list[KafkaPosition] = []
    delivery_errors: list[str] = []
    for bar in events:
        event = bar.to_event(ingested_at_utc)

        def delivered(
            error: object | None,
            message: KafkaMessageLike,
            *,
            delivered_event: dict[str, Any] = event,
        ) -> None:
            if error is not None:
                delivery_errors.append(str(error))
                return
            positions.append(
                KafkaPosition(
                    topic=message.topic(),
                    partition=message.partition(),
                    offset=message.offset(),
                    event=delivered_event,
                )
            )

        payload = json.dumps(event, separators=(",", ":"))
        while True:
            try:
                producer.produce(
                    topic,
                    key=bar.symbol,
                    value=payload,
                    on_delivery=delivered,
                )
                break
            except BufferError:
                producer.poll(1.0)
        producer.poll(0.0)
    undelivered = producer.flush(30)
    if undelivered or delivery_errors or len(positions) != len(events):
        raise RuntimeError(
            "historical Kafka delivery failed "
            f"events={len(events)} positions={len(positions)} undelivered={undelivered} "
            f"errors={len(delivery_errors)}"
        )
    return tuple(sorted(positions, key=lambda position: (position.partition, position.offset)))


def wait_for_bronze_archive(
    s3: Any,
    *,
    bucket: str,
    positions: tuple[KafkaPosition, ...],
    timeout_seconds: float,
    poll_seconds: float,
    clock: Any = time.monotonic,
    sleep: Any = time.sleep,
) -> tuple[str, ...]:
    """Block Spark publication until raw-archive-sink persisted every Kafka position."""
    outstanding = {
        market_bar_bronze_key(
            position.event,
            position.topic,
            position.partition,
            position.offset,
        )
        for position in positions
    }
    all_keys = tuple(sorted(outstanding))
    deadline = clock() + timeout_seconds
    while outstanding:
        for key in tuple(outstanding):
            try:
                s3.head_object(Bucket=bucket, Key=key)
                outstanding.remove(key)
            except ClientError as error:
                status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
                code = error.response.get("Error", {}).get("Code")
                if status != 404 and code not in {"404", "NoSuchKey", "NotFound"}:
                    raise
        if not outstanding:
            return all_keys
        if clock() >= deadline:
            raise TimeoutError(
                f"Bronze archive barrier timed out with {len(outstanding)} Kafka records missing"
            )
        sleep(poll_seconds)
    return all_keys


def backfill_historical_session(
    settings: HistoricalSettings,
    *,
    logical_date: date,
    symbols: tuple[str, ...],
    run_id: UUID,
    client: AlpacaHistoricalClient | None = None,
    producer: ProducerLike | None = None,
    s3: Any | None = None,
) -> dict[str, object]:
    """Acquire one closed session and prove its Kafka records reached Bronze."""
    normalized = tuple(sorted({symbol.strip().upper() for symbol in symbols if symbol.strip()}))
    if not normalized:
        raise ValueError("historical backfill requires at least one symbol")
    unknown = set(normalized) - set(settings.configured_symbols)
    if unknown:
        raise ValueError(f"historical symbols outside MARKET_SYMBOLS: {','.join(sorted(unknown))}")
    start_utc, end_utc = xnys_session_bounds(logical_date)
    if end_utc >= datetime.now(UTC):
        raise ValueError("historical backfill requires a closed XNYS session")
    object_store = s3 or boto3.client(
        "s3",
        endpoint_url=settings.minio_endpoint,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
    )
    existing = read_manifest(
        object_store,
        bucket=settings.bronze_bucket,
        run_id=str(run_id),
        logical_date=logical_date,
    )
    if existing is not None:
        if existing.get("symbols") != list(normalized) or existing.get("feed") != settings.feed:
            raise ValueError("existing historical manifest scope does not match the retry")
        return {
            "status": "already_archived",
            "run_id": str(run_id),
            "logical_date": logical_date.isoformat(),
            "events": int(existing["events"]),
        }

    api = client or AlpacaHistoricalClient(
        base_url=settings.base_url,
        api_key=settings.api_key,
        api_secret=settings.api_secret,
        feed=settings.feed,
        timeout_seconds=settings.request_timeout_seconds,
        max_attempts=settings.request_max_attempts,
        requests_per_second=settings.max_requests_per_second,
        page_limit=settings.page_limit,
    )
    pages = list(api.pages(symbols=normalized, start_utc=start_utc, end_utc=end_utc))
    page_digests: list[str] = []
    for page in pages:
        _key, digest = archive_source_page(
            object_store,
            bucket=settings.bronze_bucket,
            logical_date=logical_date,
            feed=settings.feed,
            payload=page.payload,
        )
        page_digests.append(digest)
    events = parse_historical_pages(pages, requested_symbols=normalized, feed=settings.feed)
    if not events:
        raise RuntimeError("Alpaca historical response contains no regular-session market bars")
    kafka = producer or Producer(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "enable.idempotence": True,
            "acks": "all",
            "client.id": f"marketpilot-historical-{run_id}",
        }
    )
    ingested_at = datetime.now(UTC)
    positions = publish_historical_events(
        kafka,
        topic=settings.kafka_topic,
        events=events,
        ingested_at_utc=ingested_at,
    )
    bronze_keys = wait_for_bronze_archive(
        object_store,
        bucket=settings.bronze_bucket,
        positions=positions,
        timeout_seconds=settings.bronze_wait_timeout_seconds,
        poll_seconds=settings.bronze_poll_seconds,
    )
    rows_by_symbol: dict[str, int] = {}
    for event in events:
        rows_by_symbol[event.symbol] = rows_by_symbol.get(event.symbol, 0) + 1
    manifest: dict[str, object] = {
        "status": "ARCHIVED",
        "schema_version": 1,
        "run_id": str(run_id),
        "logical_date": logical_date.isoformat(),
        "feed": settings.feed,
        "symbols": list(normalized),
        "events": len(events),
        "rows_by_symbol": rows_by_symbol,
        "source_page_sha256": sorted(page_digests),
        "bronze_keys": list(bronze_keys),
        "ingested_at_utc": ingested_at.isoformat(),
    }
    manifest_path = write_manifest(
        object_store,
        bucket=settings.bronze_bucket,
        run_id=str(run_id),
        logical_date=logical_date,
        manifest=manifest,
    )
    summary = {
        "status": "archived",
        "run_id": str(run_id),
        "logical_date": logical_date.isoformat(),
        "source_pages": len(pages),
        "events": len(events),
        "rows_by_symbol": rows_by_symbol,
        "manifest_key": manifest_path,
    }
    logger.info("historical session archived %s", json.dumps(summary, separators=(",", ":")))
    return summary


def backfill_historical_session_from_env(
    *,
    logical_date: str,
    symbols: list[str],
    run_id: str,
) -> dict[str, object]:
    return backfill_historical_session(
        HistoricalSettings.from_env(),
        logical_date=date.fromisoformat(logical_date),
        symbols=tuple(symbols),
        run_id=UUID(run_id),
    )
