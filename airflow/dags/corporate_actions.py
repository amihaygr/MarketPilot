"""Poll Alpaca corporate actions as bounded Airflow work."""

from datetime import timedelta
from uuid import NAMESPACE_URL, uuid5

import pendulum
from airflow.models.param import Param
from airflow.sdk import DAG, get_current_context, task

from marketpilot.corporate_actions.ingestion import ingest_corporate_actions


@task(task_id="archive_and_publish_corporate_actions", pool="alpaca_api_pool")
def poll_corporate_actions() -> dict[str, object]:
    context = get_current_context()
    end_value = context["params"].get("end") or context["ds"]
    end = pendulum.parse(end_value).date()
    start_value = context["params"].get("start")
    start = pendulum.parse(start_value).date() if start_value else end - timedelta(days=90)
    if end < start or (end - start).days > 90:
        raise ValueError("corporate-action window must be between 0 and 90 days")
    run_id = uuid5(NAMESPACE_URL, f"marketpilot:corporate-actions:{context['run_id']}")
    return ingest_corporate_actions(start=start, end=end, run_id=run_id)


with DAG(
    dag_id="corporate_actions",
    description="Archive and publish Alpaca splits, dividends and other corporate actions",
    schedule="15 6 * * 1-5",
    start_date=pendulum.datetime(2026, 1, 1, tz="America/New_York"),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(minutes=20),
    params={
        "start": Param(default=None, type=["null", "string"], format="date"),
        "end": Param(default=None, type=["null", "string"], format="date"),
    },
    default_args={
        "owner": "marketpilot",
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
        "execution_timeout": timedelta(minutes=10),
    },
    tags=["marketpilot", "alpaca", "corporate-actions"],
) as dag:
    poll_corporate_actions()
