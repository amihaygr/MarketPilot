# Web App

The Phase 7 Web App is a dependency-free static dashboard served by Nginx at
<http://localhost:3000>. Nginx proxies relative `/api/` requests to `backend-api`,
so browser code never receives MariaDB, MinIO, Alpaca, or internal network details.

The dashboard provides:

- asset and freshness summaries;
- symbol, date, and certification filters;
- a one-minute close-price chart and paginated OHLCV table;
- recent SEC filing links;
- explicit `PROVISIONAL` and `CERTIFIED` status labels.

The Nginx response includes a restrictive Content Security Policy and other basic
browser hardening headers. This local MVP does not implement end-user authentication.
