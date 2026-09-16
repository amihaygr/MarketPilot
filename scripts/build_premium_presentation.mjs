import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";
import JSZip from "jszip";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const workspaceDir = path.resolve(scriptDir, "..");
const buildDir = path.join(workspaceDir, ".presentation-build", "premium");
const candidatePath = path.join(buildDir, "MarketPilot-premium-candidate.pptx");
const assetsDir = path.join(workspaceDir, "docs", "presentation", "assets");

await fs.mkdir(buildDir, { recursive: true });

const W = 1280;
const H = 720;
const FONT = "Arial";
const MONO = "Cascadia Mono";

const C = {
  ink: "#091827",
  ink2: "#10283C",
  paper: "#F4F1E9",
  white: "#F8FBFF",
  teal: "#35D4B5",
  tealDark: "#117C70",
  blue: "#5B91FF",
  amber: "#F4B94F",
  amberDark: "#9A6200",
  coral: "#EF7484",
  mutedDark: "#9AB1C5",
  muted: "#5B6B78",
  lineDark: "#294157",
  lineLight: "#C9D2D8",
};

const presentation = Presentation.create({
  slideSize: { width: W, height: H },
});

const iso = (value) => value;
const rtl = (value) => value;
const containsHebrew = (value) => /[\u0590-\u05FF]/.test(value);
const stripBidiControls = (value) =>
  String(value).replace(/[\u200E\u200F\u202A-\u202E\u2066-\u2069]/g, "");

function base(slide) {
  slide.background.fill = C.ink;
  rect(slide, 0, 0, 18, H, C.teal);
}

function rect(slide, x, y, w, h, fill, radius = 0, line = "none") {
  return slide.shapes.add({
    geometry: radius ? "roundRect" : "rect",
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: line === "none" ? { fill: "none", width: 0 } : line,
    ...(radius ? { borderRadius: radius } : {}),
  });
}

function rule(slide, x, y, w, color, weight = 1) {
  return slide.shapes.add({
    geometry: "line",
    position: { left: x, top: y, width: w, height: 0 },
    fill: "none",
    line: { style: "solid", fill: color, width: weight },
  });
}

function text(slide, value, x, y, w, h, options = {}) {
  const cleanValue = stripBidiControls(value);
  const hasHebrew = containsHebrew(cleanValue);
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width: w, height: h },
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  shape.text = cleanValue;
  shape.text.style = {
    typeface: options.font ?? FONT,
    fontSize: options.size ?? 24,
    bold: options.bold ?? false,
    color: options.color ?? C.white,
    alignment: hasHebrew ? "right" : (options.align ?? "left"),
    verticalAlignment: options.valign ?? "top",
    autoFit: options.autoFit ?? "shrinkText",
    wrap: "square",
    lineSpacing: options.lineSpacing ?? 1,
    insets: options.insets ?? { top: 0, right: 0, bottom: 0, left: 0 },
  };
  return shape;
}

function label(slide, value, x, y, w, color = C.teal, align = "left") {
  return text(slide, value, x, y, w, 22, {
    font: MONO,
    size: 13,
    bold: true,
    color,
    align,
    valign: "middle",
  });
}

function slideNumber(slide, number) {
  text(slide, String(number).padStart(2, "0"), 52, 676, 36, 18, {
    font: MONO,
    size: 11,
    bold: true,
    color: C.mutedDark,
    align: "left",
  });
  rule(slide, 96, 686, 1128, C.lineDark, 1);
}

function title(slide, titleText, kicker, number) {
  label(slide, kicker, 64, 38, 420, C.teal, "left");
  text(slide, rtl(titleText), 440, 56, 776, 58, {
    size: 32,
    bold: true,
    color: C.white,
    align: "right",
    valign: "top",
  });
  slideNumber(slide, number);
}

function notes(slide, duration, body, source) {
  slide.speakerNotes.textFrame.setText(
    `זמן מומלץ: ${duration}\n\n${body}\n\nמקור ואימות: ${source}`,
  );
  slide.speakerNotes.setVisible(true);
}

function addImage(slide, filename, x, y, w, h, alt, fit = "cover", crop) {
  return fs.readFile(path.join(assetsDir, filename)).then((bytes) =>
    slide.images.add({
      blob: bytes,
      contentType: "image/png",
      alt,
      fit,
      position: { left: x, top: y, width: w, height: h },
      geometry: "roundRect",
      borderRadius: 14,
      ...(crop ? { crop } : {}),
    }),
  );
}

