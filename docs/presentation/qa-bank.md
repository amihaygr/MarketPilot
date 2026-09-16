<div dir="rtl" align="right">

# <bdi dir="ltr"><code>MarketPilot</code></bdi> — מאגר שאלות ותשובות

בכל תשובה: משפט ישיר, ראיה מהפרויקט, הסיבה להחלטה ולבסוף מגבלה אם קיימת.

## עשר שאלות שחייבים לדעת

### למה נתונים היסטוריים אינם משלימים את 20 ימי ה־<bdi dir="ltr">Shadow Mode</bdi>?

כי <bdi dir="ltr">Backfill</bdi> יודע את העבר מראש ואינו מדמה תפעול חי, <bdi dir="ltr">freshness</bdi> ותיקונים שמגיעים
בזמן אמת. הוא ראיה טובה ל־<bdi dir="ltr">Backtesting</bdi>, אך שער ה־<bdi dir="ltr">Shadow</bdi> דורש 20 ימים עוקבים
שבהם ההמלצה נוצרה לפני שהתוצאה הייתה ידועה. ההפרדה מוצגת במפורש בדשבורד.

נכון לבדיקת <bdi dir="ltr"><code>2026-09-17</code></bdi>, קיימים 53 ימי מסחר
היסטוריים מאושרים ו־11 ריצות <bdi dir="ltr"><code>Backtest</code></bdi>, אך המונה החי
עומד על <bdi dir="ltr"><code>2/20</code></bdi>. יום נכנס למונה רק לאחר שרשרת אישור
יומית מוצלחת. זו התנהגות
<bdi dir="ltr"><code>fail closed</code></bdi>, לא ניסיון להציג התקדמות מלאכותית.

### 1. למה <bdi dir="ltr"><code>Kafka</code></bdi> אם נפח הנתונים קטן?

<bdi dir="ltr">Kafka</bdi> אינו נבחר רק בגלל <bdi dir="ltr">scale</bdi>. הוא מפריד <bdi dir="ltr">producer</bdi> מצרכנים, שומר <bdi dir="ltr">offsets</bdi> ומאפשר
ל־<bdi dir="ltr">Streaming</bdi> ול־<bdi dir="ltr">archive</bdi> לצרוך אותו <bdi dir="ltr">event</bdi> בנפרד. ב־<bdi dir="ltr">MVP broker</bdi> יחיד מספיק; <bdi dir="ltr">cluster</bdi>
גדול יותר מוצדק רק לאחר מדידה.

### 2. למה גם <bdi dir="ltr"><code>MinIO</code></bdi> וגם <bdi dir="ltr"><code>MariaDB</code></bdi>?

<bdi dir="ltr">MariaDB</bdi> הוא <bdi dir="ltr">Gold serving</bdi> לשאילתות היישום. <bdi dir="ltr">MinIO</bdi> מחזיק <bdi dir="ltr">raw immutable</bdi>, <bdi dir="ltr">Silver</bdi>
<bdi dir="ltr">Parquet</bdi> וארכיון. שמירת הכול רק ב־<bdi dir="ltr">MariaDB</bdi> הייתה מחלישה <bdi dir="ltr">replay</bdi>, <bdi dir="ltr">compression</bdi> ו־<bdi dir="ltr">restore</bdi>.

### 3. למה <bdi dir="ltr"><code>Airflow</code></bdi> אינו מפעיל <bdi dir="ltr"><code>Streaming</code></bdi>?

<bdi dir="ltr">Streaming</bdi> הוא <bdi dir="ltr">process</bdi> שאינו אמור להסתיים. <bdi dir="ltr">Docker</bdi> מנהל <bdi dir="ltr">lifecycle</bdi> ו־<bdi dir="ltr">restart</bdi>;
<bdi dir="ltr">Airflow</bdi> מנהל <bdi dir="ltr">dependencies</bdi> ו־<bdi dir="ltr">retries</bdi> של <bdi dir="ltr">jobs</bdi> תחומים. ההפרדה מתועדת ב־<bdi dir="ltr">ADR-002</bdi>.

### 4. האם המערכת <bdi dir="ltr"><code>exactly once</code></bdi>?

לא קיימת טענת <bdi dir="ltr">exactly-once</bdi> בין כל הגבולות. <bdi dir="ltr">Kafka</bdi>, <bdi dir="ltr">Spark</bdi> ומסד יכולים לבצע <bdi dir="ltr">retry</bdi>.
הנכונות נשמרת באמצעות <bdi dir="ltr">deterministic event IDs</bdi>, <bdi dir="ltr">checkpoints</bdi>, <bdi dir="ltr">unique keys</bdi> ו־<bdi dir="ltr">upserts</bdi>.

