"""Opt-in Docker-backed Phase 7 API, UI, and privilege-boundary verification."""

import json
import os
import subprocess
from urllib.request import urlopen

import pytest

pytestmark = pytest.mark.integration


def compose(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "compose", *arguments],
        check=True,
        capture_output=True,
        text=True,
        timeout=180,
    )


@pytest.mark.skipif(
    os.environ.get("MARKETPILOT_RUN_SERVING_INTEGRATION") != "1",
    reason="set MARKETPILOT_RUN_SERVING_INTEGRATION=1 to inspect the serving runtime",
)
def test_api_ui_and_read_only_identity() -> None:
    with urlopen("http://localhost:8000/health/ready", timeout=10) as response:
        assert json.load(response)["status"] == "ready"
    with urlopen("http://localhost:8000/api/v1/symbols", timeout=10) as response:
        symbols = json.load(response)
    assert symbols["total"] > 0
    with urlopen("http://localhost:3000/", timeout=10) as response:
        html = response.read().decode("utf-8")
    assert "MarketPilot" in html
    assert "MARIADB_APP_PASSWORD" not in html
    assert "MINIO_ROOT_PASSWORD" not in html
    assert "ALPACA_API_SECRET" not in html
    probe = compose(
        "exec",
        "-T",
        "backend-api",
        "python",
        "-m",
        "services.backend_api.permission_probe",
    )
    assert json.loads(probe.stdout) == {"read_allowed": True, "write_denied": True}
