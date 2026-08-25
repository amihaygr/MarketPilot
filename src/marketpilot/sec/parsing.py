"""Normalize the columnar SEC submissions response into versioned filing records."""

from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from marketpilot.contracts.sec_filing import SecFilingV1


def parse_recent_filings(
    payload: dict[str, Any],
    *,
    symbol: str,
    cik: str,
    forms: frozenset[str],
    bronze_uri: str,
    source_sha256: str,
    pipeline_run_id: UUID,
    code_version: str,
    ingested_at_utc: datetime,
) -> tuple[SecFilingV1, ...]:
    company_name = str(payload["name"]).strip()
    recent = payload["filings"]["recent"]
    if not isinstance(recent, dict):
        raise ValueError("SEC recent filings must be a columnar JSON object")
    accessions = recent.get("accessionNumber")
    if not isinstance(accessions, list):
        raise ValueError("SEC recent filings are missing accessionNumber")

    filings: list[SecFilingV1] = []
    for index, raw_accession in enumerate(accessions):
        form_type = _required_text(recent, "form", index).upper()
        if form_type not in forms:
            continue
        accession = str(raw_accession).strip()
        primary_document = _required_text(recent, "primaryDocument", index)
        filing = SecFilingV1(
            accession_number=accession,
            cik=cik,
            symbol=symbol,
            company_name=company_name,
            form_type=form_type,
            filing_date=date.fromisoformat(_required_text(recent, "filingDate", index)),
            report_date=_optional_date(_column_value(recent, "reportDate", index)),
            acceptance_datetime_utc=_optional_acceptance_datetime(
                _column_value(recent, "acceptanceDateTime", index)
            ),
            primary_document=primary_document,
            primary_document_description=_optional_text(
                _column_value(recent, "primaryDocDescription", index)
            ),
            items=_optional_text(_column_value(recent, "items", index)),
            file_number=_optional_text(_column_value(recent, "fileNumber", index)),
            film_number=_optional_text(_column_value(recent, "filmNumber", index)),
            filing_size=_optional_int(_column_value(recent, "size", index)),
            is_xbrl=_as_bool(_column_value(recent, "isXBRL", index)),
            is_inline_xbrl=_as_bool(_column_value(recent, "isInlineXBRL", index)),
            source_url=_filing_url(cik, accession, primary_document),
            bronze_uri=bronze_uri,
            source_sha256=source_sha256,
            pipeline_run_id=pipeline_run_id,
            code_version=code_version,
            ingested_at_utc=ingested_at_utc,
        )
        filing.validate()
        filings.append(filing)
    return tuple(filings)


def latest_filing_date(payload: dict[str, Any], fallback: date) -> date:
    try:
        filing_dates = payload["filings"]["recent"]["filingDate"]
    except (KeyError, TypeError):
        return fallback
    parsed = [date.fromisoformat(str(value)) for value in filing_dates if value]
    return max(parsed, default=fallback)


def _filing_url(cik: str, accession: str, primary_document: str) -> str:
    compact_accession = accession.replace("-", "")
    return (
        f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{compact_accession}/{primary_document}"
    )


def _column_value(columns: dict[str, Any], name: str, index: int) -> Any:
    values = columns.get(name)
    if not isinstance(values, list) or index >= len(values):
        return None
    return values[index]


def _required_text(columns: dict[str, Any], name: str, index: int) -> str:
    value = _optional_text(_column_value(columns, name, index))
    if value is None:
        raise ValueError(f"SEC recent filings are missing {name} at index {index}")
    return value


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_date(value: Any) -> date | None:
    text = _optional_text(value)
    return date.fromisoformat(text) if text else None


def _optional_int(value: Any) -> int | None:
    text = _optional_text(value)
    return int(text) if text else None


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _optional_acceptance_datetime(value: Any) -> datetime | None:
    text = _optional_text(value)
    if text is None:
        return None
    if text.endswith("Z"):
        parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    elif text.isdigit() and len(text) == 14:
        parsed = datetime.strptime(text, "%Y%m%d%H%M%S").replace(
            tzinfo=ZoneInfo("America/New_York")
        )
    else:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=ZoneInfo("America/New_York"))
    return parsed.astimezone(UTC)
