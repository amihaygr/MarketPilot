# Local Credential Rotation Runbook

This runbook covers the Docker Compose development environment. Real values belong
only in the ignored `.env`; never put them in `.env.example`, a command line, a
commit, a screenshot, or a support conversation.

## Why editing `.env` is not always enough

Some credentials are read every time a container starts. Others also create a
persistent account or encrypt persistent data. Changing only the file can therefore
leave the server and its clients with different credentials.

- MariaDB and PostgreSQL initialization variables do not update accounts in an
  existing named volume.
- Airflow Fernet keys encrypt connection and variable values already stored in its
  metadata database.
- MinIO root credentials are startup settings, but every S3 client must receive the
  same new pair.
- An `env_file` change is not loaded by `docker compose restart`; the affected
  container must be recreated.

Official references:

- [MariaDB password reset for an existing data directory](https://mariadb.com/docs/server/server-management/automated-mariadb-deployment-and-administration/docker-and-mariadb/docker-official-image-frequently-asked-questions)
- [PostgreSQL official image initialization behavior](https://hub.docker.com/_/postgres)
- [Airflow Fernet key rotation](https://airflow.apache.org/docs/apache-airflow/3.0.0/security/secrets/fernet.html)
- [MinIO root credential settings](https://min.io/docs/minio/linux/operations/install-deploy-manage/deploy-minio-single-node-multi-drive.html)

## Rotation matrix

| Variables | `.env` only? | Persistent action | Affected runtime | Recommendation |
|---|---|---|---|---|
| `ALPACA_API_KEY`, `ALPACA_API_SECRET` | No | None | `market-producer` recreation | Rotate the pair together when Alpaca issues a new pair. |
| `SEC_USER_AGENT` | No | None | Airflow scheduler and DAG processor recreation | Safe to change when the monitored contact changes. |
| `MARIADB_APP_PASSWORD` | Yes, for now | The Phase 7 read-only account must later be created with the same value. | No current consumer | Set a strong value before the Backend API is created. |
| `AIRFLOW_ADMIN_PASSWORD` | No | Rewrite the password file through `airflow-init`. | Airflow API login | Low-risk coordinated rotation. |
| `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` | No | None for this unencrypted local store | MinIO, raw sink, SEC tasks, and Spark Batch | Rotate together in a maintenance window. Prefer dedicated service accounts later. |
| `MARIADB_INGEST_PASSWORD` | No | `ALTER USER` through `003_ingest_grants.sh` | Spark Streaming | Coordinated database and client rotation. |
| `MARIADB_PUBLISH_PASSWORD` | No | `ALTER USER` through `005_batch_grants.sh` | Spark Batch submitted by Airflow | Coordinated database and client rotation. |
| `MARIADB_SEC_PASSWORD` | No | `ALTER USER` through `007_sec_grants.sh` | Airflow SEC tasks | Coordinated database and client rotation. |
| `MARIADB_ROOT_PASSWORD` | No | Change both `root@localhost` and `root@%` in MariaDB | MariaDB administration and grant scripts | High-risk; perform only with a verified backup and rollback plan. |
| `AIRFLOW_DB_PASSWORD` and both Airflow SQLAlchemy URLs | No | `ALTER ROLE airflow PASSWORD` in PostgreSQL | Every Airflow component | High-risk coordinated rotation; the three values must agree. |
| `AIRFLOW_SECRET_KEY` | No | None | Every Airflow component and existing sessions/tokens | Rotate all Airflow components together; users must sign in again. |
| `AIRFLOW_FERNET_KEY` | Never directly | Two-key rotation plus `airflow rotate-fernet-key` | Encrypted Airflow connections and variables | High-risk; never replace the old key in one step. |

`AIRFLOW_ADMIN_EMAIL` is contact metadata rather than an authentication secret in
the current Simple Auth Manager setup. Updating it currently has no runtime effect.
`AIRFLOW_METADATA_DATABASE_URL` is retained for project compatibility, while
Airflow itself reads `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN`; both URLs must remain
consistent with `AIRFLOW_DB_PASSWORD`.

## Safe order before Phase 7

The recommended pre-Phase-7 change is deliberately small:

1. Choose a strong, unique `MARIADB_APP_PASSWORD` in a password manager and put it
   in `.env`. No current container consumes it, so this causes no outage.
2. Choose a different strong `AIRFLOW_ADMIN_PASSWORD` and put it in `.env`.
3. Rebuild only the Airflow password file and API container:

   ```powershell
   docker compose run --rm --no-deps airflow-init
   docker compose up -d --no-deps --force-recreate airflow-api-server
   docker compose ps airflow-api-server
   ```

4. Sign in to Airflow with the new admin password and verify the health page.
5. Do not rotate the active MariaDB, MinIO, PostgreSQL, Airflow secret, or Fernet
   credentials in the same change.

The `MARIADB_APP_PASSWORD` account creation and read-only grants belong to the
Phase 7 Backend API migration. Until that migration exists, the variable is only a
prepared secret and no `marketpilot_app` database account should exist.

## Coordinated MariaDB service-password rotation

Rotate the ingest, publisher, and SEC identities together only during a reviewed
maintenance window. Do not include the root password in this operation.

1. Confirm all containers are healthy and no bounded batch or SEC run is active.
2. Pause `sec_polling` and keep the daily/backfill DAGs paused.
3. Stop the credential consumers:

   ```powershell
   docker compose stop spark-streaming airflow-scheduler airflow-dag-processor
   ```

4. Put new, distinct values for the three service passwords in `.env`.
5. Recreate MariaDB so the mounted grant scripts see the new environment. The
   persistent database volume is preserved:

   ```powershell
   docker compose up -d --no-deps --force-recreate mariadb
   ```

6. Apply the idempotent grant scripts inside MariaDB:

   ```powershell
   docker compose exec -T mariadb bash /docker-entrypoint-initdb.d/003_ingest_grants.sh
   docker compose exec -T mariadb bash /docker-entrypoint-initdb.d/005_batch_grants.sh
   docker compose exec -T mariadb bash /docker-entrypoint-initdb.d/007_sec_grants.sh
   ```

7. Recreate the consumers so they load the new values:

   ```powershell
   docker compose up -d --no-deps --force-recreate spark-streaming airflow-dag-processor airflow-scheduler
   ```

8. Verify Spark Streaming remains active, Airflow imports all DAGs, and each
   account can perform only its intended operation. Unpause `sec_polling` last.

If a check fails, stop the affected consumers, restore the three prior values in
`.env`, recreate MariaDB, re-run the same grant scripts, and recreate the consumers.

## Coordinated MinIO root rotation

The current MVP uses the MinIO root pair for several internal clients. Rotate both
values together and preserve the named data volume.

1. Pause SEC and bounded batch activity.
2. Stop the raw sink and Airflow components that can access S3.
3. Change both MinIO root values in `.env`.
4. Recreate MinIO with `--no-deps`, wait for health, then recreate
   `raw-archive-sink`, `airflow-dag-processor`, and `airflow-scheduler`.
5. Verify existing Bronze and Silver objects are readable before resuming work.

The longer-term hardening action is to replace shared root access with separate
least-privilege MinIO service accounts. That is a security improvement, not a
prerequisite for starting Phase 7 locally.

## Rotations that require a separate approved maintenance plan

Do not rotate any of the following as an incidental `.env` edit:

- MariaDB root: it is stored in the persistent MariaDB account table.
- Airflow PostgreSQL password: the PostgreSQL role and every Airflow connection
  string must change atomically.
- Airflow Fernet: use `new_key,old_key`, run `airflow rotate-fernet-key`, verify,
  and only then remove the old key.
- Airflow secret key: all Airflow containers must switch together and active
  sessions/tokens will be invalidated.

Each operation needs a database backup, exact rollback commands, a service outage
window, and post-rotation authentication tests.

## Post-change verification

Use commands that do not print the effective Compose configuration because that
configuration contains interpolated secrets:

```powershell
docker compose config --quiet
docker compose ps
docker compose logs --since 10m --no-color mariadb minio spark-streaming airflow-api-server airflow-scheduler
ruff check .
ruff format --check .
pytest -q
```

Never use `docker compose config` without `--quiet` in a shared transcript after
real credentials have been configured.
