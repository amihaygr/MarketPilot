<div dir="rtl" align="right">

# מרכז ההצגה של ⁦MarketPilot⁩

כאן נמצאים כל החומרים הדרושים למצגת ולדמו החי, בסדר שבו מומלץ להשתמש בהם.

## מתחילים כאן

1. [הורדת המצגת הסופית בגרסת RTL כהה](output/MarketPilot-Final-Presentation-Dark-RTL-v3.pptx) — 12 שקופיות בתבנית כהה ואחידה, עם סיפור עסקי ברור, השוואת חלופות טכנולוגיות, כיווניות עברית מלאה והערות מציג לכל שקופית.
2. [מדריך ההצגה והדמו המלא](demo-day-step-by-step-he.md) — מה מפעילים, מה אומרים בכל שקף, לאן עוברים בדמו ומה עושים במקרה תקלה.
3. [תרחיש הדמו החי](live-demo-script-he.md) — גרסת כיס של שש דקות, תחנה אחר תחנה.

## חומרי לימוד והכנה

- [חוברת המציג](presenter-handbook.md) — הסברים מעמיקים על המערכת.
- [מילון המונחים](glossary.md) — הגדרות קצרות למושגים מרכזיים.
- [מאגר שאלות ותשובות](qa-bank.md) — הכנה לשאלות הסוקר.
- [תוכנית חזרה ותרחישי תקלה](rehearsal-and-failure-playbook.md) — מה לעשות אם רכיב אינו זמין.
- [הסבר מרכז ההזדמנויות](phase14-opportunity-center-he.md) — פירוט מסך התמיכה בהחלטות.

## ראיות חזותיות

- [מסך המחקר הראשי](assets/dashboard.png)
- [מרכז ההזדמנויות](assets/opportunity-center.png)
- [מעבדת הבדיקה ההיסטורית](assets/backtesting.png)
- [סיפור הפרויקט](assets/project-story.png)

## הפעלת הדמו

פתח <bdi dir="ltr"><code>PowerShell</code></bdi>, עבור לתיקיית הפרויקט והריץ:

<div dir="ltr" align="left">

```powershell
Set-Location "C:\Users\Amichai\Documents\naya_college_de\final_project\MarketPilot"
docker compose up -d
.\scripts\demo-preflight.ps1 -OpenPages
```

</div>

כאשר כל הבדיקות ירוקות, הצג את המצגת ועבור לדמו החי בשקופית 12.

</div>
