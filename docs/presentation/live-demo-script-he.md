<div dir="rtl" align="right">

# תרחיש דמו חי של <bdi dir="ltr"><code>MarketPilot</code></bdi>

זהו המסלול הבטוח להצגה חיה של כ־6 דקות, לאחר סיום המצגת. הדמו הוא לקריאה
בלבד: אין להפעיל השלמה היסטורית, לשנות נתונים או להציג סודות.

## לפני כניסת הקהל

הרץ מתוך תיקיית הפרויקט:

<div dir="ltr" align="left">

```powershell
.\scripts\demo-preflight.ps1 -OpenPages
```

</div>

הסקריפט בודק את תצורת <bdi dir="ltr"><code>Docker Compose</code></bdi>, את שירותי הליבה,
את שבעת ממשקי ההדגמה, את מצב <bdi dir="ltr"><code>Shadow Mode</code></bdi> ואת הפעלת
ה־<bdi dir="ltr"><code>daily_market_close DAG</code></bdi>. הוא אינו משנה נתונים ואינו מציג סיסמאות.

## הכנה ידנית

1. התחבר מראש ל־<bdi dir="ltr"><code>MinIO</code></bdi> ול־<bdi dir="ltr"><code>Airflow</code></bdi>.
2. ב־<bdi dir="ltr"><code>Dashboard</code></bdi> בחר <bdi dir="ltr"><code>AAPL</code></bdi> וטווח של 7 ימים.
3. ב־<bdi dir="ltr"><code>Kafka UI</code></bdi> פתח את <bdi dir="ltr"><code>market.bars.1m.v1</code></bdi>.
4. ב־<bdi dir="ltr"><code>MinIO</code></bdi> פתח אובייקט אחד מתוך <bdi dir="ltr"><code>marketpilot-bronze</code></bdi>.
5. ב־<bdi dir="ltr"><code>Airflow</code></bdi> פתח את <bdi dir="ltr"><code>daily_market_close</code></bdi> ואת הריצה האחרונה.
6. ב־<bdi dir="ltr"><code>Opportunity Center</code></bdi> בחר מניה שמציגה תרחיש מלא.
7. ב־<bdi dir="ltr"><code>Backtesting Lab</code></bdi> בחר את הריצה שכוללת 41 ימי מסחר.
8. סגור את <bdi dir="ltr"><code>.env</code></bdi>, טרמינלים וכל חלון שעלול לחשוף סוד.

## תחנה 1 — המוצר למשתמש

**זמן:** <bdi dir="ltr"><code>00:00–00:50</code></bdi>

**פתח:** <bdi dir="ltr"><code>http://localhost:3000/</code></bdi>

**מה להראות:** מספר הנכסים, מספר רשומות השוק, דיווחי החברות, טריות הנתונים
והגרף של <bdi dir="ltr"><code>AAPL</code></bdi>.

**מה לומר:**

> זהו מסך המחקר הראשי. הוא מאחד מחיר, מחזור מסחר, מדדים טכניים ודיווחי חברות.
> הדפדפן קורא רק דרך <bdi dir="ltr"><code>Backend API</code></bdi>. הוא אינו מחזיק
> פרטי גישה למסד הנתונים או לאחסון האובייקטים.

**מה חשוב שיבינו:** התוצאה העסקית נמצאת בחזית, אך מאחוריה קיימת שרשרת נתונים מלאה.

## תחנה 2 — האירוע החי

**זמן:** <bdi dir="ltr"><code>00:50–01:40</code></bdi>

**פתח:** <bdi dir="ltr"><code>Kafka UI</code></bdi>

**מה להראות:** ‏<bdi dir="ltr"><code>key</code></bdi>, ‏<bdi dir="ltr"><code>partition</code></bdi>,
‏<bdi dir="ltr"><code>offset</code></bdi> וגוף <bdi dir="ltr"><code>JSON</code></bdi> של הודעה אחת.

**מה לומר:**

> <bdi dir="ltr"><code>Kafka</code></bdi> מפריד בין מקור הנתונים לבין הצרכנים.
> אותו אירוע יכול להמשיך לעיבוד החי וגם להישמר כראיית מקור, בלי להצמיד בין השירותים.

## תחנה 3 — ראיית המקור

**זמן:** <bdi dir="ltr"><code>01:40–02:25</code></bdi>

**פתח:** <bdi dir="ltr"><code>MinIO</code></bdi>

