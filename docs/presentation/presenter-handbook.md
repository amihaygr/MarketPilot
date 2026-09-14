<div dir="rtl" align="right">

# <bdi dir="ltr"><code>MarketPilot</code></bdi> — חוברת המסביר

המטרה של החוברת היא שלא רק תדע מה ללחוץ, אלא תבין מה אתה מציג ותוכל להסביר
אותו במילים שלך. אין צורך לשנן את כל הטקסט. למד קודם את המודלים המחשבתיים ואת
ההבדלים החשובים.

## הסיפור במשפט אחד

<bdi dir="ltr">MarketPilot</bdi> מקבל נתוני שוק ו־<bdi dir="ltr">SEC</bdi>, שומר מקור גולמי שניתן לשחזור, מעבד נתונים
במסלול חי ובמסלול <bdi dir="ltr">Batch</bdi> מאושר, ומציג <bdi dir="ltr">Gold</bdi> ו־<bdi dir="ltr">Analytics</bdi> למשתמש דרך <bdi dir="ltr">API</bdi> מוגבל.

## הסיפור בשבעה משפטים

1. <bdi dir="ltr">Alpaca</bdi> שולח <bdi dir="ltr">bars</bdi> של דקה, וה־<bdi dir="ltr">producer</bdi> מתרגם אותם לחוזה <bdi dir="ltr"><code>MarketBarV1</code></bdi>.
2. <bdi dir="ltr">Kafka</bdi> מפריד בין המקור לצרכנים ושומר סדר ומיקום באמצעות <bdi dir="ltr">partition</bdi> ו־<bdi dir="ltr">offset</bdi>.
3. <bdi dir="ltr">Spark Streaming</bdi> מפרסם מהר ל־<bdi dir="ltr">Gold</bdi> כ־<bdi dir="ltr">PROVISIONAL</bdi>, ובמקביל <bdi dir="ltr">raw-archive-sink</bdi> שומר <bdi dir="ltr">Bronze</bdi> ב־<bdi dir="ltr">MinIO</bdi>.
4. <bdi dir="ltr">Airflow</bdi> מפעיל עבודות <bdi dir="ltr">Spark Batch</bdi> מוגבלות בזמן שבונות <bdi dir="ltr">Silver</bdi> ומפרסמות <bdi dir="ltr">CERTIFIED</bdi> רק אחרי <bdi dir="ltr">DQ</bdi>.
5. ה־<bdi dir="ltr">Dashboard</bdi> קורא רק דרך <bdi dir="ltr">Backend API</bdi> עם משתמש <bdi dir="ltr">MariaDB</bdi> בעל <bdi dir="ltr">SELECT</bdi> בלבד.
6. <bdi dir="ltr">Historical Backfill</bdi> מכניס <bdi dir="ltr">Alpaca IEX</bdi> דרך <bdi dir="ltr">topic</bdi> נפרד, <bdi dir="ltr">Bronze barrier</bdi> ואותו מסלול <bdi dir="ltr">Certification</bdi>.
7. <bdi dir="ltr">Backtesting</bdi> משתמש רק ב־<bdi dir="ltr">Certified Gold</bdi> ושומר תוצאה מלאה, הנחות ו־<bdi dir="ltr">lineage</bdi> שניתנים לשחזור.
8. <bdi dir="ltr">Opportunity Center</bdi> מפריד בין ראיות היסטוריות לבין <bdi dir="ltr">Live Shadow Mode</bdi>, ומציג תרחיש מחקר מוסבר בלי לבצע פקודה.

## ההבחנה החדשה שחובה להסביר

- **<bdi dir="ltr">Historical Evidence</bdi>:** ימים מאושרים מן העבר שמשמשים לגרף, <bdi dir="ltr">Backtest</bdi> והערכת רעיונות.
- **<bdi dir="ltr">Live Shadow Mode</bdi>:** המלצות שנוצרו בזמן אמת ונמדדות רק לאחר שהזמן באמת חלף.
- <bdi dir="ltr">Backfill</bdi> היסטורי לעולם אינו מגדיל את מונה <bdi dir="ltr"><code>1/20</code></bdi> של השער החי.
- המשמעות המקצועית: אפשר להציג מערכת עשירה היום בלי לזייף תקופת תצפית עתידית.

## חמשת המסלולים שאתה חייב להסביר ללא דף

