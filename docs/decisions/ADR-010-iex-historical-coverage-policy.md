# ADR-010: Feed-aware IEX historical coverage policy

- Status: Accepted
- Date: 2026-09-17

## Context

The first governed Phase 15 historical window fetched all requested symbols and
archived every source page, but the Silver quality gate rejected 22 of 23 trading
sessions. The previous rule required every symbol to contain at least 80 percent
of the 390-minute consolidated XNYS session.

That rule is appropriate for a consolidated SIP feed, but Alpaca's free IEX feed
contains trades reported by one exchange. It legitimately omits a minute when no
IEX trade occurred for that symbol. In the observed 2024-09-17 through 2024-10-17
window, active symbols commonly contained 350-390 bars while UNH contained as few
as 148. The complete eleven-symbol universe still contained 3,716-4,103 bars per
session and every requested symbol was present.

Lowering one universal threshold would hide weak sessions. Synthesizing missing
minutes would also create evidence that Alpaca never supplied.

## Decision

Historical IEX certification uses two blocking completeness checks:

1. Every requested symbol must be present and contain at least 35 percent of the
   expected regular-session minutes.
2. The complete requested universe must contain at least 80 percent of the
   expected regular-session bars across all symbols.

All existing null, duplicate, OHLC, schema, lineage, logical-date and freshness
checks remain blocking. Missing minutes remain missing and visible. The source is
retained as `IEX`, so downstream confidence and model documentation continue to
identify the feed as partial.

The daily close pipeline remains stricter. A future entitled SIP backfill must use
the original 80 percent per-symbol threshold (or a stricter documented policy),
not the IEX profile.

## Consequences

The policy accepts real single-exchange sparsity without weakening aggregate
session completeness. A symbol with fewer than 35 percent of expected minutes or
a universe below 80 percent still fails certification. The separate metrics are
persisted in `data_quality_result`, making the decision auditable and preventing a
high-volume symbol from silently masking a missing symbol.