function node(slide, value, sub, x, y, w, accent, dark = true) {
  const shape = rect(
    slide,
    x,
    y,
    w,
    88,
    C.ink2,
    12,
    { style: "solid", fill: accent, width: 1.5 },
  );
  text(slide, value, x + 10, y + 17, w - 20, 28, {
    font: MONO,
    size: 19,
    bold: true,
    color: C.white,
    align: "center",
    valign: "middle",
  });
  text(slide, rtl(sub), x + 8, y + 50, w - 16, 20, {
    size: 15,
    color: C.mutedDark,
    align: "center",
  });
  return shape;
}

function connectLeft(slide, fromShape, toShape, color = C.teal) {
  return slide.shapes.connect(fromShape, toShape, {
    kind: "straight",
    fromSide: "left",
    toSide: "right",
    line: { style: "solid", fill: color, width: 2 },
    tail: { type: "triangle", width: "sm", length: "sm" },
  });
}

// 1 — Cover
{
  const slide = presentation.slides.add();
  base(slide);
  label(slide, "MARKETPILOT · FINAL PROJECT", 68, 58, 430, C.teal, "left");
  text(slide, rtl("מערכת נתונים\nשמחברת בין שוק חי,\nאמון והחלטה"), 540, 132, 670, 246, {
    size: 58,
    bold: true,
    color: C.white,
    align: "right",
    lineSpacing: 0.9,
  });
  text(
    slide,
    rtl(`פלטפורמת ${iso("Data Engineering")} מקומית לנתוני שוק, דיווחי ${iso("SEC")}, ניתוח טכני ובדיקת החלטות על ההיסטוריה`),
    630,
    392,
    580,
    76,
    { size: 24, color: C.mutedDark, align: "right", lineSpacing: 1.05 },
  );

  const stages = [
    ["01", "LIVE", "מה קורה עכשיו"],
    ["02", "CERTIFIED", "מה עבר בדיקה"],
    ["03", "EXPLAINED", "למה התקבלה התוצאה"],
  ];
  stages.forEach(([n, en, he], index) => {
    const yy = 208 + index * 108;
    text(slide, n, 78, yy, 38, 24, { font: MONO, size: 12, color: C.teal, align: "left" });
    text(slide, en, 126, yy - 7, 300, 36, { font: MONO, size: 24, bold: true, color: C.white, align: "left" });
    text(slide, rtl(he), 126, yy + 32, 300, 28, { size: 17, color: C.mutedDark, align: "left" });
    if (index < stages.length - 1) rule(slide, 78, yy + 78, 330, C.lineDark, 1);
  });
  text(slide, rtl("עמיחי · פרויקט גמר · הנדסת נתונים"), 68, 644, 430, 24, {
    size: 14,
    color: C.mutedDark,
    align: "left",
  });
  notes(
    slide,
    "00:00–00:30",
    "פתח במשפט אחד: MarketPilot היא פלטפורמת מחקר לסוחר. היא לא שולחת פקודות מסחר. היא מחברת מידע חי, מקור גולמי, בדיקות איכות והסבר שניתן לשחזר. אל תפרט עדיין את הטכנולוגיות.",
    "docs/project-context.md; docs/architecture/architecture.md",
  );
}

// 2 — Problem
{
  const slide = presentation.slides.add();
  base(slide);
  label(slide, "THE PROBLEM", 64, 42, 260, C.teal, "left");
  text(slide, rtl("סוחר רואה מספר.\nאבל האם אפשר לסמוך עליו?"), 420, 122, 790, 132, {
    size: 44,
    bold: true,
    color: C.white,
    align: "right",
    lineSpacing: 0.92,
  });
  text(
    slide,
    rtl("מחיר לבדו אינו מסביר אם הנתון טרי, אם החברה פרסמה מידע מהותי, ואם רעיון מסחר שרד בדיקה היסטורית הוגנת."),
    530,
    270,
    680,
    74,
    { size: 24, color: C.mutedDark, align: "right" },
  );

  const questions = [
    ["01", "מה קורה עכשיו?", "מחיר, נפח ומגמה"],
    ["02", "האם הנתון אמין?", "טריות, איכות ומקור"],
    ["03", "מה השתנה בחברה?", `דיווחי ${iso("SEC")} רשמיים`],
    ["04", "האם הרעיון עבד בעבר?", `בדיקה מול ${iso("SPY")} ועלויות`],
  ];
  questions.forEach(([n, q, a], index) => {
    const x = 964 - index * 302;
    if (index < questions.length - 1) rect(slide, x - 18, 414, 1, 152, C.lineDark);
    text(slide, n, x, 398, 34, 22, { font: MONO, size: 12, color: C.teal, align: "left" });
    text(slide, rtl(q), x, 436, 252, 48, { size: 25, bold: true, color: C.white, align: "right" });
    text(slide, rtl(a), x, 505, 252, 40, { size: 20, color: C.mutedDark, align: "right" });
  });
  slideNumber(slide, 2);
  notes(
    slide,
    "00:30–01:15",
    "הצג את הבעיה מנקודת המבט של הסוחר: יש הרבה מסכים ומספרים, אבל קשה לדעת מה טרי, מה נבדק ומה אפשר לשחזר. ארבע השאלות בתחתית הן דרישות המוצר, לא רשימת פיצ'רים.",
    "docs/project-context.md",
  );
}

