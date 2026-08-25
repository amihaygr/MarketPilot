"""Poll configured SEC company submissions as one bounded Airflow task."""

import logging
from datetime import timedelta
from uuid import NAMESPACE_URL, uuid5

import pendulum
from airflow.models.param import Param
from airflow.providers.standard.operators.python import ShortCircuitOperator
from airflow.sdk import DAG, get_current_context, task

from marketpilot.sec.polling import poll_sec_from_env
from marketpilot.sec.settings import SecSettings

logger = logging.getLogger(__name__)


def sec_poll_window_open() -> bool:
    context = get_current_context()
    settings = SecSettings.from_env()
    if not settings.enabled:
        logger.info("SEC polling is disabled by SEC_POLL_ENABLED")
        return False
    if context["params"].get("force"):
        return True
    now = pendulum.now("America/New_York")
    return now.weekday() < 5 and (6 <= now.hour < 22 or (now.hour == 22 and now.minute == 0))


@task(task_id="poll_sec_submissions", pool="sec_api_pool")
def poll_sec_submissions() -> dict[str, object]:
    context = get_current_context()
    run_id = uuid5(NAMESPACE_URL, f"marketpilot:sec:{context['run_id']}")
    return poll_sec_from_env(str(run_id))


with DAG(
    dag_id="sec_polling",
    description="Discover, archive, and idempotently publish configured SEC filings",
    schedule="*/15 6-22 * * 1-5",
    start_date=pendulum.datetime(2026, 1, 1, tz="America/New_York"),
    catchup=False,
    max_active_runs=1,
    max_active_tasks=1,
    dagrun_timeout=timedelta(minutes=20),
    params={"force": Param(default=False, type="boolean")},
    default_args={
        "owner": "marketpilot",
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
        "retry_exponential_backoff": True,
        "execution_timeout": timedelta(minutes=10),
    },
    tags=["marketpilot", "sec", "external-source"],
) as dag:
    window_gate = ShortCircuitOperator(
        task_id="polling_enabled_and_in_window",
        python_callable=sec_poll_window_open,
    )
    window_gate >> poll_sec_submissions()