### המסלול החי (<bdi dir="ltr">Live</bdi>)

<bdi dir="ltr"><code>Alpaca -> Producer -> Kafka -> Spark Streaming -> MariaDB Gold PROVISIONAL</code></bdi>

מטרתו לתת נתון טרי. הוא מהיר, אך יום שעדיין פתוח עלול לקבל אירועים מאוחרים או
תיקונים. לכן התוצאה מסומנת <bdi dir="ltr">Provisional</bdi>.

### המסלול הגולמי (<bdi dir="ltr">Raw</bdi>)

<bdi dir="ltr"><code>Kafka -> raw-archive-sink -> MinIO Bronze</code></bdi>

מטרתו לשמור את העובדות המקוריות. אם צריך לתקן קוד, לבצע <bdi dir="ltr">backfill</bdi> או להוכיח
<bdi dir="ltr">lineage</bdi>, אפשר לחזור ל־<bdi dir="ltr">Bronze</bdi> במקום להסתמך רק על מה שכבר עובד.

### המסלול המאושר (<bdi dir="ltr">Certified</bdi>)

<bdi dir="ltr"><code>Bronze -> Spark Batch -> Silver -> DQ -> Spark Batch -> Gold CERTIFIED</code></bdi>

מטרתו לבנות מחדש יום סגור ממקור גולמי, לנקות ולבדוק אותו, ורק אז לפרסם תוצאה
סמכותית. <bdi dir="ltr">Batch</bdi> הוא המסלול המאשר; <bdi dir="ltr">Streaming</bdi> הוא המסלול המהיר.

### <bdi dir="ltr">SEC</bdi>

<bdi dir="ltr"><code>SEC EDGAR -> SEC adapter -> MinIO Bronze + MariaDB Gold metadata</code></bdi>

ה־<bdi dir="ltr">JSON</bdi> המקורי נשמר ב־<bdi dir="ltr">Bronze. Metadata</bdi> שימושי נשמר ב־<bdi dir="ltr">Gold. accession number</bdi>
משמש כמפתח עסקי שמונע כפילות גם כשה־<bdi dir="ltr">poll</bdi> חוזר על אותן הגשות.

## כרטיסי הסבר לרכיבים מרכזיים

### <bdi dir="ltr"><code>Kafka</code></bdi>

- **במשפט:** מערכת תורים מבוזרת שמעבירה <bdi dir="ltr">events</bdi> בין <bdi dir="ltr">producers</bdi> ל־<bdi dir="ltr">consumers</bdi>.
- **ב־<bdi dir="ltr">MarketPilot</bdi>:** מקבלת <bdi dir="ltr">MarketBarV1</bdi> ומאפשרת ל־<bdi dir="ltr">Streaming</bdi> ול־<bdi dir="ltr">archive</bdi> לצרוך בנפרד.
- **למה לא לדלג:** חיבור ישיר בין <bdi dir="ltr">Alpaca</bdi> ל־<bdi dir="ltr">Spark</bdi> היה מצמיד בין הרכיבים ומחליש <bdi dir="ltr">replay</bdi>.
- **מה להראות:** <bdi dir="ltr">Topic</bdi>, <bdi dir="ltr">key</bdi>, <bdi dir="ltr">partition</bdi>, <bdi dir="ltr">offset</bdi> ו־<bdi dir="ltr">consumer group</bdi>.
- **בלבול נפוץ:** <bdi dir="ltr">Kafka</bdi> אינו מסד הנתונים העסקי; הוא <bdi dir="ltr">transport</bdi> ו־<bdi dir="ltr">log</bdi> של <bdi dir="ltr">events</bdi>.
- **עומק:** אין טענה ל־<bdi dir="ltr">exactly once</bdi> בין כל המערכות; <bdi dir="ltr">offset</bdi> ו־<bdi dir="ltr">idempotency</bdi> מגנים על הנכונות.

### <bdi dir="ltr"><code>Spark Structured Streaming</code></bdi>