**מה להראות:** את נתיב האובייקט ואת השדות <bdi dir="ltr"><code>event_id</code></bdi>,
‏<bdi dir="ltr"><code>event_time_utc</code></bdi>, ‏<bdi dir="ltr"><code>ingested_at_utc</code></bdi>
ו־<bdi dir="ltr"><code>schema_version</code></bdi>.

**מה לומר:**

> לפני אישור ההודעה לצרכן, המערכת שומרת עותק גולמי ובלתי משתנה.
> הנתיב כולל את המיקום המקורי ב־<bdi dir="ltr"><code>Kafka</code></bdi>, ולכן אפשר לבצע
> ביקורת, שחזור ועיבוד חוזר.

## תחנה 4 — אישור יומי

**זמן:** <bdi dir="ltr"><code>02:25–03:20</code></bdi>

**פתח:** <bdi dir="ltr"><code>Airflow</code></bdi>

**מה להראות:** את רצף המשימות של <bdi dir="ltr"><code>daily_market_close</code></bdi>,
מה־<bdi dir="ltr"><code>exchange_session_gate</code></bdi> ועד
<bdi dir="ltr"><code>verify_shadow_mode_progress</code></bdi>.

**מה לומר:**

> <bdi dir="ltr"><code>Airflow</code></bdi> מנהל עבודות תחומות בזמן בלבד.
> <bdi dir="ltr"><code>Spark Batch</code></bdi> בונה מחדש את היום מהמקור הגולמי,
> מפעיל בדיקות איכות ומפרסם תוצאה מאושרת. בדיקת הסיום מוודאת שגם מונה הניסוי החי התקדם.

## תחנה 5 — תמיכה בהחלטה

**זמן:** <bdi dir="ltr"><code>03:20–04:35</code></bdi>

**פתח:** <bdi dir="ltr"><code>Opportunity Center</code></bdi>

**מה להראות:** רשימת המעקב, ‏<bdi dir="ltr"><code>BUY ZONE</code></bdi>, נקודת
הביטול, שני היעדים, יחס הסיכון, גודל הפוזיציה וההסבר בעברית.

**מה לומר:**

> המערכת אינה מציגה מחיר קסם. היא מציגה תרחיש שניתן להסביר ולשחזר: טווח כניסה,
> נקודת ביטול, יעדים וגודל פוזיציה לפי מגבלת הסיכון. המצב החי עדיין נמצא
> ב־<bdi dir="ltr"><code>Shadow Mode</code></bdi>, ולכן אין ביצוע פקודות ואין הבטחת תשואה.

## תחנה 6 — אימות על ההיסטוריה

**זמן:** <bdi dir="ltr"><code>04:35–05:35</code></bdi>

**פתח:** <bdi dir="ltr"><code>Backtesting Lab</code></bdi>

**מה להראות:** 41 ימי מסחר, 46,749 תצפיות, 1,059 שינויי פוזיציה, תשואה,
ירידה מרבית והשוואה ל־<bdi dir="ltr"><code>SPY</code></bdi>.

**מה לומר:**

> הבדיקה משתמשת רק בנתונים מאושרים. אות שנוצר בנר מסוים משפיע רק מהנר הבא,
> והחישוב כולל עלויות והחלקת מחיר. התוצאה אינה חייבת להיות יפה כדי להיות שימושית;
> החשיבות היא שהניסוי שחזורי ואינו מסתיר מגבלות.

## סיום הדמו

**זמן:** <bdi dir="ltr"><code>05:35–06:00</code></bdi>

> ראינו אירוע מהמקור, דרך תעבורה ושמירה גולמית, עד נתון מאושר ומוצר שמסביר
> תרחיש החלטה. כל שכבה ניתנת לבדיקה, והמערכת שומרת הפרדה בין מהיר, מאושר והיסטורי.

## אם משהו אינו עובד

- מסך עסקי לא זמין: הצג את צילום המסך המתאים במצגת.
- <bdi dir="ltr"><code>Kafka UI</code></bdi> לא זמין: הצג אובייקט
  <bdi dir="ltr"><code>Bronze</code></bdi> מוכן והסבר את נתיב המקור.
- <bdi dir="ltr"><code>Airflow</code></bdi> לא זמין: הצג את שקופית הארכיטקטורה ואת
  מסמך האימות המתוארך.
- נתון חי ישן: הצג את אזהרת הטריות בכנות. תקינות שירות וטריות נתונים הן בדיקות שונות.
- אין להתחיל תיקון ארוך מול הקהל. עבור מיד לראיה החלופית והמשך במסלול.

</div>
