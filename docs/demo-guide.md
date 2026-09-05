# MarketPilot - תרחיש ההצגה הסופי

זהו מקור האמת היחיד לזמני ההצגה לאחר Phase 12. ברירת המחדל היא 15 דקות;
קיימות גם גרסאות של 10 ו-20 דקות ב-`Presenter Console`.

> המסר המרכזי: MarketPilot מכניס נתוני שוק חיים והיסטוריים דרך מסלולים ניתנים
> לשחזור, מפריד בין מהיר למאושר, והופך Certified Gold ל-Analytics ול-Backtesting
> בלי לעקוף את Kafka, Bronze, Data Quality או גבול ה-API.

## המספרים שמותר להציג

אלה תוצאות Release Candidate מתאריך 2026-09-05, ולא מצב Production חי:

- 18 מתוך 18 שירותי Compose היו healthy.
- 86 בדיקות עברו; 7 בדיקות Docker אופציונליות דולגו אך הגבולות שלהן נבדקו בריצה המלאה.
- 20 ימי מסחר תקינים לפי לוח XNYS, מ-2026-08-03 עד 2026-08-28.
- 23,349 observations ו-555 שינויי פוזיציה ב-Backtest הסופי.
- 513 רשומות synthetic מסוף שבוע זוהו, נשמרו ל-audit והוחרגו מהחישוב.
- Run סופי: `48cf39e5-ccb0-5df6-9149-df5bc8741469`; code version: `bed1fb7`.

תוצאות האסטרטגיה הן ראיית Engineering בלבד. אין להציג אותן כהמלצה או כהבטחת תשואה.

## טבלת הזמן הקנונית - 15 דקות

| זמן | מקטע | מסך | המסר שחייב לעבור |
|---:|---|---|---|
| 00:00-01:30 | בעיה והבטחה | Project Story | מהיר, אבל גם גולמי, מאושר וניתן לשחזור |
| 01:30-03:30 | ארכיטקטורה | Project Story | לכל workload יש מסלול ובעלים |
| 03:30-06:00 | Live event | Dashboard, Kafka, MinIO | אירוע אחד מגיע למוצר ונשמר כראיית מקור |
| 06:00-08:30 | Historical to Certified | Airflow | היסטוריה אמיתית אינה עוקפת את Medallion |
| 08:30-10:30 | Backtesting | Backtesting Lab | רק Certified, ללא look-ahead, עם lineage |
| 10:30-12:00 | אמינות והתאוששות | Project Story Evidence | DQ, idempotency, checkpoint, archive ו-restore |
| 12:00-14:00 | החלטות וסיכום | Project Story | מה החלטתי, מה למדתי ומה הגבולות |
| 14:00-15:00 | מרווח | המסך הנוכחי | ניווט, שאלה קצרה או סיום רגוע |

## לפני שנכנסים לחדר

1. הרץ `docker compose ps` וודא שכל 18 השירותים healthy.
2. פתח מראש, בסדר הזה:
   - <http://localhost:3000/presenter.html>
   - <http://localhost:3000/showcase.html>
   - <http://localhost:3000/>
   - <http://localhost:8085/>
   - אובייקט Bronze מוכן תחת <http://localhost:9001/>
   - ה-run `phase12_month_lineage_final_20260905` תחת <http://localhost:8080/>
   - <http://localhost:3000/backtesting.html>
3. ב-Dashboard בחר `AAPL`; ב-Backtesting Lab ודא שה-run החדש ביותר נבחר.
4. סגור `.env`, טרמינלים עם secrets וכל clipboard שמכיל credentials.
5. אל תפעיל Backfill, Archive, SQL write או event ידני בזמן ההצגה.
6. בחר מצב 15 דקות ב-Presenter Console ואפס את הטיימר.

## תסריט מלא: מה לומר ומה לעשות

### 00:00-01:30 - הבעיה וההבטחה

**אמור:**

> MarketPilot הוא פרויקט Data Engineering מקומי עבור 11 נכסים ונתוני SEC.
> רציתי לפתור מתח אמיתי: להציג מידע מהר, בלי לוותר על מקור גולמי, איכות,
> שחזור ויכולת להסביר מאיפה כל תוצאה הגיעה. זו פלטפורמת Analytics ומחקר,
> לא מערכת לביצוע מסחר ולא הבטחת תשואה.

**הראה:** כותרת וארבעת עקרונות ה-Project Story.

