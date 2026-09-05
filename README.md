# MarketPilot

> Local setup note: the repository uses the Apache Kafka 3.9.0 and Apache Spark
> 3.5.8 official images. The original Bitnami tags referenced by the generated
> engineering bundle were removed from Docker Hub and can no longer be pulled.

Spark master and worker remain on `data-plane`. Phase 5 adds a tested Airflow path
for bounded Spark submissions while keeping long-running streaming under Compose.

MarketPilot is a review-ready reference architecture and implementation scaffold for a local market-data platform. It combines Kafka, Spark Structured Streaming, Spark Batch, Airflow, MinIO, MariaDB, a backend API, and a web client without confusing service supervision with workflow orchestration.

## Start with the story

With the local stack running, open:

- **Project Story:** <http://localhost:3000/showcase.html> — architecture, decisions,
  measured evidence, implementation journey and demo launchpad.
- **Presenter Console:** <http://localhost:3000/presenter.html> — timed 10, 15 and
  20-minute routes with speaker cues, transitions and safe fallbacks.
- **Interactive Dashboard:** <http://localhost:3000/> — Gold market data, freshness,
  indicators and explained observations.
- **Backtesting Lab:** <http://localhost:3000/backtesting.html> — bounded historical
  strategy runs, assumptions, benchmark comparison and daily equity curves.
- **Final Demo Guide:** [`docs/demo-guide.md`](docs/demo-guide.md) — the canonical
  15-minute presentation path through the Phase 12 release candidate, with 10 and
  20-minute variants.
- **Presenter learning aids:** [`docs/presentation/`](docs/presentation/) — architecture
  explanations, glossary, reviewer Q&A, rehearsal and failure recovery.

## Architectural position

- Docker Compose owns long-running processes and restarts them after failure.
- Spark Structured Streaming consumes Kafka continuously and publishes provisional Gold records.
- Airflow schedules bounded workloads only. It submits Spark Batch jobs, enforces quality gates, and publishes certified partitions.
- Bronze and Silver live in object storage. Gold is served from MariaDB.
- The same event can follow two valid paths: raw archival for replay and low-latency processing for application freshness.

## Repository map

| Path | Purpose |
|---|---|
| `AGENTS.md` | Binding engineering instructions for Codex |
| `docs/architecture/` | System design, diagrams and execution semantics |
| `docs/decisions/` | Accepted architecture decisions |
| `docs/runbooks/` | Operational and recovery procedures |
| `airflow/dags/` | Bounded orchestration workflows |
| `spark/jobs/` | Streaming and batch Spark entry points |
| `services/` | Long-running ingestion and archival adapters |
| `src/marketpilot/contracts/` | Versioned event contracts |
| `db/migrations/` | MariaDB Gold DDL |
| `infrastructure/` | Container build assets |
| `tests/` | Unit, contract and integration tests |

## Quick start for Codex in VS Code

1. Extract this repository and open its root folder in VS Code.
2. Run `git init` and make an initial checkpoint commit.
3. Copy `.env.example` to `.env` and replace placeholders locally.
4. Open `docs/prompts/codex-first-run.md` and give Prompt 1 to Codex.
5. Require Codex to read `AGENTS.md` and accepted ADRs before editing.

## Local quality gate

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
make lint
make test
cp .env.example .env
make compose-config
```

On Windows PowerShell use `.venv\\Scripts\\python.exe` and run the equivalent commands directly if `make` is unavailable.

## Phase 1 on Windows

The repository has a single Compose file. The explicit `-f` flag below keeps the
commands clear and easy to reuse from scripts or another working directory.

```powershell
Copy-Item .env.example .env  # first run only; .env is ignored by Git
docker compose -f .\docker-compose.yml --env-file .\.env config
docker compose -f .\docker-compose.yml --env-file .\.env up -d kafka minio mariadb spark-master spark-worker
docker compose -f .\docker-compose.yml --env-file .\.env ps
docker compose -f .\docker-compose.yml --env-file .\.env logs --tail=200 kafka minio mariadb spark-master spark-worker
```

The MinIO console is available at <http://localhost:9001>. Kafka and MariaDB are
intentionally reachable only from the internal Docker network during Phase 1.

## Phase 2 synthetic raw path

Phase 2 adds an idempotent initialization job, a deterministic synthetic producer,
and a raw archive consumer:

```text
Synthetic MarketBarV1 -> Kafka -> raw-archive-sink -> MinIO Bronze
                                      |
                                      +-> MinIO quarantine (invalid events)
