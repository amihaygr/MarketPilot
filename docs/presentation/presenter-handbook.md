# MarketPilot - חוברת המסביר

המטרה של החוברת היא שלא רק תדע מה ללחוץ, אלא תבין מה אתה מציג ותוכל להסביר
אותו במילים שלך. אין צורך לשנן את כל הטקסט. למד קודם את המודלים המחשבתיים ואת
ההבדלים החשובים.

## הסיפור במשפט אחד

MarketPilot מקבל נתוני שוק ו-SEC, שומר מקור גולמי שניתן לשחזור, מעבד נתונים
במסלול חי ובמסלול Batch מאושר, ומציג Gold ו-Analytics למשתמש דרך API מוגבל.

## הסיפור בשבעה משפטים

1. Alpaca שולח bars של דקה, וה-producer מתרגם אותם לחוזה `MarketBarV1`.
2. Kafka מפריד בין המקור לצרכנים ושומר סדר ומיקום באמצעות partition ו-offset.
3. Spark Streaming מפרסם מהר ל-Gold כ-PROVISIONAL, ובמקביל raw-archive-sink שומר Bronze ב-MinIO.
4. Airflow מפעיל עבודות Spark Batch מוגבלות בזמן שבונות Silver ומפרסמות CERTIFIED רק אחרי DQ.
5. ה-Dashboard קורא רק דרך Backend API עם משתמש MariaDB בעל SELECT בלבד.
6. Historical Backfill מכניס Alpaca IEX דרך topic נפרד, Bronze barrier ואותו מסלול Certification.
7. Backtesting משתמש רק ב-Certified Gold ושומר תוצאה מלאה, הנחות ו-lineage שניתנים לשחזור.

## חמשת המסלולים שאתה חייב להסביר ללא דף

### Live

`Alpaca -> Producer -> Kafka -> Spark Streaming -> MariaDB Gold PROVISIONAL`

מטרתו לתת נתון טרי. הוא מהיר, אך יום שעדיין פתוח עלול לקבל אירועים מאוחרים או
תיקונים. לכן התוצאה מסומנת Provisional.

### Raw

`Kafka -> raw-archive-sink -> MinIO Bronze`

מטרתו לשמור את העובדות המקוריות. אם צריך לתקן קוד, לבצע backfill או להוכיח
lineage, אפשר לחזור ל-Bronze במקום להסתמך רק על מה שכבר עובד.

### Certified

`Bronze -> Spark Batch -> Silver -> DQ -> Spark Batch -> Gold CERTIFIED`

מטרתו לבנות מחדש יום סגור ממקור גולמי, לנקות ולבדוק אותו, ורק אז לפרסם תוצאה
סמכותית. Batch הוא המסלול המאשר; Streaming הוא המסלול המהיר.

### SEC

`SEC EDGAR -> SEC adapter -> MinIO Bronze + MariaDB Gold metadata`

ה-JSON המקורי נשמר ב-Bronze. Metadata שימושי נשמר ב-Gold. accession number
משמש כמפתח עסקי שמונע כפילות גם כשה-poll חוזר על אותן הגשות.

## כרטיסי הסבר לרכיבים מרכזיים

### Kafka

- **במשפט:** מערכת תורים מבוזרת שמעבירה events בין producers ל-consumers.
- **ב-MarketPilot:** מקבלת MarketBarV1 ומאפשרת ל-Streaming ול-archive לצרוך בנפרד.
- **למה לא לדלג:** חיבור ישיר בין Alpaca ל-Spark היה מצמיד בין הרכיבים ומחליש replay.
- **מה להראות:** Topic, key, partition, offset ו-consumer group.
- **בלבול נפוץ:** Kafka אינו מסד הנתונים העסקי; הוא transport ו-log של events.
- **עומק:** אין טענה ל-exactly once בין כל המערכות; offset ו-idempotency מגנים על הנכונות.

### Spark Structured Streaming

- **במשפט:** מנוע שמעבד stream כמיקרו-batches מתמשכים.
- **ב-MarketPilot:** קורא Kafka, מאמת events, משתמש ב-event time ומבצע upsert ל-Gold.
- **למה לא לדלג:** הוא נותן מסלול כמעט בזמן אמת עם recovery מ-checkpoint.
- **מה להראות:** Spark application, Worker ונתוני PROVISIONAL ב-Gold.
- **בלבול נפוץ:** Streaming אינו מופעל כל בוקר מ-Airflow; הוא שירות ארוך חיים.
- **עומק:** checkpoint מכיל offset והתקדמות state ולכן הוא state קריטי שאסור למחוק סתם.

### Spark Batch

