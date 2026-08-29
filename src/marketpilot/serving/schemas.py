"""Versioned, storage-safe response models for the Backend API."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthResponse(ApiModel):
    status: Literal["alive", "ready"]
    service: Literal["marketpilot-backend-api"] = "marketpilot-backend-api"


class ApiIndexResponse(ApiModel):
    name: str = "MarketPilot Backend API"
    api_version: str = "v1"
    docs_url: str = "/docs"
    health_url: str = "/health/ready"


class SymbolRead(ApiModel):
    symbol: str
    display_name: str | None
    is_active: bool
    market_bar_count: int = Field(ge=0)
    latest_bar_time_utc: datetime | None
    latest_certification_status: Literal["PROVISIONAL", "CERTIFIED"] | None


class SymbolListResponse(ApiModel):
    items: list[SymbolRead]
    total: int = Field(ge=0)


class PageMetadata(ApiModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=200)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class MarketBarRead(ApiModel):
    symbol: str
    event_time_utc: datetime
    interval: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int = Field(ge=0)
    certification_status: Literal["PROVISIONAL", "CERTIFIED"]
    source: str
    ingested_at_utc: datetime
    data_version: str
    schema_version: int = Field(ge=1)


class MarketBarPage(ApiModel):
    items: list[MarketBarRead]
    pagination: PageMetadata


class IndicatorRead(ApiModel):
    symbol: str
    event_time_utc: datetime
    indicator_code: Literal["SMA_20", "RSI_14", "REALIZED_VOLATILITY_20", "VOLUME_RATIO_20"]
    indicator_version: int = Field(ge=1)
    value: Decimal
    lookback_bars: int = Field(ge=1)
    certification_status: Literal["PROVISIONAL", "CERTIFIED"]
    data_version: str
    schema_version: int = Field(ge=1)


class IndicatorPage(ApiModel):
    items: list[IndicatorRead]
    pagination: PageMetadata


class SignalRead(ApiModel):
    symbol: str
    signal_time_utc: datetime
    signal_code: Literal[
        "PRICE_CROSS_ABOVE_SMA20",
        "PRICE_CROSS_BELOW_SMA20",
        "RSI_CROSS_OVERSOLD",
        "RSI_CROSS_OVERBOUGHT",
        "VOLUME_SPIKE",
    ]
    model_version: int = Field(ge=1)
    direction: Literal["BULLISH", "BEARISH", "WATCH"]
    strength: Decimal = Field(ge=0, le=1)
    explanation: str
    certification_status: Literal["PROVISIONAL", "CERTIFIED"]
    data_version: str
    schema_version: int = Field(ge=1)


class SignalPage(ApiModel):
    items: list[SignalRead]
    pagination: PageMetadata


class BacktestRunRead(ApiModel):
    run_id: str
    strategy_code: Literal["SMA_CROSS_LONG_CASH"]
    strategy_version: int = Field(ge=1)
    start_date: date
    end_date: date
    symbols: list[str]
    benchmark_symbol: str
    short_window: int = Field(ge=2)
    long_window: int = Field(ge=3)
    initial_capital: Decimal = Field(gt=0)
    transaction_cost_bps: Decimal = Field(ge=0)
    slippage_bps: Decimal = Field(ge=0)
    status: Literal["RUNNING", "PUBLISHED", "FAILED"]
    schema_version: int = Field(ge=1)
    started_at_utc: datetime
    completed_at_utc: datetime | None


class BacktestRunPage(ApiModel):
    items: list[BacktestRunRead]
    pagination: PageMetadata


class BacktestResultRead(ApiModel):
    symbol: str
    first_event_time_utc: datetime
    last_event_time_utc: datetime
    observation_count: int = Field(gt=0)
    trade_count: int = Field(ge=0)
    total_return_pct: Decimal
    benchmark_return_pct: Decimal
    excess_return_pct: Decimal
    max_drawdown_pct: Decimal = Field(le=0)
    annualized_volatility_pct: Decimal = Field(ge=0)
    sharpe_ratio: Decimal | None


class BacktestRunDetail(ApiModel):
    run: BacktestRunRead
    results: list[BacktestResultRead]


class BacktestEquityRead(ApiModel):
    symbol: str
    trading_date: date
    event_time_utc: datetime
    equity: Decimal = Field(gt=0)
    benchmark_equity: Decimal = Field(gt=0)
    drawdown_pct: Decimal = Field(le=0)
    applied_position: Literal[0, 1]


class BacktestEquityResponse(ApiModel):
    items: list[BacktestEquityRead]
    total: int = Field(ge=0)


class SecFilingRead(ApiModel):
    accession_number: str
    symbol: str
    company_name: str
    form_type: str
    filing_date: date
    report_date: date | None
    acceptance_datetime_utc: datetime | None
    primary_document: str
    primary_document_description: str | None
    source_url: str
    ingested_at_utc: datetime
    schema_version: int = Field(ge=1)


class SecFilingPage(ApiModel):
    items: list[SecFilingRead]
    pagination: PageMetadata


class PipelineWatermarkRead(ApiModel):
    pipeline_name: str
    partition_key: str
    watermark_utc: datetime | None
    status: Literal["STARTED", "VALIDATED", "PUBLISHED", "FAILED"]
    updated_at_utc: datetime


class SymbolFreshnessRead(ApiModel):
    symbol: str
    latest_event_time_utc: datetime | None
    latest_ingested_at_utc: datetime | None
    latest_certification_status: Literal["PROVISIONAL", "CERTIFIED"] | None


class MarketFreshnessRead(ApiModel):
    latest_event_time_utc: datetime | None
    latest_ingested_at_utc: datetime | None
    bar_count: int = Field(ge=0)
    provisional_count: int = Field(ge=0)
    certified_count: int = Field(ge=0)
    latest_certification_status: Literal["PROVISIONAL", "CERTIFIED"] | None


class SecFreshnessRead(ApiModel):
    latest_filing_date: date | None
    latest_ingested_at_utc: datetime | None
    filing_count: int = Field(ge=0)


class FreshnessResponse(ApiModel):
    generated_at_utc: datetime
    market: MarketFreshnessRead
    sec: SecFreshnessRead
    symbols: list[SymbolFreshnessRead]
    pipelines: list[PipelineWatermarkRead]
    code_version: str
