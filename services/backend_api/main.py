"""FastAPI entrypoint for read-only MarketPilot Gold data."""

from __future__ import annotations

import json
import logging
from datetime import UTC, date, datetime
from time import perf_counter
from uuid import UUID, uuid4

import pymysql
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from marketpilot.serving.repository import MariaDbReadRepository, ReadRepository
from marketpilot.serving.schemas import (
    ApiIndexResponse,
    BacktestEquityResponse,
    BacktestRunDetail,
    BacktestRunPage,
    FreshnessResponse,
    HealthResponse,
    IndicatorPage,
    MarketBarPage,
    SecFilingPage,
    SignalPage,
    SymbolListResponse,
)
from marketpilot.serving.settings import ServingSettings
from marketpilot.serving.validation import QueryRangeError, filing_date_range, market_time_range

logger = logging.getLogger("marketpilot.backend_api")
MAX_PAGE = 1_000
MAX_PAGE_SIZE = 200


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in (
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "error_type",
            "error_code",
        ):
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        return json.dumps(payload, separators=(",", ":"))


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


def create_app(
    settings: ServingSettings | None = None,
    repository: ReadRepository | None = None,
) -> FastAPI:
    resolved_settings = settings or ServingSettings.from_environ()
    resolved_repository = repository or MariaDbReadRepository(resolved_settings)
    app = FastAPI(
        title="MarketPilot Backend API",
        version="1.0.0",
        description="Read-only, bounded access to MarketPilot MariaDB Gold data.",
    )
    app.state.settings = resolved_settings
    app.state.repository = resolved_repository
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved_settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["Accept", "Content-Type", "X-Request-ID"],
    )

    @app.middleware("http")
    async def request_observability(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID", str(uuid4()))[:128]
        request.state.request_id = request_id
        started = perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round((perf_counter() - started) * 1000, 2),
            },
        )
        return response

    @app.exception_handler(pymysql.MySQLError)
    async def database_error(request: Request, error: pymysql.MySQLError) -> JSONResponse:
        logger.error(
            "database request failed",
            extra={
                "request_id": getattr(request.state, "request_id", "unknown"),
                "error_type": type(error).__name__,
                "error_code": error.args[0] if error.args else "unknown",
            },
        )
        return JSONResponse(status_code=503, content={"detail": "serving database unavailable"})

    @app.get("/", response_model=ApiIndexResponse, tags=["service"])
    def index() -> ApiIndexResponse:
        return ApiIndexResponse()

    @app.get("/health/live", response_model=HealthResponse, tags=["health"])
    def live() -> HealthResponse:
        return HealthResponse(status="alive")

    @app.get("/health/ready", response_model=HealthResponse, tags=["health"])
    def ready() -> HealthResponse:
        if not resolved_repository.ready():
            raise HTTPException(status_code=503, detail="serving database unavailable")
        return HealthResponse(status="ready")

    @app.get("/api/v1/symbols", response_model=SymbolListResponse, tags=["market"])
    def symbols() -> SymbolListResponse:
        items = resolved_repository.list_symbols()
        return SymbolListResponse(items=items, total=len(items))

    @app.get("/api/v1/market-bars", response_model=MarketBarPage, tags=["market"])
    def market_bars(
        symbol: str = Query(pattern=r"^[A-Z][A-Z0-9.-]{0,15}$"),
        start_utc: datetime | None = None,
        end_utc: datetime | None = None,
        certification_status: str | None = Query(
            default=None,
            pattern=r"^(PROVISIONAL|CERTIFIED)$",
        ),
        page: int = Query(default=1, ge=1, le=MAX_PAGE),
        page_size: int = Query(default=50, ge=1, le=MAX_PAGE_SIZE),
    ) -> MarketBarPage:
        try:
            start, end = market_time_range(
                start_utc,
                end_utc,
                now_utc=datetime.now(UTC),
                max_days=resolved_settings.max_market_range_days,
            )
        except QueryRangeError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        result = resolved_repository.list_market_bars(
            symbol=symbol,
            start_utc=start,
            end_utc=end,
            certification_status=certification_status,
            page=page,
            page_size=page_size,
        )
        return MarketBarPage.model_validate(result)

    @app.get("/api/v1/sec-filings", response_model=SecFilingPage, tags=["sec"])
    def sec_filings(
        symbol: str | None = Query(default=None, pattern=r"^[A-Z][A-Z0-9.-]{0,15}$"),
        form_type: str | None = Query(default=None, pattern=r"^[A-Z0-9-]{1,32}$"),
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = Query(default=1, ge=1, le=MAX_PAGE),
        page_size: int = Query(default=50, ge=1, le=MAX_PAGE_SIZE),
    ) -> SecFilingPage:
        try:
            start, end = filing_date_range(
                start_date,
                end_date,
                today=datetime.now(UTC).date(),
                max_days=resolved_settings.max_filing_range_days,
            )
        except QueryRangeError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        result = resolved_repository.list_sec_filings(
            symbol=symbol,
            form_type=form_type,
            start_date=start,
            end_date=end,
            page=page,
            page_size=page_size,
        )
        return SecFilingPage.model_validate(result)

    @app.get("/api/v1/indicators", response_model=IndicatorPage, tags=["analytics"])
    def indicators(
        symbol: str = Query(pattern=r"^[A-Z][A-Z0-9.-]{0,15}$"),
        start_utc: datetime | None = None,
        end_utc: datetime | None = None,
        indicator_code: str | None = Query(
            default=None,
            pattern=r"^(SMA_20|RSI_14|REALIZED_VOLATILITY_20|VOLUME_RATIO_20)$",
        ),
        page: int = Query(default=1, ge=1, le=MAX_PAGE),
        page_size: int = Query(default=100, ge=1, le=MAX_PAGE_SIZE),
    ) -> IndicatorPage:
        try:
            start, end = market_time_range(
                start_utc,
                end_utc,
                now_utc=datetime.now(UTC),
                max_days=resolved_settings.max_market_range_days,
            )
        except QueryRangeError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return IndicatorPage.model_validate(
            resolved_repository.list_indicators(
                symbol=symbol,
                start_utc=start,
                end_utc=end,
                indicator_code=indicator_code,
                page=page,
                page_size=page_size,
            )
        )

    @app.get("/api/v1/signals", response_model=SignalPage, tags=["analytics"])
    def signals(
        symbol: str | None = Query(default=None, pattern=r"^[A-Z][A-Z0-9.-]{0,15}$"),
        start_utc: datetime | None = None,
        end_utc: datetime | None = None,
        direction: str | None = Query(default=None, pattern=r"^(BULLISH|BEARISH|WATCH)$"),
        page: int = Query(default=1, ge=1, le=MAX_PAGE),
        page_size: int = Query(default=25, ge=1, le=MAX_PAGE_SIZE),
    ) -> SignalPage:
        try:
            start, end = market_time_range(
                start_utc,
                end_utc,
                now_utc=datetime.now(UTC),
                max_days=resolved_settings.max_market_range_days,
            )
        except QueryRangeError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return SignalPage.model_validate(
            resolved_repository.list_signals(
                symbol=symbol,
                start_utc=start,
                end_utc=end,
                direction=direction,
                page=page,
                page_size=page_size,
            )
        )

    @app.get("/api/v1/backtests", response_model=BacktestRunPage, tags=["backtesting"])
    def backtest_runs(
        page: int = Query(default=1, ge=1, le=MAX_PAGE),
        page_size: int = Query(default=20, ge=1, le=100),
    ) -> BacktestRunPage:
        return BacktestRunPage.model_validate(
            resolved_repository.list_backtest_runs(page=page, page_size=page_size)
        )

    @app.get(
        "/api/v1/backtests/{run_id}",
        response_model=BacktestRunDetail,
        tags=["backtesting"],
    )
    def backtest_detail(run_id: str) -> BacktestRunDetail:
        try:
            normalized_run_id = str(UUID(run_id))
        except ValueError as error:
            raise HTTPException(status_code=422, detail="run_id must be a UUID") from error
        result = resolved_repository.get_backtest_run(run_id=normalized_run_id)
        if result is None:
            raise HTTPException(status_code=404, detail="backtest run not found")
        return BacktestRunDetail.model_validate(result)

    @app.get(
        "/api/v1/backtests/{run_id}/equity",
        response_model=BacktestEquityResponse,
        tags=["backtesting"],
    )
    def backtest_equity(
        run_id: str,
        symbol: str = Query(pattern=r"^[A-Z][A-Z0-9.-]{0,15}$"),
    ) -> BacktestEquityResponse:
        try:
            normalized_run_id = str(UUID(run_id))
        except ValueError as error:
            raise HTTPException(status_code=422, detail="run_id must be a UUID") from error
        items = resolved_repository.list_backtest_equity(
            run_id=normalized_run_id,
            symbol=symbol,
        )
        return BacktestEquityResponse(items=items, total=len(items))

    @app.get("/api/v1/freshness", response_model=FreshnessResponse, tags=["service"])
    def freshness() -> FreshnessResponse:
        result = resolved_repository.freshness(
            code_version=resolved_settings.code_version,
            generated_at_utc=datetime.now(UTC),
        )
        return FreshnessResponse.model_validate(result)

    return app


configure_logging()