- **במשפט:** עבודת עיבוד שמתחילה, מעבדת קלט תחום ומסתיימת.
- **ב-MarketPilot:** מבצעת Bronze to Silver, Silver to Gold, analytics, backfill ותחזוקה.
- **למה לא לדלג:** היא מאפשרת חישוב מחדש דטרמיניסטי של יום סגור ובדיקות מלאות.
- **מה להראות:** DAG tasks, Spark job ו-Silver Parquet.
- **בלבול נפוץ:** Spark הוא מנוע החישוב; Airflow הוא מנהל סדר העבודה.
- **עומק:** פרסום Gold נעשה בגבול אטומי ורק לאחר DQ חוסם.

### Airflow

- **במשפט:** Orchestrator לעבודות בעלות התחלה וסיום.
- **ב-MarketPilot:** מתזמן SEC, Batch, DQ, backfill, compaction ו-archive.
- **למה לא לדלג:** הוא מנהל dependencies, retries, timeouts, pools וסטטוס.
- **מה להראות:** `daily_market_close`, סדר המשימות ו-`max_active_runs=1`.
- **בלבול נפוץ:** Airflow אינו supervisor של Kafka, Streaming, MariaDB או Web App.
- **עומק:** `SparkSubmitOperator` שולח job ל-Spark Master ומחכה ל-terminal state.

### MinIO, Bronze ו-Silver

- **במשפט:** MinIO הוא object storage מקומי תואם S3.
- **ב-MarketPilot:** Bronze שומר raw immutable; Silver שומר Parquet נקי וקנוני.
- **למה לא לדלג:** MariaDB לבדו אינו מתאים ל-raw replay, Parquet analytics וארכיון.
- **מה להראות:** bucket, partitioned path, JSON ב-Bronze ו-Parquet ב-Silver.
- **בלבול נפוץ:** Bronze אינו טבלה נקייה; הוא ראיית המקור. Silver אינו שכבת היישום.
- **עומק:** S3 הוא החלופה העתידית בלי לשנות את התפקיד הלוגי של השכבה.

### MariaDB Gold

- **במשפט:** מסד ה-serving שמחזיק מודלים מוכנים ליישום.
- **ב-MarketPilot:** bars, indicators, signals, SEC metadata, DQ, watermarks ו-manifests.
- **למה לא לדלג:** ה-API צריך SQL, indexes וקריאות מהירות ומוגבלות.
- **מה להראות:** `fact_market_bar_1m`, `fact_indicator_1m`, `etl_watermark`.
- **בלבול נפוץ:** Gold אינו העותק היחיד של ההיסטוריה.
- **עומק:** business keys ו-upserts הופכים retries לבטוחים.

### Provisional לעומת Certified

- **Provisional:** טרי, נכתב מ-Streaming, מתאים לתצוגה בזמן שה-session פתוח.
- **Certified:** נבנה מחדש מ-Bronze, עבר DQ ומייצג מחיצה סגורה וסמכותית.
- **למה שניהם:** בלי Provisional אין freshness; בלי Certified אין אמון מלא ביום הסגור.
- **המשפט לזכור:** "Streaming אומר מה ידוע עכשיו; Batch קובע מה מאושר לאחר הסגירה."

### Data Quality

- **במשפט:** בדיקות שמחליטות אם partition ראוי לפרסום.
- **בדיקות:** freshness, completeness, duplicates, nulls, OHLC, expected bars ו-schema.
- **מה קורה בכשל:** אין watermark חדש, staging מתנקה וה-Certified הקודם נשאר.
- **למה חשוב:** מערכת יכולה להיות זמינה טכנית ועדיין לפרסם נתון שגוי.

### Idempotency

- **במשפט:** אותה פעולה יכולה לרוץ שוב בלי ליצור תוצאה עסקית כפולה.
- **ב-MarketPilot:** event IDs דטרמיניסטיים, unique keys, upserts והחלפת partition אטומית.
- **דוגמה:** שליחה כפולה של AAPL באותו timestamp משאירה רשומה עסקית אחת.
- **המשפט לזכור:** "אנחנו לא מונעים כל retry; אנחנו הופכים retry לבטוח."

### Checkpoint

- **במשפט:** מצב שמאפשר ל-Streaming לדעת מאיפה להמשיך לאחר restart.
- **ב-MarketPilot:** נשמר ב-named volume ומשותף ל-driver ול-worker לפי הצורך.
- **למה חשוב:** בלעדיו process שחזר עלול להתחיל מחדש או לאבד state.
- **זהירות:** לא מוחקים checkpoint כדי 'לתקן' תקלה בלי תכנית replay מפורשת.

### Lineage

- **במשפט:** היכולת להסביר מאיפה הגיעה רשומה ואיזה תהליך יצר אותה.
- **ב-MarketPilot:** source, event ID, Kafka position, run, code, data ו-schema/model versions.
- **למה חשוב:** מאפשר debugging, audit, replay והשוואה בין Provisional ל-Certified.

