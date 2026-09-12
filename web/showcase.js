"use strict";

const paths = {
  live: {
    owner: "DOCKER COMPOSE · שירות ארוך־חיים",
    title: "מידע שוק עדכני מגיע ל־Gold בלי להמתין ל־DAG היומי.",
    description:
      "נתוני Alpaca נכנסים ל־Producer בעל חוזה גרסה, עוברים דרך Kafka ונצרכים ב־Spark Structured Streaming עם Checkpoint עמיד. כתיבות לפי מפתח עסקי מפרסמות נתוני Gold זמניים ומתאוששות לאחר הפעלה מחדש.",
    outcome: "Gold זמני בזמן השהיה נמוך, עם רציפות לאחר Restart",
    nodes: ["Alpaca", "market-producer", "Kafka", "Spark Streaming", "MariaDB Gold"],
  },
  certified: {
    owner: "AIRFLOW · עבודות SPARK תחומות",
    title: "נתונים סגורים נבנים מחדש מההיסטוריה הגולמית לפני שהם מאושרים.",
    description:
      "Airflow שולח יישומי Spark תחומים ברצף מפורש מ־Bronze ל־Silver ול־Gold. בדיקות איכות חוסמות חייבות לעבור לפני שהפרסום האטומי מחליף את המחיצה ומקדם את ה־Watermark.",
    outcome: "Gold נקי, מאושר ועם Lineage מלא",
    nodes: ["Bronze", "Spark Batch", "Silver Parquet", "DQ gate", "Certified Gold"],
  },
  historical: {
    owner: "AIRFLOW · רכישה ואישור תחומים",
    title: "נתונים היסטוריים נכנסים דרך אותה שרשרת ראיות כמו הנתונים החיים.",
    description:
      "ריצת Airflow תחומה מושכת עמודים מ־Alpaca IEX, שומרת את תגובות המקור לפי SHA-256, מפרסמת אירועים אחידים ל־Kafka Topic מבודד וממתינה לכל Offset ב־Bronze. רק לאחר מכן מתחילים אישור Spark וה־Backtest.",
    outcome: "היסטוריה אמיתית עם מקור גולמי, בדיקות איכות ו־Lineage ניתן לשחזור",
    nodes: ["Alpaca IEX", "Historical Kafka", "Bronze barrier", "Certified Gold", "Backtest"],
  },
  archive: {
    owner: "KAFKA SINK · פעולות תחומות",
    title: "מסד הנתונים המשרת לעולם אינו העותק היחיד של ההיסטוריה.",
    description:
      "ה־Offsets של Kafka נשמרים ב־Bronze בלתי משתנה לצורך Replay. ייצוא תקופות סגורות יוצר אובייקטי Parquet, רשימות SHA-256 ו־Manifests ב־MariaDB. תרגילי שחזור פועלים על Schema מבודד ואינם משנים Gold חי.",
    outcome: "היסטוריה גולמית ניתנת ל־Replay וראיות התאוששות מאומתות",
    nodes: ["Kafka offsets", "MinIO Bronze", "Parquet archive", "Hash manifest", "Isolated restore"],
  },
};

