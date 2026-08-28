"""Certify one completed XNYS session through ordered, bounded Spark jobs."""

from datetime import timedelta

import pendulum
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.standard.operators.python import ShortCircuitOperator
from airflow.sdk import DAG, get_current_context

from marketpilot.orchestration.batch_scope import prepare_daily_scope

SPARK_CONF = {
    "spark.cores.max": "2",
    "spark.executor.cores": "2",
    "spark.executor.memory": "768m",
    "spark.driver.bindAddress": "0.0.0.0",
    "spark.driver.host": "airflow-scheduler",
    "spark.driver.port": "39001",
    "spark.blockManager.port": "39002",
}


def _resolve_daily_scope() -> dict[str, object] | None:
    context = get_current_context()
    params = context["params"]
    logical_date = params.get("logical_date") or context["ds"]
    return prepare_daily_scope(
        logical_date,
        context["run_id"],
        params.get("expected_bars_override"),
    )


with DAG(
    dag_id="daily_market_close",
    description="Certify the closed XNYS market-bar partition",
    schedule="30 16 * * 1-5",
    start_date=pendulum.datetime(2026, 1, 1, tz="America/New_York"),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=2),
    render_template_as_native_obj=True,
    params={"logical_date": None, "expected_bars_override": None},
    default_args={
        "owner": "marketpilot",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
        "retry_exponential_backoff": True,
        "execution_timeout": timedelta(minutes=45),
    },
    tags=["marketpilot", "batch", "certification"],
) as dag:
    session_gate = ShortCircuitOperator(
        task_id="exchange_session_gate",
        python_callable=_resolve_daily_scope,
    )
    bronze_to_silver = SparkSubmitOperator(
        task_id="bronze_to_silver",
        application="/opt/marketpilot/spark/jobs/bronze_to_silver.py",
        conn_id="spark_standalone",
        application_args=[
            "--logical-date",
            "{{ ti.xcom_pull(task_ids='exchange_session_gate')['logical_date'] }}",
            "--run-id",
            "{{ ti.xcom_pull(task_ids='exchange_session_gate')['run_id'] }}",
        ],
        conf=SPARK_CONF,
        pool="spark_batch_pool",
        verbose=False,
    )
    silver_quality_gate = SparkSubmitOperator(
        task_id="silver_quality_gate",
        application="/opt/marketpilot/spark/jobs/validate_silver.py",
        conn_id="spark_standalone",
        application_args=[
            "--logical-date",
            "{{ ti.xcom_pull(task_ids='exchange_session_gate')['logical_date'] }}",
            "--run-id",
            "{{ ti.xcom_pull(task_ids='exchange_session_gate')['run_id'] }}",
            "--expected-bars-per-symbol={{ "
            "ti.xcom_pull(task_ids='exchange_session_gate')['expected_bars_per_symbol'] }}",
        ],
        conf=SPARK_CONF,
        pool="spark_batch_pool",
        verbose=False,
    )
    silver_to_gold = SparkSubmitOperator(
        task_id="silver_to_gold_certified",
        application="/opt/marketpilot/spark/jobs/silver_to_gold.py",
        conn_id="spark_standalone",
        application_args=[
            "--logical-date",
            "{{ ti.xcom_pull(task_ids='exchange_session_gate')['logical_date'] }}",
            "--run-id",
            "{{ ti.xcom_pull(task_ids='exchange_session_gate')['run_id'] }}",
        ],
        conf=SPARK_CONF,
        pool="spark_batch_pool",
        verbose=False,
    )
    calculate_market_analytics = SparkSubmitOperator(
        task_id="calculate_market_analytics",
        application="/opt/marketpilot/spark/jobs/calculate_market_analytics.py",
        conn_id="spark_standalone",
        application_args=[
            "--logical-date",
            "{{ ti.xcom_pull(task_ids='exchange_session_gate')['logical_date'] }}",
            "--run-id",
            "{{ ti.xcom_pull(task_ids='exchange_session_gate')['run_id'] }}",
        ],
        conf=SPARK_CONF,
        pool="spark_batch_pool",
        verbose=False,
    )

    (
        session_gate
        >> bronze_to_silver
        >> silver_quality_gate
        >> silver_to_gold
        >> calculate_market_analytics
    )