// 3 — Product value
{
  const slide = presentation.slides.add();
  base(slide);
  title(slide, "מה המערכת נותנת לסוחר", "PRODUCT VALUE", 3, false);
  const stages = [
    ["04", "מסבירה", "תרחיש החלטה\nעם סיכון והקשר", C.amber],
    ["03", "בודקת", "איכות נתונים\nוהיסטוריה", C.blue],
    ["02", "מבינה", "מגמה, תנודתיות\nודיווחי חברה", C.teal],
    ["01", "אוספת", "שוק חי ומידע\nרשמי", C.teal],
  ];
  const nodes = [];
  stages.forEach(([n, verb, desc, accent], index) => {
    const x = 68 + index * 295;
    text(slide, n, x, 176, 48, 24, { font: MONO, size: 12, bold: true, color: accent, align: "left" });
    text(slide, rtl(verb), x, 212, 250, 54, { size: 38, bold: true, color: C.white, align: "right" });
    text(slide, rtl(desc), x, 283, 250, 62, { size: 23, color: C.mutedDark, align: "right" });
    const marker = rect(slide, x, 376, 18, 18, accent, 9);
    nodes.push(marker);
    if (index < stages.length - 1) rule(slide, x + 18, 385, 277, C.lineDark, 2);
  });
  text(
    slide,
    rtl(`התוצאה: סביבת מחקר אחת שמראה גם את המספר, גם את רמת האמון בו וגם את הדרך שבה נוצר.`),
    238,
    460,
    978,
    92,
    { size: 34, bold: true, color: C.white, align: "right", lineSpacing: 0.95 },
  );
  text(slide, rtl(`המערכת מספקת ${iso("Decision Support")} בלבד. ההחלטה והביצוע נשארים בידי המשתמש.`), 520, 576, 696, 34, {
    size: 20,
    color: C.coral,
    align: "right",
  });
  notes(
    slide,
    "01:15–02:00",
    "הסבר את שרשרת הערך מימין לשמאל. מתחילים באיסוף, מוסיפים הקשר, בודקים את האיכות וההיסטוריה, ורק אז מציגים תרחיש החלטה. הדגש שהמערכת עוזרת לחשוב ואינה מבצעת קנייה או מבטיחה רווח.",
    "docs/project-context.md; docs/decisions/ADR-008-decision-intelligence.md",
  );
}

