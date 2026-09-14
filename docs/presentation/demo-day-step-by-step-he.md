<div dir="rtl" align="right">

# <bdi dir="ltr"><code>MarketPilot</code></bdi> — דף ליווי פשוט להצגה

הקובץ הזה הוא הדף היחיד שצריך לפתוח בזמן ההצגה. אין צורך לזכור הכול בעל פה.
המסלול בנוי ל־15 דקות, ובכל שלב כתוב בדיוק לאן לנווט, מה להראות ומה לומר.
להעמקה במסך ההחלטות אפשר להיעזר ב־<a dir="ltr" href="phase14-opportunity-center-he.md"><code>phase14-opportunity-center-he.md</code></a>.

## לפני ההצגה — הכנה של חמש דקות

פתח את כל הדפים הבאים מראש, כל אחד בלשונית נפרדת ובסדר הזה:

1. **<bdi dir="ltr">Presenter Console</bdi>:** <http://localhost:3000/presenter.html>
2. **<bdi dir="ltr">Project Story</bdi>:** <http://localhost:3000/showcase.html>
3. **<bdi dir="ltr">Dashboard</bdi>:** <http://localhost:3000/>
4. **<bdi dir="ltr">Kafka UI</bdi>:** <http://localhost:8085/>
5. **<bdi dir="ltr">MinIO</bdi>:** <http://localhost:9001/>
6. **<bdi dir="ltr">Airflow</bdi>:** <http://localhost:8080/>
7. **<bdi dir="ltr">Opportunity Center</bdi>:** <http://localhost:3000/opportunities.html>
8. **<bdi dir="ltr">Backtesting Lab</bdi>:** <http://localhost:3000/backtesting.html>

בצע לפני שהקהל נכנס:

- התחבר מראש ל־<bdi dir="ltr">MinIO</bdi> ול־<bdi dir="ltr">Airflow</bdi>. אל תציג סיסמאות בזמן ההצגה.
- ב־<bdi dir="ltr">Presenter Console</bdi> בחר **15 דקות** ולחץ **איפוס**.
- ב־<bdi dir="ltr">Dashboard</bdi> בחר <bdi dir="ltr"><code>AAPL</code></bdi>.
- ב־<bdi dir="ltr">Kafka UI</bdi> פתח את ה־<bdi dir="ltr">topic</bdi> בשם <bdi dir="ltr"><code>market.bars.1m.v1</code></bdi>.
- ב־<bdi dir="ltr">MinIO</bdi> פתח מראש אובייקט <bdi dir="ltr">JSON</bdi> אחד מתוך <bdi dir="ltr"><code>marketpilot-bronze</code></bdi>.
- ב־<bdi dir="ltr">Airflow</bdi> מצא את ה־<bdi dir="ltr">DAG</bdi> בשם <bdi dir="ltr"><code>historical_market_backfill</code></bdi> ואת הריצה
  <bdi dir="ltr"><code>phase14_historical_evidence_20260914</code></bdi>.
- ב־<bdi dir="ltr">Backtesting Lab</bdi> בחר את הריצה שמתחילה ב־<bdi dir="ltr"><code>2bf99281</code></bdi> וודא שמופיעים
  **41 <bdi dir="ltr">sessions</bdi>**, **46,749 <bdi dir="ltr">observations</bdi>** ו־**1,059 <bdi dir="ltr">trades</bdi>**.
- סגור את <bdi dir="ltr"><code>.env</code></bdi>, טרמינלים שמציגים הגדרות וכל מקום שעלול לחשוף <bdi dir="ltr">credentials</bdi>.

## מפת המסלול במשפט אחד

<bdi dir="ltr"><code>Project Story → Dashboard → Kafka → MinIO → Airflow → Opportunity Center → Backtesting → Project Story</code></bdi>

אם הלכת לאיבוד, חזור ל־<bdi dir="ltr">Presenter Console</bdi>. הכרטיס המסומן אומר מה התחנה הבאה.

