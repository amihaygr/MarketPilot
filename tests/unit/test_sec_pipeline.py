import json
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.error import URLError
from uuid import uuid4

import pytest

from marketpilot.sec.client import RateLimiter, SecClient
from marketpilot.sec.parsing import latest_filing_date, parse_recent_filings
from marketpilot.sec.settings import parse_company_ciks

FIXTURE = Path("tests/fixtures/sec/submissions/CIK0000320193.json")


class FakeResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


def test_company_cik_mapping_is_normalized_and_sorted() -> None:
    assert parse_company_ciks("msft:789019,AAPL:0000320193") == (
        ("AAPL", "0000320193"),
        ("MSFT", "0000789019"),
    )


def test_rate_limiter_enforces_five_requests_per_second() -> None:
    now = [100.0]
    sleeps: list[float] = []

    def clock() -> float:
        return now[0]

    def sleep(seconds: float) -> None:
        sleeps.append(seconds)
        now[0] += seconds

    limiter = RateLimiter(5, clock=clock, sleep=sleep)
    limiter.wait()
    limiter.wait()
    limiter.wait()

    assert sleeps == pytest.approx([0.2, 0.2])


def test_sec_client_retries_transient_network_failure() -> None:
    body = FIXTURE.read_bytes()
    attempts = [URLError("temporary"), FakeResponse(body)]
    sleeps: list[float] = []

    def opener(*_args: object, **_kwargs: object) -> FakeResponse:
        result = attempts.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    client = SecClient(
        base_url="https://data.sec.gov",
        user_agent="MarketPilot engineering@example.com",
        requests_per_second=5,
        timeout_seconds=5,
        max_attempts=2,
        opener=opener,
        sleep=sleeps.append,
    )
    _url, payload, decoded = client.company_submissions("0000320193")

    assert payload == body
    assert decoded["name"] == "Apple Inc."
    assert 1 in sleeps


def test_recent_filings_are_filtered_and_versioned() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    run_id = uuid4()
    filings = parse_recent_filings(
        payload,
        symbol="AAPL",
        cik="0000320193",
        forms=frozenset({"10-Q", "8-K"}),
        bronze_uri="s3://marketpilot-bronze/object.json",
        source_sha256="a" * 64,
        pipeline_run_id=run_id,
        code_version="test",
        ingested_at_utc=datetime(2026, 8, 26, tzinfo=UTC),
    )

    assert len(filings) == 2
    assert {filing.form_type for filing in filings} == {"10-Q", "8-K"}
    assert filings[0].schema_version == 1
    assert filings[0].pipeline_run_id == run_id
    assert filings[0].acceptance_datetime_utc == datetime(2026, 7, 31, 20, 1, 10, tzinfo=UTC)
    assert latest_filing_date(payload, date(2020, 1, 1)) == date(2026, 7, 31)


def test_sec_contract_rejects_non_hex_digest() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    filing = parse_recent_filings(
        payload,
        symbol="AAPL",
        cik="0000320193",
        forms=frozenset({"10-Q"}),
        bronze_uri="s3://marketpilot-bronze/object.json",
        source_sha256="a" * 64,
        pipeline_run_id=uuid4(),
        code_version="test",
        ingested_at_utc=datetime(2026, 8, 26, tzinfo=UTC),
    )[0]

    invalid = replace(filing, source_sha256="z" * 64)

    with pytest.raises(ValueError, match="SHA-256"):
        invalid.validate()
