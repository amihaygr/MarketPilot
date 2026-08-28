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

The Nginx response includes a restrictive Content Security Policy and other basic
browser hardening headers. This local MVP does not implement end-user authentication.
