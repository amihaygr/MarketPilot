from datetime import UTC, date, datetime
from typing import Any

from fastapi.testclient import TestClient

from marketpilot.serving.settings import ServingSettings
from services.backend_api.main import create_app


class FakeReadRepository:
    def __init__(self) -> None:
        self.market_query: dict[str, Any] | None = None

    def ready(self) -> bool:
        return True

    def list_symbols(self) -> list[dict[str, Any]]:
        return [
            {
                "symbol": "AAPL",
                "display_name": "Apple Inc.",
                "is_active": True,
                "market_bar_count": 1,
                "latest_bar_time_utc": datetime(2026, 8, 26, 14, 30, tzinfo=UTC),
                "latest_certification_status": "PROVISIONAL",
            }
        ]

    def list_market_bars(self, **parameters: Any) -> dict[str, Any]:
        self.market_query = parameters
        return {
            "items": [
                {
                    "symbol": "AAPL",
                    "event_time_utc": datetime(2026, 8, 26, 14, 30, tzinfo=UTC),
                    "interval": "1Min",
                    "open": "230.10",
                    "high": "230.50",
                    "low": "230.00",
                    "close": "230.40",
                    "volume": 1000,
                    "certification_status": "PROVISIONAL",
                    "source": "alpaca",
                    "ingested_at_utc": datetime(2026, 8, 26, 14, 30, 2, tzinfo=UTC),
                    "data_version": "market-bar-v1",
                    "schema_version": 1,
                }
            ],
            "pagination": {"page": 1, "page_size": 50, "total": 1, "total_pages": 1},
        }

    def list_sec_filings(self, **_parameters: Any) -> dict[str, Any]:
        return {
            "items": [
                {
                    "accession_number": "0000320193-26-000001",
                    "symbol": "AAPL",
                    "company_name": "Apple Inc.",
                    "form_type": "8-K",
                    "filing_date": date(2026, 8, 20),
                    "report_date": date(2026, 8, 20),
                    "acceptance_datetime_utc": datetime(2026, 8, 20, 21, 0, tzinfo=UTC),
                    "primary_document": "filing.htm",
                    "primary_document_description": "Current report",
                    "source_url": "https://www.sec.gov/Archives/example",
                    "ingested_at_utc": datetime(2026, 8, 20, 21, 1, tzinfo=UTC),
                    "schema_version": 1,
                }
            ],
            "pagination": {"page": 1, "page_size": 50, "total": 1, "total_pages": 1},
        }

    def list_indicators(self, **_parameters: Any) -> dict[str, Any]:
        return {
            "items": [
                {
                    "symbol": "AAPL",
                    "event_time_utc": datetime(2026, 8, 26, 14, 30, tzinfo=UTC),
                    "indicator_code": "RSI_14",
                    "indicator_version": 1,
                    "value": "42.125",
                    "lookback_bars": 14,
                    "certification_status": "PROVISIONAL",
                    "data_version": "market-analytics-v1",
                    "schema_version": 1,
                }
            ],
            "pagination": {"page": 1, "page_size": 100, "total": 1, "total_pages": 1},
        }

    def list_signals(self, **_parameters: Any) -> dict[str, Any]:
        return {
            "items": [
                {
                    "symbol": "AAPL",
                    "signal_time_utc": datetime(2026, 8, 26, 14, 30, tzinfo=UTC),
                    "signal_code": "VOLUME_SPIKE",
                    "model_version": 1,
                    "direction": "WATCH",
                    "strength": "0.4",
                    "explanation": "Volume is at least 2x its prior 20-bar mean; ratio=3.2",
                    "certification_status": "PROVISIONAL",
                    "data_version": "market-signals-v1",
                    "schema_version": 1,
                }
            ],
            "pagination": {"page": 1, "page_size": 25, "total": 1, "total_pages": 1},
        }

    def list_backtest_runs(self, **_parameters: Any) -> dict[str, Any]:
        return {
            "items": [self._backtest_run()],
            "pagination": {"page": 1, "page_size": 20, "total": 1, "total_pages": 1},
        }

    def get_backtest_run(self, *, run_id: str) -> dict[str, Any] | None:
        if run_id != "11111111-1111-4111-8111-111111111111":
            return None
        return {
            "run": self._backtest_run(),
            "results": [
                {
                    "symbol": "AAPL",
                    "first_event_time_utc": datetime(2026, 8, 21, 14, 30, tzinfo=UTC),
                    "last_event_time_utc": datetime(2026, 8, 24, 20, 0, tzinfo=UTC),
                    "observation_count": 500,
                    "trade_count": 4,
                    "total_return_pct": "2.5",
                    "benchmark_return_pct": "1.5",
                    "excess_return_pct": "1.0",
                    "max_drawdown_pct": "-0.8",
                    "annualized_volatility_pct": "12.4",
                    "sharpe_ratio": "1.2",
                }
            ],
        }

    def list_backtest_equity(self, *, run_id: str, symbol: str) -> list[dict[str, Any]]:
        assert run_id == "11111111-1111-4111-8111-111111111111"
        assert symbol == "AAPL"
        return [
            {
                "symbol": "AAPL",
                "trading_date": date(2026, 8, 24),
                "event_time_utc": datetime(2026, 8, 24, 20, 0, tzinfo=UTC),
                "equity": "10250",
                "benchmark_equity": "10150",
                "drawdown_pct": "-0.2",
                "applied_position": 1,
            }
        ]

    @staticmethod
    def _backtest_run() -> dict[str, Any]:
        return {
            "run_id": "11111111-1111-4111-8111-111111111111",
            "strategy_code": "SMA_CROSS_LONG_CASH",
            "strategy_version": 1,
            "start_date": date(2026, 8, 21),
            "end_date": date(2026, 8, 24),
            "symbols": ["AAPL"],
            "benchmark_symbol": "SPY",
            "short_window": 20,
            "long_window": 50,
            "initial_capital": "10000",
            "transaction_cost_bps": "1",
            "slippage_bps": "1",
            "status": "PUBLISHED",
            "schema_version": 1,
            "started_at_utc": datetime(2026, 8, 25, 1, 0, tzinfo=UTC),
            "completed_at_utc": datetime(2026, 8, 25, 1, 1, tzinfo=UTC),
        }

    def freshness(self, *, code_version: str, generated_at_utc: datetime) -> dict[str, Any]:
        return {
            "generated_at_utc": generated_at_utc,
            "market": {
                "latest_event_time_utc": datetime(2026, 8, 26, 14, 30, tzinfo=UTC),
                "latest_ingested_at_utc": datetime(2026, 8, 26, 14, 30, 2, tzinfo=UTC),
                "bar_count": 1,
                "provisional_count": 1,
                "certified_count": 0,
                "latest_certification_status": "PROVISIONAL",
            },
            "sec": {
                "latest_filing_date": date(2026, 8, 20),
                "latest_ingested_at_utc": datetime(2026, 8, 20, 21, 1, tzinfo=UTC),
                "filing_count": 1,
            },
            "symbols": [
                {
                    "symbol": "AAPL",
                    "latest_event_time_utc": datetime(2026, 8, 26, 14, 30, tzinfo=UTC),
                    "latest_ingested_at_utc": datetime(2026, 8, 26, 14, 30, 2, tzinfo=UTC),
                    "latest_certification_status": "PROVISIONAL",
                }
            ],
            "pipelines": [],
            "code_version": code_version,
        }


