# MarketPilot - מסלול הדגמה רשמי

זהו מקור האמת לזמני ההצגה. המסלול הראשי הוא 15 דקות, עם גרסאות מכוונות של
10 ו-20 דקות. המטרה אינה לפתוח את כל הכלים, אלא להוכיח סיפור אחד:

> MarketPilot הופך אירוע שוק לנתון מהיר, גולמי, מאושר וניתן להצגה - תוך שמירה
> על replay, איכות, lineage, התאוששות וגבול API מאובטח.

## בחירת מסלול

| מסלול | מתי לבחור | מה נשאר תמיד |
|---|---|---|
| 10 דקות | הזמן קוצר או שיש שאלות רבות | הבעיה, תרשים אחד, אירוע מקצה לקצה, Dashboard והוכחת אמינות אחת |
| 15 דקות | ברירת המחדל המומלצת | כל הסיפור המרכזי עם הוכחה חיה וזמן ניווט |
| 20 דקות | ניתנה מסגרת רחבה במפורש | SEC, Airflow לעומק, DQ, archive/restore, lineage ו-tradeoffs |

## טבלת הזמן הקנונית - 15 דקות

| זמן | מקטע | מסך ראשי | תוצאה רצויה |
|---:|---|---|---|
| 00:00-01:30 | הבעיה, ההיקף וההבטחה | Project Story | הקהל מבין מה נבנה ולמי |
| 01:30-04:00 | הארכיטקטורה וארבעת המסלולים | מסמך/Project Story | הקהל מבין Live, Raw, Certified ו-SEC |
| 04:00-09:30 | הוכחה מקצה לקצה | Dashboard, Kafka, MinIO | אירוע עובר ממקור עד מוצר עם lineage |
| 09:30-11:30 | Batch, איכות והתאוששות | Airflow, Spark, verification | ברור למה נתון מהיר עדיין אינו Certified |
| 11:30-13:00 | Analytics והערך למשתמש | Dashboard | הנתונים הופכים להסבר ולא רק לטבלה |
| 13:00-14:00 | בגרות הנדסית וסיכום | Evidence | בדיקות, אבטחה, archive וגבולות |
| 14:00-15:00 | מרווח ניווט או שאלה | המסך הנוכחי | לא ממהרים ולא חורגים מהזמן |

## הכנה לפני ההצגה

1. הרץ `docker compose ps` וודא שכל השירותים הנדרשים בריאים.
2. פתח מראש, בסדר הזה:
   - Presenter Console: <http://localhost:3000/presenter.html>
   - Project Story: <http://localhost:3000/showcase.html>
   - Dashboard: <http://localhost:3000/>
   - Kafka UI: <http://localhost:8085/>
   - MinIO: <http://localhost:9001/>
   - Airflow: <http://localhost:8080/>
   - Spark: <http://localhost:18080/>
   - Adminer: <http://localhost:8086/>
   - Backend API: <http://localhost:8000/docs>
3. בחר מראש Symbol עם נתונים בטווח שבעת הימים האחרונים, בדרך כלל `AAPL`.
4. פתח מראש אובייקט Bronze אחד, Topic אחד ו-DAG אחד. אל תחפש בזמן אמת מול הקהל.
5. אל תפתח `.env`, אל תציג סיסמאות ואל תפעיל Backfill או Archive בזמן הדמו.

## המסלול המלא - מה לומר ומה להראות

### 00:00-01:30 - הבעיה והפתרון

**אמור:**

> MarketPilot הוא פרויקט Data Engineering מקומי שמרכז נתוני שוק ו-SEC עבור
> 11 נכסים. האתגר הוא לספק נתון מהר, אבל גם לשמור מקור גולמי ולבנות גרסה
> מאושרת שאפשר להסביר ולשחזר. לכן המערכת מפרידה בין Live, Raw ו-Certified.

**הראה:** כותרת ה-Project Story וארבעת עקרונות הפרויקט.

**הקהל צריך להבין:** זו פלטפורמת נתונים ו-Analytics, לא מערכת לביצוע מסחר.

**מעבר:** "כדי להשיג גם מהירות וגם אמינות, לכל סוג עבודה יש מסלול ובעלים ברורים."

### 01:30-04:00 - הארכיטקטורה

הצג את התרשים המלא או את בורר המסלולים ב-Project Story.

**Live:** `Alpaca -> market-producer -> Kafka -> Spark Streaming -> Gold PROVISIONAL`

**Raw:** `Kafka -> raw-archive-sink -> MinIO Bronze`

**Certified:** `Bronze -> Spark Batch -> Silver -> DQ -> Spark Batch -> Gold CERTIFIED`

**SEC:** `SEC EDGAR -> SEC adapter -> Bronze + Gold metadata`

**אמור:**

> Docker Compose מנהל שירותים שחיים כל הזמן. Airflow מנהל רק עבודות שמתחילות
> ומסתיימות. זו הסיבה ש-Spark Streaming אינו Task של Airflow.

**הבחנה שחייבים לזכור:** MinIO מחזיק חומר גלם, Parquet וארכיון; MariaDB מחזיק
Gold שמוכן לשאילתות היישום.

### 04:00-09:30 - הוכחה של אירוע מקצה לקצה

#### Dashboard

