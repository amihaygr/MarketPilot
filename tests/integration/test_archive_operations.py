"""Opt-in Docker-backed Phase 8 compaction, archive, and restore checks."""

import os
import subprocess
from datetime import UTC, datetime
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


def run_spark(job: str, *arguments: str) -> subprocess.CompletedProcess[str]:
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
    )


def database_scalar(query: str) -> int:
    result = compose(
        "exec",
        "-T",
        "mariadb",
        "sh",
        "-c",
        f'mariadb -N -uroot -p"$MARIADB_ROOT_PASSWORD" -D marketpilot -e "{query}"',
    )
    return int(result.stdout.strip())


@pytest.mark.skipif(
    os.environ.get("MARKETPILOT_RUN_OPERATIONS_INTEGRATION") != "1",
    reason="set MARKETPILOT_RUN_OPERATIONS_INTEGRATION=1 to run Phase 8 boundaries",
)
def test_compaction_archive_and_sample_restore() -> None:
    logical_date = os.environ.get("MARKETPILOT_COMPACTION_TEST_DATE", "2026-08-25")
    compaction_run = str(uuid4())
    rows_before = database_scalar(
        f"SELECT COUNT(*) FROM fact_market_bar_1m WHERE DATE(event_time_utc)='{logical_date}';"
    )
    run_spark(
        "compact_silver.py",
        "--through-date",
        logical_date,
        "--lookback-days",
        "1",
        "--run-id",
        compaction_run,
    )
    assert (
        database_scalar(
            f"SELECT COUNT(*) FROM fact_market_bar_1m WHERE DATE(event_time_utc)='{logical_date}';"
        )
        == rows_before
    )

    archive_year = datetime.now(UTC).year
    archive_run = str(uuid4())
    run_spark(
        "archive_market_bars.py",
        "--archive-year",
        str(archive_year),
        "--archive-version",
        "1",
        "--run-id",
        archive_run,
        "--validation-snapshot",
    )
    assert (
        database_scalar(
            "SELECT COUNT(*) FROM archive_manifest "
            "WHERE dataset_name='fact_market_bar_1m_validation_snapshot' "
            f"AND archive_year={archive_year} AND archive_version=1;"
        )
        == 1
    )

    restore_run = str(uuid4())
    run_spark(
        "restore_archive_sample.py",
        "--dataset-name",
        "fact_market_bar_1m_validation_snapshot",
        "--archive-year",
        str(archive_year),
        "--archive-version",
        "1",
        "--restore-run-id",
        restore_run,
        "--sample-size",
        "25",
    )
    assert (
        database_scalar(
            "SELECT sample_row_count FROM archive_restore_result "
            f"WHERE restore_run_id='{restore_run}';"
        )
        == 25
    )
