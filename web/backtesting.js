"use strict";

const API = "/api/v1";
const elements = {};
let currentDetail = null;

document.addEventListener("DOMContentLoaded", () => {
  ["backtest-state", "backtest-state-label", "run-count", "run-select", "backtest-symbol", "strategy-name", "strategy-window", "strategy-period", "strategy-costs", "strategy-benchmark", "backtest-message", "backtest-content", "data-diagnostic", "diagnostic-title", "diagnostic-message", "diagnostic-bars", "diagnostic-sessions", "diagnostic-trades", "metric-return", "metric-excess", "metric-benchmark", "metric-drawdown", "metric-sharpe", "metric-volatility", "equity-count", "equity-chart", "strategy-line", "benchmark-line", "strategy-point", "benchmark-point", "chart-start", "chart-end", "chart-note", "backtest-results"].forEach((id) => { elements[id] = document.getElementById(id); });
  elements["run-select"].addEventListener("change", loadRun);
  elements["backtest-symbol"].addEventListener("change", renderSelectedSymbol);
  loadRuns();
});

async function loadRuns() {
  setState("connecting", "Loading runs");
  showMessage("Loading published runs…");
  try {
    const page = await fetchJson(`${API}/backtests?page=1&page_size=100`);
    elements["run-count"].textContent = `${page.pagination.total} run${page.pagination.total === 1 ? "" : "s"}`;
    elements["run-select"].replaceChildren();
    page.items.forEach((run) => {
      const option = document.createElement("option");
      option.value = run.run_id;
      option.textContent = `${run.start_date} → ${run.end_date} · ${run.symbols.length} assets · ${run.status}`;
      elements["run-select"].append(option);
    });
    if (!page.items.length) {
      setState("ready", "No published runs");
      showMessage("No backtests have been published yet. Trigger historical_backtest in Airflow to create the first run.");
      return;
    }
    await loadRun();
    setState("ready", "API healthy");
  } catch (error) { showFailure(error); }
}

async function loadRun() {
  const runId = elements["run-select"].value;
  if (!runId) return;
  showMessage("Loading run metrics and lineage…");
  try {
    currentDetail = await fetchJson(`${API}/backtests/${encodeURIComponent(runId)}`);
    const run = currentDetail.run;
    elements["strategy-name"].textContent = `${run.strategy_code} · v${run.strategy_version}`;
    elements["strategy-window"].textContent = `SMA ${run.short_window} / ${run.long_window}`;
    elements["strategy-period"].textContent = `${run.start_date} → ${run.end_date}`;
    elements["strategy-costs"].textContent = `${formatNumber(Number(run.transaction_cost_bps) + Number(run.slippage_bps), 2)} bps / change`;
    elements["strategy-benchmark"].textContent = run.benchmark_symbol;
    elements["backtest-symbol"].replaceChildren();
    currentDetail.results.forEach((result) => {
      const option = document.createElement("option");
      option.value = result.symbol;
      option.textContent = result.symbol;
      elements["backtest-symbol"].append(option);
    });
    renderResultTable(currentDetail.results);
    renderDiagnostic(currentDetail);
    elements["backtest-message"].hidden = true;
    elements["backtest-content"].hidden = false;
    await renderSelectedSymbol();
  } catch (error) { showFailure(error); }
}

async function renderSelectedSymbol() {
  if (!currentDetail) return;
  const symbol = elements["backtest-symbol"].value;
  const result = currentDetail.results.find((item) => item.symbol === symbol);
  if (!result) return;
  setMetric("metric-return", result.total_return_pct);
  setMetric("metric-excess", result.excess_return_pct);
  setMetric("metric-drawdown", result.max_drawdown_pct);
  elements["metric-benchmark"].textContent = `${currentDetail.run.benchmark_symbol} return ${formatPercent(result.benchmark_return_pct)}`;
  elements["metric-sharpe"].textContent = result.sharpe_ratio === null ? "—" : formatNumber(result.sharpe_ratio, 2);
  elements["metric-volatility"].textContent = `Annualized volatility ${formatPercent(result.annualized_volatility_pct)}`;
  try {
    const equity = await fetchJson(`${API}/backtests/${encodeURIComponent(currentDetail.run.run_id)}/equity?symbol=${encodeURIComponent(symbol)}`);
    renderEquity(equity.items);
  } catch (error) { showFailure(error); }
}