---

## שלב 1 — פתיחה: מה בניתי ולמה

**זמן:** 00:00–01:30
**נווט אל:** <http://localhost:3000/showcase.html>

### מה להציג

- את הכותרת הגדולה בראש העמוד.
- את ארבעת הכרטיסים שמתחתיה.
- אין צורך לגלול עדיין לארכיטקטורה.

### מה לומר

> שלום, אני מציג את <bdi dir="ltr">MarketPilot</bdi> — מרכז מחקר חכם לסוחר, שמחבר במקום אחד את
> תמונת השוק, מצב החברות והיכולת לבדוק רעיונות על ההיסטוריה.
>
> כסוחר, אני רוצה לקבל תשובות לארבע שאלות: מה קורה עכשיו במחיר ובמחזור המסחר;
> האם הנתון שאני רואה טרי ואמין; האם החברה פרסמה דיווח רשמי שעשוי להסביר את
> התנועה; והאם רעיון מסחר מסוים היה עובד בעבר אחרי עלויות.
>
> <bdi dir="ltr">MarketPilot</bdi> אוספת נתוני מניות מ־<bdi dir="ltr">Alpaca</bdi>
> ודיווחים רשמיים של חברות מה־<bdi dir="ltr">SEC</bdi>, שהוא רשות ניירות הערך
> האמריקאית. היא הופכת את המידע לגרפים, מדדי <bdi dir="ltr">SMA</bdi>
> ו־<bdi dir="ltr">RSI</bdi>, תנודתיות, איתותים מוסברים ובדיקה היסטורית
> (<bdi dir="ltr">Backtesting</bdi>) מול <bdi dir="ltr">SPY</bdi> כמדד השוואה.
>
> אבל המוצר לא רק מציג מספרים יפים. מאחורי כל תוצאה נשמר המקור הגולמי,
> מופעלות בדיקות איכות, ויש אפשרות לדעת מאיזה אירוע (<bdi dir="ltr">Event</bdi>),
> תהליך וגרסת קוד היא נוצרה.
> כך הסוחר מקבל סביבת מחקר אחת שמחברת מהירות, הקשר ואמון. המערכת אינה מבצעת
> פקודות קנייה או מכירה ואינה מבטיחה רווח; היא עוזרת לקבל החלטות מושכלות יותר.

### מה המערכת מאפשרת לסוחר

- לראות מחירי דקה, מחזורי מסחר ומצב עדכניות במקום אחד.
- לקבל מדדים (<bdi dir="ltr">Indicators</bdi>) ואיתותים עם הסבר, ולא רק צבע ירוק או אדום.
- לחבר תנועת מחיר לדיווחים רשמיים שהחברה הגישה ל־<bdi dir="ltr">SEC</bdi>.
- לבדוק אסטרטגיה על נתונים היסטוריים מאושרים ולהשוות אותה ל־<bdi dir="ltr">SPY</bdi>.
- להבין אם המידע עדיין <bdi dir="ltr"><code>PROVISIONAL</code></bdi> או שכבר עבר בדיקות וקיבל <bdi dir="ltr"><code>CERTIFIED</code></bdi>.
- לחזור למקור ולהסביר כיצד כל נתון ותוצאה נוצרו.

### מה הקהל צריך להבין

לא בנית רק לוח מחוונים (<bdi dir="ltr">Dashboard</bdi>) ולא רק מספר קונטיינרים
(<bdi dir="ltr">Containers</bdi>). בנית מוצר מחקר לסוחר, ומאחוריו מסלול הנדסת
נתונים (<bdi dir="ltr">Data Engineering</bdi>) מלא שמייצר אמון בנתון.

### משפט מעבר

> כדי להשיג גם מהירות וגם אמינות, חילקתי את המערכת למסלולים ברורים.

---

## שלב 2 — הארכיטקטורה: מי עושה מה