- **במשפט:** מנוע שמעבד <bdi dir="ltr">stream</bdi> כמיקרו־<bdi dir="ltr">batches</bdi> מתמשכים.
- **ב־<bdi dir="ltr">MarketPilot</bdi>:** קורא <bdi dir="ltr">Kafka</bdi>, מאמת <bdi dir="ltr">events</bdi>, משתמש ב־<bdi dir="ltr">event time</bdi> ומבצע <bdi dir="ltr">upsert</bdi> ל־<bdi dir="ltr">Gold</bdi>.
- **למה לא לדלג:** הוא נותן מסלול כמעט בזמן אמת עם <bdi dir="ltr">recovery</bdi> מ־<bdi dir="ltr">checkpoint</bdi>.
- **מה להראות:** <bdi dir="ltr">Spark application</bdi>, <bdi dir="ltr">Worker</bdi> ונתוני <bdi dir="ltr">PROVISIONAL</bdi> ב־<bdi dir="ltr">Gold</bdi>.
- **בלבול נפוץ:** <bdi dir="ltr">Streaming</bdi> אינו מופעל כל בוקר מ־<bdi dir="ltr">Airflow</bdi>; הוא שירות ארוך חיים.
- **עומק:** <bdi dir="ltr">checkpoint</bdi> מכיל <bdi dir="ltr">offset</bdi> והתקדמות <bdi dir="ltr">state</bdi> ולכן הוא <bdi dir="ltr">state</bdi> קריטי שאסור למחוק סתם.

### <bdi dir="ltr"><code>Spark Batch</code></bdi>

- **במשפט:** עבודת עיבוד שמתחילה, מעבדת קלט תחום ומסתיימת.
- **ב־<bdi dir="ltr">MarketPilot</bdi>:** מבצעת <bdi dir="ltr">Bronze to Silver</bdi>, <bdi dir="ltr">Silver to Gold</bdi>, <bdi dir="ltr">analytics</bdi>, <bdi dir="ltr">backfill</bdi> ותחזוקה.
- **למה לא לדלג:** היא מאפשרת חישוב מחדש דטרמיניסטי של יום סגור ובדיקות מלאות.
- **מה להראות:** <bdi dir="ltr">DAG tasks</bdi>, <bdi dir="ltr">Spark job</bdi> ו־<bdi dir="ltr">Silver Parquet</bdi>.
- **בלבול נפוץ:** <bdi dir="ltr">Spark</bdi> הוא מנוע החישוב; <bdi dir="ltr">Airflow</bdi> הוא מנהל סדר העבודה.
- **עומק:** פרסום <bdi dir="ltr">Gold</bdi> נעשה בגבול אטומי ורק לאחר <bdi dir="ltr">DQ</bdi> חוסם.

### <bdi dir="ltr"><code>Airflow</code></bdi>

- **במשפט:** <bdi dir="ltr">Orchestrator</bdi> לעבודות בעלות התחלה וסיום.
- **ב־<bdi dir="ltr">MarketPilot</bdi>:** מתזמן <bdi dir="ltr">SEC</bdi>, <bdi dir="ltr">Batch</bdi>, <bdi dir="ltr">DQ</bdi>, <bdi dir="ltr">backfill</bdi>, <bdi dir="ltr">compaction</bdi> ו־<bdi dir="ltr">archive</bdi>.
- **למה לא לדלג:** הוא מנהל <bdi dir="ltr">dependencies</bdi>, <bdi dir="ltr">retries</bdi>, <bdi dir="ltr">timeouts</bdi>, <bdi dir="ltr">pools</bdi> וסטטוס.
- **מה להראות:** <bdi dir="ltr"><code>daily_market_close</code></bdi>, סדר המשימות ו־<bdi dir="ltr"><code>max_active_runs=1</code></bdi>.
- **בלבול נפוץ:** <bdi dir="ltr">Airflow</bdi> אינו <bdi dir="ltr">supervisor</bdi> של <bdi dir="ltr">Kafka</bdi>, <bdi dir="ltr">Streaming</bdi>, <bdi dir="ltr">MariaDB</bdi> או <bdi dir="ltr">Web App</bdi>.
- **עומק:** <bdi dir="ltr"><code>SparkSubmitOperator</code></bdi> שולח <bdi dir="ltr">job</bdi> ל־<bdi dir="ltr">Spark Master</bdi> ומחכה ל־<bdi dir="ltr">terminal state</bdi>.

### <bdi dir="ltr"><code>MinIO</code></bdi>, ‏<bdi dir="ltr"><code>Bronze</code></bdi> ו־<bdi dir="ltr"><code>Silver</code></bdi>