def settings() -> ServingSettings:
    return ServingSettings.from_environ(
        {
            "MARIADB_HOST": "mariadb",
            "MARIADB_DATABASE": "marketpilot",
            "MARIADB_APP_USER": "marketpilot_app",
            "MARIADB_APP_PASSWORD": "secret",
            "API_CORS_ORIGINS": "http://localhost:3000",
            "MARKETPILOT_CODE_VERSION": "test",
        }
    )


def test_health_symbols_and_cors_are_read_only() -> None:
    repository = FakeReadRepository()
    client = TestClient(create_app(settings(), repository))

    assert client.get("/health/live").json()["status"] == "alive"
    assert client.get("/health/ready").json()["status"] == "ready"
    symbols = client.get("/api/v1/symbols", headers={"Origin": "http://localhost:3000"})
    assert symbols.status_code == 200
    assert symbols.json()["items"][0]["symbol"] == "AAPL"
    assert symbols.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert client.post("/api/v1/symbols").status_code == 405


def test_market_bars_enforce_filters_pagination_and_aware_bounds() -> None:
    repository = FakeReadRepository()
    client = TestClient(create_app(settings(), repository))
    response = client.get(
        "/api/v1/market-bars",
        params={
            "symbol": "AAPL",
            "start_utc": "2026-08-20T00:00:00Z",
            "end_utc": "2026-08-27T00:00:00Z",
            "certification_status": "PROVISIONAL",
        },
    )

    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == 1
    assert repository.market_query is not None
    assert repository.market_query["symbol"] == "AAPL"
    assert repository.market_query["certification_status"] == "PROVISIONAL"
    assert (
        client.get(
            "/api/v1/market-bars",
            params={
                "symbol": "AAPL",
                "start_utc": "2026-01-01T00:00:00Z",
                "end_utc": "2026-08-27T00:00:00Z",
            },
        ).status_code
        == 422
    )
    assert client.get("/api/v1/market-bars", params={"symbol": "bad symbol"}).status_code == 422
    assert (
        client.get("/api/v1/market-bars", params={"symbol": "AAPL", "page_size": 201}).status_code
        == 422
    )


