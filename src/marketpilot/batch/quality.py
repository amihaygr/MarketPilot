"""Pure data-quality policy for the canonical market-bar Silver dataset."""

from dataclasses import dataclass

QUALITY_CHECK_NAMES = (
    "non_empty",
    "expected_symbols",
    "expected_market_bars",
    "required_fields",
    "business_key_duplicates",
    "ohlc_consistency",
    "logical_date",
    "schema_version",
    "ingestion_freshness",
    "event_before_ingestion",
)


@dataclass(frozen=True, slots=True)
class QualityMetrics:
    total_rows: int
    distinct_business_keys: int
    required_null_rows: int
    invalid_ohlc_rows: int
    wrong_logical_date_rows: int
    invalid_schema_rows: int
    event_after_ingestion_rows: int
    maximum_ingestion_lag_seconds: int | None
    rows_by_symbol: dict[str, int]


@dataclass(frozen=True, slots=True)
class QualityPolicy:
    expected_symbols: tuple[str, ...]
    expected_bars_per_symbol: int
    maximum_ingestion_lag_seconds: int

    def __post_init__(self) -> None:
        if not self.expected_symbols:
            raise ValueError("expected_symbols must not be empty")
        if self.expected_bars_per_symbol < 1:
            raise ValueError("expected_bars_per_symbol must be positive")
        if self.maximum_ingestion_lag_seconds < 0:
            raise ValueError("maximum_ingestion_lag_seconds must be non-negative")


@dataclass(frozen=True, slots=True)
class QualityResult:
    check_name: str
    status: str
    observed_value: str
    expected_value: str


class QualityGateFailed(RuntimeError):
    """Raised after blocking quality results have been recorded."""


def evaluate_quality_gate(
    metrics: QualityMetrics,
    policy: QualityPolicy,
) -> tuple[QualityResult, ...]:
    """Evaluate all blocking checks without Spark or database dependencies."""
    expected_symbols = set(policy.expected_symbols)
    actual_symbols = set(metrics.rows_by_symbol)
    minimum_symbol_rows = min(
        (metrics.rows_by_symbol.get(symbol, 0) for symbol in expected_symbols),
        default=0,
    )
    lag = metrics.maximum_ingestion_lag_seconds

    checks = (
        _result("non_empty", metrics.total_rows > 0, metrics.total_rows, ">0"),
        _result(
            "expected_symbols",
            actual_symbols == expected_symbols,
            ",".join(sorted(actual_symbols)),
            ",".join(sorted(expected_symbols)),
        ),
        _result(
            "expected_market_bars",
            minimum_symbol_rows >= policy.expected_bars_per_symbol,
            minimum_symbol_rows,
            f">={policy.expected_bars_per_symbol} per symbol",
        ),
        _result("required_fields", metrics.required_null_rows == 0, metrics.required_null_rows, 0),
        _result(
            "business_key_duplicates",
            metrics.total_rows == metrics.distinct_business_keys,
            metrics.total_rows - metrics.distinct_business_keys,
            0,
        ),
        _result("ohlc_consistency", metrics.invalid_ohlc_rows == 0, metrics.invalid_ohlc_rows, 0),
        _result(
            "logical_date",
            metrics.wrong_logical_date_rows == 0,
            metrics.wrong_logical_date_rows,
            0,
        ),
        _result("schema_version", metrics.invalid_schema_rows == 0, metrics.invalid_schema_rows, 0),
        _result(
            "ingestion_freshness",
            lag is not None and lag <= policy.maximum_ingestion_lag_seconds,
            "missing" if lag is None else lag,
            f"<={policy.maximum_ingestion_lag_seconds} seconds",
        ),
        _result(
            "event_before_ingestion",
            metrics.event_after_ingestion_rows == 0,
            metrics.event_after_ingestion_rows,
            0,
        ),
    )
    if tuple(result.check_name for result in checks) != QUALITY_CHECK_NAMES:
        raise AssertionError("quality check catalogue and evaluation order diverged")
    return checks


def quality_gate_passed(results: tuple[QualityResult, ...]) -> bool:
    return bool(results) and all(result.status == "PASS" for result in results)


def _result(name: str, passed: bool, observed: object, expected: object) -> QualityResult:
    return QualityResult(
        check_name=name,
        status="PASS" if passed else "FAIL",
        observed_value=str(observed),
        expected_value=str(expected),
    )