**זמן:** 01:30–03:30
**הישאר ב:** <bdi dir="ltr">Project Story</bdi>
**לחץ:** בתפריט העליון על **<bdi dir="ltr">Architecture</bdi>**.

### מה להציג

באזור הארכיטקטורה לחץ לפי הסדר על:

1. **<bdi dir="ltr">Live path</bdi>**
2. **<bdi dir="ltr">Certified path</bdi>**
3. **<bdi dir="ltr">Historical path</bdi>**
4. **<bdi dir="ltr">Raw + archive</bdi>**

### מה לומר

> במסלול החי, <bdi dir="ltr">Alpaca</bdi> שולח נתונים ל־<bdi dir="ltr">Producer</bdi>, משם ל־<bdi dir="ltr">Kafka</bdi>, אחר כך <bdi dir="ltr">Spark</bdi>
> <bdi dir="ltr">Streaming</bdi> מעבד אותם וכותב ל־<bdi dir="ltr">MariaDB Gold</bdi> כ־<bdi dir="ltr">Provisional</bdi> — נתון מהיר שעדיין
> לא עבר סגירת יום מלאה.
>
> במקביל, אותו <bdi dir="ltr">Event</bdi> נשמר ב־<bdi dir="ltr">MinIO Bronze</bdi> כחומר גלם שאפשר לשחזר ממנו.
>
> במסלול המאושר, <bdi dir="ltr">Spark Batch</bdi> בונה <bdi dir="ltr">Bronze</bdi> ל־<bdi dir="ltr">Silver</bdi>, מפעיל בדיקות <bdi dir="ltr">Data Quality</bdi>,
> ורק לאחר שהן עוברות מפרסם <bdi dir="ltr">Gold</bdi> כ־<bdi dir="ltr">Certified</bdi>.
>
> במסלול ההיסטורי, גם מידע ישן מ־<bdi dir="ltr">Alpaca</bdi> חייב לעבור <bdi dir="ltr">Kafka</bdi>, <bdi dir="ltr">Bronze</bdi> ובדיקות;
> הוא לא נכתב ישירות למסד רק כדי לקצר דרך.

### המשפט החשוב ביותר כאן

> <bdi dir="ltr">Docker Compose</bdi> מנהל שירותים שעובדים כל הזמן. <bdi dir="ltr">Airflow</bdi> מנהל רק עבודות שיש
> להן התחלה וסיום. <bdi dir="ltr">Spark</bdi> מבצע את החישוב, ו־<bdi dir="ltr">Airflow</bdi> מנהל את הסדר והתזמון.

### משפט מעבר

> עכשיו אראה שהתרשים הזה באמת מחובר למערכת עובדת.

---

## שלב 3 — אירוע חי: מהמקור עד המשתמש

**זמן:** 03:30–06:00

### 3א — <bdi dir="ltr">Dashboard</bdi>

**נווט אל:** <http://localhost:3000/>
**לחץ:** בחר <bdi dir="ltr"><code>AAPL</code></bdi> אם הוא אינו מסומן.

**הצג:**

- מספר רשומות ו־<bdi dir="ltr">Freshness</bdi>.
- מצב <bdi dir="ltr"><code>CERTIFIED</code></bdi> או <bdi dir="ltr"><code>PROVISIONAL</code></bdi> שמופיע במסך.
- גרף המחיר וקו <bdi dir="ltr"><code>SMA</code></bdi>.
- כרטיסי ה־<bdi dir="ltr">Indicators</bdi>.

**אמור:**

> זה המסך שהמשתמש רואה. הדפדפן אינו מתחבר ישירות ל־<bdi dir="ltr">MariaDB</bdi> או ל־<bdi dir="ltr">MinIO</bdi>.
> כל הנתונים מגיעים דרך <bdi dir="ltr">Backend API</bdi> מוגבל לקריאה.

### 3ב — <bdi dir="ltr">Kafka</bdi>