### 5. מה ההבדל בין <bdi dir="ltr"><code>Provisional</code></bdi> ל־<bdi dir="ltr"><code>Certified</code></bdi>?

<bdi dir="ltr">Provisional</bdi> נכתב מהר מ־<bdi dir="ltr">Streaming. Certified</bdi> נבנה מחדש מ־<bdi dir="ltr">Bronze</bdi> עבור מחיצה סגורה
ורק לאחר <bdi dir="ltr">DQ</bdi> חוסם. הכשל ב־<bdi dir="ltr">Batch</bdi> אינו מסתיר את ה־<bdi dir="ltr">Certified</bdi> הקודם.

### 6. מה קורה אם <bdi dir="ltr"><code>Spark Streaming</code></bdi> נופל?

<bdi dir="ltr">Docker</bdi> מפעיל אותו מחדש, והוא ממשיך מה־<bdi dir="ltr">checkpoint</bdi> וה־<bdi dir="ltr">Kafka progress</bdi> השמורים.
<bdi dir="ltr">Phase 3</bdi> אימת <bdi dir="ltr">restart</bdi> של <bdi dir="ltr">driver</bdi> ו־<bdi dir="ltr">worker</bdi> בלי כפילות במפתחות העסקיים.

### 7. כיצד מונעים כפילויות?

<bdi dir="ltr">Market bar</bdi> מזוהה לפי <bdi dir="ltr">Symbol</bdi>, <bdi dir="ltr">timestamp</bdi> ו־<bdi dir="ltr">interval</bdi>; <bdi dir="ltr">SEC</bdi> לפי <bdi dir="ltr">accession number</bdi>.
כתיבות <bdi dir="ltr">Gold</bdi> הן <bdi dir="ltr">upserts</bdi> ו־<bdi dir="ltr">Batch</bdi> מפרסם <bdi dir="ltr">partition</bdi> באופן דטרמיניסטי ואטומי.

### 8. כיצד אתה יודע שהנתונים נכונים?

הפרסום המאושר תלוי בבדיקות <bdi dir="ltr">freshness</bdi>, <bdi dir="ltr">completeness</bdi>, <bdi dir="ltr">duplicates</bdi>, <bdi dir="ltr">nulls</bdi>, <bdi dir="ltr">OHLC</bdi>,
<bdi dir="ltr">expected bars</bdi> ו־<bdi dir="ltr">schema</bdi>. תוצאות <bdi dir="ltr">DQ</bdi> ו־<bdi dir="ltr">watermarks</bdi> נשמרות כראיה.

### 9. למה הדפדפן אינו פונה ישירות למסד?

<bdi dir="ltr">API</bdi> מאפשר <bdi dir="ltr">validation</bdi>, <bdi dir="ltr">pagination</bdi>, טווחים מוגבלים ו־<bdi dir="ltr">response model</bdi> בטוח. זהות
האפליקציה בעלת <bdi dir="ltr">SELECT</bdi> בלבד וניסיון <bdi dir="ltr">UPDATE</bdi> מבוקר נדחה עם <bdi dir="ltr">MariaDB 1142</bdi>.

### 10. מה היה האתגר ההנדסי המשמעותי ביותר?

ניסוח מוצע: "שמירת ההפרדה בין מסלול חי למסלול מאושר בלי לאבד <bdi dir="ltr">lineage</bdi> או
<bdi dir="ltr">idempotency</bdi>. פתרתי זאת באמצעות <bdi dir="ltr">Bronze immutable</bdi>, <bdi dir="ltr">checkpoint</bdi>, <bdi dir="ltr">business keys</bdi>,
<bdi dir="ltr">publication states</bdi> ו־<bdi dir="ltr">DQ watermark</bdi>."

## שאלות עומק

### למה ה־<bdi dir="ltr"><code>Backfill</code></bdi> ההיסטורי אינו כותב ישירות ל־<bdi dir="ltr"><code>MariaDB</code></bdi>?

כי היסטוריה חייבת לעבור את אותה שרשרת אמון. <bdi dir="ltr">Phase 12</bdi> שומר <bdi dir="ltr">source pages</bdi> לפי
<bdi dir="ltr">SHA-256</bdi>, מפרסם ל־<bdi dir="ltr">Kafka</bdi>, מוכיח <bdi dir="ltr">Bronze</bdi> לפי <bdi dir="ltr">offset</bdi> ורק אז מפעיל <bdi dir="ltr">Silver</bdi>, <bdi dir="ltr">DQ</bdi> ו־<bdi dir="ltr">Gold</bdi>.
המחיר הוא תהליך איטי יותר; הרווח הוא <bdi dir="ltr">replay</bdi> ו־<bdi dir="ltr">lineage</bdi> אמיתיים.

