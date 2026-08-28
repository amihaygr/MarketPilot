"use strict";

const paths = {
  live: {
    owner: "DOCKER COMPOSE · LONG-RUNNING",
    title: "Fresh market context reaches Gold without waiting for a daily DAG.",
    description:
      "Alpaca bars enter the versioned producer, cross Kafka, and are consumed by durable Spark Structured Streaming. Business-key upserts publish provisional application data and recover from checkpoints after restart.",
    outcome: "Low-latency, provisional Gold with restart continuity",
    nodes: ["Alpaca", "market-producer", "Kafka", "Spark Streaming", "MariaDB Gold"],
  },
  certified: {
    owner: "AIRFLOW · BOUNDED SPARK JOBS",
    title: "Closed data is rebuilt from raw history before it becomes certified.",
    description:
      "Airflow submits bounded Spark applications in an explicit Bronze-to-Silver-to-Gold sequence. Blocking quality checks must pass before the atomic publisher replaces the requested partition and advances its watermark.",
    outcome: "Clean, lineage-bearing, certified Gold",
    nodes: ["Bronze", "Spark Batch", "Silver Parquet", "DQ gate", "Certified Gold"],
  },
  archive: {
    owner: "KAFKA SINK + BOUNDED OPERATIONS",
    title: "The serving database is never the only copy of history.",
    description:
      "Kafka offsets are archived into immutable Bronze for replay. Closed-period exports produce Parquet objects, SHA-256 inventories, and MariaDB manifests. Restore drills target isolated schemas and never mutate live Gold.",
    outcome: "Replayable raw history and verified recovery evidence",
    nodes: ["Kafka offsets", "MinIO Bronze", "Parquet archive", "Hash manifest", "Isolated restore"],
  },
};

const phases = {
  0: {
    label: "PHASES 0–2",
    title: "A reproducible event enters Kafka and survives as immutable Bronze.",
    description:
      "Repository rules, core infrastructure, a versioned event contract, deterministic production, and quarantine behavior establish the first trusted vertical slice.",
    proof: "Proof: the same Kafka record maps to one recoverable Bronze object.",
  },
  3: {
    label: "PHASES 3–5",
    title: "The live and certified paths become independently operable.",
    description:
      "Structured Streaming publishes provisional Gold with durable checkpoints. Spark Batch creates Silver and certified Gold, while Airflow owns only bounded scheduling and quality gates.",
    proof: "Proof: restart recovery and partition reprocessing preserve unique business keys.",
  },
  6: {
    label: "PHASES 6–7",
    title: "Real sources become a safe, read-only product experience.",
    description:
      "Alpaca and SEC adapters preserve the tested contracts. A narrow API identity exposes bounded data to an Nginx-served application without leaking storage or database access to the browser.",
    proof: "Proof: live source authentication succeeds while the application identity is denied writes.",
  },
  8: {
    label: "PHASES 8–9",
    title: "Recovery and explainability turn the pipeline into a trustworthy platform.",
    description:
      "Compaction, archive manifests, backup drills, monitoring, versioned Indicators, explained Signals, and atomic analytics publication make correctness visible and recoverable.",
    proof: "Proof: archive hashes restore cleanly and repeated analytics runs remain idempotent.",
  },
  10: {
    label: "PHASE 10",
    title: "Engineering evidence becomes a clear story others can inspect.",
    description:
      "The dashboard, architecture narrative, demo guide, verification record, and presentation package connect every claim to a running interface or a dated test result.",
    proof: "Proof: one guided demo traverses source, transport, storage, compute, orchestration, and serving.",
  },
};

document.addEventListener("DOMContentLoaded", () => {
  bindPathTabs();
  bindPhaseButtons();
  renderPath("live");
  loadLiveProof();
});

function bindPathTabs() {
  document.querySelectorAll("[data-path]").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll("[data-path]").forEach((candidate) => {
        candidate.setAttribute("aria-selected", String(candidate === button));
      });
      renderPath(button.dataset.path);
    });
  });
}

function renderPath(pathName) {
  const path = paths[pathName];
  const flow = document.getElementById("path-flow");
  flow.replaceChildren();
  path.nodes.forEach((node, index) => {
    const element = document.createElement("div");
    element.className = "flow-node";
    const order = document.createElement("span");
    order.textContent = String(index + 1).padStart(2, "0");
    const label = document.createElement("strong");
    label.textContent = node;
    element.append(order, label);
    flow.append(element);
    if (index < path.nodes.length - 1) {
      const connector = document.createElement("span");
      connector.className = "flow-connector";
      connector.setAttribute("aria-hidden", "true");
      connector.textContent = "→";
      flow.append(connector);
    }
  });
  document.getElementById("path-owner").textContent = path.owner;
  document.getElementById("path-title").textContent = path.title;
  document.getElementById("path-description").textContent = path.description;
  document.getElementById("path-outcome").textContent = path.outcome;
}

function bindPhaseButtons() {
  document.querySelectorAll(".phase-button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".phase-button").forEach((candidate) => {
        const active = candidate === button;
        candidate.classList.toggle("active", active);
        candidate.setAttribute("aria-pressed", String(active));
      });
      const phase = phases[button.dataset.phase];
      document.getElementById("phase-label").textContent = phase.label;
      document.getElementById("phase-title").textContent = phase.title;
      document.getElementById("phase-description").textContent = phase.description;
      document.getElementById("phase-proof").textContent = phase.proof;
    });
  });
}

async function loadLiveProof() {
  try {
    const response = await fetch("/api/v1/freshness", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    document.getElementById("proof-bars").textContent = number(data.market.bar_count);
    document.getElementById("proof-assets").textContent = number(data.symbols.length);
    document.getElementById("proof-filings").textContent = number(data.sec.filing_count);
    document.getElementById("proof-certification").textContent =
      data.symbols.find((item) => item.latest_certification_status)?.latest_certification_status || "NO DATA";
    document.getElementById("proof-generated").textContent =
      `Backend API snapshot · ${formatTimestamp(data.generated_at_utc)} UTC`;
    document.getElementById("proof-status").textContent = "Local platform responding";
    document.getElementById("proof-dot").classList.add("ready");
  } catch (_error) {
    document.getElementById("proof-status").textContent = "Live proof unavailable";
    document.getElementById("proof-generated").textContent =
      "Start the local stack to load current evidence. Dated verification results remain below.";
    document.getElementById("proof-dot").classList.add("error");
  }
}

function number(value) {
  return new Intl.NumberFormat("en-US").format(Number(value || 0));
}

function formatTimestamp(value) {
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: "UTC",
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(value));
}