**נווט אל:** <http://localhost:8085/>
**פתח:** <bdi dir="ltr"><code>market.bars.1m.v1</code></bdi> ואז את אזור ההודעות.

**הצג:** <bdi dir="ltr"><code>key</code></bdi>, <bdi dir="ltr"><code>partition</code></bdi>, <bdi dir="ltr"><code>offset</code></bdi> וה־<bdi dir="ltr">JSON</bdi> של הודעה אחת.

**אמור:**

> <bdi dir="ltr">Kafka</bdi> הוא שכבת התעבורה. הוא מפריד בין מי שמייצר את האירוע לבין הצרכנים.
> <bdi dir="ltr">Partition</bdi> הוא מסילה מסודרת, ו־<bdi dir="ltr">Offset</bdi> הוא המספר של ההודעה על אותה מסילה.

### 3ג — <bdi dir="ltr">MinIO Bronze</bdi>

**נווט אל:** <http://localhost:9001/>
**פתח:** את אובייקט ה־<bdi dir="ltr">JSON</bdi> שהכנת מראש.

**הצג בתוך ה־<bdi dir="ltr">JSON</bdi>:**

- <bdi dir="ltr"><code>event_id</code></bdi>
- <bdi dir="ltr"><code>symbol</code></bdi>
- <bdi dir="ltr"><code>event_time_utc</code></bdi>
- <bdi dir="ltr"><code>ingested_at_utc</code></bdi>
- <bdi dir="ltr"><code>schema_version</code></bdi>

**הצג בנתיב הקובץ:** <bdi dir="ltr"><code>topic</code></bdi>, <bdi dir="ltr"><code>partition</code></bdi> ו־<bdi dir="ltr"><code>offset</code></bdi>.

**אמור:**

> גוף האירוע נמצא בתוך ה־<bdi dir="ltr">JSON</bdi>. המיקום המקורי שלו ב־<bdi dir="ltr">Kafka</bdi> נשמר בנתיב.
> כך אפשר להוכיח <bdi dir="ltr">Lineage</bdi>, לבצע <bdi dir="ltr">Replay</bdi> ולמנוע בלבול בין הודעות.

### משפט מעבר

> עד כאן ראינו נתון מהיר ומקור גולמי. עכשיו נראה כיצד היסטוריה אמיתית הופכת למאושרת.

---

## שלב 4 — <bdi dir="ltr">Airflow</bdi>: היסטוריה אמיתית עד <bdi dir="ltr">Certified Gold</bdi>

**זמן:** 06:00–08:30
**נווט אל:** <http://localhost:8080/>
**פתח:** <bdi dir="ltr"><code>historical_market_backfill</code></bdi>
**בחר:** <bdi dir="ltr"><code>phase14_historical_evidence_20260914</code></bdi>

### מה להציג

הצבע על סדר המשימות בגרף, בלי להפעיל דבר:

1. משיכת נתונים מ־<bdi dir="ltr">Alpaca IEX</bdi>.
2. שמירת תגובות המקור ב־<bdi dir="ltr">Bronze</bdi> לפי <bdi dir="ltr"><code>SHA-256</code></bdi>.
3. פרסום ל־<bdi dir="ltr">Kafka topic</bdi> היסטורי נפרד.
4. <bdi dir="ltr"><code>Bronze barrier</code></bdi> שמוודא שכל <bdi dir="ltr">Offset</bdi> נשמר.
5. <bdi dir="ltr">Bronze</bdi> → <bdi dir="ltr">Silver</bdi>.
6. <bdi dir="ltr">Data Quality</bdi>.
7. <bdi dir="ltr">Silver</bdi> → <bdi dir="ltr">Gold Certified</bdi>.
8. <bdi dir="ltr">Backtest</bdi> רק לאחר שכל השלבים עברו.

### מה לומר

