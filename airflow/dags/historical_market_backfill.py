"""Manual Alpaca-to-certified-Gold backfill followed by a reproducible backtest."""

import os
from datetime import timedelta

import pendulum
from airflow.models.param import Param
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.sdk import DAG, get_current_context, task

from marketpilot.historical.ingestion import backfill_historical_session_from_env
from marketpilot.orchestration.batch_scope import configured_market_symbols
from marketpilot.orchestration.historical_scope import prepare_historical_backfill_plan

SPARK_CONF = {
    "spark.cores.max": "2",
    "spark.executor.cores": "2",
    "spark.executor.memory": "768m",
    "spark.driver.memory": "768m",
    "spark.driver.bindAddress": "0.0.0.0",
    "spark.driver.host": "airflow-scheduler",
    "spark.driver.port": "39601",
    "spark.blockManager.port": "39602",
}
DEFAULT_SYMBOLS = ["AAPL", "MSFT", "SPY"]


@task(task_id="validate_historical_scope")
def validate_scope() -> dict[str, object]:
    context = get_current_context()
    parameters = context["params"]
    lag_days = int(os.environ.get("HISTORICAL_MAX_INGESTION_LAG_DAYS", "3660"))
    return prepare_historical_backfill_plan(
        start_date_value=parameters["start_date"],
        end_date_value=parameters["end_date"],
        requested_symbols=parameters["symbols"],
        benchmark_symbol=parameters["benchmark_symbol"],
        configured_symbols=configured_market_symbols(os.environ["MARKET_SYMBOLS"]),
        airflow_run_id=context["run_id"],
        minimum_coverage_pct=parameters["minimum_coverage_pct"],
        maximum_ingestion_lag_seconds=lag_days * 24 * 60 * 60,
        short_window=parameters["short_window"],
        long_window=parameters["long_window"],
        initial_capital=str(parameters["initial_capital"]),
        transaction_cost_bps=str(parameters["transaction_cost_bps"]),
        slippage_bps=str(parameters["slippage_bps"]),
    )


@task(task_id="ingestion_arguments")
def ingestion_arguments(plan: dict[str, object]) -> list[dict[str, object]]:
    return plan["ingestion"]  # type: ignore[return-value]


@task(task_id="spark_arguments")
def spark_arguments(plan: dict[str, object], stage: str) -> list[list[str]]:
    return plan[stage]  # type: ignore[return-value]


@task(task_id="backtest_arguments")
def backtest_arguments(plan: dict[str, object]) -> list[str]:
    return plan["backtest"]  # type: ignore[return-value]


@task(
    task_id="fetch_archive_historical_bars",
    pool="alpaca_api_pool",
    max_active_tis_per_dag=1,
)
def fetch_archive_historical_bars(
    session_date: str,
    symbols: list[str],
    run_id: str,
) -> dict[str, object]:
    return backfill_historical_session_from_env(
        logical_date=session_date,
        symbols=symbols,
        run_id=run_id,
    )


with DAG(
    dag_id="historical_market_backfill",
    description="Acquire Alpaca history, certify Gold, then run the Phase 11 backtest",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="America/New_York"),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=12),
    render_template_as_native_obj=True,
    params={
        "start_date": Param(default="2026-08-17", type="string", format="date"),
        "end_date": Param(default="2026-08-28", type="string", format="date"),
        "symbols": Param(default=DEFAULT_SYMBOLS, type="array", items={"type": "string"}),
        "benchmark_symbol": Param(default="SPY", type="string"),
        "minimum_coverage_pct": Param(default=80, type="integer", minimum=1, maximum=100),
        "short_window": Param(default=20, type="integer", minimum=2, maximum=389),
        "long_window": Param(default=50, type="integer", minimum=3, maximum=390),
        "initial_capital": Param(default=10000, type="number", exclusiveMinimum=0),
        "transaction_cost_bps": Param(default=1, type="number", minimum=0, maximum=1000),
        "slippage_bps": Param(default=1, type="number", minimum=0, maximum=1000),
    },
    default_args={
        "owner": "marketpilot",
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
        "retry_exponential_backoff": True,
        "execution_timeout": timedelta(hours=3),
    },
    tags=["marketpilot", "manual", "historical", "backfill", "backtest"],
) as dag:
    plan = validate_scope()
    ingestion_args = ingestion_arguments(plan)
    bronze_args = spark_arguments.override(task_id="bronze_arguments")(plan, "bronze")
    quality_args = spark_arguments.override(task_id="quality_arguments")(plan, "quality")
    gold_args = spark_arguments.override(task_id="gold_arguments")(plan, "gold")
    final_backtest_args = backtest_arguments(plan)

    acquire = fetch_archive_historical_bars.expand_kwargs(ingestion_args)
    bronze_to_silver = SparkSubmitOperator.partial(
        task_id="bronze_to_silver",
        application="/opt/marketpilot/spark/jobs/bronze_to_silver.py",
        conn_id="spark_standalone",
        conf=SPARK_CONF,
        pool="spark_batch_pool",
        max_active_tis_per_dag=1,
        verbose=False,
    ).expand(application_args=bronze_args)
    silver_quality_gate = SparkSubmitOperator.partial(
        task_id="silver_quality_gate",
        application="/opt/marketpilot/spark/jobs/validate_silver.py",
        conn_id="spark_standalone",
        conf=SPARK_CONF,
        pool="spark_batch_pool",
        max_active_tis_per_dag=1,
        verbose=False,
    ).expand(application_args=quality_args)
    silver_to_gold = SparkSubmitOperator.partial(
        task_id="silver_to_gold_certified",
        application="/opt/marketpilot/spark/jobs/silver_to_gold.py",
        conn_id="spark_standalone",
        conf=SPARK_CONF,
        pool="spark_batch_pool",
        max_active_tis_per_dag=1,
        verbose=False,
    ).expand(application_args=gold_args)
    run_backtest = SparkSubmitOperator(
        task_id="run_historical_backtest",
        application="/opt/marketpilot/spark/jobs/run_historical_backtest.py",
        conn_id="spark_standalone",
        application_args=final_backtest_args,
        conf=SPARK_CONF,
        pool="spark_batch_pool",
        verbose=False,
    )

    acquire >> bronze_to_silver >> silver_quality_gate >> silver_to_gold >> run_backtest
