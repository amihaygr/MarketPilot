# External Source Activation Runbook

Use this runbook only after the synthetic Kafka, Bronze, streaming, and batch paths
are healthy. Keep all values in the ignored `.env`; never paste or commit secrets.

## Preflight

```powershell
docker compose config --quiet
docker compose ps
docker compose logs --tail=100 market-producer raw-archive-sink spark-streaming
```

Confirm Kafka, MinIO, MariaDB, Spark, the raw sink, and streaming are healthy. Keep
the Airflow DAGs paused while changing source configuration.

## Activate Alpaca market bars

1. Put the Alpaca API key and secret in `.env`.
2. Choose the entitled feed, normally `iex` for a free local account.
3. Set `MARKET_DATA_SOURCE=alpaca` only after reviewing the configured symbols.
4. Recreate only the producer:

```powershell
docker compose up -d --build --force-recreate market-producer
docker compose logs --tail=200 -f market-producer
```

Verify a bar in Kafka UI, its raw object in MinIO, and the corresponding
`PROVISIONAL` Gold row in MariaDB. If authentication, entitlement, or repeated
disconnect errors appear, restore `MARKET_DATA_SOURCE=synthetic` and recreate the
producer. Do not run a second producer for the same source and symbols during this
check.

## Activate SEC polling

1. Set `SEC_USER_AGENT` to an application name plus a real monitored contact
   email, for example `MarketPilot owner@example.com`.
2. Review `SEC_COMPANY_CIKS`, `SEC_FORMS`, and the default five-requests-per-second
   limit.
3. Set `SEC_POLL_ENABLED=true`.
4. Recreate the Airflow scheduler and DAG processor so they receive the new
   environment:

```powershell
docker compose up -d --force-recreate airflow-scheduler airflow-dag-processor
docker compose exec -T airflow-scheduler airflow dags list-import-errors
```

Run one reviewed manual DAG execution before unpausing the schedule. Verify the raw
SEC JSON in `marketpilot-bronze`, accession uniqueness in `fact_sec_filing`, and a
`PUBLISHED` SEC watermark. Unpause only after those three checks pass.

## Disable safely

- Alpaca: set `MARKET_DATA_SOURCE=synthetic` and recreate `market-producer`.
- SEC: set `SEC_POLL_ENABLED=false`, recreate the Airflow scheduler, and pause
  `sec_polling`.

Disabling either source does not delete Kafka data, Bronze objects, checkpoints,
or MariaDB history.