- **במשפט:** <bdi dir="ltr">MinIO</bdi> הוא <bdi dir="ltr">object storage</bdi> מקומי תואם <bdi dir="ltr">S3</bdi>.
- **ב־<bdi dir="ltr">MarketPilot</bdi>:** <bdi dir="ltr">Bronze</bdi> שומר <bdi dir="ltr">raw immutable</bdi>; <bdi dir="ltr">Silver</bdi> שומר <bdi dir="ltr">Parquet</bdi> נקי וקנוני.
- **למה לא לדלג:** <bdi dir="ltr">MariaDB</bdi> לבדו אינו מתאים ל־<bdi dir="ltr">raw replay</bdi>, <bdi dir="ltr">Parquet analytics</bdi> וארכיון.
- **מה להראות:** <bdi dir="ltr">bucket</bdi>, <bdi dir="ltr">partitioned path</bdi>, <bdi dir="ltr">JSON</bdi> ב־<bdi dir="ltr">Bronze</bdi> ו־<bdi dir="ltr">Parquet</bdi> ב־<bdi dir="ltr">Silver</bdi>.
- **בלבול נפוץ:** <bdi dir="ltr">Bronze</bdi> אינו טבלה נקייה; הוא ראיית המקור. <bdi dir="ltr">Silver</bdi> אינו שכבת היישום.
- **עומק:** <bdi dir="ltr">S3</bdi> הוא החלופה העתידית בלי לשנות את התפקיד הלוגי של השכבה.

### <bdi dir="ltr"><code>MariaDB Gold</code></bdi>

- **במשפט:** מסד ה־<bdi dir="ltr">serving</bdi> שמחזיק מודלים מוכנים ליישום.
- **ב־<bdi dir="ltr">MarketPilot</bdi>:** <bdi dir="ltr">bars</bdi>, <bdi dir="ltr">indicators</bdi>, <bdi dir="ltr">signals</bdi>, <bdi dir="ltr">SEC metadata</bdi>, <bdi dir="ltr">DQ</bdi>, <bdi dir="ltr">watermarks</bdi> ו־<bdi dir="ltr">manifests</bdi>.
- **למה לא לדלג:** ה־<bdi dir="ltr">API</bdi> צריך <bdi dir="ltr">SQL</bdi>, <bdi dir="ltr">indexes</bdi> וקריאות מהירות ומוגבלות.
- **מה להראות:** <bdi dir="ltr"><code>fact_market_bar_1m</code></bdi>, <bdi dir="ltr"><code>fact_indicator_1m</code></bdi>, <bdi dir="ltr"><code>etl_watermark</code></bdi>.
- **בלבול נפוץ:** <bdi dir="ltr">Gold</bdi> אינו העותק היחיד של ההיסטוריה.
- **עומק:** <bdi dir="ltr">business keys</bdi> ו־<bdi dir="ltr">upserts</bdi> הופכים <bdi dir="ltr">retries</bdi> לבטוחים.

### <bdi dir="ltr"><code>Provisional</code></bdi> לעומת <bdi dir="ltr"><code>Certified</code></bdi>

- **<bdi dir="ltr">Provisional</bdi>:** טרי, נכתב מ־<bdi dir="ltr">Streaming</bdi>, מתאים לתצוגה בזמן שה־<bdi dir="ltr">session</bdi> פתוח.
- **<bdi dir="ltr">Certified</bdi>:** נבנה מחדש מ־<bdi dir="ltr">Bronze</bdi>, עבר <bdi dir="ltr">DQ</bdi> ומייצג מחיצה סגורה וסמכותית.
- **למה שניהם:** בלי <bdi dir="ltr">Provisional</bdi> אין <bdi dir="ltr">freshness</bdi>; בלי <bdi dir="ltr">Certified</bdi> אין אמון מלא ביום הסגור.
- **המשפט לזכור:** "<bdi dir="ltr">Streaming</bdi> אומר מה ידוע עכשיו; <bdi dir="ltr">Batch</bdi> קובע מה מאושר לאחר הסגירה."

### <bdi dir="ltr"><code>Data Quality</code></bdi>

- **במשפט:** בדיקות שמחליטות אם <bdi dir="ltr">partition</bdi> ראוי לפרסום.
- **בדיקות:** <bdi dir="ltr">freshness</bdi>, <bdi dir="ltr">completeness</bdi>, <bdi dir="ltr">duplicates</bdi>, <bdi dir="ltr">nulls</bdi>, <bdi dir="ltr">OHLC</bdi>, <bdi dir="ltr">expected bars</bdi> ו־<bdi dir="ltr">schema</bdi>.
- **מה קורה בכשל:** אין <bdi dir="ltr">watermark</bdi> חדש, <bdi dir="ltr">staging</bdi> מתנקה וה־<bdi dir="ltr">Certified</bdi> הקודם נשאר.
- **למה חשוב:** מערכת יכולה להיות זמינה טכנית ועדיין לפרסם נתון שגוי.