### למה יש <bdi dir="ltr">Topic</bdi> היסטורי נפרד?

כדי ש־<bdi dir="ltr">burst</bdi> של אלפי <bdi dir="ltr">bars</bdi> היסטוריים לא ייכנס ל־<bdi dir="ltr">Spark Streaming</bdi> שמיועד ל־<bdi dir="ltr">Live</bdi>.
<bdi dir="ltr"><code>market.bars.1m.backfill.v1</code></bdi> נשמר ב־<bdi dir="ltr">Bronze</bdi> אך אינו נצרך ב־<bdi dir="ltr">live application</bdi>.

### כיצד מנעת <bdi dir="ltr">Look-ahead bias</bdi>?

ה־<bdi dir="ltr">position</bdi> שנובע מ־<bdi dir="ltr">bar</bdi> <bdi dir="ltr"><code>t</code></bdi> מוחל רק על תשואת <bdi dir="ltr"><code>t+1</code></bdi>. בנוסף רק <bdi dir="ltr">Certified Gold</bdi>
נכנס לריצה, והפרמטרים, <bdi dir="ltr">costs</bdi>, <bdi dir="ltr">slippage</bdi> ו־<bdi dir="ltr">code version</bdi> נשמרים עם ה־<bdi dir="ltr">run</bdi>.

### למה תוצאת ה־<bdi dir="ltr">Backtest</bdi> אינה מרשימה פיננסית?

המטרה היא להוכיח <bdi dir="ltr">pipeline</bdi> נכון, לא לבצע <bdi dir="ltr">curve fitting</bdi>. ב־<bdi dir="ltr">run</bdi> הסופי <bdi dir="ltr">AAPL</bdi> הניב
<bdi dir="ltr">1.36%</bdi> מול <bdi dir="ltr">benchmark</bdi> של <bdi dir="ltr">2.67%</bdi>, ושתי סדרות אחרות היו שליליות. הצגת תוצאה מעורבת
עם <bdi dir="ltr">lineage</bdi> עדיפה על הבטחת ביצועים שאינה נתמכת.

### מה למדת מהתקלה של 513 הרשומות?

למדתי ש־<bdi dir="ltr">filter</bdi> לפי תאריך בלבד אינו מספיק. הרשומות נשמרו ל־<bdi dir="ltr">audit</bdi>, אבל <bdi dir="ltr">Spark</bdi>
מצרף <bdi dir="ltr">input</bdi> לחלונות <bdi dir="ltr">XNYS</bdi> חוקיים ומבודד <bdi dir="ltr"><code>source=alpaca</code></bdi> ב־<bdi dir="ltr">certification</bdi> ההיסטורי.
הבדיקה הוסיפה כלל ארכיטקטוני שניתן לאימות ולא תיקון ידני חד-פעמי.

### למה <bdi dir="ltr">KRaft</bdi> ולא <bdi dir="ltr">ZooKeeper</bdi>?

הגרסה המקומית משתמשת ב־<bdi dir="ltr">Kafka</bdi> מודרני עם <bdi dir="ltr">metadata quorum</bdi> פנימי, ולכן אין צורך
בשירות <bdi dir="ltr">ZooKeeper</bdi> נוסף. זה מקטין את מספר הרכיבים במחשב המקומי.

### למה <bdi dir="ltr">LocalExecutor</bdi> ולא <bdi dir="ltr">Celery</bdi>?

נפח ה־<bdi dir="ltr">MVP</bdi> אינו מצדיק <bdi dir="ltr">Redis</bdi> ו־<bdi dir="ltr">workers</bdi> מבוזרים. <bdi dir="ltr">LocalExecutor</bdi> מספק <bdi dir="ltr">parallelism</bdi>
מספיק תוך שמירה על תפעול פשוט. מעבר ל־<bdi dir="ltr">Celery</bdi> יישקל רק לאחר הוכחת צורך.

### למה <bdi dir="ltr">MariaDB</bdi> ולא <bdi dir="ltr">Data Warehouse</bdi>?

היישום צריך <bdi dir="ltr">serving SQL</bdi> מקומי על נפח קטן יחסית. <bdi dir="ltr">MariaDB</bdi> מספק <bdi dir="ltr">indexes</bdi>, <bdi dir="ltr">constraints</bdi>
ו־<bdi dir="ltr">upserts. Parquet</bdi> ב־<bdi dir="ltr">MinIO</bdi> משמש ל־<bdi dir="ltr">analytics</bdi> וארכיון; <bdi dir="ltr">Warehouse</bdi> מנוהל הוא הרחבה עתידית.