const phases = {
  0: {
    label: "PHASES 0–2",
    title: "אירוע ניתן לשחזור נכנס ל־Kafka ונשמר כ־Bronze בלתי משתנה.",
    description:
      "כללי Repository, תשתית בסיסית, חוזה אירוע עם גרסה, יצירה דטרמיניסטית ו־Quarantine יוצרים מסלול ראשון שאפשר לסמוך עליו.",
    proof: "ראיה: אותה רשומת Kafka ממופה לאובייקט Bronze יחיד שניתן לשחזור.",
  },
  3: {
    label: "PHASES 3–5",
    title: "המסלול החי והמסלול המאושר ניתנים להפעלה עצמאית.",
    description:
      "Structured Streaming מפרסם Gold זמני עם Checkpoints עמידים. Spark Batch יוצר Silver ו־Gold מאושר, ו־Airflow אחראי רק לתזמון תחום ולשערי איכות.",
    proof: "ראיה: התאוששות ועיבוד מחיצה חוזר שומרים על מפתחות עסקיים ייחודיים.",
  },
  6: {
    label: "PHASES 6–7",
    title: "מקורות אמיתיים הופכים לחוויית מוצר בטוחה המיועדת לקריאה בלבד.",
    description:
      "מתאמי Alpaca ו־SEC שומרים על החוזים שנבדקו. זהות API מצומצמת חושפת מידע תחום לאפליקציה דרך Nginx בלי לתת לדפדפן גישה לאחסון או למסד הנתונים.",
    proof: "ראיה: ההזדהות מול המקור החי מצליחה, אך זהות האפליקציה אינה מורשית לכתוב.",
  },
  8: {
    label: "PHASES 8–9",
    title: "התאוששות והסבריות הופכות את ה־Pipeline לפלטפורמה אמינה.",
    description:
      "Compaction, רשומות ארכיון, תרגילי גיבוי, ניטור, Indicators בעלי גרסה, Signals מוסברים ופרסום Analytics אטומי הופכים את התקינות לנראית וניתנת לשחזור.",
    proof: "ראיה: חתימות הארכיון משתחזרות בהצלחה וריצות Analytics חוזרות נשארות Idempotent.",
  },
  10: {
    label: "PHASE 10",
    title: "הראיות ההנדסיות הופכות לסיפור ברור שאחרים יכולים לבדוק.",
    description:
      "לוח המחוונים, סיפור הארכיטקטורה, מדריך ההדגמה, מסמך האימות וחבילת ההצגה מחברים כל טענה לממשק פעיל או לתוצאת בדיקה מתוארכת.",
    proof: "ראיה: הדגמה מודרכת אחת עוברת דרך מקור, תעבורה, אחסון, עיבוד, תזמור והגשה.",
  },
  11: {
    label: "PHASE 11",
    title: "היסטוריה מאושרת הופכת לתוצאת מחקר ניתנת לשחזור ומודעת להטיות.",
    description:
      "Backtest תחום ב־Spark מחיל כל Signal רק על הרשומה הבאה, כולל עלויות מפורשות, שומר ראיות מפורטות ב־Parquet ומגיש סיכומים תחומים דרך ה־API.",
    proof: "ראיה: ריצה בלתי משתנה אחת מקשרת מדדים, הון יומי, פרמטרים, קוד וגרסאות נתונים.",
  },
  12: {
    label: "PHASE 12",
    title: "היסטוריית Alpaca אמיתית מגיעה למודל בלי לעקוף את Kafka או Bronze.",
    description:
      "עשרים ימי מסחר סגורים ב־XNYS עוברים דרך ארכיון מקור מבוסס תוכן, Topic היסטורי מבודד, מחסום Bronze ברמת Offset, שערי איכות ב־Spark, Gold מאושר וה־Backtest הסופי.",
    proof: "ראיה: 23,349 רשומות תקינות הותאמו, ו־513 רשומות ביקורת מחוץ למסחר הוחרגו במפורש.",
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
      // Desktop RTL flow reads 01 from the right toward 02 on its left.
      connector.textContent = "←";
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
      `צילום מצב של Backend API · ${formatTimestamp(data.generated_at_utc)} UTC`;
    document.getElementById("proof-status").textContent = "הפלטפורמה המקומית מגיבה";
    document.getElementById("proof-dot").classList.add("ready");
  } catch (_error) {
    document.getElementById("proof-status").textContent = "הראיה החיה אינה זמינה";
    document.getElementById("proof-generated").textContent =
      "יש להפעיל את הסביבה המקומית כדי לטעון ראיה עדכנית. תוצאות האימות המתוארכות נשארות זמינות בהמשך הדף.";
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
