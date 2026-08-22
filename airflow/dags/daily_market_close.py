"""Certify the completed trading session through bounded Spark jobs."""

from datetime import timedelta

import pendulum
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.standard.operators.empty import EmptyOperator

from airflow import DAG

with DAG(
    dag_id="daily_market_close",
    schedule="30 16 * * 1-5",
    start_date=pendulum.datetime(2026, 1, 1, tz="America/New_York"),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["marketpilot", "certification"],
) as dag:
    session_gate = EmptyOperator(task_id="exchange_session_gate")
    bronze_to_silver = SparkSubmitOperator(
        task_id="bronze_to_silver",
        application="/opt/marketpilot/spark/jobs/bronze_to_silver.py",
        conn_id="spark_standalone",
        application_args=["--logical-date", "{{ ds }}"],
        pool="spark_batch_pool",
    )
    silver_to_gold = SparkSubmitOperator(
        task_id="silver_to_gold",
        application="/opt/marketpilot/spark/jobs/silver_to_gold.py",
        conn_id="spark_standalone",
        application_args=["--logical-date", "{{ ds }}", "--certification-status", "CERTIFIED"],
        pool="spark_batch_pool",
    )
    publish = EmptyOperator(task_id="publish_certified_partition")

    session_gate >> bronze_to_silver >> silver_to_gold >> publish
