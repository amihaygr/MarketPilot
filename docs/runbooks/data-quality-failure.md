# Data Quality Failure Runbook

1. Keep the failed partition unpublished.
2. Record check name, observed value, expected value, dataset and run ID.
3. Compare source count, Bronze count, Silver count and Gold count.
4. Inspect duplicate keys, null required fields, OHLC violations and session coverage.
5. Correct code or source mapping through a reviewed change.
6. Replay only the affected date and symbol scope.
7. Re-run all gates, not only the originally failed check.
8. Advance the certified watermark only after every blocking check passes.
