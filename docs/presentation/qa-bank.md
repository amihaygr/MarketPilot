# MarketPilot - מאגר שאלות ותשובות

בכל תשובה: משפט ישיר, ראיה מהפרויקט, הסיבה להחלטה ולבסוף מגבלה אם קיימת.

## עשר שאלות שחייבים לדעת

### 1. למה Kafka אם נפח הנתונים קטן?

Kafka אינו נבחר רק בגלל scale. הוא מפריד producer מצרכנים, שומר offsets ומאפשר
ל-Streaming ול-archive לצרוך אותו event בנפרד. ב-MVP broker יחיד מספיק; cluster
גדול יותר מוצדק רק לאחר מדידה.

### 2. למה גם MinIO וגם MariaDB?

MariaDB הוא Gold serving לשאילתות היישום. MinIO מחזיק raw immutable, Silver
Parquet וארכיון. שמירת הכול רק ב-MariaDB הייתה מחלישה replay, compression ו-restore.

### 3. למה Airflow אינו מפעיל Streaming?

Streaming הוא process שאינו אמור להסתיים. Docker מנהל lifecycle ו-restart;
Airflow מנהל dependencies ו-retries של jobs תחומים. ההפרדה מתועדת ב-ADR-002.

### 4. האם המערכת exactly once?

לא קיימת טענת exactly-once בין כל הגבולות. Kafka, Spark ומסד יכולים לבצע retry.
הנכונות נשמרת באמצעות deterministic event IDs, checkpoints, unique keys ו-upserts.

### 5. מה ההבדל בין Provisional ל-Certified?

Provisional נכתב מהר מ-Streaming. Certified נבנה מחדש מ-Bronze עבור מחיצה סגורה
ורק לאחר DQ חוסם. הכשל ב-Batch אינו מסתיר את ה-Certified הקודם.

### 6. מה קורה אם Spark Streaming נופל?

Docker מפעיל אותו מחדש, והוא ממשיך מה-checkpoint וה-Kafka progress השמורים.
Phase 3 אימת restart של driver ו-worker בלי כפילות במפתחות העסקיים.

### 7. כיצד מונעים כפילויות?

Market bar מזוהה לפי Symbol, timestamp ו-interval; SEC לפי accession number.
כתיבות Gold הן upserts ו-Batch מפרסם partition באופן דטרמיניסטי ואטומי.

### 8. כיצד אתה יודע שהנתונים נכונים?

הפרסום המאושר תלוי בבדיקות freshness, completeness, duplicates, nulls, OHLC,
expected bars ו-schema. תוצאות DQ ו-watermarks נשמרות כראיה.

### 9. למה הדפדפן אינו פונה ישירות למסד?

API מאפשר validation, pagination, טווחים מוגבלים ו-response model בטוח. זהות
האפליקציה בעלת SELECT בלבד וניסיון UPDATE מבוקר נדחה עם MariaDB 1142.

### 10. מה היה האתגר ההנדסי המשמעותי ביותר?

ניסוח מוצע: "שמירת ההפרדה בין מסלול חי למסלול מאושר בלי לאבד lineage או
idempotency. פתרתי זאת באמצעות Bronze immutable, checkpoint, business keys,
publication states ו-DQ watermark."

## שאלות עומק

### למה KRaft ולא ZooKeeper?

הגרסה המקומית משתמשת ב-Kafka מודרני עם metadata quorum פנימי, ולכן אין צורך
בשירות ZooKeeper נוסף. זה מקטין את מספר הרכיבים במחשב המקומי.

### למה LocalExecutor ולא Celery?

נפח ה-MVP אינו מצדיק Redis ו-workers מבוזרים. LocalExecutor מספק parallelism
מספיק תוך שמירה על תפעול פשוט. מעבר ל-Celery יישקל רק לאחר הוכחת צורך.

### למה MariaDB ולא Data Warehouse?

היישום צריך serving SQL מקומי על נפח קטן יחסית. MariaDB מספק indexes, constraints
ו-upserts. Parquet ב-MinIO משמש ל-analytics וארכיון; Warehouse מנוהל הוא הרחבה עתידית.

### מה קורה לאירוע malformed?

הוא אינו נזרק בשקט ואינו מפיל את ה-stream. הוא נשלח ל-DLQ או quarantine עם reason
ומטא-דאטה של המקור כדי שאפשר יהיה לחקור ולתקן.

### כיצד מטופלים חגים וסגירה מוקדמת?

המערכת שומרת UTC אך משתמשת ב-`America/New_York` וב-exchange calendar של XNYS
כדי לחשב session, holidays ו-early close. Offset UTC קבוע אינו מספיק בגלל DST.

### למה Backfill ידני ולא catchup של Airflow?

Backfill דורש טווח וסמלים מפורשים ובדוקים. Catchup אוטומטי עלול ליצור ריצות רבות
או חופפות. לכן יש DAG פרמטרי עם `max_active_runs=1`.

### איך SEC נשאר idempotent?

ה-client שומר raw JSON לפי content hash ו-Gold משתמש ב-accession number כמפתח.
בריצה חיה שנייה נוצרו אפס inserts חדשים והעדכונים נשארו idempotent.

### מה ההבדל בין backup ל-archive?

Backup משחזר את מסד הנתונים כיחידה תפעולית. Archive מייצא datasets סגורים ל-Parquet
עם schema, inventory ו-hashes לקריאה ושימור ארוך טווח. שניהם עברו restore drill.

### למה אין Elasticsearch?

ה-MVP משתמש ב-structured JSON logs וב-operational monitor. Elasticsearch מוסיף
עלות זיכרון ותפעול. הוא מתאים לשלב המשך של centralized log search, לא ליבת הנתונים.

### כיצד המערכת עוברת לענן?

MinIO מוחלף ב-S3, Docker services יכולים לעבור לשירותים מנוהלים, וה-API יכול להיפרס
מאחורי TLS ואימות. החוזים, הנתיבים הלוגיים, lineage והפרדת lifecycle נשארים.

## שאלות עליך ועל תהליך העבודה

### מה אתה למדת מהפרויקט?

ניסוח מוצע: "למדתי ש-Data Engineering אינו רק להעביר נתון. צריך להגדיר בעלות על
processes, חוזים, זמני event, retry semantics, איכות, lineage ויכולת restore."

### מה היית עושה אחרת בגרסה שנייה?

ניסוח מוצע: "הייתי מוסיף מוקדם יותר observability אחיד ומפריד כבר בתחילת הדרך
בין ראיה חיה לראיית verification. הארכיטקטורה הנוכחית מאפשרת להוסיף זאת בלי
לשנות את מסלולי הנתונים."

### איזה חלק הוא החלטה שלך ולא רק שימוש בכלי?

הדגש את ADR-002 ו-ADR-004: הפרדת Docker/Airflow והבחנה Provisional/Certified.
אלה החלטות ארכיטקטוניות שמסבירות מדוע הכלים מחוברים כך, לא רשימת טכנולוגיות.

### מה טרם Production-ready?

Authentication, TLS, rate limiting, shared secret management, multi-broker Kafka,
centralized logs, capacity testing ו-disaster recovery רחב. המערכת הנוכחית מיועדת
ל-localhost ומוכיחה את העקרונות והגבולות.