// 4 — Architecture
{
  const slide = presentation.slides.add();
  base(slide);
  title(slide, "ארכיטקטורת המערכת", "SYSTEM ARCHITECTURE", 4);
  text(slide, rtl("הזרימה מוצגת מימין לשמאל, מן המקור אל המשתמש"), 744, 106, 472, 30, {
    size: 21,
    color: C.mutedDark,
    align: "right",
  });

  const n1 = node(slide, "Alpaca + SEC", "מקורות", 1045, 238, 155, C.teal);
  const n2 = node(slide, "Python", "קליטה וחוזה", 850, 238, 150, C.teal);
  const n3 = node(slide, "Kafka", "תעבורה ו־Replay", 655, 238, 150, C.blue);
  const n4 = node(slide, "Spark", "Streaming + Batch", 460, 238, 150, C.blue);
  const n5 = node(slide, "MariaDB Gold", "נתון מוכן ליישום", 255, 238, 160, C.amber);
  const n6 = node(slide, "API + Web", "המוצר למשתמש", 60, 238, 150, C.teal);
  connectLeft(slide, n1, n2);
  connectLeft(slide, n2, n3);
  connectLeft(slide, n3, n4, C.blue);
  connectLeft(slide, n4, n5, C.amber);
  connectLeft(slide, n5, n6, C.teal);

  const bronze = node(slide, "MinIO Bronze", "מקור גולמי ובלתי משתנה", 650, 430, 190, C.teal, true);
  const silver = node(slide, "MinIO Silver", "Parquet נקי וקנוני", 425, 430, 190, C.blue, true);
  slide.shapes.connect(n3, bronze, {
    kind: "elbow",
    fromSide: "bottom",
    toSide: "top",
    line: { style: "dashed", fill: C.teal, width: 2 },
    tail: { type: "triangle", width: "sm", length: "sm" },
  });
  connectLeft(slide, bronze, silver, C.blue);
  slide.shapes.connect(silver, n5, {
    kind: "elbow",
    fromSide: "top",
    toSide: "bottom",
    line: { style: "dashed", fill: C.amber, width: 2 },
    tail: { type: "triangle", width: "sm", length: "sm" },
  });
  text(slide, "Airflow", 222, 448, 150, 30, { font: MONO, size: 20, bold: true, color: C.amber, align: "center" });
  text(slide, rtl("מתזמן עבודות תחומות בלבד"), 160, 486, 272, 28, { size: 18, color: C.mutedDark, align: "right" });
  text(slide, rtl(`הדפדפן מדבר רק עם ה־${iso("API")}`), 62, 352, 260, 30, { size: 19, color: C.teal, bold: true, align: "right" });
  notes(
    slide,
    "02:00–03:15",
    "עקוב אחר החצים מימין לשמאל. המקורות נכנסים לשירותי Python, עוברים דרך Kafka, מעובדים ב-Spark ומגיעים ל-Gold. במקביל נשמר מקור גולמי ב-Bronze ונבנה Silver. Airflow מתזמן עבודות שמסתיימות, אך אינו מנהל את חיי שירותי ה-Streaming. ציין שהדפדפן פונה רק ל-API.",
    "docs/architecture/architecture.md; docs/decisions/ADR-001-storage-strategy.md; ADR-002-airflow-boundary.md; ADR-003-streaming-lifecycle.md",
  );
}

// 5 — Live vs certified
{
  const slide = presentation.slides.add();
  base(slide);
  title(slide, "שני מסלולים, שתי הבטחות", "LIVE VS CERTIFIED", 5, false);
  text(slide, rtl("מהיר עכשיו"), 940, 142, 274, 42, { size: 30, bold: true, color: C.teal, align: "right" });
  text(slide, rtl("המסלול החי מספק תמונת מצב בזמן שהשוק פעיל"), 660, 186, 554, 32, { size: 22, color: C.mutedDark, align: "right" });
  const liveLabels = ["Gold PROVISIONAL", "Spark Streaming", "Kafka", "Alpaca"];
  const liveNodes = liveLabels.map((v, i) => node(slide, v, i === 0 ? "מוכן לתצוגה" : "", 72 + i * 287, 236, 235, C.teal, false));
  for (let i = liveNodes.length - 1; i > 0; i--) connectLeft(slide, liveNodes[i], liveNodes[i - 1], C.teal);
  label(slide, "DOCKER COMPOSE OWNS THE LIFECYCLE", 72, 336, 480, C.teal, "left");

  rule(slide, 64, 378, 1152, C.lineDark, 1);
  text(slide, rtl("אמין לאחר הסגירה"), 862, 408, 352, 42, { size: 30, bold: true, color: C.blue, align: "right" });
  text(slide, rtl("המסלול המאושר בונה מחדש את היום מן המקור ומפעיל שערי איכות"), 566, 452, 648, 32, { size: 22, color: C.mutedDark, align: "right" });
  const certLabels = ["Gold CERTIFIED", "Data Quality", "Silver", "Spark Batch", "Bronze"];
  const certNodes = certLabels.map((v, i) => node(slide, v, "", 64 + i * 230, 505, 184, C.blue, false));
  for (let i = certNodes.length - 1; i > 0; i--) connectLeft(slide, certNodes[i], certNodes[i - 1], C.blue);
  label(slide, "AIRFLOW SCHEDULES AND MONITORS", 64, 614, 390, C.blue, "left");
  notes(
    slide,
    "03:15–04:15",
    "הסבר את ההבדל כהבטחה למשתמש. Provisional אומר מה ידוע עכשיו. Certified אומר שהיום נבנה מחדש מן המקור ועבר בדיקות. Docker Compose מנהל שירותים ארוכי חיים; Airflow מתזמן ומנטר עבודות תחומות. אל תגיד ש-Airflow מפעיל את ה-Streaming.",
    "docs/decisions/ADR-002-airflow-boundary.md; docs/decisions/ADR-004-provisional-certified-publication.md",
  );
}

