"""Opt-in Docker-backed Phase 4 Medallion and certification checks."""

import os
import subprocess
from uuid import uuid4

import pytest

pytestmark = pytest.mark.integration


def compose(*arguments: str, timeout: int = 300, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "compose", *arguments],
        check=check,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def run_batch(job: str, *arguments: str, check: bool = True) -> subprocess.CompletedProcess:
    return compose(
        "run",
        "--rm",
        "--no-deps",
        "spark-batch",
        "/opt/spark/bin/spark-submit",
        "--master",
        "spark://spark-master:7077",
        "--conf",
        "spark.cores.max=2",
        f"/opt/marketpilot/spark/jobs/{job}",
        *arguments,
        check=check,
    )


def database_scalar(query: str) -> int:
    completed = compose(
        "exec",
        "-T",
        "mariadb",
        "sh",
        "-c",
        f'mariadb -N -uroot -p"$MARIADB_ROOT_PASSWORD" -D marketpilot -e "{query}"',
    )
    return int(completed.stdout.strip())


@pytest.mark.skipif(
    os.environ.get("MARKETPILOT_RUN_BATCH_INTEGRATION") != "1",
    reason="set MARKETPILOT_RUN_BATCH_INTEGRATION=1 to run bounded Spark Batch checks",
)
def test_batch_partition_is_certified_idempotently_and_failed_gate_blocks() -> None:
    logical_date = os.environ.get("MARKETPILOT_BATCH_TEST_DATE", "2026-08-22")
    run_id = str(uuid4())
    common = ("--logical-date", logical_date, "--run-id", run_id)
    run_batch("bronze_to_silver.py", *common)
    run_batch(
        "validate_silver.py",
        *common,
        "--expected-bars-per-symbol",
        "1",
        "--maximum-ingestion-lag-seconds",
        "300",
    )
    run_batch("silver_to_gold.py", *common)

    certified_before = database_scalar(
        "SELECT COUNT(*) FROM fact_market_bar_1m "
        f"WHERE DATE(event_time_utc)='{logical_date}' AND certification_status='CERTIFIED';"
    )
    assert certified_before > 0

    run_batch("bronze_to_silver.py", *common)
    run_batch(
        "validate_silver.py",
        *common,
        "--expected-bars-per-symbol",
        "1",
        "--maximum-ingestion-lag-seconds",
        "300",
    )
    run_batch("silver_to_gold.py", *common)
    certified_after = database_scalar(
        "SELECT COUNT(*) FROM fact_market_bar_1m "
        f"WHERE DATE(event_time_utc)='{logical_date}' AND certification_status='CERTIFIED';"
    )
    assert certified_after == certified_before

    failed_run_id = str(uuid4())
    failed_common = ("--logical-date", logical_date, "--run-id", failed_run_id)
    failed_quality = run_batch(
        "validate_silver.py",
        *failed_common,
        "--expected-bars-per-symbol",
        "1000000",
        check=False,
    )
    assert failed_quality.returncode != 0
    blocked_publication = run_batch("silver_to_gold.py", *failed_common, check=False)
    assert blocked_publication.returncode != 0
    assert (
        database_scalar(
            "SELECT COUNT(*) FROM etl_watermark "
            "WHERE pipeline_name='market-bars-certified-publication' "
            f"AND partition_key='{logical_date}' AND run_id='{failed_run_id}';"
        )
        == 0
    )