### מה קורה לאירוע <bdi dir="ltr">malformed</bdi>?

הוא אינו נזרק בשקט ואינו מפיל את ה־<bdi dir="ltr">stream</bdi>. הוא נשלח ל־<bdi dir="ltr">DLQ</bdi> או <bdi dir="ltr">quarantine</bdi> עם <bdi dir="ltr">reason</bdi>
ומטא-דאטה של המקור כדי שאפשר יהיה לחקור ולתקן.

### כיצד מטופלים חגים וסגירה מוקדמת?

המערכת שומרת <bdi dir="ltr">UTC</bdi> אך משתמשת ב־<bdi dir="ltr"><code>America/New_York</code></bdi> וב־<bdi dir="ltr">exchange calendar</bdi> של <bdi dir="ltr">XNYS</bdi>
כדי לחשב <bdi dir="ltr">session</bdi>, <bdi dir="ltr">holidays</bdi> ו־<bdi dir="ltr">early close. Offset UTC</bdi> קבוע אינו מספיק בגלל <bdi dir="ltr">DST</bdi>.

### למה <bdi dir="ltr">Backfill</bdi> ידני ולא <bdi dir="ltr">catchup</bdi> של <bdi dir="ltr">Airflow</bdi>?

<bdi dir="ltr">Backfill</bdi> דורש טווח וסמלים מפורשים ובדוקים. <bdi dir="ltr">Catchup</bdi> אוטומטי עלול ליצור ריצות רבות
או חופפות. לכן יש <bdi dir="ltr">DAG</bdi> פרמטרי עם <bdi dir="ltr"><code>max_active_runs=1</code></bdi>.

### איך <bdi dir="ltr">SEC</bdi> נשאר <bdi dir="ltr">idempotent</bdi>?

ה־<bdi dir="ltr">client</bdi> שומר <bdi dir="ltr">raw JSON</bdi> לפי <bdi dir="ltr">content hash</bdi> ו־<bdi dir="ltr">Gold</bdi> משתמש ב־<bdi dir="ltr">accession number</bdi> כמפתח.
בריצה חיה שנייה נוצרו אפס <bdi dir="ltr">inserts</bdi> חדשים והעדכונים נשארו <bdi dir="ltr">idempotent</bdi>.

### מה ההבדל בין <bdi dir="ltr">backup</bdi> ל־<bdi dir="ltr">archive</bdi>?

<bdi dir="ltr">Backup</bdi> משחזר את מסד הנתונים כיחידה תפעולית. <bdi dir="ltr">Archive</bdi> מייצא <bdi dir="ltr">datasets</bdi> סגורים ל־<bdi dir="ltr">Parquet</bdi>
עם <bdi dir="ltr">schema</bdi>, <bdi dir="ltr">inventory</bdi> ו־<bdi dir="ltr">hashes</bdi> לקריאה ושימור ארוך טווח. שניהם עברו <bdi dir="ltr">restore drill</bdi>.

### למה אין <bdi dir="ltr">Elasticsearch</bdi>?

ה־<bdi dir="ltr">MVP</bdi> משתמש ב־<bdi dir="ltr">structured JSON logs</bdi> וב־<bdi dir="ltr">operational monitor. Elasticsearch</bdi> מוסיף
עלות זיכרון ותפעול. הוא מתאים לשלב המשך של <bdi dir="ltr">centralized log search</bdi>, לא ליבת הנתונים.

### כיצד המערכת עוברת לענן?

<bdi dir="ltr">MinIO</bdi> מוחלף ב־<bdi dir="ltr">S3</bdi>, <bdi dir="ltr">Docker services</bdi> יכולים לעבור לשירותים מנוהלים, וה־<bdi dir="ltr">API</bdi> יכול להיפרס
מאחורי <bdi dir="ltr">TLS</bdi> ואימות. החוזים, הנתיבים הלוגיים, <bdi dir="ltr">lineage</bdi> והפרדת <bdi dir="ltr">lifecycle</bdi> נשארים.

### למה מודל <bdi dir="ltr"><code>v2</code></bdi> נמצא ב־<bdi dir="ltr"><code>FALLBACK</code></bdi>?

