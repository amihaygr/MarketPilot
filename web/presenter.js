"use strict";

const core = {
  opening: {
    purpose: "פתיחה · למה הפרויקט קיים",
    title: "הבעיה, ההיקף והבטחת המוצר",
    say: "MarketPilot הוא פרויקט Data Engineering מקומי שמרכז נתוני שוק ו-SEC עבור 11 נכסים. האתגר הוא לספק נתון מהר, אבל גם לשמור מקור גולמי ולבנות גרסה מאושרת שאפשר להסביר ולשחזר.",
    show: "Project Story: הכותרת, היקף הפרויקט וארבעת העקרונות.",
    notice: "זו פלטפורמת נתונים ו-Analytics, לא מערכת לביצוע מסחר.",
    transition: "כדי להשיג גם מהירות וגם אמינות, לכל סוג עבודה יש מסלול ובעלים ברורים.",
    fallback: "השתמש בעמוד הראשון של מסמך הארכיטקטורה וסכם את חמשת משפטי הפרויקט.",
    url: "/showcase.html",
  },
  architecture: {
    purpose: "ארכיטקטורה · ארבעה מסלולים",
    title: "Live, Raw, Certified ו-SEC - כל מסלול פותר צורך אחר",
    say: "Docker Compose מנהל שירותים שחיים כל הזמן. Airflow מנהל רק עבודות שמתחילות ומסתיימות. Streaming נותן freshness, Bronze שומר replay, ו-Batch מפרסם Certified רק אחרי Data Quality.",
    show: "Project Story: עבור בין Live, Certified ו-Raw. ציין גם את מסלול SEC.",
    notice: "Spark מבצע חישוב; Airflow מתזמן Batch. MinIO שומר raw ו-Parquet; MariaDB מגיש Gold.",
    transition: "עכשיו אעקוב אחרי אירוע אחד ואוכיח שהתרשים אינו רק ציור.",
    fallback: "פתח את עמוד 4 ב-MarketPilot.pdf או את docs/architecture/architecture.md.",
    url: "/showcase.html#architecture",
  },
  event: {
    purpose: "הוכחה חיה · מקור עד מוצר",
    title: "אירוע אחד עובר דרך Dashboard, Kafka ו-Bronze",
    say: "המשתמש רואה את Gold דרך API בלבד. מאחורי המסך Kafka מפריד בין המפיק לצרכנים, ובמקביל raw-archive-sink שומר את אותו אירוע ב-Bronze לפני commit של ה-offset.",
    show: "Dashboard על AAPL/7D, Topic market.bars.1m.v1, ואז Bronze JSON עם event_id וזמני מקור וקליטה.",
    notice: "partition ו-offset הם מיקום ההודעה ב-Kafka; הם נשמרים בנתיב לצורך lineage ו-replay.",
    transition: "הוכחנו נתון מהיר ומקור גולמי. השאלה הבאה היא כיצד הוא הופך למאושר.",
    fallback: "הצג Bronze object שהוכן מראש ואת Phase 3/6 verification; אל תיצור אירוע ידני.",
    url: "/",
  },
  certified: {
    purpose: "אמינות · Batch, DQ והתאוששות",
    title: "יום סגור נבנה מחדש לפני שהוא מקבל CERTIFIED",
    say: "Airflow שולח Spark Batch בסדר Bronze, Silver, Data Quality ו-Gold. כשל בבדיקה אינו מקדם watermark ואינו מסתיר את ה-Certified הקודם. Streaming ממשיך גם אם Airflow אינו זמין.",
    show: "Airflow daily_market_close, Spark Master, וסדר המשימות עד Analytics.",
    notice: "max_active_runs=1 מגן על partition; Backfill נעשה ב-DAG פרמטרי ולא באמצעות catchup אוטומטי.",
    transition: "אחרי שהנתון נקי ומאושר, אפשר להפוך אותו ל-context שימושי למשתמש.",
    fallback: "השתמש ב-Phase 4/5 verification: 1,881 rows, עשר בדיקות וריצה שלילית בטוחה.",
    url: "http://localhost:8080/",
  },
  analytics: {
    purpose: "ערך למשתמש · Analytics מוסבר",
    title: "Gold הופך לגרפים, Indicators ו-Signals שאפשר להסביר",
    say: "ה-Analytics אינו המלצת מסחר. הוא מספק context מוסבר: SMA, RSI, realized volatility ו-volume ratio. כל תוצאה נושאת version ו-lineage, והפרסום האטומי נשמר idempotent.",
    show: "Dashboard: קו SMA, כרטיסי Indicators ו-Signal מוסבר אחד.",
    notice: "הסבר Signal חשוב יותר מהצבע שלו; המשתמש צריך להבין מה נמדד.",
    transition: "הערך העסקי חשוב, אבל הפרויקט נבחן גם במה שקורה מחוץ ל-Happy Path.",
    fallback: "הצג Phase 9 verification ואת אזור Evidence ב-Project Story.",
    url: "/",
  },
  maturity: {
    purpose: "בגרות הנדסית · מעבר ל-Happy Path",
    title: "המערכת נבדקה גם ב-restart, retry, archive ו-restore",
    say: "אימתתי restart מ-checkpoint, idempotency, DQ חוסם, הרשאת SELECT בלבד, compaction, archive עם SHA-256 ושחזור מבודד. איני טוען ל-exactly once; אני מוכיח נכונות עסקית.",
    show: "Evidence ב-Project Story והמספרים המתוארכים מ-Phase 8 עד Phase 10.",
    notice: "יש להבדיל בין מצב API חי לבין verification snapshot מתאריך מסוים.",
    transition: "אסכם את הערך ואת ההחלטות הארכיטקטוניות המרכזיות.",
    fallback: "פתח docs/phase8-verification.md ו-docs/phase10-verification.md.",
    url: "/showcase.html#evidence",
  },
  operations: {
    purpose: "העמקה · SEC, תפעול וגבולות",
    title: "מקורות חיצוניים ותחזוקה נשארים בטוחים ותחומים",
    say: "SEC פועל כ-poll bounded עם User-Agent, throttling ו-accession key. Archive ו-backup אינם רק נוצרים - הם עוברים hash ו-restore drill. ה-MVP אינו מבצע purge אוטומטי.",
    show: "Airflow SEC DAG, MinIO SEC Bronze, watermarks ו-archive manifest אם הזמן מאפשר.",
    notice: "Archive אינו purge, ו-Adminer הוא כלי פיתוח - לא מסלול הגישה של המשתמש.",
    transition: "הדוגמאות האלו ממחישות שהחלטות התפעול הן חלק מהארכיטקטורה.",
    fallback: "הצג Phase 6/8 verification ואת Runbook archive-and-recovery.",
    url: "http://localhost:8080/",
  },
  summary: {
    purpose: "סיום · המסר שנשאר",
    title: "Data Platform קטנה, שלמה וניתנת לשחזור",
    say: "MarketPilot מדגים מסלול מלא מהמקור, דרך transport, storage ו-compute, ועד API, Analytics וחוויית משתמש. ההחלטות החשובות הן הפרדת lifecycle, הבחנת Provisional/Certified ושמירת raw מחוץ ל-serving database.",
    show: "חזור לכותרת Project Story או הישאר ב-Evidence.",
    notice: "סיים בהחלטה ובמה שלמדת, לא ברשימת טכנולוגיות.",
    transition: "תודה, אשמח לשאלות.",
    fallback: "אין צורך במסך; אמור את חמשת משפטי הסיפור מהזיכרון.",
    url: "/showcase.html",
  },
  buffer: {
    purpose: "מרווח · ניווט או שאלה",
    title: "אל תוסיף נושא חדש בדקה האחרונה",
    say: "השתמש בזמן כדי להשלים מעבר, לענות על שאלה קצרה או לחזור למשפט הסיום. אם סיימת מוקדם, עצור בביטחון.",
    show: "הישאר במסך הנוכחי.",
    notice: "מרווח מתוכנן הוא חלק מדמו מקצועי, לא זמן שחייבים למלא.",
    transition: "תודה, אשמח לשאלות.",
    fallback: "סכם במשפט אחד והזמן שאלות.",
    url: "/showcase.html",
  },
};