def test_sec_and_freshness_responses_hide_storage_credentials() -> None:
    client = TestClient(create_app(settings(), FakeReadRepository()))

    filing = client.get("/api/v1/sec-filings").json()["items"][0]
    freshness = client.get("/api/v1/freshness").json()

    assert filing["source_url"].startswith("https://www.sec.gov/")
    assert "bronze_uri" not in filing
    assert freshness["market"]["latest_certification_status"] == "PROVISIONAL"
    assert freshness["code_version"] == "test"


def test_analytics_endpoints_are_bounded_versioned_and_read_only() -> None:
    client = TestClient(create_app(settings(), FakeReadRepository()))
    parameters = {
        "symbol": "AAPL",
        "start_utc": "2026-08-20T00:00:00Z",
        "end_utc": "2026-08-27T00:00:00Z",
    }
    indicator = client.get("/api/v1/indicators", params=parameters)
    signal = client.get("/api/v1/signals", params=parameters)

    assert indicator.status_code == 200
    assert indicator.json()["items"][0]["indicator_code"] == "RSI_14"
    assert indicator.json()["items"][0]["schema_version"] == 1
    assert signal.status_code == 200
    assert signal.json()["items"][0]["direction"] == "WATCH"
    assert client.post("/api/v1/signals").status_code == 405
    invalid = dict(parameters, indicator_code="DROP_TABLE")
    assert client.get("/api/v1/indicators", params=invalid).status_code == 422


def test_backtest_endpoints_are_read_only_bounded_and_hide_internal_storage() -> None:
    client = TestClient(create_app(settings(), FakeReadRepository()))
    run_id = "11111111-1111-4111-8111-111111111111"
    runs = client.get("/api/v1/backtests")
    detail = client.get(f"/api/v1/backtests/{run_id}")
    equity = client.get(f"/api/v1/backtests/{run_id}/equity", params={"symbol": "AAPL"})

    assert runs.status_code == 200
    assert detail.status_code == 200
    assert detail.json()["results"][0]["benchmark_return_pct"] == "1.5"
    assert "detailed_output_uri" not in detail.text
    assert equity.status_code == 200
    assert equity.json()["total"] == 1
    assert client.get("/api/v1/backtests/not-a-uuid").status_code == 422
    invalid_symbol = client.get(
        f"/api/v1/backtests/{run_id}/equity",
        params={"symbol": "bad symbol"},
    )
    assert invalid_symbol.status_code == 422
    assert client.post("/api/v1/backtests").status_code == 405
