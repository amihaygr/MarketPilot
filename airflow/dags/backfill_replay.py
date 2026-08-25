"""Manual, parameterized and bounded Bronze-to-Gold historical replay."""

import os
from datetime import timedelta

import pendulum
from airflow.models.param import Param
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.sdk import DAG, get_current_context, task

from marketpilot.orchestration.batch_scope import (
    configured_market_symbols,
    prepare_backfill_arguments,
)

SPARK_CONF = {
    "spark.cores.max": "2",
    "spark.executor.cores": "2",
    "spark.executor.memory": "768m",
    "spark.driver.bindAddress": "0.0.0.0",
    "spark.driver.host": "airflow-scheduler",
    "spark.driver.port": "39001",
    "spark.blockManager.port": "39002",
}
DEFAULT_SYMBOLS = [
    "AAPL",
    "MSFT",
    "AMZN",
    "NVDA",
    "GOOGL",
    "META",
    "TSLA",
    "JPM",
    "UNH",
    "XOM",
    "SPY",
]


@task(task_id="validate_backfill_scope")
def validate_backfill_scope() -> dict[str, list[list[str]]]:
    context = get_current_context()
    params = context["params"]
    return prepare_backfill_arguments(
        start_date_value=params["start_date"],
        end_date_value=params["end_date"],
        requested_symbols=params["symbols"],
        configured_symbols=configured_market_symbols(os.environ["MARKET_SYMBOLS"]),
        airflow_run_id=context["run_id"],
        expected_bars_override=params.get("expected_bars_override"),
    )


@task(task_id="bronze_arguments")
def bronze_arguments(arguments: dict[str, list[list[str]]]) -> list[list[str]]:
    return arguments["bronze"]


@task(task_id="quality_arguments")
def quality_arguments(arguments: dict[str, list[list[str]]]) -> list[list[str]]:
    return arguments["quality"]


@task(task_id="gold_arguments")
def gold_arguments(arguments: dict[str, list[list[str]]]) -> list[list[str]]:
    return arguments["gold"]


with DAG(
    dag_id="backfill_replay",
    description="Replay at most 31 days for a validated subset of MARKET_SYMBOLS",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="America/New_York"),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=8),
    render_template_as_native_obj=True,
    params={
        "start_date": Param(default="2026-08-22", type="string", format="date"),
        "end_date": Param(default="2026-08-22", type="string", format="date"),
        "symbols": Param(default=DEFAULT_SYMBOLS, type="array", items={"type": "string"}),
        "expected_bars_override": Param(default=None, type=["null", "integer"], minimum=1),
    },
    default_args={
        "owner": "marketpilot",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
        "retry_exponential_backoff": True,
        "execution_timeout": timedelta(minutes=60),
    },
    tags=["marketpilot", "manual", "backfill"],
) as dag:
    arguments = validate_backfill_scope()
    bronze_application_args = bronze_arguments(arguments)
    quality_application_args = quality_arguments(arguments)
    gold_application_args = gold_arguments(arguments)
    bronze_to_silver = SparkSubmitOperator.partial(
        task_id="bronze_to_silver",
        application="/opt/marketpilot/spark/jobs/bronze_to_silver.py",
        conn_id="spark_standalone",
        conf=SPARK_CONF,
        pool="spark_batch_pool",
        max_active_tis_per_dag=1,
        verbose=False,
    ).expand(application_args=bronze_application_args)
    silver_quality_gate = SparkSubmitOperator.partial(
        task_id="silver_quality_gate",
        application="/opt/marketpilot/spark/jobs/validate_silver.py",
        conn_id="spark_standalone",
        conf=SPARK_CONF,
        pool="spark_batch_pool",
        max_active_tis_per_dag=1,
        verbose=False,
    ).expand(application_args=quality_application_args)
    silver_to_gold = SparkSubmitOperator.partial(
        task_id="silver_to_gold_certified",
        application="/opt/marketpilot/spark/jobs/silver_to_gold.py",
        conn_id="spark_standalone",
        conf=SPARK_CONF,
        pool="spark_batch_pool",
        max_active_tis_per_dag=1,
        verbose=False,
    ).expand(application_args=gold_application_args)

    bronze_to_silver >> silver_quality_gate >> silver_to_gold
