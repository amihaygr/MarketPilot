"""Manual, bounded training and registry workflow for Phase 15."""

from datetime import timedelta

import pendulum
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.sdk import DAG
from daily_market_close import SPARK_CONF

with DAG(
    dag_id="hybrid_model_training",
    description="Train, calibrate and register a PREVIEW hybrid decision model",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="America/New_York"),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=2),
    params={"model_version": "decision-intelligence-v2-hybrid-preview-1"},
    default_args={
        "owner": "marketpilot",
        "retries": 0,
        "execution_timeout": timedelta(minutes=90),
    },
    tags=["marketpilot", "decision-intelligence", "ml", "manual"],
) as dag:
    train_and_register_preview = SparkSubmitOperator(
        task_id="train_and_register_preview",
        application="/opt/marketpilot/spark/jobs/train_hybrid_decision_model.py",
        conn_id="spark_standalone",
        application_args=[
            "--run-id",
            "{{ run_id }}",
            "--model-version",
            "{{ params.model_version }}",
        ],
        conf=SPARK_CONF,
        pool="spark_batch_pool",
        verbose=False,
    )
