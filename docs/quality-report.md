# Delivery Quality Report

## Verified in the delivery environment

- Python source, service, Spark, Airflow and test files compile successfully.
- The canonical `MarketBarV1` contract validates and serializes a valid UTC event.
- `pyproject.toml` and VS Code JSON files parse successfully.
- Required architecture, ADR, DAG, Spark and DDL assets are present.
- Common private-key and AWS access-key patterns are absent.
- Legacy Word and PDF diagrams are excluded from this rebuilt delivery.

## Deferred to the target workstation or CI

- `docker compose config`, because Docker is not installed in the delivery environment.
- Ruff lint and format checks, because Ruff is declared as a development dependency but is not installed in the delivery environment.
- Airflow DAG import tests, because Airflow providers are runtime dependencies of the Airflow image rather than the host package.
- Kafka, MinIO, MariaDB and Spark integration tests, which require the Compose stack.

Run `make validate` after installing development dependencies and creating `.env`. A reviewer should not accept the runtime milestone until Compose configuration, health checks and the integration suite pass on the target machine.