// 6 — Technology choices
{
  const slide = presentation.slides.add();
  base(slide);
  title(slide, "בחירות טכנולוגיות עם סיבה", "TECHNOLOGY CHOICES", 6, false);
  const rows = [
    ["Kafka", `שומר סדר לפי ${iso("Offset")} ומאפשר ${iso("Replay")} בין צרכנים נפרדים`, C.teal],
    ["Spark", `מנוע אחד לעיבוד ${iso("Streaming")} ולעיבוד ${iso("Batch")}`, C.blue],
    ["Airflow", "מנהל סדר, תלויות וניסיונות חוזרים של עבודות תחומות", C.amber],
    ["MinIO", `שומר ${iso("Bronze")} גולמי, ${iso("Silver")} בפורמט ${iso("Parquet")} וארכיון`, C.teal],
    ["MariaDB", `מגיש ${iso("Gold")} מוכן ל־${iso("API")} עם מפתחות עסקיים ו־${iso("Upsert")}`, C.blue],
    ["Docker Compose", "מעלה סביבה מקומית שחוזרת על עצמה ומבודדת שירותים", C.amber],
  ];
  text(slide, rtl("החלטה הנדסית"), 560, 132, 650, 28, { size: 17, bold: true, color: C.mutedDark, align: "right" });
  text(slide, "Technology", 72, 132, 250, 28, { font: MONO, size: 15, bold: true, color: C.mutedDark, align: "left" });
  rule(slide, 64, 174, 1152, C.lineDark, 1);
  rows.forEach(([tech, why, accent], index) => {
    const y = 194 + index * 72;
    text(slide, tech, 72, y, 260, 34, { font: MONO, size: 23, bold: true, color: accent, align: "left", valign: "middle" });
    text(slide, rtl(why), 390, y, 820, 36, { size: 23, color: C.white, align: "right", valign: "middle" });
    if (index < rows.length - 1) rule(slide, 64, y + 55, 1152, C.lineDark, 1);
  });
  notes(
    slide,
    "04:15–05:05",
    "אל תקריא את כל השורות. בחר שלוש דוגמאות: Kafka להפרדה ול-Replay, MinIO לשמירת המקור הגולמי, ו-Airflow לניהול עבודות תחומות. אם נשאלת למה המערכת מורכבת, הסבר שכל רכיב פותר כשל אחר ולא נבחר רק כדי להוסיף טכנולוגיה.",
    "docs/architecture/architecture.md",
  );
}

// 7 — Dashboard evidence
{
  const slide = presentation.slides.add();
  base(slide);
  title(slide, "המוצר מתחיל בנתון שאפשר לבדוק", "PRODUCT EVIDENCE", 7, false);
  await addImage(slide, "dashboard.png", 58, 150, 825, 474, "MarketPilot Data Command Center screenshot");
  text(slide, rtl("מסך המחקר הראשי"), 918, 160, 298, 48, { size: 30, bold: true, color: C.white, align: "right" });
  text(slide, rtl(`מחיר, נפח, ${iso("Indicators")}, דיווחי חברה וטריות נתונים במקום אחד.`), 918, 222, 298, 86, {
    size: 22,
    color: C.mutedDark,
    align: "right",
  });
  rule(slide, 918, 330, 298, C.lineDark, 1);
  const facts = [
    ["11", "נכסים במעקב"],
    ["57,217", "רשומות Gold"],
    ["937", "דיווחי SEC"],
  ];
  facts.forEach(([metric, caption], index) => {
    const y = 354 + index * 82;
    text(slide, metric, 918, y, 150, 35, { font: MONO, size: 26, bold: true, color: index === 1 ? C.blue : C.teal, align: "left" });
    text(slide, rtl(caption), 1050, y + 4, 166, 30, { size: 19, color: C.mutedDark, align: "right" });
  });
  notes(
    slide,
    "05:05–05:45",
    "הצג את צילום המסך כראיה, לא כקישוט. הסבר שהמשתמש רואה נתון עסקי פשוט, אך כל ערך מגיע דרך API וכולל מצב פרסום וטריות. המספרים בצד נלקחו מהצילום המתוארך ל-16 בספטמבר 2026.",
    "docs/presentation/assets/dashboard.png; docs/final-presentation-verification.md",
  );
}