> זו ריצת ההרחבה ההיסטורית של <bdi dir="ltr">Phase 14</bdi>. היא עיבדה 20 ימי מסחר אמיתיים ביולי,
> וכעת קיימים במערכת 41 ימי מסחר מאושרים לפי לוח <bdi dir="ltr">XNYS</bdi>.
> בחרתי לא לכתוב את הנתונים ישירות ל־<bdi dir="ltr">MariaDB</bdi>. כל <bdi dir="ltr">Response</bdi> נשמר קודם ב־<bdi dir="ltr">Bronze</bdi>,
> וכל הודעת <bdi dir="ltr">Kafka</bdi> נבדקת לפי <bdi dir="ltr">Partition</bdi> ו־<bdi dir="ltr">Offset</bdi> לפני ש־<bdi dir="ltr">Spark</bdi> מתחיל לעבד.
> ה־<bdi dir="ltr">Topic</bdi> ההיסטורי נפרד כדי שכמות גדולה של נתוני עבר לא תיכנס למסלול החי.

### מה הקהל צריך להבין

<bdi dir="ltr">Airflow</bdi> מנהל תהליך מוגבל בזמן. הוא אינו מפעיל או מכבה את <bdi dir="ltr">Kafka</bdi>, <bdi dir="ltr">Spark Streaming</bdi>,
<bdi dir="ltr">MariaDB</bdi> או <bdi dir="ltr">Web App</bdi>.

### משפט מעבר

> לאחר שיש לי היסטוריה מאושרת ובעלת <bdi dir="ltr">Lineage</bdi>, אני יכול לבדוק עליה אסטרטגיה בצורה אחראית.

---

## שלב 5 — <bdi dir="ltr">Opportunity Center</bdi>: כיצד המערכת תומכת בהחלטה

**זמן:** 08:30–11:00
**נווט אל:** <http://localhost:3000/opportunities.html>

### מה להציג

- את ההפרדה בין <bdi dir="ltr"><code>HISTORICAL EVIDENCE</code></bdi> לבין <bdi dir="ltr"><code>LIVE SHADOW MODE</code></bdi>.
- מעבר בין <bdi dir="ltr"><code>AAPL</code></bdi> ל־<bdi dir="ltr"><code>MSFT</code></bdi> ברשימת ההזדמנויות.
- <bdi dir="ltr"><code>BUY ZONE</code></bdi>, שני יעדים, <bdi dir="ltr"><code>STOP</code></bdi> ו־<bdi dir="ltr"><code>Risk / Reward</code></bdi>.
- מחשבון גודל הפוזיציה וההסבר בעברית תחת <bdi dir="ltr"><code>WHY NOW?</code></bdi>.

### מה לומר

> כאן הנתונים הופכים לתרחיש החלטה. המערכת אינה מציגה מחיר קסם אלא טווח כניסה,
> נקודת ביטול, שני יעדים וגודל פוזיציה שמוגבל לפי הסיכון בתיק. הציון משלב
> ניתוח טכני במספר חלונות זמן עם נתוני <bdi dir="ltr">SEC</bdi> פונדמנטליים.
>
> חשוב להפריד בין שתי ראיות: נתונים היסטוריים מאושרים מאפשרים <bdi dir="ltr">Backtesting</bdi>
> והדגמה עשירה, אבל אינם מתחזים לימים חיים. רק <bdi dir="ltr">Live Shadow Mode</bdi> מתקדם אל שער
> 20 ימי המסחר. עד אז כל המלצה נשמרת כ־<bdi dir="ltr">non-actionable</bdi> והביצוע תמיד ידני.

### משפט מעבר

> אחרי שראינו את תרחיש ההחלטה הנוכחי, נבדוק כיצד רעיון מסחר התנהג על העבר.

---

## שלב 6 — <bdi dir="ltr">Backtesting</bdi>: מה הנתונים מאפשרים לעשות