### <bdi dir="ltr"><code>Idempotency</code></bdi>

- **במשפט:** אותה פעולה יכולה לרוץ שוב בלי ליצור תוצאה עסקית כפולה.
- **ב־<bdi dir="ltr">MarketPilot</bdi>:** <bdi dir="ltr">event IDs</bdi> דטרמיניסטיים, <bdi dir="ltr">unique keys</bdi>, <bdi dir="ltr">upserts</bdi> והחלפת <bdi dir="ltr">partition</bdi> אטומית.
- **דוגמה:** שליחה כפולה של <bdi dir="ltr">AAPL</bdi> באותו <bdi dir="ltr">timestamp</bdi> משאירה רשומה עסקית אחת.
- **המשפט לזכור:** "אנחנו לא מונעים כל <bdi dir="ltr">retry</bdi>; אנחנו הופכים <bdi dir="ltr">retry</bdi> לבטוח."

### <bdi dir="ltr"><code>Checkpoint</code></bdi>

- **במשפט:** מצב שמאפשר ל־<bdi dir="ltr">Streaming</bdi> לדעת מאיפה להמשיך לאחר <bdi dir="ltr">restart</bdi>.
- **ב־<bdi dir="ltr">MarketPilot</bdi>:** נשמר ב־<bdi dir="ltr">named volume</bdi> ומשותף ל־<bdi dir="ltr">driver</bdi> ול־<bdi dir="ltr">worker</bdi> לפי הצורך.
- **למה חשוב:** בלעדיו <bdi dir="ltr">process</bdi> שחזר עלול להתחיל מחדש או לאבד <bdi dir="ltr">state</bdi>.
- **זהירות:** לא מוחקים <bdi dir="ltr">checkpoint</bdi> כדי 'לתקן' תקלה בלי תכנית <bdi dir="ltr">replay</bdi> מפורשת.

### <bdi dir="ltr"><code>Lineage</code></bdi>

- **במשפט:** היכולת להסביר מאיפה הגיעה רשומה ואיזה תהליך יצר אותה.
- **ב־<bdi dir="ltr">MarketPilot</bdi>:** <bdi dir="ltr">source</bdi>, <bdi dir="ltr">event ID</bdi>, <bdi dir="ltr">Kafka position</bdi>, <bdi dir="ltr">run</bdi>, <bdi dir="ltr">code</bdi>, <bdi dir="ltr">data</bdi> ו־<bdi dir="ltr">schema/model versions</bdi>.
- **למה חשוב:** מאפשר <bdi dir="ltr">debugging</bdi>, <bdi dir="ltr">audit</bdi>, <bdi dir="ltr">replay</bdi> והשוואה בין <bdi dir="ltr">Provisional</bdi> ל־<bdi dir="ltr">Certified</bdi>.

### <bdi dir="ltr"><code>Backend API</code></bdi> והגבול לדפדפן

- **במשפט:** שכבת שירות מבוקרת בין <bdi dir="ltr">UI</bdi> למסד.
- **ב־<bdi dir="ltr">MarketPilot</bdi>:** <bdi dir="ltr">validation</bdi>, <bdi dir="ltr">pagination</bdi>, טווחים מוגבלים ו־<bdi dir="ltr">response models</bdi> ללא שדות פנימיים.
- **הוכחה:** משתמש <bdi dir="ltr"><code>marketpilot_app</code></bdi> קורא ב־<bdi dir="ltr">SELECT</bdi> וניסיון <bdi dir="ltr">UPDATE</bdi> נדחה.
- **מגבלה:** לפני חשיפה לאינטרנט דרושים <bdi dir="ltr">authentication</bdi>, <bdi dir="ltr">TLS</bdi> ו־<bdi dir="ltr">rate limiting</bdi>.

### <bdi dir="ltr"><code>Archive</code></bdi> ו־<bdi dir="ltr"><code>Restore</code></bdi>