**חשוב שיבינו:** לא בנית אוסף containers; בנית שרשרת אמון בנתונים.

**מעבר:** “כדי להשיג גם מהירות וגם אמינות, נתתי לכל סוג עבודה מסלול ובעלים ברורים.”

### 01:30-03:30 - הארכיטקטורה

עבור בין ארבעת ה-tabs ב-Project Story.

- Live: `Alpaca -> Producer -> Kafka -> Spark Streaming -> Gold PROVISIONAL`
- Raw: `Kafka -> raw-archive-sink -> MinIO Bronze`
- Certified: `Bronze -> Spark Batch -> Silver -> DQ -> Gold CERTIFIED`
- Historical: `Alpaca IEX -> Historical Kafka -> Bronze barrier -> Certified -> Backtest`
- SEC, במשפט: `SEC EDGAR -> raw Bronze + deduplicated Gold metadata`

**אמור:**

> Docker Compose מנהל שירותים ארוכי חיים. Airflow מנהל רק jobs שמתחילים
> ומסתיימים. Spark מבצע את החישוב; Airflow מסדר, מתזמן ומנטר אותו. MinIO
> מחזיק raw ו-Parquet, ואילו MariaDB מחזיק Gold שמוכן ל-API.

**מעבר:** “עכשיו אוכיח שהתרשים הזה הוא מערכת עובדת, לא architecture theater.”

### 03:30-06:00 - אירוע Live מקצה לקצה

1. ב-Dashboard הצג `AAPL`, freshness, certification, Close ו-SMA.
2. ב-Kafka UI פתח `market.bars.1m.v1` והצבע על key, partition ו-offset.
3. ב-MinIO פתח Bronze JSON מוכן והצבע על `event_id`, זמן מקור,
   `ingested_at_utc` ו-`schema_version`; ה-partition וה-offset נמצאים בנתיב.

**אמור:**

> אותו event משרת שני צרכנים עצמאיים. Spark Streaming מעדכן Gold כ-Provisional,
> ו-raw-archive-sink שומר Bronze לפני commit של ה-offset. הדפדפן אינו מכיר
> MariaDB או MinIO; הוא קורא רק דרך Backend API מוגבל.

**מעבר:** “ה-Live נותן מהירות. עכשיו אראה איך הכנסתי עבר אמיתי וקיבלתי אמון.”

### 06:00-08:30 - Historical to Certified

ב-Airflow פתח את `phase12_month_lineage_final_20260905` ב-DAG
`historical_market_backfill`. הצבע על הרצף:

`acquire -> Bronze barrier -> Bronze to Silver -> DQ -> Certified Gold -> Backtest`

**אמור:**

> לא כתבתי היסטוריה ישירות ל-MariaDB. כל response של Alpaca נשמר לפי SHA-256,
> וכל bar עבר topic היסטורי נפרד. Barrier מוכיח שכל partition ו-offset הגיעו
> ל-Bronze לפני ש-Spark מתחיל. לאחר מכן משתמשים באותו מסלול Certification.
> הריצה הסופית עיבדה 20 sessions אמיתיים לפי לוח XNYS.

**החלטה להדגיש:** topic היסטורי נפרד מונע burst של Backfill במסלול Streaming החי.

**מעבר:** “כעת יש היסטוריה אמיתית, מאושרת ובעלת lineage; אפשר לבחון עליה רעיון.”

### 08:30-10:30 - Backtesting

ב-Backtesting Lab בחר את ה-run שמתחיל `48cf39e5` ואת `AAPL`.

**אמור:**

> זה Spark Batch תחום בזמן, ורק Certified Gold רשאי להיכנס. אות שחושב ב-bar
> מסוים משפיע רק מה-bar הבא, כדי למנוע look-ahead bias. Costs ו-slippage
> מפורשים, והפלט המלא נשמר כ-Parquet עם run, data, code ו-schema versions.

הצג: 20 sessions, 23,349 observations, 555 trades, Equity Curve וטבלת ההשוואה.

**אמור על התוצאה:**

> AAPL החזיר 0.19% מול benchmark של 2.60%. MSFT ו-SPY באסטרטגיה היו שליליים.
> איני מסתיר תוצאה לא מחמיאה: ההצלחה כאן היא pipeline אמין ושחזור מלא,
> לא התאמת אסטרטגיה בדיעבד.