- בחר `AAPL` וטווח `7D`.
- הצג Freshness, מצב Certification, גרף Close וקו SMA 20.
- הצג Indicator אחד ו-Signal מוסבר אחד.

**אמור:** "המשתמש רואה רק נתונים שמגיעים דרך Backend API. הדפדפן אינו מכיר
כתובת או סיסמה של MariaDB או MinIO."

#### Kafka UI

- פתח `market.bars.1m.v1`.
- הצג key של Symbol, partition, offset ו-consumer groups.

**אמור:** "Kafka מפריד בין המפיק לצרכנים. אותו אירוע יכול להגיע גם למסלול
Streaming וגם למסלול הארכיון בלי שהמפיק יכיר את שניהם."

#### MinIO Bronze

- פתח אובייקט תחת `source=alpaca` או `source=synthetic`.
- הצג `event_id`, זמן מקור, `ingested_at_utc` ו-schema version.
- הצג את partition/offset בשם האובייקט או הנתיב.

**אמור:** "ה-JSON הוא גוף האירוע. מיקום Kafka נשמר בנתיב כדי לתמוך ב-lineage,
idempotency ו-replay. האובייקט נכתב לפני שה-consumer מאשר את ה-offset."

**מעבר:** "עד כאן הוכחנו נתון מהיר ומקור גולמי. עכשיו נראה כיצד יום סגור הופך
לנתון מאושר."

### 09:30-11:30 - Certified, איכות והתאוששות

#### Airflow

- הצג `daily_market_close`.
- עקוב אחר הסדר Bronze -> Silver -> DQ -> Gold -> Analytics.
- הצג `max_active_runs=1` ואת DAG ה-Backfill הפרמטרי.

#### Spark

- הצג Master ו-Worker בריאים.
- הסבר ש-Airflow שולח Spark Batch מוגבל בזמן, בעוד Streaming נשאר פעיל תחת Docker.

**אמור:**

> Batch בונה מחדש את המחיצה מ-Bronze. רק אם בדיקות freshness, completeness,
> duplicates, nulls ו-OHLC עוברות, מתקדמים ל-CERTIFIED. כשל אינו מוחק את
> ה-Certified הקודם ואינו מקדם watermark.

**ראיית גיבוי:** `docs/phase4-verification.md` מתעד 1,881 רשומות, עשר בדיקות
חוסמות וריצה שלילית שלא שינתה את Gold הקודם.

### 11:30-13:00 - Analytics והערך למשתמש

חזור ל-Dashboard.

- הצג SMA 20, RSI 14, Realized Volatility ו-Volume Ratio.
- הצג הסבר של Signal, לא רק את הכיוון שלו.

**אמור:**

> שכבת Analytics אינה נותנת המלצת מסחר. היא מספקת context מוסבר ומתועד.
> כל Indicator ו-Signal נושא version, run, code, data ו-certification lineage.

### 13:00-14:00 - בגרות הנדסית וסיכום

חזור לאזור Evidence ב-Project Story.

**אמור:**

> מעבר ל-Happy Path, בדקתי restart מ-checkpoint, idempotency, הרשאת SELECT בלבד,
> DQ חוסם, compaction, archive עם SHA-256 ושחזור מבודד. המערכת אינה טוענת
> ל-exactly once מקצה לקצה; היא משיגה נכונות עסקית באמצעות replay, keys ו-upserts.

סיים במשפט:

> MarketPilot מדגים כיצד בונים Data Platform קטנה אבל שלמה: מהמקור, דרך transport,
> storage ו-compute, ועד API, Analytics וחוויית משתמש שניתנת להסבר ולשחזור.

### 14:00-15:00 - מרווח

אל תוסיף נושא חדש. השתמש בזמן כדי לעבור מסך, לענות על שאלה קצרה או לחזור למשפט
הסיום. אם הקדמת, עצור בביטחון; אין צורך למלא כל שנייה.

## קיצור ל-10 דקות

השאר: פתיחה, תרשים אחד, Dashboard, Kafka, Bronze, משפט על Airflow/DQ וסיכום.

דלג על: Spark UI, Adminer, SEC לעומק, archive numbers, פירוט כל Indicator.

חלוקה: 1:00 פתיחה, 1:30 ארכיטקטורה, 4:00 אירוע, 1:30 אמינות, 1:30 Dashboard,
0:30 סיכום.

## הרחבה ל-20 דקות

הוסף בלבד:

- SEC: User-Agent, throttling, accession number ו-raw JSON ב-Bronze;
- Adminer: Gold tables, watermarks ו-DQ results;
- archive/restore: manifest, SHA-256 ושחזור לסכמה מבודדת;
- tradeoffs: LocalExecutor, Kafka יחיד, localhost security והדרך לענן.

אל תחזור פעמיים על אותו מסלול נתונים.

## כללי בטיחות להצגה

- אין להציג `.env`, credentials או connection strings.
- אין לבצע כתיבות ידניות למסד לצורך אפקט.
- אין להפעיל DAG תחזוקתי ללא הכנה ואישור.
- מספרים מ-Verification מוצגים עם תאריך; מספרים מה-API מוצגים כמצב חי.
- אם ממשק אינו זמין, אומרים זאת במפורש ועוברים לראיה מתועדת.
