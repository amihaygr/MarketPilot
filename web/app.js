"use strict";

const API = "/api/v1";
const PAGE_SIZE = 50;
const state = {
  page: 1,
  totalPages: 0,
  bars: [],
  indicators: [],
};

const elements = {};

document.addEventListener("DOMContentLoaded", () => {
  captureElements();
  setDefaultDates();
  bindEvents();
  loadDashboard();
});

function captureElements() {
  [
    "system-state",
    "system-state-label",
    "generated-at",
    "asset-count",
    "latest-market-time",
    "latest-market-age",
    "bar-count",
    "certification-mix",
    "filing-count",
    "latest-filing-date",
    "symbol-filter",
    "start-date",
    "end-date",
    "status-filter",
    "market-filters",
    "bar-result-count",
    "chart-symbol",
    "chart-last-price",
    "chart-range",
    "price-line",
    "price-area",
    "sma-line",
    "chart-empty",
    "bars-body",
    "previous-page",
    "next-page",
    "page-label",
    "symbol-freshness",
    "filing-list",
    "rsi-value",
    "rsi-time",
    "sma-value",
    "volatility-value",
    "volume-ratio-value",
    "signal-symbol",
    "signal-count",
    "signal-list",
    "error-toast",
    "error-message",
  ].forEach((id) => {
    elements[id] = document.getElementById(id);
  });
}

function setDefaultDates() {
  const end = new Date();
  const start = new Date(end);
  start.setUTCDate(start.getUTCDate() - 7);
  elements["start-date"].value = dateInput(start);
  elements["end-date"].value = dateInput(end);
}

function bindEvents() {
  elements["market-filters"].addEventListener("submit", (event) => {
    event.preventDefault();
    state.page = 1;
    loadBars();
  });
  elements["previous-page"].addEventListener("click", () => {
    if (state.page > 1) {
      state.page -= 1;
      loadBars();
    }
  });
  elements["next-page"].addEventListener("click", () => {
    if (state.page < state.totalPages) {
      state.page += 1;
      loadBars();
    }
  });
}

async function loadDashboard() {
  setSystemState("connecting", "Connecting");
  try {
    const [symbols, freshness, filings] = await Promise.all([
      fetchJson(`${API}/symbols`),
      fetchJson(`${API}/freshness`),
      fetchJson(`${API}/sec-filings?page=1&page_size=6`),
    ]);
    renderSymbols(symbols.items);
    renderFreshness(freshness);
    renderFilings(filings.items);
    await loadBars();
    setSystemState("ready", "API healthy");
  } catch (error) {
    setSystemState("error", "API unavailable");
    showError(error);
  }
}

async function loadBars() {
  const symbol = elements["symbol-filter"].value;
  if (!symbol) return;
  const parameters = new URLSearchParams({
    symbol,
    start_utc: `${elements["start-date"].value}T00:00:00Z`,
    end_utc: `${elements["end-date"].value}T23:59:59Z`,
    page: String(state.page),
    page_size: String(PAGE_SIZE),
  });
  const status = elements["status-filter"].value;
  if (status) parameters.set("certification_status", status);
  try {
    const analyticsParameters = new URLSearchParams({
      symbol,
      start_utc: `${elements["start-date"].value}T00:00:00Z`,
      end_utc: `${elements["end-date"].value}T23:59:59Z`,
      page: "1",
      page_size: "200",
    });
    const signalParameters = new URLSearchParams(analyticsParameters);
    signalParameters.set("page_size", "25");
    const [result, indicators, signals] = await Promise.all([
      fetchJson(`${API}/market-bars?${parameters.toString()}`),
      fetchJson(`${API}/indicators?${analyticsParameters.toString()}`),
      fetchJson(`${API}/signals?${signalParameters.toString()}`),
    ]);
    state.bars = result.items;
    state.indicators = indicators.items;
    state.totalPages = result.pagination.total_pages;
    renderBars(result);
    renderAnalytics(indicators.items, signals);
  } catch (error) {
    showError(error);
  }
}

async function fetchJson(url) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch (_error) {
      // Keep the status-only message when the response is not JSON.
    }
    throw new Error(detail);
  }
  return response.json();
}

function renderSymbols(symbols) {
  elements["symbol-filter"].replaceChildren();
  symbols.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.symbol;
    option.textContent = item.symbol;
    elements["symbol-filter"].append(option);
  });
  if (symbols.some((item) => item.symbol === "AAPL")) {
    elements["symbol-filter"].value = "AAPL";
  }
  elements["asset-count"].textContent = number(symbols.length);
}