```

Start the Phase 2 services:

```powershell
docker compose -f .\docker-compose.yml --env-file .\.env up -d --build platform-init market-producer raw-archive-sink
docker compose -f .\docker-compose.yml --env-file .\.env logs --tail=100 platform-init market-producer raw-archive-sink
```

`platform-init` exits with code zero after creating the required Kafka topics and
MinIO buckets. This is expected. The producer and sink remain long-running. Bronze
object names include Kafka topic, partition, and offset so retrying the same Kafka
record overwrites the same immutable logical object before its offset is committed.

## Phase 3 live Streaming to Gold

Phase 3 adds the continuously running provisional Gold path:

```text
Kafka -> Spark Structured Streaming -> MariaDB fact_market_bar_1m (PROVISIONAL)
             |
             +-> Kafka DLQ (invalid events)
```

Build the custom Spark image and start the streaming application:

```powershell
docker compose --env-file .env up -d --build spark-master spark-worker spark-streaming
docker compose ps spark-master spark-worker spark-streaming
docker compose logs --tail=200 spark-streaming
```

The custom image embeds the Spark 3.5.8 Kafka connector at build time because the
runtime `data-plane` network intentionally has no Internet access. The official
Spark image currently contains Python 3.10, so the streaming-only sink is kept
compatible with Python 3.10 while the project services and quality gate remain on
Python 3.12.

Streaming uses two durable checkpoint subdirectories in the `spark-checkpoints`
volume: `gold` for valid records and `dlq` for rejected records. The same named
volume is mounted on the streaming driver and Spark worker because stateful
executors also write checkpoint state. Never delete these directories without a
reviewed replay plan.

Apply the Phase 3 migration to an existing local MariaDB volume once:

```powershell
docker compose exec -T mariadb sh -c 'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" < /docker-entrypoint-initdb.d/002_phase3_streaming.sql'
```

Fresh MariaDB volumes apply both migrations automatically. The ingestion identity
requires only `SELECT`, `INSERT`, and `UPDATE` on `dim_symbol` and
`fact_market_bar_1m`.

## Phase 4 Batch Medallion pipeline

Phase 4 adds bounded, independently runnable Spark applications:

```text
MinIO Bronze -> Bronze-to-Silver -> partitioned Silver Parquet
                                      |
                                      v
                                blocking DQ gate
                                      |
                                      v
MariaDB staging -> atomic transaction -> Gold CERTIFIED + publication watermark
```

Create one run ID and submit all three steps with the same logical date and run ID:

```powershell
$runId = [guid]::NewGuid().ToString()
$logicalDate = "2026-08-22"

