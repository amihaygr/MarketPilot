<div dir="rtl" align="right">

# אימות סופי — גרסת ההגשה של <bdi dir="ltr"><code>MarketPilot</code></bdi>

**תאריך אימות:** 17 בספטמבר 2026<br>
**מסלול הצגה מרכזי:** 15 דקות<br>
**מסלולים חלופיים:** 10 או 20 דקות

## מה נמסר

- [המצגת הסופית](presentation/output/MarketPilot-Final-Presentation.pptx) — 12 שקופיות
  בתבנית כהה ואחידה, עברית מימין לשמאל, מונחים טכניים מבודדים משמאל לימין,
  צילומי מסך אמיתיים והערות מציג.
- [מסמך הארכיטקטורה המלא](architecture/architecture.md) — מקור האמת הטכני של
  גרסת ההגשה.
- [מסמך הארכיטקטורה להעלאה](architecture/output/MarketPilot.pdf) — קובץ
  <bdi dir="ltr"><code>PDF</code></bdi> בן 12 עמודי
  <bdi dir="ltr"><bdo dir="ltr"><code>A4</code></bdo></bdi> לרוחב.
- [מדריך ההצגה](presentation/demo-day-step-by-step-he.md) — סדר הפעולות,
  המשפטים המומלצים, הסברים למושגים, תרחיש הדמו ותוכנית התאוששות.
