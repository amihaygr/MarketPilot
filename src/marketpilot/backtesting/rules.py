"""Pure, deterministic rules for the Phase 11 historical backtest."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

BACKTEST_SCHEMA_VERSION = 1
STRATEGY_CODE = "SMA_CROSS_LONG_CASH"
STRATEGY_VERSION = 1
MAX_BACKTEST_DAYS = 366
MAX_SYMBOLS = 20
PERIODS_PER_YEAR = 252 * 390
UTC = timezone.utc  # noqa: UP017 -- imported by Spark 3.5.8 on Python 3.10.


@dataclass(frozen=True, slots=True)
class BacktestScope:
    run_id: str
    start_date: date
    end_date: date
    symbols: tuple[str, ...]
    benchmark_symbol: str
    short_window: int
    long_window: int
    initial_capital: Decimal
    transaction_cost_bps: Decimal
    slippage_bps: Decimal


@dataclass(frozen=True, slots=True)
class PriceBar:
    symbol_id: int
    symbol: str
    event_time_utc: datetime
    close: Decimal


@dataclass(frozen=True, slots=True)
class EquityPoint:
    symbol_id: int
    symbol: str
    event_time_utc: datetime
    close: Decimal
    short_sma: Decimal | None
    long_sma: Decimal | None
    desired_position: int
    applied_position: int
    gross_return: Decimal
    cost_return: Decimal
    net_return: Decimal
    equity: Decimal
    benchmark_equity: Decimal
    drawdown: Decimal


@dataclass(frozen=True, slots=True)
class BacktestResult:
    symbol_id: int
    symbol: str
    first_event_time_utc: datetime
    last_event_time_utc: datetime
    observation_count: int
    trade_count: int
    total_return_pct: Decimal
    benchmark_return_pct: Decimal
    excess_return_pct: Decimal
    max_drawdown_pct: Decimal
    annualized_volatility_pct: Decimal
    sharpe_ratio: Decimal | None
    curve: tuple[EquityPoint, ...]


def resolve_backtest_scope(
    *,
    run_id: str,
    start_date_value: str,
    end_date_value: str,
    symbols_value: str,
    benchmark_symbol: str = "SPY",
    short_window: int = 20,
    long_window: int = 50,
    initial_capital: str = "10000",
    transaction_cost_bps: str = "1",
    slippage_bps: str = "1",
) -> BacktestScope:
    UUID(run_id)
    start_date = date.fromisoformat(start_date_value)
    end_date = date.fromisoformat(end_date_value)
    if end_date < start_date:
        raise ValueError("backtest end date must not precede start date")
    if (end_date - start_date).days + 1 > MAX_BACKTEST_DAYS:
        raise ValueError(f"backtest range cannot exceed {MAX_BACKTEST_DAYS} days")
    if short_window < 2 or long_window > 390 or short_window >= long_window:
        raise ValueError("SMA windows must satisfy 2 <= short < long <= 390")

    symbols = tuple(dict.fromkeys(_symbol(value) for value in symbols_value.split(",") if value))
    if not symbols or len(symbols) > MAX_SYMBOLS:
        raise ValueError(f"backtest requires between 1 and {MAX_SYMBOLS} symbols")
    benchmark = _symbol(benchmark_symbol)
    capital = Decimal(initial_capital)
    transaction_cost = Decimal(transaction_cost_bps)
    slippage = Decimal(slippage_bps)
    if capital <= 0:
        raise ValueError("initial capital must be positive")
    if transaction_cost < 0 or slippage < 0 or transaction_cost + slippage > 1000:
        raise ValueError("combined transaction cost and slippage must be between 0 and 1000 bps")
    return BacktestScope(
        run_id=run_id,
        start_date=start_date,
        end_date=end_date,
        symbols=symbols,
        benchmark_symbol=benchmark,
        short_window=short_window,
        long_window=long_window,
        initial_capital=capital,
        transaction_cost_bps=transaction_cost,
        slippage_bps=slippage,
    )


def run_long_cash_backtest(
    bars: list[PriceBar],
    scope: BacktestScope,
    *,
    benchmark_bars: list[PriceBar] | None = None,
) -> BacktestResult:
    """Run an SMA crossover whose close-of-bar signal applies to the next return."""
    if not bars:
        raise ValueError("backtest contains no bars")
    ordered = sorted(bars, key=lambda bar: bar.event_time_utc)
    symbol_ids = {bar.symbol_id for bar in ordered}
    symbols = {bar.symbol for bar in ordered}
    if len(symbol_ids) != 1 or len(symbols) != 1:
        raise ValueError("one backtest calculation must contain exactly one symbol")
    if len(ordered) <= scope.long_window:
        raise ValueError("backtest does not contain enough bars for the long SMA window")
    if len({bar.event_time_utc for bar in ordered}) != len(ordered):
        raise ValueError("backtest contains duplicate event timestamps")
    if any(bar.close <= 0 for bar in ordered):
        raise ValueError("backtest close prices must be positive")
    if any(_as_utc(bar.event_time_utc) != bar.event_time_utc for bar in ordered):
        raise ValueError("backtest timestamps must be timezone-aware UTC")

    closes = [bar.close for bar in ordered]
    benchmark_source = benchmark_bars if benchmark_bars is not None else ordered
    benchmark_by_time = {bar.event_time_utc: bar.close for bar in benchmark_source}
    if any(bar.event_time_utc not in benchmark_by_time for bar in ordered):
        raise ValueError("benchmark is missing timestamps required by the strategy symbol")
    short_smas = _rolling_means(closes, scope.short_window)
    long_smas = _rolling_means(closes, scope.long_window)
    desired = [
        int(short is not None and long is not None and short > long)
        for short, long in zip(short_smas, long_smas, strict=True)
    ]
    equity = scope.initial_capital
    benchmark_equity = scope.initial_capital
    peak = equity
    previous_position = 0
    net_returns: list[float] = []
    curve: list[EquityPoint] = []
    trade_count = 0
    total_cost_bps = scope.transaction_cost_bps + scope.slippage_bps

    for index in range(1, len(ordered)):
        applied_position = desired[index - 1]
        turnover = abs(applied_position - previous_position)
        trade_count += turnover
        market_return = closes[index] / closes[index - 1] - Decimal(1)
        gross_return = Decimal(applied_position) * market_return
        cost_return = Decimal(turnover) * total_cost_bps / Decimal(10000)
        net_return = gross_return - cost_return
        if net_return <= Decimal(-1):
            raise ValueError("backtest equity became non-positive")
        equity *= Decimal(1) + net_return
        benchmark_previous = benchmark_by_time[ordered[index - 1].event_time_utc]
        benchmark_current = benchmark_by_time[ordered[index].event_time_utc]
        if benchmark_previous <= 0 or benchmark_current <= 0:
            raise ValueError("benchmark close prices must be positive")
        benchmark_return_for_bar = benchmark_current / benchmark_previous - Decimal(1)
        benchmark_equity *= Decimal(1) + benchmark_return_for_bar
        peak = max(peak, equity)
        drawdown = equity / peak - Decimal(1)
        net_returns.append(float(net_return))
        curve.append(
            EquityPoint(
                symbol_id=ordered[index].symbol_id,
                symbol=ordered[index].symbol,
                event_time_utc=ordered[index].event_time_utc,
                close=ordered[index].close,
                short_sma=short_smas[index],
                long_sma=long_smas[index],
                desired_position=desired[index],
                applied_position=applied_position,
                gross_return=gross_return,
                cost_return=cost_return,
                net_return=net_return,
                equity=equity,
                benchmark_equity=benchmark_equity,
                drawdown=drawdown,
            )
        )
        previous_position = applied_position

    volatility = statistics.stdev(net_returns) if len(net_returns) > 1 else 0.0
    annualized_volatility = volatility * math.sqrt(PERIODS_PER_YEAR)
    sharpe = None
    if volatility > 0:
        annualized_mean = statistics.mean(net_returns) * math.sqrt(PERIODS_PER_YEAR)
        sharpe = Decimal(str(annualized_mean / volatility))
    total_return = (equity / scope.initial_capital - Decimal(1)) * Decimal(100)
    benchmark_return = (benchmark_equity / scope.initial_capital - Decimal(1)) * Decimal(100)
    return BacktestResult(
        symbol_id=ordered[0].symbol_id,
        symbol=ordered[0].symbol,
        first_event_time_utc=curve[0].event_time_utc,
        last_event_time_utc=curve[-1].event_time_utc,
        observation_count=len(curve),
        trade_count=trade_count,
        total_return_pct=total_return,
        benchmark_return_pct=benchmark_return,
        excess_return_pct=total_return - benchmark_return,
        max_drawdown_pct=min(point.drawdown for point in curve) * Decimal(100),
        annualized_volatility_pct=Decimal(str(annualized_volatility * 100)),
        sharpe_ratio=sharpe,
        curve=tuple(curve),
    )


def daily_equity_points(curve: tuple[EquityPoint, ...]) -> tuple[EquityPoint, ...]:
    """Return the final point for each UTC date for a bounded API read model."""
    by_date: dict[date, EquityPoint] = {}
    for point in curve:
        by_date[point.event_time_utc.date()] = point
    return tuple(by_date[key] for key in sorted(by_date))


def _rolling_means(values: list[Decimal], window: int) -> list[Decimal | None]:
    result: list[Decimal | None] = []
    running = Decimal(0)
    for index, value in enumerate(values):
        running += value
        if index >= window:
            running -= values[index - window]
        result.append(running / window if index + 1 >= window else None)
    return result


def _symbol(value: str) -> str:
    symbol = value.strip().upper()
    if not symbol or len(symbol) > 12 or not symbol.replace(".", "").replace("-", "").isalnum():
        raise ValueError(f"invalid symbol: {value!r}")
    return symbol


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC)