docker compose build spark-master
docker compose run --rm --no-deps spark-batch /opt/spark/bin/spark-submit --master spark://spark-master:7077 /opt/marketpilot/spark/jobs/bronze_to_silver.py --logical-date $logicalDate --run-id $runId
docker compose run --rm --no-deps spark-batch /opt/spark/bin/spark-submit --master spark://spark-master:7077 /opt/marketpilot/spark/jobs/validate_silver.py --logical-date $logicalDate --run-id $runId --expected-bars-per-symbol 171
docker compose run --rm --no-deps spark-batch /opt/spark/bin/spark-submit --master spark://spark-master:7077 /opt/marketpilot/spark/jobs/silver_to_gold.py --logical-date $logicalDate --run-id $runId
```

Normally `validate_silver.py` derives expected one-minute bars from the `XNYS`
exchange calendar, including holidays and early closes. The explicit
`--expected-bars-per-symbol` override above exists for synthetic fixtures; the sample
date is a weekend because the Phase 2 synthetic producer is intentionally not yet
market-session-aware.

The Silver layout is
`dataset=market_bars_1m/year=YYYY/month=MM/day=DD/symbol=SYMBOL`. Each row contains
event and dataset schema versions plus source object, Kafka position, run, code, and
data lineage. A failed gate records `FAILED` and exits non-zero. The Gold publisher
checks the gate before staging and again inside the publication transaction.

## Local developer UIs

The management interfaces bind to `127.0.0.1` only. Kafka and MariaDB remain on
internal Docker networks and are not published directly to the host.

| Interface | URL | Purpose |
|---|---|---|
| MinIO Console | <http://localhost:9001> | Browse Bronze, Silver, checkpoints, and quarantine objects |
| Kafka UI | <http://localhost:8085> | Inspect topics, messages, partitions, and consumer lag |
| Adminer | <http://localhost:8086> | Inspect MariaDB schemas and tables |
| Airflow | <http://localhost:8080> | Inspect bounded daily and backfill workflows |
| Spark Master | <http://localhost:18080> | Inspect cluster workers and submitted applications |
| Spark Worker | <http://localhost:18081> | Inspect worker resources and executors |
| MarketPilot Web App | <http://localhost:3000> | Explore Gold bars, freshness, certification and SEC filings |
| MarketPilot Backtesting Lab | <http://localhost:3000/backtesting.html> | Inspect historical runs, assumptions, benchmark results and equity curves |
| MarketPilot Project Story | <http://localhost:3000/showcase.html> | Present architecture, evidence and the end-to-end engineering journey |
| MarketPilot Presenter Console | <http://localhost:3000/presenter.html> | Run a timed demo with speaker notes, navigation and fallbacks |
| Backend API docs | <http://localhost:8000/docs> | Inspect and exercise bounded read-only REST endpoints |

For Adminer, select `MySQL`, use server `mariadb`, database `marketpilot`, and
credentials from your local `.env`. MinIO also uses the credentials from `.env`.
Airflow uses `AIRFLOW_ADMIN_USERNAME` and `AIRFLOW_ADMIN_PASSWORD` from the same
ignored local file. On the verified workstation, `sec_polling` is enabled after a
successful live idempotency check; `daily_market_close` and `backfill_replay`
remain paused. The tracked default still keeps the SEC environment gate disabled.

## Phase 6 external sources

Phase 6 adds two independently controlled flows while preserving the existing
synthetic path:

```text
Alpaca WebSocket -> market-producer -> Kafka -> existing Bronze and live Gold paths

Airflow sec_polling -> SEC submissions JSON -> MinIO Bronze
                                      \-> MariaDB fact_sec_filing
```

`MARKET_DATA_SOURCE=synthetic` and `SEC_POLL_ENABLED=false` are the safe defaults.
The Alpaca adapter uses `MarketBarV1`, filters to regular XNYS minutes, and
reconnects with capped exponential backoff. SEC polling is bounded, rate-limited,
archives raw JSON before publication, and uses accession number as its idempotent
business key. Follow `docs/runbooks/external-source-activation.md` before enabling
either external connection.

## Phase 7 serving layer

Phase 7 completes the application-facing boundary:

```text
Browser -> Nginx Web App -> FastAPI Backend API -> MariaDB Gold
                                      |
                                      +-> marketpilot_app (SELECT only)
```

Start or rebuild the two serving services after applying the application grant to
an existing MariaDB volume:

```powershell
docker compose exec -T mariadb bash /docker-entrypoint-initdb.d/008_app_grants.sh
docker compose up -d --build backend-api web-app
docker compose ps backend-api web-app
```

If `MARIADB_APP_PASSWORD` was changed after MariaDB was already created, follow
`docs/runbooks/serving-recovery.md` to recreate only the MariaDB container while
preserving its named volume, apply the grant, and verify row counts.

Open <http://localhost:3000> for the dashboard or <http://localhost:8000/docs>
for OpenAPI. The Web App uses only relative `/api/` requests. The API enforces
parameterized filters, a maximum 31-day market range, bounded pagination and safe
response models that omit internal object-storage and lineage details.

## Phase 8 operations and archive

Phase 8 adds safe, bounded operational workflows without changing the lifecycle
boundary:

```text
Airflow -> Spark compaction/archive -> MinIO archive + MariaDB manifest
Compose -> operational-monitor -> read-only health and freshness probes
Operator -> backup/restore scripts -> isolated recovery database
```

`weekly_compaction` and `annual_archive` are paused by default. The annual job
accepts only a closed year in production. Archives are verified by row count,
time bounds, schema and checksums; sample restores and full database drills never
target the live schema. Follow `docs/runbooks/archive-and-recovery.md` before an
operator-triggered run.

## Phase 9 explainable analytics

The bounded daily Gold path now continues into versioned analytics:

```text
Certified Gold bars -> Spark window analytics -> Indicators + explained Signals
                                                -> Backend API -> Dashboard