function renderFreshness(data) {
  elements["generated-at"].textContent = formatTimestamp(data.generated_at_utc);
  elements["latest-market-time"].textContent = formatTimestamp(data.market.latest_event_time_utc);
  elements["latest-market-age"].textContent = ageLabel(data.market.latest_event_time_utc);
  elements["bar-count"].textContent = number(data.market.bar_count);
  elements["certification-mix"].textContent =
    `${number(data.market.certified_count)} certified · ${number(data.market.provisional_count)} provisional`;
  elements["filing-count"].textContent = number(data.sec.filing_count);
  elements["latest-filing-date"].textContent = data.sec.latest_filing_date
    ? `Latest filing ${data.sec.latest_filing_date}`
    : "No filing data";

  elements["symbol-freshness"].replaceChildren();
  data.symbols.forEach((item) => {
    const row = document.createElement("div");
    row.className = "pulse-row";
    const symbol = document.createElement("strong");
    symbol.textContent = item.symbol;
    const copy = document.createElement("div");
    copy.className = "pulse-copy";
    const time = document.createElement("time");
    time.textContent = formatCompactTimestamp(item.latest_event_time_utc);
    const status = document.createElement("span");
    status.textContent = item.latest_certification_status || "NO DATA";
    copy.append(time, status);
    const indicator = document.createElement("span");
    indicator.className = `pulse-indicator ${
      item.latest_certification_status === "PROVISIONAL" ? "provisional" : ""
    }`;
    row.append(symbol, copy, indicator);
    elements["symbol-freshness"].append(row);
  });
}

function renderBars(result) {
  const bars = result.items;
  const pagination = result.pagination;
  elements["bar-result-count"].textContent = `${number(pagination.total)} results`;
  elements["page-label"].textContent =
    pagination.total_pages === 0 ? "No pages" : `Page ${pagination.page} of ${pagination.total_pages}`;
  elements["previous-page"].disabled = pagination.page <= 1;
  elements["next-page"].disabled = pagination.page >= pagination.total_pages;
  elements["chart-symbol"].textContent = elements["symbol-filter"].value;
  elements["chart-range"].textContent =
    `${elements["start-date"].value} → ${elements["end-date"].value}`;

  elements["bars-body"].replaceChildren();
  bars.forEach((bar) => {
    const row = document.createElement("tr");
    row.append(
      cell(formatTimestamp(bar.event_time_utc)),
      cell(price(bar.open)),
      cell(price(bar.high)),
      cell(price(bar.low)),
      cell(price(bar.close)),
      cell(number(bar.volume)),
      statusCell(bar.certification_status),
    );
    elements["bars-body"].append(row);
  });
  renderChart(bars, state.indicators);
}

function renderChart(bars, indicators) {
  const ordered = [...bars].reverse();
  if (!ordered.length) {
    elements["price-line"].setAttribute("d", "");
    elements["price-area"].setAttribute("d", "");
    elements["sma-line"].setAttribute("d", "");
    elements["chart-last-price"].textContent = "—";
    elements["chart-empty"].hidden = false;
    return;
  }
  elements["chart-empty"].hidden = true;
  const values = ordered.map((bar) => Number(bar.close));
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const spread = maximum - minimum || 1;
  const x = (index) => 20 + (index / Math.max(values.length - 1, 1)) * 860;
  const y = (value) => 215 - ((value - minimum) / spread) * 175;
  const points = values.map((value, index) => `${x(index).toFixed(2)},${y(value).toFixed(2)}`);
  const line = points.map((point, index) => `${index === 0 ? "M" : "L"}${point}`).join(" ");
  const area = `${line} L${x(values.length - 1).toFixed(2)},225 L20,225 Z`;
  elements["price-line"].setAttribute("d", line);
  elements["price-area"].setAttribute("d", area);
  const smaByTime = new Map(
    indicators
      .filter((item) => item.indicator_code === "SMA_20")
      .map((item) => [new Date(item.event_time_utc).getTime(), Number(item.value)]),
  );
  const smaPoints = ordered
    .map((bar, index) => {
      const value = smaByTime.get(new Date(bar.event_time_utc).getTime());
      return value === undefined ? null : `${x(index).toFixed(2)},${y(value).toFixed(2)}`;
    })
    .filter(Boolean);
  elements["sma-line"].setAttribute(
    "d",
    smaPoints.map((point, index) => `${index === 0 ? "M" : "L"}${point}`).join(" "),
  );
  elements["chart-last-price"].textContent = `$${price(ordered.at(-1).close)}`;
}