**זמן:** 11:00–12:30
**נווט אל:** <http://localhost:3000/backtesting.html>
**בחר:** את הריצה החדשה ביותר ואת <bdi dir="ltr"><code>AAPL</code></bdi>.

### מה להציג

- 41 <bdi dir="ltr">Sessions</bdi>.
- 46,749 <bdi dir="ltr">Observations</bdi>.
- 1,059 <bdi dir="ltr">Trades</bdi> בסך הכול.
- כרטיסי ה־<bdi dir="ltr">KPI</bdi>.
- <bdi dir="ltr">Equity Curve</bdi>.
- טבלת ההשוואה בין <bdi dir="ltr"><code>AAPL</code></bdi>, <bdi dir="ltr"><code>MSFT</code></bdi> ו־<bdi dir="ltr"><code>SPY</code></bdi>.

### מה לומר

> ה־<bdi dir="ltr">Backtest</bdi> הוא עבודת <bdi dir="ltr">Spark Batch</bdi> מוגבלת בזמן. הוא רשאי לקרוא רק <bdi dir="ltr">Gold</bdi>
> במצב <bdi dir="ltr">Certified</bdi>. אות שנוצר ב־<bdi dir="ltr">Bar</bdi> מסוים מיושם רק על ה־<bdi dir="ltr">Bar</bdi> הבא, כדי לא להשתמש
> במידע מהעתיד. גם עלויות עסקה ו־<bdi dir="ltr">Slippage</bdi> נכללות בחישוב.
>
> ב־<bdi dir="ltr">AAPL</bdi> התקבלה תשואה של 1.36 אחוז מול <bdi dir="ltr">Benchmark</bdi> של 2.67 אחוז. התוצאה אינה
> מרשימה פיננסית — וזה בסדר. מטרת הפרויקט היא להוכיח <bdi dir="ltr">Pipeline</bdi> אמין ושחזור
> מלא, לא להתאים אסטרטגיה בדיעבד או להבטיח רווח.

### אם שואלים “אז האסטרטגיה נכשלה?”

> התוצאה ההיסטורית של האסטרטגיה הפשוטה אינה טובה מה־<bdi dir="ltr">Benchmark</bdi>. ההצלחה
> ההנדסית היא שאני יכול להוכיח בדיוק באילו נתונים, קוד, הנחות ועלויות השתמשתי.

### משפט מעבר

> תוצאה אמינה חשובה יותר מתוצאה יפה. עכשיו אראה כיצד המערכת מגיבה לנתונים בעייתיים.

---

## שלב 7 — אמינות: מה קורה כשיש בעיה

**זמן:** 12:30–13:15
**נווט חזרה אל:** <http://localhost:3000/showcase.html#evidence>

### מה להציג

- 18 מתוך 18 שירותים היו <bdi dir="ltr">Healthy</bdi> בבדיקת ה־<bdi dir="ltr">Release Candidate</bdi>.
- 99 בדיקות עברו.
- 41 ימי מסחר אושרו.
- 513 רשומות לא תקינות לסשן זוהו והוחרגו.
- 0 מפתחות עסקיים כפולים בבדיקת ה־<bdi dir="ltr">Idempotency</bdi>.

### מה לומר

> בדקתי <bdi dir="ltr">Restart</bdi> מ־<bdi dir="ltr">Checkpoint</bdi>, כתיבות <bdi dir="ltr">Idempotent</bdi>, <bdi dir="ltr">Data Quality</bdi> חוסם,
> הרשאת <bdi dir="ltr">API</bdi> לקריאה בלבד, <bdi dir="ltr">Archive</bdi> עם <bdi dir="ltr">SHA-256</bdi> ושחזור לסכמה מבודדת.
>
> בריצת החודש המערכת מצאה 513 רשומות <bdi dir="ltr">Synthetic</bdi> מתאריך שבת. לא מחקתי אותן
> כדי להסתיר את הבעיה; שמרתי אותן ל־<bdi dir="ltr">Audit</bdi>, אבל החרגתי אותן מהחישוב לפי לוח
> המסחר <bdi dir="ltr">XNYS</bdi>. זו דוגמה לבאג שהפך לכלל איכות קבוע.

