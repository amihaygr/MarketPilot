"""Opt-in Phase 9 Spark, MariaDB, API, and read-only-boundary verification."""

import json
import os
import subprocess
from urllib.parse import urlencode
from urllib.request import urlopen
from uuid import uuid4

import pytest

pytestmark = pytest.mark.integration


def compose(*arguments: str, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "compose", *arguments],
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


@pytest.mark.skipif(
    os.environ.get("MARKETPILOT_RUN_ANALYTICS_INTEGRATION") != "1",
    reason="set MARKETPILOT_RUN_ANALYTICS_INTEGRATION=1 to run Phase 9 boundaries",
)
def test_analytics_publication_api_and_idempotency() -> None:
    logical_date = os.environ.get("MARKETPILOT_ANALYTICS_TEST_DATE", "2026-08-25")
    command = (
        "run",
        "--rm",
        "--no-deps",
        "spark-batch",
        "/opt/spark/bin/spark-submit",
        "--master",
        "spark://spark-master:7077",
        "--conf",
        "spark.cores.max=2",
        "/opt/marketpilot/spark/jobs/calculate_market_analytics.py",
        "--logical-date",
        logical_date,
        "--run-id",
        str(uuid4()),
    )
    compose(*command)
    first = _analytics_counts(logical_date)
    compose(*command[:-1], str(uuid4()))
    assert _analytics_counts(logical_date) == first
    assert first[0] > 0

    query = urlencode(
        {
            "symbol": "AAPL",
            "start_utc": f"{logical_date}T00:00:00Z",
            "end_utc": f"{logical_date}T23:59:59Z",
            "page_size": 5,
        }
    )
    with urlopen(f"http://localhost:8000/api/v1/indicators?{query}", timeout=10) as response:
        assert json.load(response)["pagination"]["total"] > 0


def _analytics_counts(logical_date: str) -> tuple[int, int]:
    result = compose(
        "exec",
        "-T",
        "mariadb",
        "sh",
        "-c",
        'mariadb -N -uroot -p"$MARIADB_ROOT_PASSWORD" -D marketpilot '
        f"-e \"SELECT COUNT(*) FROM fact_indicator_1m WHERE DATE(event_time_utc)='{logical_date}'; "
        f"SELECT COUNT(*) FROM fact_signal WHERE DATE(signal_time_utc)='{logical_date}';\"",
    )
    values = [int(value) for value in result.stdout.splitlines()]
    return values[0], values[1]
