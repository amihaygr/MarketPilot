"""Archive bounded JSONL batches before committing Kafka offsets."""

import io
import json
import logging
import os
from datetime import datetime
from typing import Any

import boto3
from confluent_kafka import Consumer, KafkaError

from marketpilot.contracts.market_bar import MarketBarV1

logger = logging.getLogger(__name__)


def parse_record(value: bytes) -> dict[str, Any]:
    event = json.loads(value)
    if not isinstance(event, dict):
        raise ValueError("event must be a JSON object")
    MarketBarV1.from_event(event)
    return event


def bronze_key(event: dict[str, Any], topic: str, partition: int, offset: int) -> str:
    event_time = datetime.fromisoformat(str(event["event_time_utc"]))
    return (
        f"source={event['source']}/event=market_bar_1m/"
        f"year={event_time:%Y}/month={event_time:%m}/day={event_time:%d}/"
        f"symbol={event['symbol']}/topic={topic}/partition={partition}/offset={offset}.json"
    )


def quarantine_key(topic: str, partition: int, offset: int) -> str:
    return f"quarantine/topic={topic}/partition={partition}/offset={offset}.json"


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='{"level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
    )
    consumer = Consumer(
        {
            "bootstrap.servers": os.environ["KAFKA_BOOTSTRAP_SERVERS"],
            "group.id": os.environ["KAFKA_CONSUMER_GROUP_RAW_ARCHIVE"],
            "enable.auto.commit": False,
            "auto.offset.reset": "earliest",
        }
    )
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["MINIO_ENDPOINT"],
        aws_access_key_id=os.environ["MINIO_ROOT_USER"],
        aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
    )
    bucket = os.environ["MINIO_BRONZE_BUCKET"]
    consumer.subscribe([os.environ["KAFKA_MARKET_BARS_TOPIC"]])

    try:
        while True:
            messages = consumer.consume(num_messages=5000, timeout=5.0)
            valid_records: list[tuple[object, dict[str, Any]]] = []
            invalid_records: list[tuple[object, str]] = []
            for message in messages:
                if message.error() and message.error().code() != KafkaError._PARTITION_EOF:
                    raise RuntimeError(message.error())
                if not message.error():
                    try:
                        valid_records.append((message, parse_record(message.value())))
                    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
                        invalid_records.append((message, str(error)))
            if not valid_records and not invalid_records:
                continue
            for message, event in valid_records:
                key = bronze_key(event, message.topic(), message.partition(), message.offset())
                s3.upload_fileobj(io.BytesIO(message.value()), bucket, key)
            for message, reason in invalid_records:
                body = json.dumps(
                    {
                        "reason": reason,
                        "raw_value": message.value().decode("utf-8", errors="replace"),
                    },
                    separators=(",", ":"),
                ).encode()
                key = quarantine_key(message.topic(), message.partition(), message.offset())
                s3.upload_fileobj(io.BytesIO(body), bucket, key)
            consumer.commit(asynchronous=False)
            logger.info(
                "archived batch valid=%d quarantined=%d",
                len(valid_records),
                len(invalid_records),
            )
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