### Backend API והגבול לדפדפן

- **במשפט:** שכבת שירות מבוקרת בין UI למסד.
- **ב-MarketPilot:** validation, pagination, טווחים מוגבלים ו-response models ללא שדות פנימיים.
- **הוכחה:** משתמש `marketpilot_app` קורא ב-SELECT וניסיון UPDATE נדחה.
- **מגבלה:** לפני חשיפה לאינטרנט דרושים authentication, TLS ו-rate limiting.

### Archive ו-Restore

- **במשפט:** היסטוריה סגורה מיוצאת ל-Parquet עם manifest ו-hashes שניתנים לאימות.
- **ב-MarketPilot:** SHA-256 לכל object, inventory checksum ושחזור לסכמה מבודדת.
- **למה חשוב:** backup שלא שוחזר הוא רק תקווה, לא הוכחת התאוששות.
- **הבחנה:** archive אינו purge; ה-MVP אינו מוחק אוטומטית היסטוריה מ-MariaDB.

### Historical Acquisition ו-Bronze Barrier

- **במשפט:** Backfill היסטורי תחום בזמן שמוכיח שהמקור נשמר לפני תחילת העיבוד.
- **ב-MarketPilot:** Alpaca IEX נשמר כ-source pages לפי SHA-256, bars מפורסמים ל-topic נפרד, ו-Airflow ממתין לכל offset ב-Bronze.
- **למה לא לדלג:** כתיבה ישירה ל-MariaDB הייתה עוקפת Kafka, raw evidence, DQ ו-lineage.
- **מה להראות:** `historical_market_backfill` והמעבר מ-acquisition ל-Bronze barrier ורק אחר כך ל-Spark.
- **בלבול נפוץ:** Historical Backfill אינו ה-Streaming החי ואינו נשלח ל-topic החי.
- **עומק:** run identities ו-session manifests דטרמיניסטיים מאפשרים retry בלי לפרסם שוב עבודה שכבר הושלמה.

### Backtesting

- **במשפט:** סימולציה היסטורית תחומה ומבוקרת של strategy מוגדרת מראש.
- **ב-MarketPilot:** Spark Batch קורא Certified Gold, מפעיל SMA crossover, friction ו-next-bar position, ושומר Parquet מלא וסיכומי Gold.
- **למה לא לדלג:** הוא מוכיח שהפלטפורמה מסוגלת להפוך lineage לתוצאה אנליטית שניתנת לביקורת.
- **מה להראות:** run, parameters, observations, trades, Equity Curve והשוואה ל-SPY.
- **בלבול נפוץ:** Backtest אינו ביצוע מסחר, ותוצאה היסטורית אינה הבטחת תשואה.
- **עומק:** אות מ-bar `t` מוחל רק על תשואת `t+1`; אחרת המודל משתמש במידע שלא היה זמין בזמן ההחלטה.

### IEX ו-XNYS

- **IEX:** feed נגיש של Alpaca שמייצג מסחר בבורסה אחת ולא consolidated SIP מלא.
- **XNYS:** לוח המסחר של New York Stock Exchange, כולל חגים וסגירות מוקדמות.
- **ב-MarketPilot:** coverage של IEX נבדק במפורש, ו-XNYS קובע אילו דקות וסשנים חוקיים לחישוב.
- **ראיה:** 513 רשומות synthetic של שבת נשמרו ל-audit אך הוחרגו מה-Backtest.

## שלוש החלטות שאתה צריך לייחס לעצמך

1. **הפרדת Lifecycle:** בחרת לא להפעיל Streaming מ-Airflow כי task אינסופי מטשטש retries ומסכן consumers כפולים.
2. **שני סוגי Gold:** בחרת Freshness מיידי לצד Certification מאוחר כדי לא להעמיד פנים שנתון חי כבר עבר יום מלא של DQ.
3. **Raw מחוץ ל-MariaDB:** בחרת MinIO ל-replay, Parquet וארכיון, תוך השארת MariaDB כשכבת serving ממוקדת.
4. **Historical ללא קיצור דרך:** בחרת topic נפרד ו-Bronze barrier במקום load ישיר למסד.

## מגבלות שאפשר לומר בביטחון

- זהו MVP מקומי עם Kafka broker יחיד, לא cluster Production.
- אין authentication למשתמשי קצה כי השירות קשור ל-localhost בלבד.
- אין הבטחת exactly-once מקצה לקצה; קיימת נכונות עסקית באמצעות idempotency.
- Indicators מחושבים כרגע ב-Batch מאושר; Streaming analytics stateful הוא הרחבה עתידית.
- S3, TLS, centralized logging ופריסה משותפת הם שלבי המשך.

הצגת מגבלה עם מנגנון שדרוג מוכיחה שיקול דעת; היא אינה מחלישה את הפרויקט.