function renderEquity(items) {
  elements["equity-count"].textContent = `${items.length} session${items.length === 1 ? "" : "s"}`;
  if (!items.length) {
    elements["strategy-line"].setAttribute("d", "");
    elements["benchmark-line"].setAttribute("d", "");
    elements["strategy-point"].hidden = true;
    elements["benchmark-point"].hidden = true;
    elements["chart-start"].textContent = "No daily equity points";
    elements["chart-end"].textContent = "—";
    elements["chart-note"].textContent = "No certified equity points were published for this selection.";
    return;
  }
  const values = items.flatMap((item) => [Number(item.equity), Number(item.benchmark_equity)]);
  let minimum = Math.min(...values);
  let maximum = Math.max(...values);
  if (minimum === maximum) { minimum *= 0.99; maximum *= 1.01; }
  const path = (field) => items.map((item, index) => {
    const x = 40 + (items.length === 1 ? 420 : index / (items.length - 1) * 840);
    const y = 240 - (Number(item[field]) - minimum) / (maximum - minimum) * 180;
    return `${index ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(" ");
  const singlePointPath = (field) => {
    const y = 240 - (Number(items[0][field]) - minimum) / (maximum - minimum) * 180;
    return `M40,${y.toFixed(2)} L880,${y.toFixed(2)}`;
  };
  elements["strategy-line"].setAttribute("d", items.length === 1 ? singlePointPath("equity") : path("equity"));
  elements["benchmark-line"].setAttribute("d", items.length === 1 ? singlePointPath("benchmark_equity") : path("benchmark_equity"));
  [
    ["strategy-point", "equity"],
    ["benchmark-point", "benchmark_equity"],
  ].forEach(([id, field]) => {
    const last = items.at(-1);
    const x = items.length === 1 ? 460 : 880;
    const y = 240 - (Number(last[field]) - minimum) / (maximum - minimum) * 180;
    elements[id].setAttribute("cx", x.toFixed(2));
    elements[id].setAttribute("cy", y.toFixed(2));
    elements[id].hidden = false;
  });
  elements["chart-start"].textContent = items[0].trading_date;
  elements["chart-end"].textContent = items.at(-1).trading_date;
  elements["chart-note"].textContent = items.length === 1
    ? "One certified session is available. The horizontal line is a real flat result, not missing chart data."
    : `${items.length} certified sessions are shown; strategy and benchmark may overlap when returns are equal.`;
  elements["equity-chart"].setAttribute("aria-label", `Equity curve from ${items[0].trading_date} through ${items.at(-1).trading_date}`);
}

function renderDiagnostic(detail) {
  const results = detail.results;
  const totalBars = results.reduce((total, result) => total + Number(result.observation_count), 0);
  const totalTrades = results.reduce((total, result) => total + Number(result.trade_count), 0);
  const oneSession = detail.run.start_date === detail.run.end_date;
  const flat = results.length > 0 && results.every((result) => Number(result.annualized_volatility_pct) === 0 && Number(result.total_return_pct) === 0);
  elements["diagnostic-bars"].textContent = totalBars.toLocaleString();
  elements["diagnostic-sessions"].textContent = oneSession ? "1" : `${detail.run.start_date} → ${detail.run.end_date}`;
  elements["diagnostic-trades"].textContent = totalTrades.toLocaleString();
  elements["data-diagnostic"].hidden = false;
  if (flat) {
    elements["diagnostic-title"].textContent = "Pipeline verified · market movement unavailable";
    elements["diagnostic-message"].textContent = "The certified verification input contains constant closing prices. The backtest completed correctly, but a flat price series cannot create volatility, crossovers, trades, or returns. Values shown as 0.00% are real results—not missing data.";
    elements["data-diagnostic"].dataset.state = "limited";
  } else if (oneSession) {
    elements["diagnostic-title"].textContent = "Single-session research run";
    elements["diagnostic-message"].textContent = "This result is valid but covers only one certified market session. Use a longer certified history before drawing strategy conclusions.";
    elements["data-diagnostic"].dataset.state = "limited";
  } else {
    elements["diagnostic-title"].textContent = "Certified historical run";
    elements["diagnostic-message"].textContent = "The run contains multiple certified sessions. Review assumptions and limitations before comparing results.";
    elements["data-diagnostic"].dataset.state = "ready";
  }
}

function renderResultTable(results) {
  elements["backtest-results"].replaceChildren();
  results.forEach((result) => {
    const row = document.createElement("tr");
    [result.symbol, formatPercent(result.total_return_pct), formatPercent(result.benchmark_return_pct), formatPercent(result.excess_return_pct), formatPercent(result.max_drawdown_pct), formatPercent(result.annualized_volatility_pct), result.sharpe_ratio === null ? "—" : formatNumber(result.sharpe_ratio, 2), String(result.trade_count), Number(result.observation_count).toLocaleString()].forEach((value, index) => {
      const cell = document.createElement("td");
      cell.textContent = value;
      if (index === 0) cell.className = "result-symbol";
      row.append(cell);
    });
    row.addEventListener("click", () => { elements["backtest-symbol"].value = result.symbol; renderSelectedSymbol(); });
    elements["backtest-results"].append(row);
  });
}

function setMetric(id, value) {
  const element = elements[id];
  const number = Number(value);
  element.textContent = formatPercent(number);
  element.classList.toggle("positive", number > 0);
  element.classList.toggle("negative", number < 0);
}

async function fetchJson(url) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  if (!response.ok) { const payload = await response.json().catch(() => ({})); throw new Error(payload.detail || `Request failed (${response.status})`); }
  return response.json();
}

function showMessage(message) { elements["backtest-content"].hidden = true; elements["backtest-message"].hidden = false; elements["backtest-message"].textContent = message; }
function showFailure(error) { setState("error", "API unavailable"); showMessage(error instanceof Error ? error.message : "Unable to load backtests"); }
function setState(state, label) { elements["backtest-state"].dataset.state = state; elements["backtest-state-label"].textContent = label; }
function formatPercent(value) { const number = Number(value); return `${number > 0 ? "+" : ""}${formatNumber(number, 2)}%`; }
function formatNumber(value, digits) { return Number(value).toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits }); }
