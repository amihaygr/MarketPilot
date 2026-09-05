import json
from datetime import UTC, date, datetime
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

from botocore.exceptions import ClientError

from marketpilot.historical.archive import archive_source_page, read_manifest, write_manifest
from marketpilot.historical.client import AlpacaHistoricalClient, HistoricalPage
from marketpilot.historical.ingestion import (
    KafkaPosition,
    parse_historical_pages,
    publish_historical_events,
    wait_for_bronze_archive,
)
from marketpilot.sources.alpaca import build_alpaca_market_bar


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = json.dumps(payload).encode()

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


class FakeS3:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}

    def head_object(self, *, Bucket: str, Key: str) -> dict[str, object]:
        if (Bucket, Key) not in self.objects:
            raise ClientError(
                {"Error": {"Code": "404"}, "ResponseMetadata": {"HTTPStatusCode": 404}},
                "HeadObject",
            )
        return {}

    def put_object(self, *, Bucket: str, Key: str, Body: bytes, **_kwargs: object) -> None:
        self.objects[(Bucket, Key)] = Body

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, object]:
        return {"Body": SimpleNamespace(read=lambda: self.objects[(Bucket, Key)])}


def _page(*bars: dict[str, object]) -> HistoricalPage:
    decoded = {"bars": {"AAPL": list(bars)}, "next_page_token": None}
    return HistoricalPage(json.dumps(decoded).encode(), decoded, 1)


def test_client_follows_page_token_and_sends_credentials_only_in_headers() -> None:
    requests = []
    responses = iter(
        [
            FakeResponse({"bars": {"AAPL": []}, "next_page_token": "next"}),
            FakeResponse({"bars": {"AAPL": []}, "next_page_token": None}),
        ]
    )

    def opener(request, **_kwargs):  # type: ignore[no-untyped-def]
        requests.append(request)
        return next(responses)

    client = AlpacaHistoricalClient(
        base_url="https://data.alpaca.markets/v2/stocks/bars",
        api_key="key",
        api_secret="secret",
        feed="iex",
        timeout_seconds=10,
        max_attempts=1,
        requests_per_second=10,
        page_limit=10000,
        opener=opener,
        sleep=lambda _delay: None,
    )
    pages = list(
        client.pages(
            symbols=("AAPL",),
            start_utc=datetime(2026, 8, 24, 13, 30, tzinfo=UTC),
            end_utc=datetime(2026, 8, 24, 20, 0, tzinfo=UTC),
        )
    )

    assert len(pages) == 2
    assert parse_qs(urlparse(requests[1].full_url).query)["page_token"] == ["next"]
    assert "secret" not in requests[0].full_url
    assert requests[0].get_header("Apca-api-secret-key") == "secret"


def test_historical_normalization_matches_live_identity_and_filters_extended_hours() -> None:
    regular = {"t": "2026-08-24T13:30:00Z", "o": 100, "h": 102, "l": 99, "c": 101, "v": 50}
    extended = {"t": "2026-08-24T12:00:00Z", "o": 90, "h": 91, "l": 89, "c": 90, "v": 5}
    events = parse_historical_pages(
        [_page(regular, extended)], requested_symbols=("AAPL",), feed="iex"
    )
    live_equivalent = build_alpaca_market_bar(
        SimpleNamespace(
            symbol="AAPL",
            timestamp=datetime(2026, 8, 24, 13, 30, tzinfo=UTC),
            open=100,
            high=102,
            low=99,
            close=101,
            volume=50,
        ),
        feed="iex",
    )
    assert events == (live_equivalent,)


def test_publish_collects_exact_kafka_positions() -> None:
    event = parse_historical_pages(
        [_page({"t": "2026-08-24T13:30:00Z", "o": 100, "h": 102, "l": 99, "c": 101, "v": 50})],
        requested_symbols=("AAPL",),
        feed="iex",
    )[0]

    class Producer:
        def produce(self, topic: str, **kwargs: object) -> None:
            message = SimpleNamespace(topic=lambda: topic, partition=lambda: 2, offset=lambda: 7)
            kwargs["on_delivery"](None, message)  # type: ignore[operator]

        def poll(self, _timeout: float) -> int:
            return 0

        def flush(self, _timeout: float | None = None) -> int:
            return 0

    positions = publish_historical_events(
        Producer(),
        topic="market.bars.1m.backfill.v1",
        events=(event,),
        ingested_at_utc=datetime(2026, 9, 5, tzinfo=UTC),
    )
    assert [(position.partition, position.offset) for position in positions] == [(2, 7)]


def test_bronze_barrier_and_manifest_are_retry_safe() -> None:
    s3 = FakeS3()
    event = {
        "source": "alpaca",
        "symbol": "AAPL",
        "event_time_utc": "2026-08-24T13:30:00+00:00",
    }
    position = KafkaPosition("market.bars.1m.backfill.v1", 0, 3, event)
    expected_key = (
        "source=alpaca/event=market_bar_1m/year=2026/month=08/day=24/"
        "symbol=AAPL/topic=market.bars.1m.backfill.v1/partition=0/offset=3.json"
    )
    s3.objects[("bronze", expected_key)] = b"{}"
    assert wait_for_bronze_archive(
        s3,
        bucket="bronze",
        positions=(position,),
        timeout_seconds=1,
        poll_seconds=0.1,
    ) == (expected_key,)

    first_key, first_digest = archive_source_page(
        s3, bucket="bronze", logical_date=date(2026, 8, 24), feed="iex", payload=b'{"bars":{}}'
    )
    second_key, second_digest = archive_source_page(
        s3, bucket="bronze", logical_date=date(2026, 8, 24), feed="iex", payload=b'{"bars":{}}'
    )
    assert (first_key, first_digest) == (second_key, second_digest)

    write_manifest(
        s3,
        bucket="bronze",
        run_id="run-1",
        logical_date=date(2026, 8, 24),
        manifest={"status": "ARCHIVED", "events": 1},
    )
    assert (
        read_manifest(s3, bucket="bronze", run_id="run-1", logical_date=date(2026, 8, 24))["events"]
        == 1
    )