const plans = {
  10: [
    [60, core.opening],
    [90, core.architecture],
    [240, core.event],
    [90, core.certified],
    [90, core.analytics],
    [30, core.summary],
  ],
  15: [
    [90, core.opening],
    [150, core.architecture],
    [330, core.event],
    [120, core.certified],
    [90, core.analytics],
    [60, core.maturity],
    [60, core.buffer],
  ],
  20: [
    [90, core.opening],
    [180, core.architecture],
    [360, core.event],
    [180, core.certified],
    [120, core.analytics],
    [120, core.operations],
    [60, core.summary],
    [90, core.buffer],
  ],
};

let mode = 15;
let plan = [];
let cueIndex = 0;
let remaining = 900;
let timerId = null;

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-mode]").forEach((button) => {
    button.addEventListener("click", () => setMode(Number(button.dataset.mode)));
  });
  document.getElementById("timer-toggle").addEventListener("click", toggleTimer);
  document.getElementById("timer-reset").addEventListener("click", resetTimer);
  document.getElementById("previous-cue").addEventListener("click", () => selectCue(cueIndex - 1, true));
  document.getElementById("next-cue").addEventListener("click", () => selectCue(cueIndex + 1, true));
  document.addEventListener("keydown", handleKeyboard);
  setMode(15);
});

