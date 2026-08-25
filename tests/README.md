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

The Phase 7 serving integration check verifies the API and Web App over their host
ports and proves that the Backend API database identity can read but receives a
MariaDB authorization error for an `UPDATE` statement:

```powershell
$env:MARKETPILOT_RUN_SERVING_INTEGRATION = "1"
pytest tests/integration/test_serving_layer.py
```
