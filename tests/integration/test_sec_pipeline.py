"""Opt-in Docker-backed SEC Bronze and Gold idempotency verification."""

import os
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[2]
MOCK_NAME = "marketpilot-sec-mock"


def command(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(arguments),
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
        timeout=180,
    )


def compose(*arguments: str) -> subprocess.CompletedProcess[str]:
    return command("docker", "compose", *arguments)


def run_mocked_poll() -> None:
    compose(
        "exec",
        "-T",
        "-e",
        "SEC_POLL_ENABLED=true",
        "-e",
        "SEC_BASE_URL=http://marketpilot-sec-mock:8080",
        "-e",
        "SEC_ALLOW_INSECURE_HTTP=true",
        "-e",
        "SEC_USER_AGENT=MarketPilot integration@example.com",
        "-e",
        "SEC_COMPANY_CIKS=AAPL:0000320193",
        "-e",
        "SEC_FORMS=10-Q,8-K",
        "airflow-scheduler",
        "python",
        "-m",
        "marketpilot.sec.polling",
        "--run-id",
        str(uuid4()),
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


def archived_sec_object_count() -> int:
    script = (
        "import os,boto3;"
        "client=boto3.client('s3',"
        "endpoint_url=os.environ['MINIO_ENDPOINT'],"
        "aws_access_key_id=os.environ['MINIO_ROOT_USER'],"
        "aws_secret_access_key=os.environ['MINIO_ROOT_PASSWORD']);"
        "print(client.list_objects_v2("
        "Bucket=os.environ.get('MINIO_BRONZE_BUCKET','marketpilot-bronze'),"
        "Prefix='source=sec/event=submissions/').get('KeyCount',0))"
    )
    result = compose("exec", "-T", "airflow-scheduler", "python", "-c", script)
    return int(result.stdout.strip())


@pytest.mark.skipif(
    os.environ.get("MARKETPILOT_RUN_SEC_INTEGRATION") != "1",
    reason="set MARKETPILOT_RUN_SEC_INTEGRATION=1 to run the local SEC boundary check",
)
def test_sec_payload_is_archived_and_accessions_are_idempotent() -> None:
    fixture_root = ROOT / "tests" / "fixtures" / "sec"
    command("docker", "rm", "-f", MOCK_NAME, check=False)
    command(
        "docker",
        "run",
        "--rm",
        "-d",
        "--name",
        MOCK_NAME,
        "--network",
        "marketpilot_data-plane",
        "-v",
        f"{fixture_root}:/data:ro",
        "-w",
        "/data",
        "python:3.12-slim",
        "python",
        "-m",
        "http.server",
        "8080",
        "--bind",
        "0.0.0.0",
    )
    try:
        run_mocked_poll()
        run_mocked_poll()

        assert (
            database_scalar(
                "SELECT COUNT(*) FROM fact_sec_filing "
                "WHERE accession_number='0000320193-26-000079';"
            )
            == 1
        )
        assert database_scalar("SELECT COUNT(*) FROM fact_sec_filing;") >= 2
        assert archived_sec_object_count() >= 1
    finally:
        command("docker", "rm", "-f", MOCK_NAME, check=False)
