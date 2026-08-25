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