כי אין עדיין 24 חודשי נתונים, 300 כניסות תקפות ו־50 הצלחות שנדרשים לשער
האימון. המערכת אינה מאמנת על מדגם קטן רק כדי להציג מספר. כללי
<bdi dir="ltr"><code>v1</code></bdi> ממשיכים לקבוע טווחי מחיר וסיכון, והשדות
<bdi dir="ltr"><code>Model Probability</code></bdi> ו־<bdi dir="ltr"><code>Expected R</code></bdi>
נשארים ריקים. זהו <bdi dir="ltr"><code>fail closed</code></bdi> מכוון.

### מה ההבדל בין <bdi dir="ltr"><code>Rule Score</code></bdi>, ‏<bdi dir="ltr"><code>Data Confidence</code></bdi> ו־<bdi dir="ltr"><code>Model Probability</code></bdi>?

<bdi dir="ltr"><code>Rule Score</code></bdi> מסכם את הראיות הטכניות והפונדמנטליות
לפי נוסחה שקופה. ‏<bdi dir="ltr"><code>Data Confidence</code></bdi> מודד איכות,
כיסוי וטריות. ‏<bdi dir="ltr"><code>Model Probability</code></bdi> היא הסתברות
מכוילת לתוצאה מוגדרת. שני הראשונים אינם הסתברות לרווח.

### כיצד מונעים מהמודל ללמוד את העתיד?

כל צילום מצב כולל רק נתוני שוק ודוחות <bdi dir="ltr"><code>SEC</code></bdi> שהיו
ידועים בזמן הצילום. האימון והבדיקה נעשים ב־<bdi dir="ltr"><code>Walk-Forward</code></bdi>
כרונולוגי: מאמנים על העבר ובודקים על תקופה מאוחרת יותר. ‏<bdi dir="ltr"><code>NO_ENTRY</code></bdi>
נמדד בנפרד ואינו מסומן בטעות כהפסד.

### למה המודל ההיברידי אינו ממציא מחיר יעד?

רמות המחיר נשארות דטרמיניסטיות ומוסברות באמצעות תמיכה, התנגדות,
<bdi dir="ltr"><code>EMA</code></bdi> ו־<bdi dir="ltr"><code>ATR</code></bdi>. תפקיד המודל
הוא רק להעריך את הסיכוי להגיע ל־<bdi dir="ltr"><code>Target 1</code></bdi> לפני
<bdi dir="ltr"><code>Stop</code></bdi> ולסייע בדירוג. כך אפשר לבקר בנפרד את המחיר ואת ההסתברות.

## שאלות עליך ועל תהליך העבודה

### מה אתה למדת מהפרויקט?

ניסוח מוצע: "למדתי ש־<bdi dir="ltr">Data Engineering</bdi> אינו רק להעביר נתון. צריך להגדיר בעלות על
<bdi dir="ltr">processes</bdi>, חוזים, זמני <bdi dir="ltr">event</bdi>, <bdi dir="ltr">retry semantics</bdi>, איכות, <bdi dir="ltr">lineage</bdi> ויכולת <bdi dir="ltr">restore</bdi>."

### מה היית עושה אחרת בגרסה שנייה?

ניסוח מוצע: "הייתי מוסיף מוקדם יותר <bdi dir="ltr">observability</bdi> אחיד ומפריד כבר בתחילת הדרך
בין ראיה חיה לראיית <bdi dir="ltr">verification</bdi>. הארכיטקטורה הנוכחית מאפשרת להוסיף זאת בלי
לשנות את מסלולי הנתונים."

### איזה חלק הוא החלטה שלך ולא רק שימוש בכלי?

הדגש את <bdi dir="ltr">ADR-002</bdi> ו־<bdi dir="ltr">ADR-004</bdi>: הפרדת <bdi dir="ltr">Docker/Airflow</bdi> והבחנה <bdi dir="ltr">Provisional/Certified</bdi>.
אלה החלטות ארכיטקטוניות שמסבירות מדוע הכלים מחוברים כך, לא רשימת טכנולוגיות.

### מה טרם <bdi dir="ltr">Production-ready</bdi>?

<bdi dir="ltr">Authentication</bdi>, <bdi dir="ltr">TLS</bdi>, <bdi dir="ltr">rate limiting</bdi>, <bdi dir="ltr">shared secret management</bdi>, <bdi dir="ltr">multi-broker Kafka</bdi>,
<bdi dir="ltr">centralized logs</bdi>, <bdi dir="ltr">capacity testing</bdi> ו־<bdi dir="ltr">disaster recovery</bdi> רחב. המערכת הנוכחית מיועדת
ל־<bdi dir="ltr">localhost</bdi> ומוכיחה את העקרונות והגבולות.

</div>