```

The Dashboard overlays SMA20 on price and shows current RSI14, realized
volatility, volume ratio, and sparse threshold-crossing observations. API queries
remain read-only, paginated, and limited to 31 days. The observations are
engineering and research output, not financial advice.

## Phase 10 final showcase and delivery

Phase 10 packages the engineering work for review without introducing another
data path. The Nginx Web App now serves a separate Project Story that loads only
the existing read-only freshness API for its live proof. Static verification
evidence is explicitly dated, and the Dashboard remains focused on exploration.

Use [`docs/demo-guide.md`](docs/demo-guide.md) and the local Presenter Console to
present the current system through the Phase 12 release candidate: one live event,
the certified historical path, and the reproducible Backtesting result. The
15-minute route is the canonical timing source; the guide includes 10 and 20-minute
variants, learning aids, and safe failure fallbacks. It avoids displaying
credentials and distinguishes current runtime state from recorded verification evidence.

## Phase 11 historical backtesting

Phase 11 adds a reproducible research path without changing the live-data paths:

```text
Airflow -> Spark Batch -> MariaDB Gold CERTIFIED bars
                         |-> MinIO detailed Parquet + manifest
                         \-> MariaDB run summaries + daily equity -> API -> Backtesting Lab
```

The manual `historical_backtest` DAG validates a bounded date and symbol scope and
submits the versioned `SMA_CROSS_LONG_CASH` strategy through
`SparkSubmitOperator`. A signal calculated at minute `t` can affect only the next
bar, and transaction cost plus slippage assumptions are explicit. Publication is
transactional and idempotent by run ID. The browser reads bounded summaries through
the Backend API; it never connects to MinIO or MariaDB directly.

Open <http://localhost:3000/backtesting.html> to inspect the verified local run.
See [`docs/phase11-verification.md`](docs/phase11-verification.md) for the evidence
and [`ADR-005`](docs/decisions/ADR-005-historical-backtesting.md) for the design.

## Phase 12 certified historical acquisition

The manual `historical_market_backfill` DAG turns Alpaca historical IEX bars into
auditable Certified Gold data and then launches the Phase 11 backtest. It is a
finite workflow with a maximum 31-calendar-day scope:

```text
Alpaca REST -> source-page Bronze archive -> historical Kafka topic
           -> raw-archive-sink -> offset-level Bronze barrier
           -> Spark Bronze/Silver/DQ/Gold Certified -> historical backtest
```

Historical traffic uses a dedicated Kafka topic and therefore never floods the
live Structured Streaming consumer. Credentials remain only in the ignored `.env`.
See [`docs/runbooks/historical-market-backfill.md`](docs/runbooks/historical-market-backfill.md)
and [`ADR-007`](docs/decisions/ADR-007-certified-historical-acquisition.md).

## Delivery maturity

This repository is a completed local engineering capstone, not a finished trading product.
The raw, streaming, batch Medallion, Airflow orchestration, external-source and
serving, archive and recovery boundaries are concrete and locally verified,
including Alpaca IEX, SEC EDGAR, the read-only API identity, browser-to-API proxy,
verified Parquet archive and isolated restore. End-user authentication remains
outside the local MVP.

## Non-goals

- Automated trading or order execution
- Financial advice
- Exactly-once claims across Kafka, Spark and MariaDB without measured proof
- Airflow supervision of permanent streaming processes
- Automatic deletion of MariaDB history after archival
