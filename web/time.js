"use strict";

(function exposeMarketPilotTime() {
  const TIME_ZONE = "Asia/Jerusalem";
  const TIME_ZONE_LABEL = "Israel time";

  const fullFormatter = new Intl.DateTimeFormat("en-GB", {
    timeZone: TIME_ZONE,
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });

  const compactFormatter = new Intl.DateTimeFormat("en-GB", {
    timeZone: TIME_ZONE,
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });

  function format(value, formatter, emptyValue) {
    if (!value) return emptyValue;
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return emptyValue;
    return `${formatter.format(parsed)} · ${TIME_ZONE_LABEL}`;
  }

  window.MarketPilotTime = Object.freeze({
    timeZone: TIME_ZONE,
    label: TIME_ZONE_LABEL,
    formatTimestamp(value) {
      return format(value, fullFormatter, "—");
    },
    formatCompactTimestamp(value) {
      return format(value, compactFormatter, "No market bars");
    },
  });
})();