- [מסך המציג](http://localhost:3000/presenter.html) — טיימר, תחנות, משפטי מעבר
  וקישורים; המסך קורא רק שני נתיבי <bdi dir="ltr"><code>API</code></bdi> תחומים
  לצורך הצגת מצב שערי ההחלטה.
- [סיפור הפרויקט](http://localhost:3000/showcase.html) — ערך עסקי, ארכיטקטורה,
  ראיות, תהליך בנייה וגבולות המוצר.

## תמונת המצב שאומתה

| מדד | ערך |
|---|---:|
| נכסים במעקב | 11 |
| רשומות שוק ב־<bdi dir="ltr"><code>Gold</code></bdi> | <bdi dir="ltr"><bdo dir="ltr"><code>162,743</code></bdo></bdi> |
| נרות מאושרים | <bdi dir="ltr"><bdo dir="ltr"><code>154,206</code></bdo></bdi> |
| רשומות <bdi dir="ltr"><code>SEC</code></bdi> | 937 |
| ימי מסחר היסטוריים מאושרים | <bdi dir="ltr"><bdo dir="ltr"><code>76</code></bdo></bdi> |
| ריצות <bdi dir="ltr"><code>Backtest</code></bdi> מפורסמות | <bdi dir="ltr"><bdo dir="ltr"><code>12</code></bdo></bdi> |
| שער <bdi dir="ltr"><code>Shadow Mode</code></bdi> של <bdi dir="ltr"><bdo dir="ltr"><code>v1</code></bdo></bdi> | <bdi dir="ltr"><bdo dir="ltr"><code>2/20</code></bdo></bdi> |
| מצב המודל ההיברידי <bdi dir="ltr"><bdo dir="ltr"><code>v2</code></bdo></bdi> | <bdi dir="ltr"><code>FALLBACK</code></bdi> |

מצב <bdi dir="ltr"><code>FALLBACK</code></bdi> הוא מצב הבטיחות הנכון: כללי
<bdi dir="ltr"><bdo dir="ltr"><code>v1</code></bdo></bdi> ממשיכים לייצר רמות מחיר וסיכון, אך המערכת
אינה מציגה הסתברות הצלחה עד שקיים מודל מאומן, מכויל ומאושר. נתונים היסטוריים
אינם מקדמים את שער 20 הימים החיים.

## שערי איכות שעברו

<div dir="ltr" align="left">

```text
repository validation   -> passed
ruff check .            -> passed
ruff format --check .   -> passed (187 files)
pytest -q               -> 113 passed, 7 skipped
docker compose config   -> passed
demo preflight          -> passed
Airflow DAG imports     -> 0 errors
```

</div>

שבע בדיקות האינטגרציה שדולגו הן בדיקות אופציונליות שמחייבות דגלי הפעלה
ייעודיים. הגבולות החיים שהן מכסות נבדקו ישירות באמצעות
<bdi dir="ltr"><code>Docker Compose</code></bdi>, בדיקות בריאות, קריאות
<bdi dir="ltr"><code>API</code></bdi>, מצב <bdi dir="ltr"><code>Airflow</code></bdi>
וה־<bdi dir="ltr"><code>Preflight</code></bdi> המלא.

## אימות סביבת הדמו

- 18 שירותי הריצה הנדרשים פועלים ובריאים. בקובץ
  <bdi dir="ltr"><code>Compose</code></bdi> מוגדרים 19 שירותים בסך הכול, כולל
  שירות האתחול התחום <bdi dir="ltr"><bdo dir="ltr"><code>airflow-init</code></bdo></bdi>.
- 12 ממשקי ההצגה החזירו <bdi dir="ltr"><bdo dir="ltr"><code>HTTP 200</code></bdo></bdi>: האפליקציה,
  מרכז ההזדמנויות, מעבדת הבדיקות ההיסטוריות, סיפור הפרויקט, מסך המציג,
  <bdi dir="ltr"><code>Kafka UI</code></bdi>, <bdi dir="ltr"><code>MinIO</code></bdi>,
  <bdi dir="ltr"><code>Airflow</code></bdi>, שני מסכי
  <bdi dir="ltr"><code>Spark</code></bdi>, <bdi dir="ltr"><code>Adminer</code></bdi>
  ותיעוד ה־<bdi dir="ltr"><code>API</code></bdi>.
- נתיבי הבריאות, הטריות, הנכסים, ההזדמנויות, מצב
  <bdi dir="ltr"><code>Shadow Mode</code></bdi>, מצב המודל וריצות הבדיקה
  ההיסטורית החזירו נתונים תקינים.
- ה־<bdi dir="ltr"><bdo dir="ltr"><code>daily_market_close</code></bdo></bdi> פעיל וזמין למתזמן;
  אין שגיאות טעינת <bdi dir="ltr"><code>DAG</code></bdi>.
- ריצת התיקון
  <bdi dir="ltr"><bdo dir="ltr"><code>repair__2026-09-16__20260917</code></bdo></bdi> השלימה את
  המסלול ההיסטורי דרך <bdi dir="ltr"><code>Kafka</code></bdi>,
  <bdi dir="ltr"><code>Bronze</code></bdi>, <bdi dir="ltr"><code>Silver</code></bdi>,
  בדיקות איכות, <bdi dir="ltr"><code>Gold</code></bdi> ו־<bdi dir="ltr"><code>Backtest</code></bdi>.
  הריצה היומית המקורית שנכשלה נשמרה
  כראיית תפעול ולא נמחקה.

## אימות חזותי

- כל 12 השקופיות רונדרו לתמונות ונבדקו כמונטאז' מלא לאחר הבנייה הסופית.
- שלמות חבילת המצגת, גאומטריה, התאמת כותרות ומדיניות הגופנים עברו ללא ממצאים
  או אזהרות.
- כל 12 עמודי ה־<bdi dir="ltr"><code>PDF</code></bdi> רונדרו; הקובץ ניתן
  לקריאה ולחיפוש ומכיל את פרק <bdi dir="ltr"><bdo dir="ltr"><code>Phase 15</code></bdo></bdi>.
- חמשת מסכי המוצר נבדקו ברוחב מחשב וברוחב טלפון. לא נמצאה גלישה אופקית של
  הדף, שגיאת <bdi dir="ltr"><code>JavaScript</code></bdi>, שגיאת קונסולה או
  משאב שהחזיר שגיאת <bdi dir="ltr"><code>HTTP</code></bdi>.
- טבלאות רחבות נשארות בתוך אזור גלילה מקומי במובייל, במקום להרחיב את כל הדף.

## גבולות שחובה לומר בהצגה

- המערכת היא סביבת מחקר ותמיכה בהחלטה; היא אינה שולחת פקודות מסחר ואינה
  מבטיחה תשואה.
- <bdi dir="ltr"><code>IEX</code></bdi> הוא פיד חינמי וחלקי, ולכן איכות המקור
  מופיעה בנפרד מהסתברות הצלחה.
- <bdi dir="ltr"><code>Rule Score</code></bdi> הוא ציון ראיות לפי כללים;
  <bdi dir="ltr"><code>Data Confidence</code></bdi> הוא ציון טריות וכיסוי;
  <bdi dir="ltr"><code>Model Probability</code></bdi> תופיע רק אחרי אימון
  ואימות. אסור להחליף ביניהם.
- <bdi dir="ltr"><bdo dir="ltr"><code>v2</code></bdo></bdi> דורש 24 חודשי נתונים, לפחות 300 תרחישים
  שנכנסו בפועל, בדיקת <bdi dir="ltr"><bdo dir="ltr"><code>Walk-Forward</code></bdo></bdi>, כיול,
  20 ימים חיים חדשים ואישור אנושי. זהו שער מוצרי מכוון, לא חור במסירה.
- אין לפתוח קובץ <bdi dir="ltr"><bdo dir="ltr"><code>.env</code></bdo></bdi> או להציג מפתחות וסיסמאות
  בזמן ההצגה.

</div>
