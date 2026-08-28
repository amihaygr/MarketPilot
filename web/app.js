"use strict";

const API = "/api/v1";
const PAGE_SIZE = 50;
const state = {
  page: 1,
  totalPages: 0,
  bars: [],
  chartBars: [],
  indicators: [],
  smaIndicators: [],
  signals: null,
  signalDirection: "ALL",
  series: { price: true, sma: true },
  chartModel: null,
  chartFocusIndex: null,
  requestSequence: 0,
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
    "apply-filters",
    "bar-result-count",
    "live-selection",
    "chart-symbol",
    "chart-last-price",
    "chart-range",
    "price-line",
    "price-area",
    "sma-line",
    "price-chart",
    "toggle-price",
    "toggle-sma",
    "chart-crosshair",
    "chart-focus-dot",
    "chart-hit-area",
    "chart-tooltip",
    "tooltip-time",
    "tooltip-price",
    "tooltip-sma",
    "tooltip-volume",
    "chart-empty",
    "range-change",
    "range-high",
    "range-low",
    "average-volume",
    "bars-body",
    "previous-page",
    "next-page",
    "page-label",
    "symbol-freshness",
    "filing-list",
    "rsi-value",
    "rsi-meter",
    "rsi-context",
    "rsi-time",
    "sma-value",
    "sma-context",
    "volatility-value",
    "volatility-context",
    "volume-ratio-value",
    "volume-context",
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
  start.setUTCDate(start.getUTCDate() - 6);
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
  elements["symbol-filter"].addEventListener("change", () => {
    state.page = 1;
    updateSelectedAsset();
    loadBars();
  });
  document.querySelectorAll(".range-button").forEach((button) => {
    button.addEventListener("click", () => applyRangePreset(Number(button.dataset.days)));
  });
  [elements["start-date"], elements["end-date"]].forEach((input) => {
    input.addEventListener("change", () => {
      document.querySelectorAll(".range-button").forEach((button) => {
        button.classList.remove("active");
        button.setAttribute("aria-pressed", "false");
      });
      updateSelectedAsset();
    });
  });
  document.querySelectorAll(".signal-filter").forEach((button) => {
    button.addEventListener("click", () => {
      state.signalDirection = button.dataset.direction;
      document.querySelectorAll(".signal-filter").forEach((candidate) => {
        const active = candidate === button;
        candidate.classList.toggle("active", active);
        candidate.setAttribute("aria-pressed", String(active));
      });
      renderSignals();
    });
  });
  elements["toggle-price"].addEventListener("click", () => toggleSeries("price"));
  elements["toggle-sma"].addEventListener("click", () => toggleSeries("sma"));
  elements["chart-hit-area"].addEventListener("pointermove", handleChartPointer);
  elements["chart-hit-area"].addEventListener("pointerleave", hideChartTooltip);
  elements["price-chart"].addEventListener("keydown", handleChartKeyboard);
  elements["price-chart"].addEventListener("blur", hideChartTooltip);
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
  if (elements["start-date"].value > elements["end-date"].value) {
    showError(new Error("The start date must be on or before the end date."));
    return;
  }
  const requestSequence = ++state.requestSequence;
  const parameters = new URLSearchParams({
    symbol,
    start_utc: `${elements["start-date"].value}T00:00:00Z`,
    end_utc: `${elements["end-date"].value}T23:59:59Z`,
    page: String(state.page),
    page_size: String(PAGE_SIZE),
  });
  const status = elements["status-filter"].value;
  if (status) parameters.set("certification_status", status);
  setLoading(true);
  try {
    const chartParameters = new URLSearchParams(parameters);
    chartParameters.set("page", "1");
    chartParameters.set("page_size", "200");
    const analyticsParameters = new URLSearchParams({
      symbol,
      start_utc: `${elements["start-date"].value}T00:00:00Z`,
      end_utc: `${elements["end-date"].value}T23:59:59Z`,
      page: "1",
      page_size: "200",
    });
    const signalParameters = new URLSearchParams(analyticsParameters);
    signalParameters.set("page_size", "25");
    const smaParameters = new URLSearchParams(analyticsParameters);
    smaParameters.set("indicator_code", "SMA_20");
    const [result, chartResult, indicators, smaIndicators, signals] = await Promise.all([
      fetchJson(`${API}/market-bars?${parameters.toString()}`),
      fetchJson(`${API}/market-bars?${chartParameters.toString()}`),
      fetchJson(`${API}/indicators?${analyticsParameters.toString()}`),
      fetchJson(`${API}/indicators?${smaParameters.toString()}`),
      fetchJson(`${API}/signals?${signalParameters.toString()}`),
    ]);
    if (requestSequence !== state.requestSequence) return;
    state.bars = result.items;
    state.chartBars = chartResult.items;
    state.indicators = indicators.items;
    state.smaIndicators = smaIndicators.items;
    state.signals = signals;
    state.totalPages = result.pagination.total_pages;
    renderBars(result);
    renderAnalytics(indicators.items, signals);
    renderMarketSnapshot(chartResult.items);
    renderChart(chartResult.items, smaIndicators.items);
    updateSelectedAsset();
  } catch (error) {
    showError(error);
  } finally {
    if (requestSequence === state.requestSequence) setLoading(false);
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
    const row = document.createElement("button");
    row.type = "button";
    row.className = "pulse-row";
    row.dataset.symbol = item.symbol;
    row.setAttribute("aria-label", `Explore ${item.symbol}`);
    row.addEventListener("click", () => selectAsset(item.symbol));
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
  updateSelectedAsset();
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
}

function renderChart(bars, indicators) {
  hideChartTooltip();
  const ordered = [...bars].reverse();
  if (!ordered.length) {
    elements["price-line"].setAttribute("d", "");
    elements["price-area"].setAttribute("d", "");
    elements["sma-line"].setAttribute("d", "");
    elements["chart-last-price"].textContent = "—";
    elements["chart-empty"].hidden = false;
    state.chartModel = null;
    hideChartTooltip();
    return;
  }
  elements["chart-empty"].hidden = true;
  const closeValues = ordered.map((bar) => Number(bar.close));
  const smaByTime = new Map(
    indicators.map((item) => [new Date(item.event_time_utc).getTime(), Number(item.value)]),
  );
  const smaValues = ordered
    .map((bar) => smaByTime.get(new Date(bar.event_time_utc).getTime()))
    .filter((value) => value !== undefined);
  const visibleValues = [
    ...(state.series.price ? closeValues : []),
    ...(state.series.sma ? smaValues : []),
  ];
  const minimum = Math.min(...visibleValues);
  const maximum = Math.max(...visibleValues);
  const spread = maximum - minimum || 1;
  const x = (index) => 20 + (index / Math.max(closeValues.length - 1, 1)) * 860;
  const y = (value) => 215 - ((value - minimum) / spread) * 175;
  const points = closeValues.map((value, index) => ({
    x: x(index),
    y: y(
      state.series.price
        ? value
        : smaByTime.get(new Date(ordered[index].event_time_utc).getTime()) ?? value,
    ),
    value,
    bar: ordered[index],
    sma: smaByTime.get(new Date(ordered[index].event_time_utc).getTime()),
  }));
  const line = points
    .map((point, index) => `${index === 0 ? "M" : "L"}${point.x.toFixed(2)},${point.y.toFixed(2)}`)
    .join(" ");
  const area = `${line} L${x(closeValues.length - 1).toFixed(2)},225 L20,225 Z`;
  elements["price-line"].setAttribute("d", line);
  elements["price-area"].setAttribute("d", area);
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
  elements["price-line"].hidden = !state.series.price;
  elements["price-area"].hidden = !state.series.price;
  elements["sma-line"].hidden = !state.series.sma;
  elements["chart-last-price"].textContent = `$${price(ordered.at(-1).close)}`;
  state.chartModel = { points };
  state.chartFocusIndex = points.length - 1;
}

function renderAnalytics(indicators, signals) {
  const latest = (code) => indicators.find((item) => item.indicator_code === code);
  const rsi = latest("RSI_14");
  const sma = latest("SMA_20");
  const volatility = latest("REALIZED_VOLATILITY_20");
  const volumeRatio = latest("VOLUME_RATIO_20");
  const rsiValue = rsi ? Number(rsi.value) : null;
  elements["rsi-value"].textContent = rsiValue === null ? "—" : rsiValue.toFixed(2);
  elements["rsi-meter"].style.width = `${Math.min(100, Math.max(0, rsiValue || 0))}%`;
  elements["rsi-context"].textContent = rsiContext(rsiValue);
  elements["rsi-time"].textContent = rsi
    ? `${formatCompactTimestamp(rsi.event_time_utc)} · ${rsi.certification_status}`
    : "No analytics in range";
  elements["sma-value"].textContent = sma ? `$${price(sma.value)}` : "—";
  const latestClose = state.chartBars.length ? Number(state.chartBars[0].close) : null;
  elements["sma-context"].replaceChildren();
  const legend = document.createElement("span");
  legend.className = "legend-line";
  legend.setAttribute("aria-hidden", "true");
  elements["sma-context"].append(
    legend,
    document.createTextNode(smaContext(latestClose, sma ? Number(sma.value) : null)),
  );
  elements["volatility-value"].textContent = volatility
    ? `${Number(volatility.value).toFixed(2)}%`
    : "—";
  elements["volatility-context"].textContent = volatilityContext(
    volatility ? Number(volatility.value) : null,
  );
  elements["volume-ratio-value"].textContent = volumeRatio
    ? `${Number(volumeRatio.value).toFixed(2)}×`
    : "—";
  elements["volume-context"].textContent = volumeContext(
    volumeRatio ? Number(volumeRatio.value) : null,
  );
  elements["signal-symbol"].textContent = elements["symbol-filter"].value;
  state.signals = signals;
  renderSignals();
}

function renderSignals() {
  if (!state.signals) return;
  const filtered = state.signals.items.filter(
    (signal) => state.signalDirection === "ALL" || signal.direction === state.signalDirection,
  );
  elements["signal-count"].textContent =
    state.signalDirection === "ALL"
      ? `${number(state.signals.pagination.total)} signals`
      : `${number(filtered.length)} shown · ${number(state.signals.pagination.total)} total`;
  elements["signal-list"].replaceChildren();
  if (!filtered.length) {
    const empty = document.createElement("div");
    empty.className = "analytics-empty";
    const icon = document.createElement("span");
    icon.className = "empty-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = "✓";
    const title = document.createElement("strong");
    title.textContent =
      state.signalDirection === "ALL"
        ? "No notable threshold crossings"
        : `No ${state.signalDirection.toLowerCase()} observations`;
    const detail = document.createElement("small");
    detail.textContent = "The selected range contains no explained signal events.";
    empty.append(icon, title, detail);
    elements["signal-list"].append(empty);
    return;
  }
  filtered.forEach((signal) => {
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

function applyRangePreset(days) {
  const end = new Date();
  const start = new Date(end);
  start.setUTCDate(start.getUTCDate() - Math.max(0, days - 1));
  elements["start-date"].value = dateInput(start);
  elements["end-date"].value = dateInput(end);
  document.querySelectorAll(".range-button").forEach((button) => {
    const active = Number(button.dataset.days) === days;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  state.page = 1;
  updateSelectedAsset();
  loadBars();
}

function selectAsset(symbol) {
  if (!Array.from(elements["symbol-filter"].options).some((option) => option.value === symbol)) {
    return;
  }
  elements["symbol-filter"].value = symbol;
  state.page = 1;
  updateSelectedAsset();
  loadBars();
  document.querySelector(".market-panel").scrollIntoView({ behavior: "smooth", block: "start" });
}

function updateSelectedAsset() {
  const symbol = elements["symbol-filter"].value || "—";
  const activeRange = document.querySelector(".range-button.active")?.textContent || "CUSTOM";
  elements["live-selection"].textContent = `${symbol} · ${activeRange}`;
  document.querySelectorAll(".pulse-row").forEach((row) => {
    const selected = row.dataset.symbol === symbol;
    row.classList.toggle("selected", selected);
    row.setAttribute("aria-pressed", String(selected));
  });
}

function setLoading(loading) {
  elements["apply-filters"].classList.toggle("loading", loading);
  elements["apply-filters"].disabled = loading;
  elements["apply-filters"].setAttribute("aria-busy", String(loading));
}

function renderMarketSnapshot(bars) {
  const ordered = [...bars].reverse();
  if (!ordered.length) {
    ["range-change", "range-high", "range-low", "average-volume"].forEach((id) => {
      elements[id].textContent = "—";
    });
    return;
  }
  const first = Number(ordered[0].close);
  const last = Number(ordered.at(-1).close);
  const change = ((last - first) / first) * 100;
  const highs = ordered.map((bar) => Number(bar.high));
  const lows = ordered.map((bar) => Number(bar.low));
  const averageVolume = ordered.reduce((sum, bar) => sum + Number(bar.volume), 0) / ordered.length;
  elements["range-change"].textContent = `${change >= 0 ? "+" : ""}${change.toFixed(2)}%`;
  elements["range-change"].className = change >= 0 ? "value-positive" : "value-negative";
  elements["range-high"].textContent = `$${price(Math.max(...highs))}`;
  elements["range-low"].textContent = `$${price(Math.min(...lows))}`;
  elements["average-volume"].textContent = compactNumber(averageVolume);
}

function toggleSeries(series) {
  const other = series === "price" ? "sma" : "price";
  if (state.series[series] && !state.series[other]) return;
  if (series === "price" && state.series.price && !state.smaIndicators.length) return;
  state.series[series] = !state.series[series];
  elements[`toggle-${series}`].setAttribute("aria-pressed", String(state.series[series]));
  renderChart(state.chartBars, state.smaIndicators);
}

function handleChartPointer(event) {
  if (!state.chartModel?.points.length) return;
  const rectangle = elements["price-chart"].getBoundingClientRect();
  const viewX = ((event.clientX - rectangle.left) / rectangle.width) * 900;
  const index = Math.round(
    ((Math.min(880, Math.max(20, viewX)) - 20) / 860) * (state.chartModel.points.length - 1),
  );
  showChartPoint(index);
}

function handleChartKeyboard(event) {
  if (!state.chartModel?.points.length || !["ArrowLeft", "ArrowRight"].includes(event.key)) return;
  event.preventDefault();
  const delta = event.key === "ArrowRight" ? 1 : -1;
  const current = state.chartFocusIndex ?? state.chartModel.points.length - 1;
  showChartPoint(Math.min(state.chartModel.points.length - 1, Math.max(0, current + delta)));
}

function showChartPoint(index) {
  const point = state.chartModel?.points[index];
  if (!point) return;
  state.chartFocusIndex = index;
  elements["chart-crosshair"].hidden = false;
  elements["chart-focus-dot"].hidden = false;
  elements["chart-crosshair"].setAttribute("x1", point.x.toFixed(2));
  elements["chart-crosshair"].setAttribute("x2", point.x.toFixed(2));
  elements["chart-focus-dot"].setAttribute("cx", point.x.toFixed(2));
  elements["chart-focus-dot"].setAttribute("cy", point.y.toFixed(2));
  elements["tooltip-time"].textContent = formatTimestamp(point.bar.event_time_utc);
  elements["tooltip-price"].textContent = `$${price(point.value)}`;
  elements["tooltip-sma"].textContent = point.sma ? `SMA $${price(point.sma)}` : "SMA unavailable";
  elements["tooltip-volume"].textContent = `Volume ${number(point.bar.volume)}`;
  const chartWidth = elements["price-chart"].clientWidth;
  const tooltipX = Math.min(chartWidth - 82, Math.max(82, (point.x / 900) * chartWidth));
  elements["chart-tooltip"].style.left = `${tooltipX}px`;
  elements["chart-tooltip"].hidden = false;
}

function hideChartTooltip() {
  elements["chart-crosshair"].hidden = true;
  elements["chart-focus-dot"].hidden = true;
  elements["chart-tooltip"].hidden = true;
}

function rsiContext(value) {
  if (value === null) return "No RSI values in this range";
  if (value >= 70) return "Upper momentum zone · descriptive only";
  if (value <= 30) return "Lower momentum zone · descriptive only";
  return "Neutral momentum zone";
}

function smaContext(close, sma) {
  if (close === null || sma === null) return "Dashed overlay unavailable in this range";
  const distance = ((close - sma) / sma) * 100;
  return `Close is ${Math.abs(distance).toFixed(2)}% ${distance >= 0 ? "above" : "below"} SMA 20`;
}

function volatilityContext(value) {
  if (value === null) return "No volatility values in this range";
  if (value < 20) return "Lower annualized realized volatility";
  if (value < 40) return "Moderate annualized realized volatility";
  return "Elevated annualized realized volatility";
}

function volumeContext(value) {
  if (value === null) return "No volume-ratio values in this range";
  if (value >= 1.5) return "Volume is elevated versus the prior window";
  if (value <= 0.7) return "Volume is below the prior-window mean";
  return "Volume is near the prior-window mean";
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

function compactNumber(value) {
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(Number(value || 0));
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