function setMode(nextMode) {
  pauseTimer();
  mode = nextMode;
  plan = buildPlan(plans[mode]);
  cueIndex = 0;
  remaining = mode * 60;
  document.querySelectorAll("[data-mode]").forEach((button) => {
    const active = Number(button.dataset.mode) === mode;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  document.getElementById("plan-label").textContent = `${mode} דקות`;
  renderSegmentList();
  renderCue();
  updateTimer();
}

function buildPlan(entries) {
  let cursor = 0;
  return entries.map(([duration, content]) => {
    const segment = { ...content, duration, start: cursor, end: cursor + duration };
    cursor += duration;
    return segment;
  });
}

function renderSegmentList() {
  const list = document.getElementById("segment-list");
  list.replaceChildren();
  plan.forEach((segment, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "segment-button";
    button.dataset.index = String(index);
    button.addEventListener("click", () => selectCue(index, true));
    const time = document.createElement("span");
    time.textContent = formatClock(segment.duration);
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = segment.title;
    const window = document.createElement("small");
    window.textContent = `${formatClock(segment.start)}-${formatClock(segment.end)}`;
    copy.append(title, window);
    button.append(time, copy);
    list.append(button);
  });
}

function selectCue(index, syncTimer = false) {
  cueIndex = Math.max(0, Math.min(plan.length - 1, index));
  if (syncTimer) remaining = mode * 60 - plan[cueIndex].start;
  renderCue();
  updateTimer();
}

function renderCue() {
  const cue = plan[cueIndex];
  document.querySelectorAll(".segment-button").forEach((button, index) => {
    button.classList.toggle("active", index === cueIndex);
    button.setAttribute("aria-current", index === cueIndex ? "step" : "false");
  });
  setText("cue-number", String(cueIndex + 1).padStart(2, "0"));
  setText("cue-window", `${formatClock(cue.start)}-${formatClock(cue.end)}`);
  setText("cue-purpose", cue.purpose);
  setText("cue-title", cue.title);
  setText("cue-say", cue.say);
  setText("cue-show", cue.show);
  setText("cue-notice", cue.notice);
  setText("cue-transition", cue.transition);
  setText("cue-fallback", cue.fallback);
  setText("cue-position", `${cueIndex + 1} מתוך ${plan.length}`);
  document.getElementById("cue-link").href = cue.url;
  document.getElementById("previous-cue").disabled = cueIndex === 0;
  document.getElementById("next-cue").disabled = cueIndex === plan.length - 1;
}

function toggleTimer() {
  if (timerId) {
    pauseTimer();
    return;
  }
  if (remaining <= 0) resetTimer();
  timerId = window.setInterval(tick, 1000);
  setText("timer-toggle", "השהה");
}

function pauseTimer() {
  if (timerId) window.clearInterval(timerId);
  timerId = null;
  setText("timer-toggle", "התחל");
}

function resetTimer() {
  pauseTimer();
  remaining = mode * 60;
  cueIndex = 0;
  renderCue();
  updateTimer();
}

function tick() {
  remaining = Math.max(0, remaining - 1);
  const elapsed = mode * 60 - remaining;
  const active = plan.findIndex((segment) => elapsed >= segment.start && elapsed < segment.end);
  if (active >= 0 && active !== cueIndex) {
    cueIndex = active;
    renderCue();
  }
  updateTimer();
  if (remaining === 0) pauseTimer();
}

function updateTimer() {
  const timer = document.getElementById("timer");
  timer.textContent = formatClock(remaining);
  timer.classList.toggle("warning", remaining > 0 && remaining <= 60);
  timer.classList.toggle("over", remaining === 0);
  const progress = ((mode * 60 - remaining) / (mode * 60)) * 100;
  document.getElementById("total-progress").style.width = `${progress}%`;
}

function handleKeyboard(event) {
  if (event.target instanceof HTMLButtonElement || event.target instanceof HTMLAnchorElement) return;
  if (event.key === "ArrowLeft") selectCue(cueIndex + 1, true);
  if (event.key === "ArrowRight") selectCue(cueIndex - 1, true);
  if (event.key === " ") {
    event.preventDefault();
    toggleTimer();
  }
  if (event.key.toLowerCase() === "r") resetTimer();
}

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function formatClock(value) {
  const minutes = Math.floor(value / 60);
  const seconds = value % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}
