"""Queue resumable 31-day Airflow runs for the Phase 15 history requirement."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from marketpilot.orchestration.history_bootstrap import (  # noqa: E402
    HistoricalWindow,
    plan_historical_windows,
    rolling_month_start,
)

DAG_ID = "historical_market_backfill"


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def request_json(
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = None
    if payload is not None:
        body = json.dumps(payload, separators=(",", ":")).encode()
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310 - local Airflow only
            return json.loads(response.read())
    except HTTPError as error:
        detail = error.read().decode(errors="replace")
        raise RuntimeError(f"Airflow API returned HTTP {error.code}: {detail}") from error


def airflow_token(base_url: str, env: dict[str, str]) -> str:
    response = request_json(
        "POST",
        f"{base_url}/auth/token",
        payload={
            "username": env["AIRFLOW_ADMIN_USERNAME"],
            "password": env["AIRFLOW_ADMIN_PASSWORD"],
        },
    )
    token = str(response.get("access_token", ""))
    if not token:
        raise RuntimeError("Airflow did not return an access token")
    return token


def existing_run(base_url: str, token: str, run_id: str) -> dict[str, Any] | None:
    try:
        return request_json(
            "GET",
            f"{base_url}/api/v2/dags/{DAG_ID}/dagRuns/{quote(run_id, safe='')}",
            token=token,
        )
    except RuntimeError as error:
        if "HTTP 404" in str(error):
            return None
        raise


def queue_window(
    base_url: str,
    token: str,
    window: HistoricalWindow,
    symbols: list[str],
    *,
    retry_failed: bool,
) -> tuple[str, str]:
    run_id = window.run_id
    previous = existing_run(base_url, token, run_id)
    if previous is not None:
        state = str(previous.get("state", "unknown"))
        if state != "failed" or not retry_failed:
            return state, run_id
        run_id = f"{run_id}__retry_{datetime.now(UTC):%Y%m%dT%H%M%SZ}"

    request_json(
        "POST",
        f"{base_url}/api/v2/dags/{DAG_ID}/dagRuns",
        token=token,
        payload={
            "dag_run_id": run_id,
            "logical_date": None,
            "conf": {
                "start_date": window.start_date.isoformat(),
                "end_date": window.end_date.isoformat(),
                "symbols": symbols,
                "benchmark_symbol": "SPY",
                "minimum_coverage_pct": 35,
                "minimum_aggregate_coverage_pct": 80,
                "short_window": 20,
                "long_window": 50,
                "initial_capital": 10000,
                "transaction_cost_bps": 1,
                "slippage_bps": 1,
            },
            "note": "Phase 15 resumable 24-month certified-history bootstrap",
        },
    )
    return "queued", run_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--months", type=int, default=24)
    parser.add_argument("--end-date", type=date.fromisoformat)
    parser.add_argument("--queue", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--airflow-url", default="http://localhost:8080")
    args = parser.parse_args()
    end_date = args.end_date or (datetime.now(UTC).date() - timedelta(days=1))
    start_date = rolling_month_start(end_date, args.months)
    windows = plan_historical_windows(start_date, end_date)

    env = dict(os.environ)
    local_env = ROOT / ".env"
    if local_env.exists():
        env.update(parse_env(local_env))
    symbols = sorted(
        {symbol.strip().upper() for symbol in env["MARKET_SYMBOLS"].split(",") if symbol.strip()}
    )
    if "SPY" not in symbols:
        raise ValueError("MARKET_SYMBOLS must contain SPY")

    print(
        f"Planned {len(windows)} bounded windows: "
        f"{windows[0].start_date} -> {windows[-1].end_date}; symbols={len(symbols)}"
    )
    if not args.queue:
        for window in windows:
            print(f"PLAN {window.run_id}")
        print("Dry run only. Add --queue to create Airflow DAG runs.")
        return

    token = airflow_token(args.airflow_url.rstrip("/"), env)
    counts: dict[str, int] = {}
    for window in windows:
        state, run_id = queue_window(
            args.airflow_url.rstrip("/"),
            token,
            window,
            symbols,
            retry_failed=args.retry_failed,
        )
        counts[state] = counts.get(state, 0) + 1
        print(f"{state.upper():>8} {run_id}")
    print("Summary: " + ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))


if __name__ == "__main__":
    main()
