# Web App

The Phase 7 Web App is a dependency-free static dashboard served by Nginx at
<http://localhost:3000>. Nginx proxies relative `/api/` requests to `backend-api`,
so browser code never receives MariaDB, MinIO, Alpaca, or internal network details.

The dashboard provides:

- asset and freshness summaries;
- linked asset, date-range, and certification filters;
- one-click 1D, 5D, 7D, and 30D exploration presets;
- an interactive one-minute chart with keyboard/pointer inspection and Close/SMA toggles;
- visible-range price, high, low, and average-volume context;
- explainable Indicator cards and client-side Signal direction filters;
- a paginated OHLCV detail table;
- recent SEC filing links;
- explicit `PROVISIONAL` and `CERTIFIED` status labels.

Asset pulse rows are interactive and update the entire analytical workspace. The
dashboard uses bounded Backend API requests only; all summary values shown in the
browser are derived from those responses and are descriptive research context, not
investment advice.

The same Nginx service also publishes `showcase.html`, a separate Project Story
for reviewers and live demonstrations. It reuses the visual language but does not
turn the analytical dashboard into a marketing page. Its only runtime request is
the existing relative `/api/v1/freshness` endpoint; dated verification evidence is
rendered as clearly labelled static project documentation.

`presenter.html` is a separate, read-only Presenter Console. It provides 10, 15,
and 20-minute routes, a local timer, Hebrew speaker cues, transitions, screen links,
and safe fallbacks. It makes no API or data-plane request and cannot mutate project
state. The canonical timing and expanded learning materials live under
`docs/demo-guide.md` and `docs/presentation/`.

The Nginx response includes a restrictive Content Security Policy and other basic
browser hardening headers. This local MVP does not implement end-user authentication.

`backtesting.html` is the Phase 11 historical research view. It uses only the
read-only `/api/v1/backtests` endpoints and provides run, symbol, assumption, KPI,
equity-curve, result-table, methodology, and limitation views. The page does not
execute a strategy in the browser and does not read MinIO directly.
