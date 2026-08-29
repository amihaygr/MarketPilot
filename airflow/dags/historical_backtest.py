"""Manual, bounded and reproducible historical strategy evaluation."""

import os
from datetime import timedelta

import pendulum
from airflow.models.param import Param
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.sdk import DAG, get_current_context, task

from marketpilot.orchestration.backtest_scope import prepare_backtest_arguments

SPARK_CONF = {
    "spark.cores.max": "2",
    "spark.executor.cores": "2",
    "spark.executor.memory": "768m",
    "spark.driver.memory": "768m",
    "spark.driver.bindAddress": "0.0.0.0",
    "spark.driver.host": "airflow-scheduler",
    "spark.driver.port": "39401",
    "spark.blockManager.port": "39402",
}
DEFAULT_SYMBOLS = ["AAPL", "MSFT", "SPY"]


@task(task_id="validate_backtest_scope")
def validate_scope() -> list[str]:
    context = get_current_context()
    parameters = context["params"]
    return prepare_backtest_arguments(
        start_date_value=parameters["start_date"],
        end_date_value=parameters["end_date"],
        requested_symbols=parameters["symbols"],
        benchmark_symbol=parameters["benchmark_symbol"],
        short_window=parameters["short_window"],
        long_window=parameters["long_window"],
        initial_capital=str(parameters["initial_capital"]),
        transaction_cost_bps=str(parameters["transaction_cost_bps"]),
        slippage_bps=str(parameters["slippage_bps"]),
        configured_symbols_value=os.environ["MARKET_SYMBOLS"],
        airflow_run_id=context["run_id"],
    )


with DAG(
    dag_id="historical_backtest",
    description="Evaluate a versioned SMA strategy over certified Gold bars",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="America/New_York"),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=4),
    render_template_as_native_obj=True,
    params={
        "start_date": Param(default="2026-08-22", type="string", format="date"),
        "end_date": Param(default="2026-08-22", type="string", format="date"),
        "symbols": Param(default=DEFAULT_SYMBOLS, type="array", items={"type": "string"}),
        "benchmark_symbol": Param(default="SPY", type="string"),
        "short_window": Param(default=20, type="integer", minimum=2, maximum=389),
        "long_window": Param(default=50, type="integer", minimum=3, maximum=390),
        "initial_capital": Param(default=10000, type="number", exclusiveMinimum=0),
        "transaction_cost_bps": Param(default=1, type="number", minimum=0, maximum=1000),
        "slippage_bps": Param(default=1, type="number", minimum=0, maximum=1000),
    },
    default_args={
        "owner": "marketpilot",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
        "retry_exponential_backoff": True,
        "execution_timeout": timedelta(hours=3),
    },
    tags=["marketpilot", "manual", "analytics", "backtest"],
) as dag:
    arguments = validate_scope()
    run_backtest = SparkSubmitOperator(
        task_id="run_historical_backtest",
        application="/opt/marketpilot/spark/jobs/run_historical_backtest.py",
        conn_id="spark_standalone",
        application_args=arguments,
        conf=SPARK_CONF,
        pool="spark_batch_pool",
        verbose=False,
    )
    arguments >> run_backtest
