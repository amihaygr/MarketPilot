# Tests

Planned suites:

- `unit`: pure logic and schema validation.
- `integration`: Kafka, MinIO, Spark, MariaDB, and Airflow boundaries.
- `data_quality`: completeness, freshness, duplicates, nulls, OHLC consistency, and archive verification.

Critical recovery scenarios:

- duplicate Kafka delivery;
- Spark Streaming restart;
- temporary Kafka failure;
- temporary MariaDB failure;
- malformed event;
- deleted or incompatible checkpoint;
- Airflow retry and overlapping DAG prevention.