### אם מופיעה אזהרת <bdi dir="ltr">Freshness</bdi>

> השירותים יכולים להיות <bdi dir="ltr">Healthy</bdi> בזמן שהמידע ישן. זו אינה אותה בדיקה.
> המערכת משאירה את האזהרה גלויה במקום להחליש את הסף כדי שהמסך יהיה ירוק.

### משפט מעבר

> אסיים בשלוש ההחלטות המרכזיות שלקחתי מהפרויקט.

---

## שלב 8 — סיכום: מה היו ההחלטות שלי

**זמן:** 13:15–14:15
**הישאר ב:** <bdi dir="ltr">Project Story</bdi>.

### מה לומר

> ההחלטה הראשונה שלי הייתה להפריד בין שירותים ארוכי חיים לעבודות <bdi dir="ltr">Batch</bdi>:
> <bdi dir="ltr">Docker</bdi> מנהל את השירותים, ו־<bdi dir="ltr">Airflow</bdi> מנהל עבודות מוגבלות בזמן.
>
> ההחלטה השנייה הייתה להפריד בין <bdi dir="ltr">Provisional</bdi>, שנותן מהירות, לבין <bdi dir="ltr">Certified</bdi>,
> שנותן אמון בנתונים של יום סגור.
>
> ההחלטה השלישית הייתה לשמור את חומר הגלם ב־<bdi dir="ltr">MinIO</bdi> ולא רק ב־<bdi dir="ltr">MariaDB</bdi>, כדי
> לאפשר <bdi dir="ltr">Replay</bdi>, <bdi dir="ltr">Parquet</bdi>, <bdi dir="ltr">Archive</bdi> ו־<bdi dir="ltr">Lineage</bdi>.
>
> מהפרויקט למדתי ש־<bdi dir="ltr">Data Engineering</bdi> אינו רק להעביר נתון ממקום למקום.
> צריך לחשוב על חוזה נתונים, זמן אירוע, <bdi dir="ltr">Retry</bdi>, איכות, אבטחה, שחזור והוכחות.

### מגבלות שאפשר לומר בביטחון

- זה <bdi dir="ltr">MVP</bdi> מקומי עם <bdi dir="ltr">Kafka Broker</bdi> יחיד.
- <bdi dir="ltr">IEX</bdi> אינו <bdi dir="ltr">Feed</bdi> מאוחד של כל השוק.
- לפני חשיפה לאינטרנט נדרשים <bdi dir="ltr">Authentication</bdi>, <bdi dir="ltr">TLS</bdi> ו־<bdi dir="ltr">Rate Limiting</bdi>.
- ה־<bdi dir="ltr">Backtest</bdi> אינו מודל השקעה ואינו כולל את כל תנאי המסחר האמיתיים.

### משפט הסיום

> <bdi dir="ltr">MarketPilot</bdi> היא <bdi dir="ltr">Data Platform</bdi> מקומית אבל שלמה: ממקור חי והיסטורי, דרך
> <bdi dir="ltr">Kafka</bdi>, אחסון, <bdi dir="ltr">Spark</bdi> ו־<bdi dir="ltr">Data Quality</bdi>, ועד <bdi dir="ltr">API</bdi>, <bdi dir="ltr">Analytics</bdi> ו־<bdi dir="ltr">Backtesting</bdi> שאני
> יכול להסביר, לבדוק ולשחזר. תודה, אשמח לשאלות.

---

## הדקה האחרונה — לא מוסיפים חומר

**זמן:** 14:15–15:00

השתמש בדקה הזאת רק לניווט שהתעכב, לשאלה קצרה או לסיום רגוע. אם סיימת מוקדם,
עצור בביטחון. אין צורך למלא בכוח את כל הזמן.

