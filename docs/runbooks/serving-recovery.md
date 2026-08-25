# Serving Layer Recovery Runbook

Use this runbook for the long-running `backend-api` and `web-app` services. Docker
Compose owns their lifecycle; Airflow must not start or stop them.

## Fast checks

```powershell
docker compose ps backend-api web-app mariadb
docker compose logs --tail=100 --no-color backend-api web-app
Invoke-RestMethod http://localhost:8000/health/ready
Invoke-RestMethod http://localhost:3000/api/v1/symbols
```

The API liveness endpoint does not query MariaDB. The readiness endpoint does, so
`live=200` with `ready=503` normally means a database, credential, privilege, or
query problem.

## API cannot authenticate to MariaDB

Do not put the password in a command or transcript. Confirm that
`MARIADB_APP_PASSWORD` is configured in the ignored `.env`.

If that value was changed after the current MariaDB container was created, perform
a reviewed container recreation. The named volume is preserved:

```powershell
docker compose stop spark-streaming airflow-scheduler
docker compose up -d --no-deps --force-recreate mariadb
docker compose up -d --wait --no-deps mariadb
docker compose exec -T mariadb bash /docker-entrypoint-initdb.d/008_app_grants.sh
docker compose start airflow-scheduler spark-streaming
docker compose up -d --wait --no-deps airflow-scheduler spark-streaming
docker compose up -d --no-deps --force-recreate backend-api
docker compose up -d --wait --no-deps backend-api
```

Compare business row counts before and after a database recreation. Never remove
the MariaDB named volume as a credential-repair step.

## Verify the privilege boundary

The probe performs `SELECT 1` and a zero-row `UPDATE`. A successful probe means
the read was allowed and MariaDB denied the update before it could mutate data:

```powershell
docker compose exec -T backend-api python -m services.backend_api.permission_probe
```

Expected result:

```json
{"read_allowed": true, "write_denied": true}
```

## API returns validation errors

- HTTP 422 is expected for an invalid symbol, timezone-naive timestamp, reversed
  range, market range over 31 days, page over 1,000, or page size over 200.
- HTTP 405 is expected for mutation methods such as POST, PUT, PATCH, and DELETE.
- HTTP 503 means the API caught a MariaDB error and returned a generic response.
  Inspect the structured log's `error_type` and `error_code`; it intentionally does
  not log SQL, parameters, or credentials.

## Web App is healthy but data does not load

Check the proxied path directly:

```powershell
Invoke-RestMethod http://localhost:3000/api/v1/freshness
```

The Nginx proxy resolves `backend-api` through Docker DNS. After replacing the API
container, allow up to ten seconds for DNS refresh. The Web App container does not
need to be replaced.

## Safe rollback

Phase 7 is downstream and read-only. If recovery is not immediate, stop only the
serving services:

```powershell
docker compose stop web-app backend-api
```

Kafka, ingestion, Bronze archival, Spark Streaming, MariaDB Gold publication and
Airflow bounded jobs continue independently. Starting the serving services later
does not replay or mutate data.