// 8 — Opportunity Center
{
  const slide = presentation.slides.add();
  base(slide);
  title(slide, "מתוצאה טכנית לתרחיש החלטה", "DECISION INTELLIGENCE", 8);
  await addImage(slide, "opportunity-center.png", 48, 142, 830, 492, "MarketPilot Opportunity Center screenshot");
  text(slide, rtl("לא מחיר קסם"), 920, 154, 290, 38, { size: 28, bold: true, color: C.white, align: "right" });
  const items = [
    ["BUY ZONE", "טווח כניסה"],
    ["STOP", "נקודת ביטול"],
    ["TARGET 1 / 2", "שני תרחישי מימוש"],
    ["RISK / REWARD", "סיכון מול פוטנציאל"],
  ];
  items.forEach(([en, he], index) => {
    const y = 222 + index * 72;
    text(slide, en, 920, y, 282, 24, { font: MONO, size: 14, bold: true, color: index === 1 ? C.coral : C.teal, align: "left" });
    text(slide, rtl(he), 920, y + 28, 282, 30, { size: 22, color: C.white, align: "right" });
  });
  rect(slide, 920, 520, 290, 2, C.lineDark);
  text(slide, "1 / 20", 920, 546, 100, 34, { font: MONO, size: 24, bold: true, color: C.amber, align: "left" });
  text(slide, rtl(`ימי ${iso("Shadow Mode")} חיים`), 1028, 550, 182, 28, { size: 18, color: C.mutedDark, align: "right" });
  text(slide, rtl("אין פקודה, אין הבטחת תשואה"), 920, 590, 290, 26, { size: 18, color: C.coral, align: "right" });
  notes(
    slide,
    "05:45–06:35",
    "הסבר שהמערכת מציגה תרחיש שלם: טווח כניסה, נקודת ביטול, יעדים וגודל פוזיציה. Shadow Mode עדיין 1 מתוך 20 ולכן ההמלצה אינה Actionable. הנתונים ההיסטוריים מעשירים את המחקר, אך אינם מתחזים לימי תצפית חיים.",
    "docs/phase14-verification.md; docs/decisions/ADR-008-decision-intelligence.md",
  );
}

// 9 — Backtesting evidence
{
  const slide = presentation.slides.add();
  base(slide);
  title(slide, "היסטוריה שנבדקת בלי לייפות", "HISTORICAL VALIDATION", 9, false);
  await addImage(slide, "backtesting.png", 52, 134, 840, 486, "MarketPilot Backtesting Lab screenshot");
  text(slide, rtl("ריצה מאושרת"), 930, 148, 280, 36, { size: 26, bold: true, color: C.white, align: "right" });
  const facts = [
    ["41", "ימי מסחר מאושרים", C.teal],
    ["46,749", "תצפיות", C.blue],
    ["1,059", "שינויי פוזיציה", C.amber],
  ];
  facts.forEach(([metric, caption, color], index) => {
    const y = 216 + index * 94;
    text(slide, metric, 930, y, 280, 43, { font: MONO, size: 32, bold: true, color, align: "left" });
    text(slide, rtl(caption), 930, y + 45, 280, 28, { size: 21, color: C.mutedDark, align: "right" });
  });
  rule(slide, 930, 506, 280, C.lineDark, 1);
  text(slide, rtl(`האות של נר ${iso("t")} משפיע רק על הנר הבא, והחישוב כולל עלויות והחלקת מחיר.`), 930, 530, 280, 74, {
    size: 20,
    color: C.mutedDark,
    align: "right",
  });
  notes(
    slide,
    "06:35–07:25",
    "הדגש שהמטרה אינה להציג תשואה מושלמת. המטרה היא להוכיח ניסוי שחזורי והוגן: Certified input בלבד, אות משפיע מהנר הבא, ועלויות אינן מוסתרות. ציין בכנות שהתוצאות משתנות בין הנכסים ואינן הבטחת תשואה.",
    "docs/phase14-historical-evidence-verification.md; docs/decisions/ADR-005-historical-backtesting.md",
  );
}

