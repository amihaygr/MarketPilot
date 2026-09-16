<div dir="rtl" align="right">

# אימות הרחבת הראיות ההיסטוריות — <bdi dir="ltr"><code>Phase 14</code></bdi>

> זהו צילום מצב היסטורי מ־14 בספטמבר. מצב ההגשה העדכני מתועד בקובץ
> <bdi dir="ltr"><code>docs/final-presentation-verification.md</code></bdi>; המסמך נשמר
> כדי לא למחוק ראיות ריצה קודמות.

**תאריך אימות:** 14 בספטמבר 2026

## התוצאה

- קיימים **41 ימי מסחר מאושרים** לכל אחת מהמניות <bdi dir="ltr"><code>AAPL</code></bdi>, ‏<bdi dir="ltr"><code>MSFT</code></bdi> ו־<bdi dir="ltr"><code>SPY</code></bdi>.
- טווח הנתונים הוא **6 ביולי עד 28 באוגוסט 2026**.
- נרות מאושרים:
  - <bdi dir="ltr"><code>AAPL — 15,769</code></bdi>
  - <bdi dir="ltr"><code>MSFT — 15,734</code></bdi>
  - <bdi dir="ltr"><code>SPY — 15,768</code></bdi>
- ריצת ההשלמה ההיסטורית <bdi dir="ltr"><code>phase14_historical_evidence_20260914</code></bdi> הסתיימה בהצלחה.
- ריצת הבדיקה ההיסטורית <bdi dir="ltr"><code>phase14_full_history_backtest_20260914</code></bdi> הסתיימה בהצלחה.
- מזהה התוצאה הוא <bdi dir="ltr"><code>2bf99281-ec93-5fec-9ce2-d72539021bea</code></bdi>.

## המסלול שעבר כל יום חדש

<div dir="ltr" align="left">

```text
Alpaca IEX → Kafka Historical Topic → MinIO Bronze
→ Spark Silver → Data Quality → MariaDB Certified Gold
```

</div>

כל 20 ימי יולי עברו קליטה, ניקוי, בדיקות איכות ופרסום מאושר. רק לאחר הצלחת
כל השלבים הופעלה הבדיקה ההיסטורית המאוחדת על מלוא החלון.

## תוצאות הבדיקה ההיסטורית

<div dir="ltr" align="left">

| Symbol | Observations | Trades | Return | Benchmark | Max Drawdown | Sharpe |
|---|---:|---:|---:|---:|---:|---:|
| AAPL | 15,594 | 353 | 1.36% | 2.67% | -5.65% | 0.57 |
| MSFT | 15,559 | 363 | -4.90% | 2.67% | -10.66% | -1.39 |
| SPY | 15,596 | 343 | -5.64% | 2.67% | -6.66% | -4.98 |
| Total | 46,749 | 1,059 | — | — | — | — |

</div>

התוצאות מוצגות כפי שהתקבלו. הן אינן הבטחת תשואה ואינן ייעוץ פיננסי.

## הפרדה חשובה להצגה

- <bdi dir="ltr"><code>Historical Backfill</code></bdi> — מעשיר את הראיות, הגרפים והבדיקות ההיסטוריות.
- <bdi dir="ltr"><code>Live Shadow Mode</code></bdi> — מתקדם רק כאשר יום מסחר נצפה בזמן אמת.

לכן ההשלמה ההיסטורית אינה מקדמת את שער הבטיחות החי, שנשאר **1 מתוך 20** ימי מסחר.

## שערי איכות

<div dir="ltr" align="left">

```text
ruff check .           -> passed
ruff format --check .  -> passed
pytest -q              -> 104 passed, 7 skipped
```

</div>

</div>