- **במשפט:** היסטוריה סגורה מיוצאת ל־<bdi dir="ltr">Parquet</bdi> עם <bdi dir="ltr">manifest</bdi> ו־<bdi dir="ltr">hashes</bdi> שניתנים לאימות.
- **ב־<bdi dir="ltr">MarketPilot</bdi>:** <bdi dir="ltr">SHA-256</bdi> לכל <bdi dir="ltr">object</bdi>, <bdi dir="ltr">inventory checksum</bdi> ושחזור לסכמה מבודדת.
- **למה חשוב:** <bdi dir="ltr">backup</bdi> שלא שוחזר הוא רק תקווה, לא הוכחת התאוששות.
- **הבחנה:** <bdi dir="ltr">archive</bdi> אינו <bdi dir="ltr">purge</bdi>; ה־<bdi dir="ltr">MVP</bdi> אינו מוחק אוטומטית היסטוריה מ־<bdi dir="ltr">MariaDB</bdi>.

### <bdi dir="ltr"><code>Historical Acquisition</code></bdi> ו־<bdi dir="ltr"><code>Bronze Barrier</code></bdi>

- **במשפט:** <bdi dir="ltr">Backfill</bdi> היסטורי תחום בזמן שמוכיח שהמקור נשמר לפני תחילת העיבוד.
- **ב־<bdi dir="ltr">MarketPilot</bdi>:** <bdi dir="ltr">Alpaca IEX</bdi> נשמר כ־<bdi dir="ltr">source pages</bdi> לפי <bdi dir="ltr">SHA-256</bdi>, <bdi dir="ltr">bars</bdi> מפורסמים ל־<bdi dir="ltr">topic</bdi> נפרד, ו־<bdi dir="ltr">Airflow</bdi> ממתין לכל <bdi dir="ltr">offset</bdi> ב־<bdi dir="ltr">Bronze</bdi>.
- **למה לא לדלג:** כתיבה ישירה ל־<bdi dir="ltr">MariaDB</bdi> הייתה עוקפת <bdi dir="ltr">Kafka</bdi>, <bdi dir="ltr">raw evidence</bdi>, <bdi dir="ltr">DQ</bdi> ו־<bdi dir="ltr">lineage</bdi>.
- **מה להראות:** <bdi dir="ltr"><code>historical_market_backfill</code></bdi> והמעבר מ־<bdi dir="ltr">acquisition</bdi> ל־<bdi dir="ltr">Bronze barrier</bdi> ורק אחר כך ל־<bdi dir="ltr">Spark</bdi>.
- **בלבול נפוץ:** <bdi dir="ltr">Historical Backfill</bdi> אינו ה־<bdi dir="ltr">Streaming</bdi> החי ואינו נשלח ל־<bdi dir="ltr">topic</bdi> החי.
- **עומק:** <bdi dir="ltr">run identities</bdi> ו־<bdi dir="ltr">session manifests</bdi> דטרמיניסטיים מאפשרים <bdi dir="ltr">retry</bdi> בלי לפרסם שוב עבודה שכבר הושלמה.

### <bdi dir="ltr"><code>Backtesting</code></bdi>

- **במשפט:** סימולציה היסטורית תחומה ומבוקרת של <bdi dir="ltr">strategy</bdi> מוגדרת מראש.
- **ב־<bdi dir="ltr">MarketPilot</bdi>:** <bdi dir="ltr">Spark Batch</bdi> קורא <bdi dir="ltr">Certified Gold</bdi>, מפעיל <bdi dir="ltr">SMA crossover</bdi>, <bdi dir="ltr">friction</bdi> ו־<bdi dir="ltr">next-bar position</bdi>, ושומר <bdi dir="ltr">Parquet</bdi> מלא וסיכומי <bdi dir="ltr">Gold</bdi>.
- **למה לא לדלג:** הוא מוכיח שהפלטפורמה מסוגלת להפוך <bdi dir="ltr">lineage</bdi> לתוצאה אנליטית שניתנת לביקורת.
- **מה להראות:** <bdi dir="ltr">run</bdi>, <bdi dir="ltr">parameters</bdi>, <bdi dir="ltr">observations</bdi>, <bdi dir="ltr">trades</bdi>, <bdi dir="ltr">Equity Curve</bdi> והשוואה ל־<bdi dir="ltr">SPY</bdi>.
- **בלבול נפוץ:** <bdi dir="ltr">Backtest</bdi> אינו ביצוע מסחר, ותוצאה היסטורית אינה הבטחת תשואה.
- **עומק:** אות מ־<bdi dir="ltr">bar</bdi> <bdi dir="ltr"><code>t</code></bdi> מוחל רק על תשואת <bdi dir="ltr"><code>t+1</code></bdi>; אחרת המודל משתמש במידע שלא היה זמין בזמן ההחלטה.