## אם מסך לא עובד

אל תתחיל לתקן <bdi dir="ltr">Docker</bdi> מול הקהל ואל תפעיל ריצה חדשה.

| המסך שלא עובד | מה לפתוח במקום | המשפט שלך |
|---|---|---|
| <bdi dir="ltr">Dashboard</bdi> | <bdi dir="ltr">Project Story</bdi> | “אציג את הארכיטקטורה ואת ראיית האימות המתוארכת.” |
| <bdi dir="ltr">Kafka UI</bdi> | אובייקט <bdi dir="ltr">Bronze</bdi> שכבר פתוח | “ה־<bdi dir="ltr">Topic</bdi>, <bdi dir="ltr">Partition</bdi> ו־<bdi dir="ltr">Offset</bdi> נשמרים בנתיב.” |
| <bdi dir="ltr">MinIO</bdi> | <bdi dir="ltr">Project Story</bdi> — <bdi dir="ltr">Raw + archive</bdi> | “הממשק אינו זמין, אבל תפקיד <bdi dir="ltr">Bronze</bdi> והראיות מתועדים.” |
| <bdi dir="ltr">Airflow</bdi> | <bdi dir="ltr"><code>docs/phase12-verification.md</code></bdi> | “זו הריצה המתועדת; לא אפעיל <bdi dir="ltr">DAG</bdi> חדש לצורך הדגמה.” |
| <bdi dir="ltr">Backtesting</bdi> | <bdi dir="ltr"><code>docs/phase12-verification.md</code></bdi> | “התוצאות מקושרות ל־<bdi dir="ltr">Run ID</bdi> ול־<bdi dir="ltr">Code Version</bdi>.” |

## חמש תשובות קצרות שכדאי לזכור

**למה <bdi dir="ltr">Kafka</bdi> אם הנפח קטן?**
כדי להפריד בין <bdi dir="ltr">Producer</bdi> לצרכנים ולאפשר <bdi dir="ltr">Replay</bdi> וצריכה עצמאית, לא רק בשביל <bdi dir="ltr">Scale</bdi>.

**למה גם <bdi dir="ltr">MinIO</bdi> וגם <bdi dir="ltr">MariaDB</bdi>?**
<bdi dir="ltr">MinIO</bdi> שומר <bdi dir="ltr">Raw</bdi>, <bdi dir="ltr">Parquet</bdi> ו־<bdi dir="ltr">Archive</bdi>; <bdi dir="ltr">MariaDB</bdi> מגיש <bdi dir="ltr">Gold</bdi> מוכן ל־<bdi dir="ltr">API</bdi>.

**למה <bdi dir="ltr">Airflow</bdi> לא מפעיל <bdi dir="ltr">Streaming</bdi>?**
<bdi dir="ltr">Streaming</bdi> הוא שירות שאמור לחיות תמיד; <bdi dir="ltr">Airflow</bdi> מתאים לעבודות שמתחילות ומסתיימות.

**האם המערכת <bdi dir="ltr">Exactly Once</bdi>?**
לא מקצה לקצה. הנכונות העסקית נשמרת בעזרת <bdi dir="ltr">Checkpoint</bdi>, <bdi dir="ltr">Business Keys</bdi> ו־<bdi dir="ltr">Upsert</bdi>.

**מה ההבדל בין <bdi dir="ltr">Provisional</bdi> ל־<bdi dir="ltr">Certified</bdi>?**
<bdi dir="ltr">Provisional</bdi> הוא מה שידוע עכשיו; <bdi dir="ltr">Certified</bdi> הוא יום סגור שנבנה מחדש ועבר בדיקות איכות.

## חוק הזהב שלך

אם שכחת פרט טכני, אל תנחש. אמור:

> אני לא רוצה להמציא תשובה. אסביר מה מימשתי ומה בדקתי, ואת הפרט המדויק אוכל
> לאמת במסמך או בקוד.

</div>
