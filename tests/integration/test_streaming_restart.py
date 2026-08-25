"""Docker-backed Phase 3 recovery check.

Run explicitly with MARKETPILOT_RUN_INTEGRATION=1 pytest tests/integration.
"""

import os
import subprocess
import time

import pytest

pytestmark = pytest.mark.integration


def compose(*arguments: str, timeout: int = 60) -> str:
    completed = subprocess.run(
        ["docker", "compose", *arguments],
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return completed.stdout.strip()


def gold_counts() -> tuple[int, int]:
    query = (
        "SELECT COUNT(*), COUNT(DISTINCT CONCAT(symbol_id, '|', event_time_utc, '|', "
        "bar_interval)) FROM marketpilot.fact_market_bar_1m;"
    )
    output = compose(
        "exec",
        "-T",
        "mariadb",
        "sh",
        "-c",
        f'mariadb -N -uroot -p"$MARIADB_ROOT_PASSWORD" -e "{query}"',
    )
    total, distinct = output.split("\t")
    return int(total), int(distinct)


def wait_for_healthy(timeout_seconds: int = 180) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        container_id = compose("ps", "-q", "spark-streaming")
        if container_id:
            status = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Health.Status}}", container_id],
                check=True,
                capture_output=True,
                text=True,
                timeout=15,
            ).stdout.strip()
            if status == "healthy":
                return
        time.sleep(5)
    raise AssertionError("spark-streaming did not become healthy")


@pytest.mark.skipif(
    os.environ.get("MARKETPILOT_RUN_INTEGRATION") != "1",
    reason="set MARKETPILOT_RUN_INTEGRATION=1 to run Docker recovery checks",
)
def test_streaming_restart_preserves_checkpoint_and_business_uniqueness() -> None:
    wait_for_healthy()
    before_total, before_distinct = gold_counts()
    assert before_total > 0
    assert before_total == before_distinct

    checkpoint_before = compose(
        "exec",
        "-T",
        "spark-streaming",
        "sh",
        "-c",
        "find /checkpoints/market-bars-v2 -type f | sort",
    )
    assert "/gold/offsets/" in checkpoint_before

    compose("restart", "spark-streaming", timeout=120)
    wait_for_healthy()

    after_total, after_distinct = gold_counts()
    assert after_total >= before_total
    assert after_total == after_distinct
    checkpoint_after = compose(
        "exec",
        "-T",
        "spark-streaming",
        "sh",
        "-c",
        "find /checkpoints/market-bars-v2 -type f | sort",
    )
    before_files = set(checkpoint_before.splitlines())
    after_files = set(checkpoint_after.splitlines())
    assert before_files.issubset(after_files)
