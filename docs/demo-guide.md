# MarketPilot Final Demo Guide

מטרת הדמו היא להראות אירוע אחד לאורך הפלטפורמה, ולא לפתוח כל כלי ללא סיפור.
המסר המרכזי: MarketPilot מפריד נכון בין קליטה רציפה, היסטוריה גולמית, עיבוד תחום
בזמן, פרסום מאושר ושכבת שירות מאובטחת.

## לפני ההצגה

1. ודא שכל השירותים בריאים:

   ```powershell
   docker compose ps
   ```

2. פתח מראש את החלונות הבאים, ללא הצגת `.env` או סיסמאות:

   - Project Story: <http://localhost:3000/showcase.html>
   - Dashboard: <http://localhost:3000/>
   - Kafka UI: <http://localhost:8085/>
   - MinIO: <http://localhost:9001/>
   - Airflow: <http://localhost:8080/>
   - Spark: <http://localhost:18080/>
   - Adminer: <http://localhost:8086/>
   - Backend API: <http://localhost:8000/docs>

3. בחר מראש סימול עם נתונים בטווח שבעת הימים האחרונים, למשל `AAPL`.
4. אל תפעיל DAG או עבודת Backfill בזמן הצגה אלא אם הוכן לכך Run ID נפרד.

## תרחיש מומלץ — שמונה דקות

### 1. הבעיה והפתרון — דקה אחת

פתח את Project Story.

אמור:

> נתוני שוק צריכים להיות זמינים מהר, אבל נתון מהיר עדיין אינו נתון מאושר.
> MarketPilot שומר את שני הצרכים: Streaming מפרסם Gold זמני, ו־Batch בונה מחדש
> את היום מה־Bronze ומפרסם Certified רק לאחר Data Quality.

הצג בקצרה את שלושת הכפתורים באזור הארכיטקטורה:

- Live path;
- Certified path;
- Raw + archive.

הדגש ש־Docker Compose מנהל שירותים רציפים, ו־Airflow מנהל עבודות שמתחילות ומסתיימות.

### 2. חוויית המוצר — דקה וחצי

עבור ל־Dashboard.

1. הצג שהמערכת מחוברת ל־API.
2. בחר `AAPL` מתוך Asset Pulse.
3. עבור בין `1D`, `5D` ו־`7D`.
4. רחף מעל הגרף והצג Close, SMA ו־Volume בנקודה מסוימת.
5. כבה והפעל את קו `SMA 20`.
6. הצג RSI, Volatility, Volume Ratio והסבר Signal אחד.

אמור:

> הדפדפן אינו מכיר את MariaDB או MinIO. כל קריאה עוברת דרך Nginx אל Backend API
> מוגבל, עם טווח מקסימלי של 31 ימים ו־pagination.

### 3. הוכחת Transport ו־Raw Lineage — דקה וחצי

פתח Kafka UI בנושא `market.bars.1m.v1`.

- הצג key של סימול;
- הצג partition ו־offset;
- הצג consumer groups והיעדר lag חריג.

עבור ל־MinIO ול־`marketpilot-bronze`.

- פתח נתיב הכולל source, date, symbol, topic, partition ו־offset;
- הראה שה־JSON מכיל `event_id`, זמן מקור, זמן קליטה וגרסת Schema;
- הסבר שהמיקום ב־Kafka נמצא בשם האובייקט כדי לאפשר Replay ואידמפוטנטיות.

### 4. הוכחת Processing ו־Orchestration — דקה וחצי

פתח Spark Master והראה Worker בריא ויישומי Spark.

פתח Airflow:

- הצג את `daily_market_close`;
- הסבר את הסדר Bronze → Silver → DQ → Gold → Analytics;
- הצג `max_active_runs=1` ושה־DAG אינו מפעיל Spark Streaming;
- הצג את DAG ה־Backfill הפרמטרי במקום Catchup אוטומטי.

### 5. הוכחת Gold ואבטחת Serving — דקה

פתח Adminer על בסיס הנתונים `marketpilot`.

- הצג `fact_market_bar_1m`;
- הצג `fact_indicator_1m` ו־`fact_signal`;
- הצג `etl_watermark` או `data_quality_result`;
- אל תציג סיסמאות או תוכן של `.env`.

פתח את OpenAPI והראה קריאת GET אחת עם Symbol וטווח.

אמור:

> זהות האפליקציה קיבלה SELECT בלבד. בבדיקת Runtime היא קראה נתונים, וניסיון UPDATE
> מבוקר נדחה על ידי MariaDB עם שגיאה 1142.

### 6. סיום — חצי דקה

חזור ל־Evidence ב־Project Story.

אמור:

> הפרויקט אינו טוען להיות מערכת מסחר. הוא מדגים פלטפורמת Data מקומית, ניתנת
> לשחזור, עם גבולות אחריות, Lineage, בדיקות איכות, Recovery ושכבת BI מוסברת.

## שאלות צפויות

### למה גם MinIO וגם MariaDB?

MariaDB הוא Gold Serving ליישום. MinIO מחזיק Raw immutable, Silver Parquet,
ארכיונים וראיות שחזור. שמירת הכול רק במסד השירות תפגע ב־Replay ובאנליטיקה ארוכת טווח.

### למה Airflow לא מפעיל את Spark Streaming?

Streaming אינו Task שמסתיים. Docker מתאים לניהול lifecycle ול־restart; Airflow מתאים
לתלויות, retries וסטטוס של עבודות תחומות בזמן.

### האם המערכת Exactly Once?

לא נטענת הבטחת Exactly Once בין כל הגבולות. המערכת מתוכננת ל־retry ומשיגה נכונות
עסקית באמצעות checkpoint, offsets, מפתחות ייחודיים ו־upserts אידמפוטנטיים.

### מה ההבדל בין Provisional ל־Certified?

Provisional הוא פלט Streaming טרי. Certified הוא פלט Batch סמכותי למחיצה סגורה,
לאחר בנייה מחדש ו־Data Quality חוסם.

### מה נדרש לפני חשיפה לאינטרנט?

Authentication, TLS, rate limiting, secret management משותף ובדיקת Threat Model
לפריסה. הגרסה הנוכחית מיועדת ל־localhost וקושרת פורטים ל־`127.0.0.1`.

## אם משהו נכשל בזמן ההצגה

- Dashboard אינו עולה: בדוק `docker compose ps web-app backend-api mariadb`.
- API מחזיר שגיאה: בדוק `docker compose logs --tail=100 backend-api`.
- אין נתוני שוק בטווח: בחר `7D` או סימול אחר; אל תיצור נתונים ידנית לצורך הדמו.
- Airflow או Spark אינם זמינים: המשך עם ראיות ה־Verification המתועדות והסבר במפורש
  שמדובר ב־snapshot מתוארך, לא במצב חי.