**מעבר:** “תוצאה אמינה חשובה יותר מתוצאה יפה. עכשיו אראה מה המערכת עושה כשמשהו אינו נקי.”

### 10:30-12:00 - אמינות והתאוששות

חזור ל-Evidence ב-Project Story.

**אמור:**

> בדקתי restart מ-checkpoint, retries, idempotent upserts, DQ חוסם, משתמש API
> עם SELECT בלבד, archive עם SHA-256 ושחזור לסכמה מבודדת. בריצת החודש זוהו
> 513 רשומות synthetic מסוף שבוע. הן לא נמחקו כדי לשמור audit trail, אבל
> הוחרגו ב-Spark SQL לפי sessions של XNYS.

הדגש: אין טענת exactly-once מקצה לקצה. הנכונות העסקית נבנית מ-offsets,
checkpoints, business keys, upserts ופרסום אטומי.

### 12:00-14:00 - החלטות, למידה וסיכום

**אמור:**

> שלוש ההחלטות המרכזיות שלי היו: לא להפוך את Airflow ל-service supervisor;
> להפריד בין Provisional מהיר ל-Certified סמכותי; ולשמור raw מחוץ למסד ה-serving.
> למדתי ש-Data Engineering אינו רק להעביר נתון. צריך להגדיר חוזים, בעלות על
> processes, semantics של retry, איכות, lineage ויכולת restore.

**מגבלות בכנות:** broker יחיד, IEX אינו feed מאוחד מלא, אין end-user auth/TLS,
אין capacity benchmark ל-Production, והאסטרטגיה אינה מודל השקעה.

**משפט סיום:**

> MarketPilot היא Data Platform מקומית אבל שלמה: ממקור חי והיסטורי, דרך
> transport, storage, compute ו-quality gates, ועד API, Analytics ו-Backtesting
> שאני יכול להסביר, לבדוק ולשחזר. תודה, אשמח לשאלות.

### 14:00-15:00 - מרווח

אל תפתח נושא חדש. השלם מעבר מסך, ענה על שאלה קצרה או סיים מוקדם ובביטחון.

## גרסת 10 דקות

שמור את הסיבתיות, לא את כל המסכים:

- 1:00 פתיחה
- 1:30 ארכיטקטורה
- 2:30 Live event
- 2:00 Historical to Certified
- 1:30 Backtesting
- 1:00 אמינות
- 0:30 סיכום

דלג על Spark UI, Adminer, SEC לעומק ופרטי Archive. הצג Bronze או Kafka, לא את שניהם.

## גרסת 20 דקות

הרחב בלבד:

- SEC: User-Agent, throttling, accession number ו-raw JSON.
- MinIO: source pages content-addressed ו-session manifest.
- Data Quality: completeness, duplicates, nulls, OHLC ו-expected bars.
- Archive/restore: inventory SHA-256 ושחזור לסכמה מבודדת.
- Tradeoffs: LocalExecutor, broker יחיד, IEX coverage והמעבר העתידי ל-S3.

## חלופות כשמסך לא עובד

| מסך שנפל | חלופה בטוחה | מה לומר |
|---|---|---|
| Dashboard | Project Story + `docs/phase9-verification.md` | “זו ראיה מתוארכת, לא מצב חי.” |
| Kafka UI | Bronze object + `docs/phase12-verification.md` | “ה-offset נשמר בנתיב ומוכיח lineage.” |
| MinIO | Historical tab + Phase 12 verification | “ה-UI הוא כלי צפייה; ה-manifest הוא הראיה.” |
| Airflow | `docs/phase12-verification.md` | “הריצה הסופית הסתיימה ב-success; איני מפעיל DAG לצורך אפקט.” |
| Backtesting Lab | טבלת Final published results ב-Phase 12 | “המספרים מתוארכים ומקושרים ל-run ול-code version.” |
| Backend API | Phase 7 verification | “איני עוקף את גבול ה-API באמצעות חיבור UI ישיר למסד.” |

## משפטי חירום שכדאי לזכור

- “הממשק המקומי אינו זמין כרגע, ולכן אעבור לראיית verification מתוארכת.”
- “אני מפריד בין מצב live לבין snapshot שנמדד.”
- “לא אשנה נתונים כדי לתקן דמו; אשתמש במסלול הגיבוי שהוכן מראש.”
- “אני לא יודע בוודאות; אומר מה נמדד ואיך הייתי בודק את השאר.”
