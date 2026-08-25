"""Shared Kafka publication boundary for synthetic and external market bars."""

import json
import logging
from collections.abc import Callable
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class ProducerLike(Protocol):
    def produce(
        self,
        topic: str,
        *,
        key: str,
        value: str,
        on_delivery: Callable[[Any, Any], None],
    ) -> None: ...

    def poll(self, timeout: float) -> int: ...

    def flush(self, timeout: float | None = None) -> int: ...


def publish_event(producer: ProducerLike, topic: str, event: dict[str, Any]) -> None:
    """Queue one canonical event and surface asynchronous delivery failures."""

    def delivery_report(error: object | None, _message: object) -> None:
        if error is not None:
            logger.error("market event delivery failed error=%s", error)

    payload = json.dumps(event, separators=(",", ":"))
    while True:
        try:
            producer.produce(
                topic,
                key=str(event["symbol"]),
                value=payload,
                on_delivery=delivery_report,
            )
            break
        except BufferError:
            producer.poll(1.0)
    producer.poll(0.0)