### <bdi dir="ltr"><code>IEX</code></bdi> ו־<bdi dir="ltr"><code>XNYS</code></bdi>

- **<bdi dir="ltr">IEX</bdi>:** <bdi dir="ltr">feed</bdi> נגיש של <bdi dir="ltr">Alpaca</bdi> שמייצג מסחר בבורסה אחת ולא <bdi dir="ltr">consolidated SIP</bdi> מלא.
- **<bdi dir="ltr">XNYS</bdi>:** לוח המסחר של <bdi dir="ltr">New York Stock Exchange</bdi>, כולל חגים וסגירות מוקדמות.
- **ב־<bdi dir="ltr">MarketPilot</bdi>:** <bdi dir="ltr">coverage</bdi> של <bdi dir="ltr">IEX</bdi> נבדק במפורש, ו־<bdi dir="ltr">XNYS</bdi> קובע אילו דקות וסשנים חוקיים לחישוב.
- **ראיה:** 513 רשומות <bdi dir="ltr">synthetic</bdi> של שבת נשמרו ל־<bdi dir="ltr">audit</bdi> אך הוחרגו מה־<bdi dir="ltr">Backtest</bdi>.

## שלוש החלטות שאתה צריך לייחס לעצמך

1. **הפרדת <bdi dir="ltr">Lifecycle</bdi>:** בחרת לא להפעיל <bdi dir="ltr">Streaming</bdi> מ־<bdi dir="ltr">Airflow</bdi> כי <bdi dir="ltr">task</bdi> אינסופי מטשטש <bdi dir="ltr">retries</bdi> ומסכן <bdi dir="ltr">consumers</bdi> כפולים.
2. **שני סוגי <bdi dir="ltr">Gold</bdi>:** בחרת <bdi dir="ltr">Freshness</bdi> מיידי לצד <bdi dir="ltr">Certification</bdi> מאוחר כדי לא להעמיד פנים שנתון חי כבר עבר יום מלא של <bdi dir="ltr">DQ</bdi>.
3. **<bdi dir="ltr">Raw</bdi> מחוץ ל־<bdi dir="ltr">MariaDB</bdi>:** בחרת <bdi dir="ltr">MinIO</bdi> ל־<bdi dir="ltr">replay</bdi>, <bdi dir="ltr">Parquet</bdi> וארכיון, תוך השארת <bdi dir="ltr">MariaDB</bdi> כשכבת <bdi dir="ltr">serving</bdi> ממוקדת.
4. **<bdi dir="ltr">Historical</bdi> ללא קיצור דרך:** בחרת <bdi dir="ltr">topic</bdi> נפרד ו־<bdi dir="ltr">Bronze barrier</bdi> במקום <bdi dir="ltr">load</bdi> ישיר למסד.

## מגבלות שאפשר לומר בביטחון

- זהו <bdi dir="ltr">MVP</bdi> מקומי עם <bdi dir="ltr">Kafka broker</bdi> יחיד, לא <bdi dir="ltr">cluster Production</bdi>.
- אין <bdi dir="ltr">authentication</bdi> למשתמשי קצה כי השירות קשור ל־<bdi dir="ltr">localhost</bdi> בלבד.
- אין הבטחת <bdi dir="ltr">exactly-once</bdi> מקצה לקצה; קיימת נכונות עסקית באמצעות <bdi dir="ltr">idempotency</bdi>.
- <bdi dir="ltr">Indicators</bdi> מחושבים כרגע ב־<bdi dir="ltr">Batch</bdi> מאושר; <bdi dir="ltr">Streaming analytics stateful</bdi> הוא הרחבה עתידית.
- <bdi dir="ltr">S3</bdi>, <bdi dir="ltr">TLS</bdi>, <bdi dir="ltr">centralized logging</bdi> ופריסה משותפת הם שלבי המשך.

הצגת מגבלה עם מנגנון שדרוג מוכיחה שיקול דעת; היא אינה מחלישה את הפרויקט.

</div>
