"""Opt-in Docker-backed checks for the Phase 5 Airflow boundary."""

import os
import subprocess

import pytest

pytestmark = pytest.mark.integration


def compose(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "compose", *arguments],
        check=check,
        capture_output=True,
        text=True,
        timeout=180,
    )


@pytest.mark.skipif(
    os.environ.get("MARKETPILOT_RUN_AIRFLOW_INTEGRATION") != "1",
    reason="set MARKETPILOT_RUN_AIRFLOW_INTEGRATION=1 to inspect the Airflow runtime",
)
def test_dags_import_and_streaming_survives_scheduler_restart() -> None:
    import_errors = compose(
        "exec",
        "-T",
        "airflow-scheduler",
        "airflow",
        "dags",
        "list-import-errors",
    )
    assert "No data found" in import_errors.stdout

    compose("stop", "airflow-scheduler")
    try:
        streaming_id = compose("ps", "-q", "spark-streaming").stdout.strip()
        assert streaming_id
        running = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", streaming_id],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert running.stdout.strip() == "true"
    finally:
        compose("start", "airflow-scheduler")
