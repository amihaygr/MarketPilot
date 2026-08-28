"""Export and register the previous closed market-bar year."""

from datetime import timedelta

import pendulum
from airflow.models.param import Param
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.sdk import DAG, get_current_context, task

from marketpilot.orchestration.operations_scope import prepare_archive_scope

SPARK_CONF = {
    "spark.cores.max": "2",
    "spark.executor.cores": "2",
    "spark.executor.memory": "768m",
    "spark.driver.bindAddress": "0.0.0.0",
    "spark.driver.host": "airflow-scheduler",
    "spark.driver.port": "39301",
    "spark.blockManager.port": "39302",
}


@task(task_id="prepare_archive_scope")
def prepare_scope() -> dict[str, object]:
    context = get_current_context()
    parameters = context["params"]
    return prepare_archive_scope(
        logical_date_value=context["ds"],
        archive_year_override=parameters.get("archive_year"),
        archive_version=int(parameters["archive_version"]),
        airflow_run_id=context["run_id"],
    )


with DAG(
    dag_id="annual_archive",
    description="Export the previous closed year to verified versioned Parquet",
    schedule="0 2 10 1 *",
    start_date=pendulum.datetime(2026, 1, 1, tz="America/New_York"),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=6),
    render_template_as_native_obj=True,
    params={
        "archive_year": None,
        "archive_version": Param(default=1, type="integer", minimum=1),
    },
    default_args={
        "owner": "marketpilot",
        "retries": 2,
        "retry_delay": timedelta(minutes=10),
        "retry_exponential_backoff": True,
        "execution_timeout": timedelta(hours=4),
    },
    tags=["marketpilot", "operations", "archive"],
) as dag:
    scope = prepare_scope()
    archive = SparkSubmitOperator(
        task_id="archive_market_bars",
        application="/opt/marketpilot/spark/jobs/archive_market_bars.py",
        conn_id="spark_standalone",
        application_args=[
            "--archive-year",
            "{{ ti.xcom_pull(task_ids='prepare_archive_scope')['archive_year'] }}",
            "--archive-version",
            "{{ ti.xcom_pull(task_ids='prepare_archive_scope')['archive_version'] }}",
            "--run-id",
            "{{ ti.xcom_pull(task_ids='prepare_archive_scope')['run_id'] }}",
        ],
        conf=SPARK_CONF,
        pool="spark_batch_pool",
        verbose=False,
    )
    scope >> archive
