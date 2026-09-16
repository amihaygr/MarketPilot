"use strict";

const core = {
  opening: {
    purpose: "פתיחה · הערך לסוחר",
    title: "מרכז מחקר אחד: שוק, חברות, אמינות ובדיקת רעיונות",
    say: "כשאני בוחן מניה, המחיר לבדו לא מספיק. אני רוצה לדעת אם הנתון טרי, מה החברה דיווחה, מה מבטל את התזה, ומה הסיכון ביחס לפוטנציאל. MarketPilot מחברת מחירי דקה, ניתוח טכני ופונדמנטלי, SEC, Backtesting ושכבת החלטה מוסברת. מאחורי כל תוצאה נשמרים מקור, איכות ו-Lineage. זו סביבת מחקר; היא לא מבצעת מסחר ולא מבטיחה תשואה.",
    show: "Project Story: הכותרת, מצב הפלטפורמה וארבעת עקרונות המוצר.",
    notice: "הערך הוא חיבור מהירות, הקשר ואמון במקום אחד; הארכיטקטורה היא מה שמאפשר זאת.",
    transition: "כדי להשיג גם מהירות וגם אמינות, לכל סוג עבודה יש מסלול ובעלים ברורים.",
    fallback: "השתמש בעמוד הראשון של מסמך הארכיטקטורה וסכם את סיפור הפרויקט במשפטים שלך.",
    url: "/showcase.html",
  },
  architecture: {
    purpose: "ארכיטקטורה · חמישה מסלולים",
    title: "חמישה מסלולי נתונים ושתי שכבות החלטה, עם גבולות ברורים",
    say: "Docker Compose מנהל שירותים שחיים כל הזמן. Airflow מנהל רק עבודות שמתחילות ומסתיימות. Live נותן Freshness, Raw שומר Replay, Certified בונה אמון, Historical Acquisition מכניס עבר דרך אותם שערים, ו-SEC מוסיף הקשר תאגידי. מעל הנתונים יושבים כללי v1 השקופים; v2 רשאי להוסיף הסתברות רק אחרי אימות וקידום.",
    show: "Project Story: עבור בין Live, Certified, Historical ו-Raw. את SEC הצג במשפט אחד.",
    notice: "Spark מבצע חישוב; Airflow מתזמן Batch. MinIO שומר raw ו-Parquet; MariaDB מגיש Gold ל-API.",
    transition: "עכשיו אעקוב אחרי אירוע אחד ואוכיח שהתרשים אינו רק ציור.",
    fallback: "פתח את MarketPilot.pdf או את docs/architecture/architecture.md.",
    url: "/showcase.html#architecture",
  },
  liveEvent: {
    purpose: "הוכחה חיה · מקור עד מוצר",
    title: "אירוע Live אחד הופך לנתון שימושי בלי לאבד את המקור",
    say: "Alpaca שולח bar של דקה. ה-producer מתאים אותו לחוזה MarketBarV1 ומפרסם ל-Kafka. Spark Streaming כותב Gold provisional, ובמקביל raw-archive-sink שומר את האירוע ב-Bronze לפני commit של ה-offset. המשתמש רואה את התוצאה רק דרך Backend API.",
    show: "Dashboard על AAPL, אחר כך Topic market.bars.1m.v1 ולבסוף Bronze JSON שהוכן מראש.",
    notice: "partition ו-offset הם מיקום ההודעה ב-Kafka; הם נשמרים בנתיב לצורך lineage ו-replay.",
    transition: "הוכחנו נתון מהיר ומקור גולמי. עכשיו אראה איך הכנסתי היסטוריה אמיתית בלי לעקוף את הארכיטקטורה.",
    fallback: "הצג Bronze object שהוכן מראש ואת Phase 3/6 verification; אל תיצור אירוע ידני.",
    url: "/",
  },
  historical: {
    purpose: "הוכחה מרכזית · Historical to Certified",
    title: "53 ימי מסחר אמיתיים זמינים למחקר ולבדיקת רעיונות",
    say: "ה-Backfill ההיסטורי אינו כותב ישירות למסד. Airflow מושך Alpaca IEX, שומר כל Response גולמי לפי SHA-256, מפרסם ל-Topic היסטורי נפרד ומחכה להוכחת Bronze לפי Partition ו-Offset. רק אז Spark בונה Silver ו-Certified Gold. כיום קיימים 53 ימי XNYS מאושרים, כולל תיקון מבוקר ל-16 בספטמבר לאחר שריצת האיכות היומית זיהתה כיסוי חלקי.",
    show: "Airflow: historical_market_backfill. הצג את run התיקון repair__2026-09-16__20260917 ואת הרצף Acquisition, Bronze barrier, Silver, DQ, Gold ו-Backtest.",
    notice: "היסטוריה אינה עוקפת את Medallion. topic נפרד מונע מ-Backfill להציף את מסלול ה-Live.",
    transition: "כעת, כשההיסטוריה מאושרת ובעלת lineage, אפשר להעריך אסטרטגיה בצורה ניתנת לשחזור.",
    fallback: "פתח את מסמך הארכיטקטורה ואת docs/final-presentation-verification.md; שניהם מתעדים את ה-Repair ואת מצב הנתונים הסופי.",
    url: "http://localhost:8080/",
  },
  decision: {
    purpose: "ערך מוצרי · Decision Intelligence",
    title: "מהיסטוריה ונתונים חיים לתרחיש החלטה מוסבר",
    say: "ב-Opportunity Center אני מקבל Buy Zone, שני Targets, Stop, Risk/Reward וגודל פוזיציה. חשוב להפריד בין שלושה מספרים: Rule Score מסכם את הראיות; Data Confidence מודד טריות וכיסוי; Model Probability תופיע רק אחרי שמודל v2 מאומן ומכויל יעבור את השערים. כרגע v1 עובד, Shadow Mode עומד על 2 מתוך 20, ו-v2 נמצא ב-FALLBACK — לכן אין הסתברות מומצאת.",
    show: "Opportunity Center: הצג 2/20, 53 sessions, RULES ACTIVE · MODEL FALLBACK. בחר META כדי להראות BUY ZONE ואז AAPL כדי להראות WATCH BREAKOUT; הצבע על Buy Zone, Stop, Targets, Position Sizing ושלוש שכבות הראיה.",
    notice: "המערכת מציעה תרחיש מחקר ולא פקודה. FALLBACK אינו כשל במוצר: זהו Fail-closed שמגן מפני מודל שלא הוכח.",
    transition: "כדי לא להסתפק בתרחיש הנוכחי, אראה גם כיצד אני בודק אסטרטגיה על היסטוריה מאושרת.",
    fallback: "פתח docs/phase14-verification.md והסבר את ההפרדה בין historical evidence ל-live gate.",
    url: "/opportunities.html",
  },
  backtesting: {
    purpose: "ערך אנליטי · Backtesting מוסבר",
    title: "מנתונים מאושרים לתוצאה שאפשר לבקר ולשחזר",
    say: "ה-Backtest הוא Spark Batch תחום בזמן, ורק Certified Gold נכנס אליו. אות שנוצר בנר מסוים מוחל רק על הנר הבא כדי למנוע Look-ahead Bias. עלויות ו-Slippage מקטינים את התוצאה. קיימות 11 ריצות מפורסמות על חלונות מאושרים; התוצאות מעורבות, וזה מחזק את אמינות ההצגה כי המערכת אינה מייפה אסטרטגיה חלשה.",
    show: "Backtesting Lab: בחר ריצה Published עם טווח של כמה שבועות, בחר AAPL והצג KPIs, Equity Curve, Benchmark ו-Lineage.",
    notice: "המטרה היא להוכיח ניסוי שניתן לשחזור, לא לטעון שהאסטרטגיה מנצחת את השוק. ביצועי עבר אינם הבטחת תשואה.",
    transition: "המספרים מעניינים, אך ההישג המרכזי הוא שאפשר להסביר ולשחזר אותם עד המקור והקוד.",
    fallback: "הצג את טבלת Final published results ב-docs/phase12-verification.md.",
    url: "/backtesting.html",
  },
  maturity: {
    purpose: "בגרות הנדסית · מעבר ל-Happy Path",
    title: "המערכת נבדקה גם ב-restart, retry, archive ו-restore",
    say: "אימתתי restart מ-checkpoint, idempotency, DQ חוסם, הרשאת SELECT בלבד, compaction, archive עם SHA-256 ושחזור מבודד. בריצת החודש המערכת גם זיהתה נתוני synthetic מסוף שבוע, החריגה 513 רשומות ושמרה אותן לביקורת. איני טוען ל-exactly once; אני מוכיח נכונות עסקית.",
    show: "Evidence ב-Project Story: 19 שירותי Compose, 113 tests, ‏53 sessions, ‏65,616 נרות Certified ו-11 backtests.",
    notice: "יש להבדיל בין מצב API חי לבין verification snapshot מתאריך מסוים.",
    transition: "אסכם את הערך ואת ההחלטות הארכיטקטוניות המרכזיות.",
    fallback: "פתח docs/phase8-verification.md ו-docs/phase12-verification.md.",
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
    say: "MarketPilot מדגים מסלול מלא ממקור חי והיסטורי, דרך transport, object storage, compute ו-quality gates, ועד API, Analytics ו-Backtesting. ההחלטות החשובות שלי הן הפרדת lifecycle, הבחנת Provisional ו-Certified, ושמירת raw מחוץ ל-serving database. בניתי מערכת שאני יכול לא רק להפעיל, אלא גם להסביר, לבדוק ולשחזר.",
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
    [75, core.architecture],
    [120, core.liveEvent],
    [90, core.historical],
    [120, core.decision],
    [75, core.backtesting],
    [30, core.maturity],
    [30, core.summary],
  ],
  15: [
    [90, core.opening],
    [120, core.architecture],
    [135, core.liveEvent],
    [120, core.historical],
    [150, core.decision],
    [90, core.backtesting],
    [75, core.maturity],
    [60, core.summary],
    [60, core.buffer],
  ],
  20: [
    [90, core.opening],
    [120, core.architecture],
    [180, core.liveEvent],
    [180, core.historical],
    [150, core.decision],
    [150, core.backtesting],
    [90, core.maturity],
    [90, core.operations],
    [90, core.summary],
    [60, core.buffer],
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
  loadRuntimeProof();
});

async function loadRuntimeProof() {
  const indicator=document.getElementById("live-indicator");
  try {
    const [evaluationResponse,modelResponse]=await Promise.all([fetch("/api/v1/decision-evaluation/status"),fetch("/api/v1/decision-model/status")]);
    if(!evaluationResponse.ok||!modelResponse.ok) throw new Error("status API unavailable");
    const evaluation=await evaluationResponse.json(); const model=await modelResponse.json();
    indicator.lastChild.textContent=` קריאה בלבד · v1 ${evaluation.completed_sessions}/${evaluation.required_sessions} · v2 ${model.status}`;
  } catch (_error) {
    indicator.lastChild.textContent=" עזר מקומי · מצב חי לא זמין";
  }
}

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
