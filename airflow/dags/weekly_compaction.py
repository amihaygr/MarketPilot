"""Compact recent closed Silver partitions as one bounded weekly Spark application."""

from datetime import timedelta

import pendulum
from airflow.models.param import Param
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.sdk import DAG, get_current_context, task

from marketpilot.orchestration.operations_scope import prepare_compaction_scope

SPARK_CONF = {
    "spark.cores.max": "2",
    "spark.executor.cores": "2",
    "spark.executor.memory": "768m",
    "spark.driver.bindAddress": "0.0.0.0",
    "spark.driver.host": "airflow-scheduler",
    "spark.driver.port": "39201",
    "spark.blockManager.port": "39202",
}


@task(task_id="prepare_compaction_scope")
def prepare_scope() -> dict[str, object]:
    context = get_current_context()
    parameters = context["params"]
    return prepare_compaction_scope(
        parameters.get("through_date") or context["ds"],
        int(parameters["lookback_days"]),
        context["run_id"],
    )


with DAG(
    dag_id="weekly_compaction",
    description="Compact and validate recent Silver Parquet partitions",
    schedule="0 6 * * 6",
    start_date=pendulum.datetime(2026, 1, 1, tz="America/New_York"),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=2),
    render_template_as_native_obj=True,
    params={
        "through_date": None,
        "lookback_days": Param(default=7, type="integer", minimum=1, maximum=31),
    },
    default_args={
        "owner": "marketpilot",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
        "retry_exponential_backoff": True,
        "execution_timeout": timedelta(minutes=60),
    },
    tags=["marketpilot", "operations", "compaction"],
) as dag:
    scope = prepare_scope()
    compact = SparkSubmitOperator(
        task_id="compact_silver_partitions",
        application="/opt/marketpilot/spark/jobs/compact_silver.py",
        conn_id="spark_standalone",
        application_args=[
            "--through-date",
            "{{ ti.xcom_pull(task_ids='prepare_compaction_scope')['through_date'] }}",
            "--lookback-days",
            "{{ ti.xcom_pull(task_ids='prepare_compaction_scope')['lookback_days'] }}",
            "--run-id",
            "{{ ti.xcom_pull(task_ids='prepare_compaction_scope')['run_id'] }}",
        ],
        conf=SPARK_CONF,
        pool="spark_batch_pool",
        verbose=False,
    )
    scope >> compact
