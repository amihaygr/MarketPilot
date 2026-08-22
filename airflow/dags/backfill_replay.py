"""Manual, parameterized, bounded historical replay."""

import pendulum
from airflow.models.param import Param
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

from airflow import DAG

with DAG(
    dag_id="backfill_replay",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    params={
        "start_date": Param(type="string", format="date"),
        "end_date": Param(type="string", format="date"),
        "symbols": Param(default=["SPY"], type="array", items={"type": "string"}),
    },
    tags=["marketpilot", "manual", "backfill"],
) as dag:
    SparkSubmitOperator(
        task_id="replay_bronze_to_gold",
        application="/opt/marketpilot/spark/jobs/backfill_replay.py",
        conn_id="spark_standalone",
        application_args=[
            "--start-date",
            "{{ params.start_date }}",
            "--end-date",
            "{{ params.end_date }}",
            "--symbols-json",
            "{{ params.symbols | tojson }}",
        ],
        pool="spark_batch_pool",
    )
