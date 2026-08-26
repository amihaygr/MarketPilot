# Phase 7 Serving Layer Verification

Verified locally on 2026-08-26 with Docker Compose, MariaDB 11.4, FastAPI 0.141.1,
Uvicorn 0.52.4, Nginx 1.27.5 and the existing Gold data produced by Phases 3, 4,
and 6.

## Implemented boundary

```text
Browser
  -> web-app :3000 (static HTML, CSS and JavaScript)
  -> Nginx relative /api/ proxy
  -> backend-api :8000 (validation and response models)
  -> marketpilot_app (SELECT only)
  -> MariaDB Gold
```

Docker Compose owns both long-running services. Airflow does not start, stop, or
monitor either service.

## Backend API

- `GET /health/live` verifies process liveness without touching MariaDB.
- `GET /health/ready` verifies the application database identity can execute a
  read query.
- `/api/v1/symbols` returns active assets and their latest publication state.
- `/api/v1/market-bars` requires a validated symbol, timezone-aware UTC bounds,
  optional certification filter, and bounded pagination.
- `/api/v1/sec-filings` supports symbol, form and date filters with bounded
  pagination.
- `/api/v1/freshness` returns market, SEC, symbol, and pipeline watermarks.
- Collection pages are limited to 1 through 1,000 and page sizes to 1 through 200.
- Market ranges default to seven days and cannot exceed 31 days.
- All SQL predicates are parameterized. Response models omit internal Bronze URIs,
  Kafka coordinates, database IDs, run IDs, and credentials.
- Request logs are structured JSON and contain request ID, method, path, status,
  duration, and sanitized database error type/code.

## MariaDB privilege boundary

`008_app_grants.sh` idempotently creates or updates `marketpilot_app`, revokes all
existing grants, and grants `SELECT` only on:

- `dim_symbol`;
- `fact_market_bar_1m`;
- `fact_sec_filing`;
- `etl_watermark`.

Before and after the controlled MariaDB container recreation, Gold retained 4,598
market bars and 930 SEC filings. The named MariaDB volume was preserved. A runtime
probe successfully executed `SELECT 1`, then attempted a zero-row `UPDATE` and
received the expected MariaDB authorization error. No business row was changed.

## Web App

- Nginx serves dependency-free static assets at <http://localhost:3000>.
- Browser requests use relative `/api/` URLs; the browser has no database or MinIO
  address and no credentials.
- The dashboard displays platform counts, latest market time, certification mix,
  a close-price chart, paginated OHLCV rows, per-symbol freshness, and SEC filings.
- A restrictive Content Security Policy blocks external scripts, objects, framing,
  unexpected API origins, camera, microphone, and geolocation access.
- The proxy uses Docker DNS with a short validity window so a replaced API
  container can be resolved without rebuilding the Web App.

## Runtime evidence

| Check | Result |
|---|---:|
| API readiness | `ready` |
| active symbols | 11 |
| Gold market bars reported by freshness | 4,598 |
| AAPL bars in the reviewed seven-day range | 418 |
| first API page size | 25 |
| first proxied Web App page size | 5 |
| AAPL SEC filings | 12 |
| total SEC filing rows retained | 930 |
| disallowed POST | HTTP 405 |
| over-limit market range | HTTP 422 |
| approved CORS origin | `http://localhost:3000` |
| CSP response header | present |
| secret variable names in rendered HTML | none |
| application identity read probe | allowed |
| application identity write probe | denied |
| Web App container during API replacement | unchanged and proxy recovered |
| desktop visual viewport | 1,440 px, no horizontal overflow |
| mobile visual viewport | 390 px, no horizontal overflow |
| rendered market rows | 50 |
| rendered SEC filing cards | 6 |
| pagination interaction | page 1 to page 2 changed the first row |
| symbol filter interaction | SPY returned 418 results |
| JavaScript runtime errors | none |
| browser HTTP responses with status 400 or higher | none |

The API, Web App, MariaDB, Spark Streaming, and Airflow Scheduler all returned to
healthy state after their reviewed recreations or restarts.

## Quality gates

- `docker compose config --quiet`: passed.
- Ruff lint and format: passed after adding the serving code.
- Unit and contract tests: 47 passed.
- Docker-backed Phase 7 boundaries: exercised directly against the running API,
  Web App, proxy, MariaDB identity, CORS, range validation and healthchecks.

## Visual browser verification

The Dashboard was rendered in local headless Chrome with JavaScript enabled and
reviewed at desktop and mobile viewport sizes. The desktop review covered the
summary cards, close-price chart, OHLCV table, freshness panel, pagination, symbol
filter, SEC filing cards, and footer. The mobile review confirmed the responsive
single-column layout and absence of horizontal overflow.

The first visual pass exposed a CSS regression: `.toast` set `display: grid`, which
overrode the initial `hidden` state and made the error message visible even though
every API request returned HTTP 200. `.toast[hidden] { display: none; }` now makes
the state explicit, and a focused regression test protects the behavior. A second
visual and interactive pass confirmed the notification is hidden, all expected
data is visible, filtering and pagination work, and the browser reported no failed
responses or JavaScript exceptions.

The checked-in `tests/integration/test_serving_layer.py` is opt-in because it
expects the local serving stack and Docker daemon. The same assertions were run
directly on the verified workstation during this phase.

## Deferred security scope

The local MVP binds the UI and API only to `127.0.0.1`. End-user authentication,
TLS, rate limiting and shared-deployment secret management are required before any
LAN, shared, or Internet-facing deployment.