// 10 — Engineering challenges
{
  const slide = presentation.slides.add();
  base(slide);
  title(slide, "החלטות הנדסיות מרכזיות", "ENGINEERING CHALLENGES", 10);
  text(slide, rtl("המתח"), 920, 132, 290, 26, { size: 16, bold: true, color: C.mutedDark, align: "right" });
  text(slide, rtl("ההחלטה"), 110, 132, 680, 26, { size: 16, bold: true, color: C.mutedDark, align: "right" });
  rule(slide, 64, 170, 1152, C.lineDark, 1);
  const rows = [
    ["מהירות מול אמינות", "נתון חי מוצג מיד. יום סגור נבנה מחדש ונבדק.", "PROVISIONAL / CERTIFIED", C.teal],
    ["כשל וניסיון חוזר", "הפעלה חוזרת אינה יוצרת רשומה עסקית כפולה.", "CHECKPOINT · BUSINESS KEY · UPSERT", C.blue],
    ["היסטוריה בלי קיצור דרך", "נתוני עבר עוברים שמירה גולמית ואיכות לפני פרסום.", "HISTORICAL TOPIC · BRONZE BARRIER", C.amber],
    ["מוצר בלי חשיפת תשתית", "הדפדפן מקבל מידע רק דרך ממשק מוגבל לקריאה.", "READ-ONLY BACKEND API", C.coral],
  ];
  rows.forEach(([problem, decision, mechanism, accent], index) => {
    const y = 194 + index * 105;
    text(slide, rtl(problem), 872, y, 338, 48, { size: 25, bold: true, color: C.white, align: "right" });
    rect(slide, 828, y + 2, 4, 58, accent);
    text(slide, rtl(decision), 110, y - 2, 675, 36, { size: 22, color: C.white, align: "right" });
    text(slide, mechanism, 110, y + 40, 675, 24, { font: MONO, size: 14, bold: true, color: accent, align: "left" });
    if (index < rows.length - 1) rule(slide, 64, y + 82, 1152, C.lineDark, 1);
  });
  notes(
    slide,
    "07:25–08:15",
    "בחר שני אתגרים והסבר אותם כסיפור של החלטה. לדוגמה: רצינו נתון מהיר בלי להעמיד פנים שהוא מאושר, ולכן הפרדנו Provisional מ-Certified. רצינו Retry בטוח, ולכן השתמשנו ב-Checkpoint, Business Keys ו-Upsert. אלה החלטות שאתה יכול לייחס לעצמך.",
    "docs/decisions/ADR-003-streaming-lifecycle.md; ADR-004-provisional-certified-publication.md; ADR-007-certified-historical-acquisition.md",
  );
}

// 11 — Roadmap
{
  const slide = presentation.slides.add();
  base(slide);
  title(slide, "מה עובד היום ומה מגיע בהמשך", "ROADMAP", 11, false);
  text(slide, rtl("המטרה אינה להוסיף עוד טכנולוגיה. המטרה היא להרחיב אמון, כיסוי ותפעול."), 505, 124, 710, 42, {
    size: 22,
    color: C.mutedDark,
    align: "right",
  });

  rule(slide, 136, 342, 1000, C.lineDark, 4);
  const milestones = [
    [1030, "01", "היום", `סביבה מקומית עובדת\n41 ימים מאושרים\n${iso("Shadow Mode 1/20")}`, C.teal],
    [635, "02", "לאחר 20 ימים חיים", `בדיקת ${iso("Calibration")}\nאישור אנושי נפרד\nפתיחת ${iso("Decision Support")}`, C.blue],
    [240, "03", "הרחבה עתידית", `${iso("SIP / S3 / Elastic")}\n${iso("Authentication + TLS")}\nפריסה משותפת`, C.amber],
  ];
  milestones.forEach(([x, n, heading, body, accent]) => {
    rect(slide, x, 327, 30, 30, accent, 15);
    text(slide, n, x - 4, 330, 38, 20, { font: MONO, size: 11, bold: true, color: C.ink, align: "center", valign: "middle" });
    text(slide, rtl(heading), x - 190, 210, 220, 60, { size: 27, bold: true, color: C.white, align: "right" });
    text(slide, rtl(body), x - 190, 390, 220, 116, { size: 21, color: C.mutedDark, align: "right", lineSpacing: 1.05 });
  });
  text(slide, rtl("הקידום יתאפשר רק לאחר ראיות חיות ובדיקה אנושית. תוצאות היסטוריות לבדן אינן מספיקות."), 464, 556, 750, 46, {
    size: 21,
    bold: true,
    color: C.coral,
    align: "right",
  });
  notes(
    slide,
    "08:15–08:55",
    "פתח במה שכבר עובד: מערכת מקומית מלאה והיסטוריה מאושרת. לאחר 20 ימים חיים ייבדקו Calibration ותוצאות Shadow Mode, ורק החלטה אנושית נפרדת תוכל לקדם את המצב. ענן, SIP, Elastic ואבטחה מלאה הם הרחבות עתידיות ולא חלק מן המימוש הנוכחי.",
    "docs/implementation-plan.md; docs/phase14-verification.md",
  );
}