function renderAnalytics(indicators, signals) {
  const latest = (code) => indicators.find((item) => item.indicator_code === code);
  const rsi = latest("RSI_14");
  const sma = latest("SMA_20");
  const volatility = latest("REALIZED_VOLATILITY_20");
  const volumeRatio = latest("VOLUME_RATIO_20");
  elements["rsi-value"].textContent = rsi ? Number(rsi.value).toFixed(2) : "—";
  elements["rsi-time"].textContent = rsi
    ? `${formatCompactTimestamp(rsi.event_time_utc)} · ${rsi.certification_status}`
    : "Waiting for analytics";
  elements["sma-value"].textContent = sma ? `$${price(sma.value)}` : "—";
  elements["volatility-value"].textContent = volatility
    ? `${Number(volatility.value).toFixed(2)}%`
    : "—";
  elements["volume-ratio-value"].textContent = volumeRatio
    ? `${Number(volumeRatio.value).toFixed(2)}×`
    : "—";
  elements["signal-symbol"].textContent = elements["symbol-filter"].value;
  elements["signal-count"].textContent = `${number(signals.pagination.total)} signals`;
  elements["signal-list"].replaceChildren();
  if (!signals.items.length) {
    const empty = document.createElement("div");
    empty.className = "analytics-empty";
    const icon = document.createElement("span");
    icon.className = "empty-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = "✓";
    const title = document.createElement("strong");
    title.textContent = "No notable threshold crossings";
    const detail = document.createElement("small");
    detail.textContent = "The selected range contains no explained signal events.";
    empty.append(icon, title, detail);
    elements["signal-list"].append(empty);
    return;
  }
  signals.items.forEach((signal) => {
    const card = document.createElement("article");
    card.className = `signal-card signal-${signal.direction.toLowerCase()}`;
    const top = document.createElement("div");
    const direction = document.createElement("strong");
    direction.textContent = signal.direction;
    const time = document.createElement("time");
    time.textContent = formatTimestamp(signal.signal_time_utc);
    top.append(direction, time);
    const code = document.createElement("span");
    code.textContent = signal.signal_code.replaceAll("_", " ");
    const explanation = document.createElement("p");
    explanation.textContent = signal.explanation;
    const strength = document.createElement("small");
    strength.textContent = `Strength ${Math.round(Number(signal.strength) * 100)}% · ${signal.certification_status}`;
    card.append(top, code, explanation, strength);
    elements["signal-list"].append(card);
  });
}

function renderFilings(filings) {
  elements["filing-list"].replaceChildren();
  filings.forEach((filing) => {
    const safeSource = secSourceUrl(filing.source_url);
    const card = safeSource ? document.createElement("a") : document.createElement("article");
    card.className = "filing-card";
    if (safeSource) {
      card.href = safeSource;
      card.target = "_blank";
      card.rel = "noopener noreferrer";
    }
    const top = document.createElement("div");
    top.className = "filing-card-top";
    const form = document.createElement("span");
    form.className = "filing-form";
    form.textContent = filing.form_type;
    const filed = document.createElement("time");
    filed.textContent = filing.filing_date;
    top.append(form, filed);
    const title = document.createElement("h3");
    title.textContent = `${filing.symbol} · ${filing.company_name}`;
    const accession = document.createElement("small");
    accession.textContent = filing.accession_number;
    card.append(top, title, accession);
    elements["filing-list"].append(card);
  });
}

function cell(value) {
  const element = document.createElement("td");
  element.textContent = value;
  return element;
}

function statusCell(status) {
  const element = document.createElement("td");
  const pill = document.createElement("span");
  pill.className = `status-pill ${
    status === "CERTIFIED" ? "status-certified" : "status-provisional"
  }`;
  pill.textContent = status;
  element.append(pill);
  return element;
}

function setSystemState(mode, label) {
  elements["system-state"].className = `system-state ${mode}`;
  elements["system-state-label"].textContent = label;
}

function showError(error) {
  elements["error-message"].textContent = error instanceof Error ? error.message : "Please try again.";
  elements["error-toast"].hidden = false;
  window.setTimeout(() => {
    elements["error-toast"].hidden = true;
  }, 6000);
}

function dateInput(value) {
  return value.toISOString().slice(0, 10);
}

function formatTimestamp(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: "UTC",
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(new Date(value));
}

function formatCompactTimestamp(value) {
  if (!value) return "No market bars";
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: "UTC",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(value));
}

function ageLabel(value) {
  if (!value) return "No market data";
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return `${seconds}s behind wall clock`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m behind wall clock`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h behind wall clock`;
  return `${Math.floor(seconds / 86400)}d behind wall clock`;
}

function number(value) {
  return new Intl.NumberFormat("en-US").format(Number(value || 0));
}

function price(value) {
  return Number(value).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  });
}

function secSourceUrl(value) {
  try {
    const url = new URL(value);
    if (url.protocol === "https:" && (url.hostname === "sec.gov" || url.hostname.endsWith(".sec.gov"))) {
      return url.href;
    }
  } catch (_error) {
    return null;
  }
  return null;
}
