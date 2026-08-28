"""Create Phase 2 Kafka topics and MinIO buckets idempotently."""

import logging
import os

import boto3
from botocore.exceptions import ClientError
from confluent_kafka.admin import AdminClient, NewTopic

logger = logging.getLogger(__name__)


def ensure_topics() -> None:
    admin = AdminClient({"bootstrap.servers": os.environ["KAFKA_BOOTSTRAP_SERVERS"]})
    topics = [
        os.environ["KAFKA_MARKET_BARS_TOPIC"],
        os.environ["KAFKA_DEAD_LETTER_TOPIC"],
    ]
    futures = admin.create_topics(
        [NewTopic(topic, num_partitions=3, replication_factor=1) for topic in topics]
    )
    for topic, future in futures.items():
        try:
            future.result()
            logger.info("created Kafka topic=%s", topic)
        except Exception as error:
            if "TOPIC_ALREADY_EXISTS" not in str(error):
                raise
            logger.info("Kafka topic already exists=%s", topic)


def ensure_buckets() -> None:
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["MINIO_ENDPOINT"],
        aws_access_key_id=os.environ["MINIO_ROOT_USER"],
        aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
    )
    for bucket in (
        os.environ["MINIO_BRONZE_BUCKET"],
        os.environ["MINIO_SILVER_BUCKET"],
        os.environ["MINIO_CHECKPOINT_BUCKET"],
        os.environ.get("MINIO_ARCHIVE_BUCKET", "marketpilot-archive"),
    ):
        try:
            s3.head_bucket(Bucket=bucket)
            logger.info("MinIO bucket already exists=%s", bucket)
        except ClientError as error:
            status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status != 404:
                raise
            s3.create_bucket(Bucket=bucket)
            logger.info("created MinIO bucket=%s", bucket)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='{"level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
    )
    ensure_topics()
    ensure_buckets()


if __name__ == "__main__":
    main()