// 12 — Demo transition
{
  const slide = presentation.slides.add();
  base(slide);
  label(slide, "LIVE DEMO · 06:00", 64, 44, 280, C.teal, "left");
  text(slide, rtl("עכשיו מוכיחים את זה בלייב"), 520, 98, 694, 62, {
    size: 42,
    bold: true,
    color: C.white,
    align: "right",
  });
  text(slide, rtl("מהאירוע הגולמי ועד תרחיש החלטה שאפשר להסביר ולשחזר"), 590, 174, 624, 50, {
    size: 23,
    color: C.mutedDark,
    align: "right",
  });

  const stops = [
    ["06", "Backtesting"],
    ["05", "Opportunity"],
    ["04", "Airflow"],
    ["03", "MinIO"],
    ["02", "Kafka"],
    ["01", "Dashboard"],
  ];
  const nodes = stops.map(([n, name], index) => {
    const x = 74 + index * 196;
    const marker = rect(slide, x, 334, 44, 44, index === 5 ? C.teal : C.ink2, 22, {
      style: "solid",
      fill: index === 5 ? C.teal : C.lineDark,
      width: 1.5,
    });
    text(slide, n, x, 346, 44, 18, { font: MONO, size: 12, bold: true, color: index === 5 ? C.ink : C.teal, align: "center" });
    text(slide, name, x - 52, 404, 148, 34, { font: MONO, size: 17, bold: true, color: C.white, align: "center" });
    return marker;
  });
  for (let i = nodes.length - 1; i > 0; i--) connectLeft(slide, nodes[i], nodes[i - 1], C.teal);
  text(slide, rtl("החלטה ובדיקה"), 64, 492, 260, 34, { size: 22, bold: true, color: C.teal, align: "right" });
  text(slide, rtl("מקור ואישור"), 510, 492, 260, 34, { size: 22, bold: true, color: C.blue, align: "right" });
  text(slide, rtl("המוצר והאירוע"), 950, 492, 264, 34, { size: 22, bold: true, color: C.amber, align: "right" });
  text(slide, rtl("הדמו לקריאה בלבד. לא מפעילים Backfill, לא משנים נתונים ולא מציגים סודות."), 378, 586, 836, 38, {
    size: 18,
    color: C.coral,
    align: "right",
  });
  slideNumber(slide, 12);
  notes(
    slide,
    "08:55–09:10",
    "סיים את חלק המצגת ועבור לדמו. אמור: עכשיו אעקוב אחרי אותה שרשרת במערכת עצמה. המסלול הוא Dashboard, Kafka, MinIO, Airflow, Opportunity Center ו-Backtesting. פתח את סקריפט הדמו והתחל את הטיימר.",
    "docs/presentation/live-demo-script-he.md; scripts/demo-preflight.ps1",
  );
}

function patchHebrewParagraph(paragraphXml) {
  const cleanParagraph = stripBidiControls(paragraphXml);
  const visibleText = cleanParagraph
    .replace(/<[^>]+>/g, "")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">");
  if (!containsHebrew(visibleText)) return cleanParagraph;

  let patched = cleanParagraph;
  if (/<a:pPr\b/.test(patched)) {
    patched = patched.replace(/<a:pPr\b([^>]*)>/, (_match, attributes) => {
      const cleanAttributes = attributes
        .replace(/\s+algn="[^"]*"/g, "")
        .replace(/\s+rtl="[^"]*"/g, "");
      return `<a:pPr${cleanAttributes} algn="r" rtl="1">`;
    });
  } else {
    patched = patched.replace(/(<a:p\b[^>]*>)/, '$1<a:pPr algn="r" rtl="1" />');
  }

  return patched.replace(/<a:(rPr|defRPr)\b([^>]*)>/g, (_match, tag, attributes) => {
    const cleanAttributes = attributes.replace(/\s+lang="[^"]*"/g, "");
    return `<a:${tag}${cleanAttributes} lang="he-IL">`;
  });
}

async function enforcePowerPointRtl(filePath) {
  const zip = await JSZip.loadAsync(await fs.readFile(filePath));
  const xmlTargets = Object.entries(zip.files).filter(([name, entry]) =>
    !entry.dir &&
    (/^ppt\/slides\/slide\d+\.xml$/.test(name) ||
      /^ppt\/notesSlides\/notesSlide\d+\.xml$/.test(name)),
  );

  for (const [name, entry] of xmlTargets) {
    const originalXml = await entry.async("string");
    const cleanXml = stripBidiControls(originalXml);
    const patchedXml = cleanXml.replace(/<a:p\b[\s\S]*?<\/a:p>/g, patchHebrewParagraph);
    zip.file(name, patchedXml);
  }

  const patchedBytes = await zip.generateAsync({
    type: "nodebuffer",
    compression: "DEFLATE",
    compressionOptions: { level: 9 },
  });
  await fs.writeFile(filePath, patchedBytes);
}

await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
await enforcePowerPointRtl(candidatePath);

console.log(JSON.stringify({ candidatePath, slideCount: presentation.slides.items.length }, null, 2));
