# Phase 10 verification

Verification date: 2026-08-28

## Delivered scope

- A responsive Project Story at `http://localhost:3000/showcase.html`.
- A clear link between the Project Story and the operational Dashboard.
- Interactive views for the live, certified, and raw/archive data paths.
- An interactive phase journey covering Phases 0 through 10.
- A demo launchpad for the local engineering interfaces.
- A Hebrew end-to-end presentation route in `docs/demo-guide.md`.
- A read-only Presenter Console at `http://localhost:3000/presenter.html` with
  synchronized 10, 15, and 20-minute routes, timer, speaker cues, transitions,
  screen links, and safe fallbacks.
- A Hebrew learning package under `docs/presentation/` covering architecture
  explanations, terminology, reviewer Q&A, rehearsal, and failure recovery.
- Updated root and Web App documentation.

The Project Story is the final presentation artifact. It is intentionally
separate from the analytical Dashboard so that the Dashboard remains a
decision surface while the Project Story explains the engineering journey.

The canonical presentation duration was revised on 2026-08-29 from the original
eight-minute suggestion to a 15-minute primary route. Ten-minute compression and
20-minute extension plans reuse the same evidence and do not introduce a new data
path.

## Architecture verification

- The browser reads live proof only through the relative Backend API route
  `/api/v1/freshness`.
- The browser does not connect directly to MariaDB, MinIO, Kafka, Spark, or
  Airflow.
- Dated engineering evidence is labelled as verification evidence rather than
  live production state.
- The Web App Docker image explicitly packages the Project Story assets.
- JavaScript rendering uses safe DOM operations and does not use `innerHTML`.

## Release evidence

The following checks passed on 2026-08-28:

- Python 3.12 presentation delivery gate: `69 passed, 7 skipped`.
- The seven skipped tests are opt-in integration suites for Airflow, archive
  operations, batch, Phase 9 analytics, SEC, serving, and streaming restart.
- Ruff lint gate: all checks passed.
- Ruff formatting gate: 125 files already formatted.
- `docker compose config --quiet` passed.
- JavaScript syntax checks passed for `web/app.js` and `web/showcase.js`.
- Nginx configuration check passed.
- All 18 Compose services were running and healthy.
- Project Story, Dashboard, Kafka UI, MinIO, Airflow, Spark master, Spark
  worker, Adminer, and Backend API documentation each returned HTTP 200.
- Presenter Console HTML, CSS, and JavaScript each returned HTTP 200; its timed
  routes were verified to total exactly 600, 900, and 1,200 seconds.
- The live API snapshot reported 7,196 Gold bars, 11 symbols, and 932 SEC
  filings. These values are a dated verification snapshot, not a permanent
  product claim.

## Visual verification note

Automated browser control could not start because the local Codex browser
connector rejected its runtime path as untrusted. HTTP responses, Nginx
routing, JavaScript syntax, DOM references, responsive CSS rules, API calls,
and service health were verified independently. Final visual acceptance still
requires opening the Project Story in the already-running local browser and
checking the tabs, phase selector, links, and responsive layout.

The same local Trusted Path limitation prevented automated visual inspection of
the Presenter Console on 2026-08-29. Static DOM checks found no missing or
duplicate identifiers; JavaScript syntax, route timing, responsive CSS, asset
packaging, HTTP responses, and service health passed. Manual visual acceptance
is still required for the 10/15/20-minute selectors, timer, cue navigation, and
Hebrew layout.

## Presentation format note

A standalone PowerPoint file was not generated because the required bundled
presentation workspace runtime was unavailable in this Codex session. The
responsive Project Story website is therefore the maintained presentation
artifact for Phase 10; the demo guide provides its speaker flow. This avoids
introducing an unverified presentation-generation dependency into the
repository.

## Restart and failure considerations

- The Project Story is static and restarts with the existing Web App service.
- If the Backend API is unavailable, the page displays an unavailable live
  proof state while the dated architecture story remains usable.
- External engineering interfaces are launch links only; their failure does
  not bypass the Backend API boundary or break the core presentation content.
