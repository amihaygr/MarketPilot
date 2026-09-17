<div dir="rtl" align="right">

# מרכז ההצגה של <bdi dir="ltr"><code dir="ltr">MarketPilot</code></bdi>

זו תיקיית המסירה הסופית למצגת ולדמו. נשארו כאן רק החומרים שמשמשים בפועל ביום ההצגה.

## שני הקבצים שמתחילים מהם

1. [המצגת הסופית](output/MarketPilot-Final-Presentation.pptx) — מצגת כהה ואחידה בת <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">12</code></bdo></bdi> שקופיות, עם הערות מציג.
2. [מדריך ההצגה והדמו](demo-day-step-by-step-he.md) — מה לומר, איזה מסך לפתוח, על מה להצביע ומה לעשות במקרה תקלה.

## חומרי הכנה

- [מילון המונחים](glossary.md) — הסבר פשוט למושגים הטכניים והפיננסיים.
- [מאגר שאלות ותשובות](qa-bank.md) — תשובות קצרות לשאלות צפויות של הסוקר.
- [תוכנית חזרה ותרחישי תקלה](rehearsal-and-failure-playbook.md) — רשימת בדיקה ליום ההצגה ומסלול חלופי לכל מסך.
- [מסמך הארכיטקטורה המלא](../architecture/architecture.md) ו־[גרסת ה־<bdi dir="ltr"><code dir="ltr">PDF</code></bdi>](../architecture/output/MarketPilot.pdf).

## הפעלת הסביבה והבדיקה המקדימה

פתח <bdi dir="ltr"><code dir="ltr">PowerShell</code></bdi> והריץ כל שורה בנפרד:

<div dir="ltr" align="left">

```powershell
Set-Location "C:\Users\Amichai\Documents\naya_college_de\final_project\MarketPilot"
docker compose up -d
.\scripts\demo-preflight.ps1 -OpenPages
```

</div>

הבדיקה המקדימה מאמתת את תצורת <bdi dir="ltr"><code dir="ltr">Compose</code></bdi>, בריאות השירותים, דפי ההדגמה, ממשקי ה־<bdi dir="ltr"><code dir="ltr">API</code></bdi>, מצב <bdi dir="ltr"><code dir="ltr">Airflow</code></bdi> והראיות הדרושות להצגה. אם מופיעה שורה אדומה, אין להתחיל את הדמו לפני שמבינים אותה.

## תמונת המצב הסופית

נכון ל־<bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">2026-09-17</code></bdo></bdi>:

- <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">11</code></bdo></bdi> נכסים במעקב.
- <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">162,743</code></bdo></bdi> נרות דקה ב־<bdi dir="ltr"><code dir="ltr">Gold</code></bdi>, מהם <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">154,206 CERTIFIED</code></bdo></bdi>.
- <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">937</code></bdo></bdi> רשומות דיווחי <bdi dir="ltr"><code dir="ltr">SEC</code></bdi>.
- <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">76</code></bdo></bdi> ימי מסחר היסטוריים מאושרים ו־<bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">12</code></bdo></bdi> ריצות <bdi dir="ltr"><code dir="ltr">Backtest</code></bdi> מפורסמות.
- שער <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">v1 Shadow Mode</code></bdo></bdi> עומד על <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">2/20</code></bdo></bdi>.
- מודל <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">v2</code></bdo></bdi> במצב <bdi dir="ltr"><code dir="ltr">FALLBACK</code></bdi>; כללי <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">v1</code></bdo></bdi> פעילים ואין הסתברות מומצאת.

אלה נתוני ראיה מתוארכים. המסכים וסקריפט ההכנה קוראים את המצב הנוכחי מהמערכת ולא מסתמכים על המספרים הכתובים כאן.

## מסלול הדמו המומלץ

1. <bdi dir="ltr"><code dir="ltr">Project Story</code></bdi> — הסיפור העסקי והארכיטקטורה.
2. <bdi dir="ltr"><code dir="ltr">Dashboard</code></bdi> — <bdi dir="ltr"><code dir="ltr">AAPL</code></bdi>, טווח של שבעה ימים, מחיר ו־<bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">SMA 20</code></bdo></bdi>.
3. <bdi dir="ltr"><code dir="ltr">Kafka UI</code></bdi> — הודעת <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">MarketBarV1</code></bdo></bdi> אחת והמיקום שלה.
4. <bdi dir="ltr"><code dir="ltr">MinIO Bronze</code></bdi> — אותו אירוע גולמי עם <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">topic / partition / offset</code></bdo></bdi> בנתיב.
5. <bdi dir="ltr"><code dir="ltr">Airflow</code></bdi> — ריצת התיקון הירוקה <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">repair__2026-09-16__20260917</code></bdo></bdi>.
6. <bdi dir="ltr"><code dir="ltr">Opportunity Center</code></bdi> — <bdi dir="ltr"><code dir="ltr">META BUY ZONE</code></bdi>, <bdi dir="ltr"><code dir="ltr">AAPL WATCH BREAKOUT</code></bdi>, שלוש שכבות הראיה ומצב המודל.
7. <bdi dir="ltr"><code dir="ltr">Backtesting Lab</code></bdi> — ריצה מפורסמת, מדדים, עקומת הון, מדד ייחוס ו־<bdi dir="ltr"><code dir="ltr">Lineage</code></bdi>.

הדמו הוא לקריאה בלבד. אין להפעיל <bdi dir="ltr"><code dir="ltr">Backfill</code></bdi>, לשנות נתונים או להציג את קובץ <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">.env</code></bdo></bdi> מול הקהל.

</div>
