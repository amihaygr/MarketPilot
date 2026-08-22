# Backend API

The Backend API is the only application-facing access path to MariaDB Gold.

Planned responsibilities:

- symbols and market bars;
- indicators and signals;
- SEC filing metadata;
- backtest results;
- freshness and certification status;
- pagination and bounded date filters.

Use a narrowly scoped database identity. The API must not expose storage credentials.
