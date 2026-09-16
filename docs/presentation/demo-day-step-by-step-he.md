<div dir="rtl" align="right">

# מדריך ההצגה והדמו של <bdi dir="ltr"><code>MarketPilot</code></bdi>

זהו המסמך המרכזי ליום ההצגה. הוא בנוי למסלול של כ־<bdi dir="ltr"><code>15 minutes</code></bdi>:
כ־9 דקות למצגת וכ־6 דקות לדמו החי. אין צורך לשנן את הנוסח. צריך להבין את
הרעיון של כל תחנה ולדבר במילים טבעיות.

## הסיפור המרכזי

<bdi dir="ltr"><code>MarketPilot</code></bdi> נבנתה כדי לגשר בין המספר שהסוחר רואה לבין
היכולת להבין אם אפשר לסמוך עליו. המערכת אוספת נתוני שוק ודיווחי חברות, שומרת
את המקור הגולמי, בודקת איכות, מחשבת אינדיקטורים ומציגה תרחיש החלטה עם סיכון,
הסבר והיסטוריה שניתנת לשחזור.

המערכת היא כלי מחקר ותמיכה בהחלטות. היא אינה שולחת פקודות מסחר ואינה מבטיחה
תשואה.

## מה מפעילים לפני ההצגה

פתח חלון <bdi dir="ltr"><code>PowerShell</code></bdi> ועבור לתיקיית הפרויקט:

<div dir="ltr" align="left">

```powershell
Set-Location "C:\Users\Amichai\Documents\naya_college_de\final_project\MarketPilot"
docker compose up -d
.\scripts\demo-preflight.ps1 -OpenPages
```

</div>

הפקודה האחרונה בודקת את תצורת <bdi dir="ltr"><code>Docker Compose</code></bdi>, את שירותי
הליבה, את ממשקי ההדגמה, את מצב <bdi dir="ltr"><code>Shadow Mode</code></bdi> ואת זמינות
ה־<bdi dir="ltr"><code>DAG</code></bdi> היומי. היא פותחת את דפי הדמו רק כאשר כל הבדיקות עברו.

אם הפקודה אינה מזוהה, הסיבה בדרך כלל היא שהטרמינל נמצא בתיקיית המשתמש ולא
בתיקיית הפרויקט. הרץ קודם את פקודת <bdi dir="ltr"><code>Set-Location</code></bdi> שמופיעה למעלה.

## הכנה לפני כניסת הקהל

1. פתח את המצגת: [MarketPilot-Final-Presentation-Dark-RTL-v2.pptx](output/MarketPilot-Final-Presentation-Dark-RTL-v2.pptx).
2. התחבר מראש ל־<bdi dir="ltr"><code>MinIO</code></bdi> ול־<bdi dir="ltr"><code>Airflow</code></bdi>.
3. סגור את קובץ <bdi dir="ltr"><code>.env</code></bdi> וכל חלון שעלול לחשוף סיסמה או מפתח.
4. במסך הראשי בחר <bdi dir="ltr"><code>AAPL</code></bdi> וטווח <bdi dir="ltr"><code>7D</code></bdi>.
5. ודא שבגרף מופיעים 5 ימי מסחר, 1,950 נרות וכיסוי מלא של <bdi dir="ltr"><code>SMA 20</code></bdi>.
6. פתח מראש הודעה אחת ב־<bdi dir="ltr"><code>Kafka UI</code></bdi> ואובייקט אחד ב־<bdi dir="ltr"><code>MinIO Bronze</code></bdi>.
7. ב־<bdi dir="ltr"><code>Airflow</code></bdi> פתח ריצה מוצלחת של <bdi dir="ltr"><code>historical_market_backfill</code></bdi> או של <bdi dir="ltr"><code>daily_market_close</code></bdi>.
8. במעבדת הבדיקה ההיסטורית בחר את הריצה שמזהה שלה מתחיל ב־<bdi dir="ltr"><code>2bf99281</code></bdi>.

## ניהול הזמן

| זמן | חלק | מטרה |
|---:|---|---|
| <bdi dir="ltr"><code>00:00–02:00</code></bdi> | שקפים <bdi dir="ltr"><code>1–3</code></bdi> | הבעיה והערך לסוחר |
| <bdi dir="ltr"><code>02:00–05:05</code></bdi> | שקפים <bdi dir="ltr"><code>4–6</code></bdi> | ארכיטקטורה ובחירות טכנולוגיות |
| <bdi dir="ltr"><code>05:05–08:55</code></bdi> | שקפים <bdi dir="ltr"><code>7–11</code></bdi> | המוצר, האתגרים והמשך הדרך |
| <bdi dir="ltr"><code>08:55–09:10</code></bdi> | שקף 12 | מעבר לדמו |
| <bdi dir="ltr"><code>09:10–15:00</code></bdi> | דמו חי | הוכחה מקצה לקצה |

אם הזמן מתקצר, אל תוותר על הבעיה, הארכיטקטורה והדמו. קצר את פירוט הטכנולוגיות
ואת מפת הדרכים.

---

## חלק א: מה לומר במצגת

### שקף 1 — פתיחה

**המסר:** המערכת מחברת מידע גולמי לתרחיש החלטה שניתן להסביר.

> שלום, אני מציג את <bdi dir="ltr"><code>MarketPilot</code></bdi>. הפרויקט התחיל משאלה פשוטה: כשסוחר רואה מחיר
> או איתות, איך הוא יודע מאיפה הנתון הגיע, אם הוא טרי, ואם הרעיון נבדק בצורה
> הוגנת? בניתי פלטפורמת מחקר מקומית שמחברת נתוני שוק, דיווחי חברות, בדיקות
> איכות וניתוח היסטורי למוצר אחד. המערכת אינה מבצעת מסחר. היא עוזרת לקבל
> החלטה מודעת יותר.

**מעבר:** “כדי להבין למה צריך מערכת כזאת, נתחיל מהבעיה.”

### שקף 2 — הבעיה

**המסר:** מחיר לבדו חסר הקשר ואמון.

> לסוחר יש היום הרבה מסכים, אבל המידע מפוזר. מחיר אינו אומר אם הנתון שלם,
> אם החברה פרסמה דיווח מהותי, או אם אסטרטגיה שנראית טובה בגרף שרדה בדיקה
> היסטורית עם עלויות. ארבע השאלות בשקף הפכו לדרישות המוצר: מה קורה עכשיו,
> האם הנתון אמין, מה השתנה בחברה, ומה קרה כשהפעלנו את אותו רעיון על העבר.

### שקף 3 — הערך למשתמש

**המסר:** המערכת בונה אמון בשלבים לפני שהיא מציגה תרחיש.

> <bdi dir="ltr"><code>MarketPilot</code></bdi> קודם אוספת עובדות. אחר כך היא מוסיפה הקשר, בודקת את איכות
> הנתונים, ורק בסוף מציגה תרחיש החלטה. המשתמש מקבל טווח כניסה, נקודת ביטול,
> יעדים וגודל פוזיציה אפשרי. ההחלטה והביצוע נשארים בידיו.

### שקף 4 — הארכיטקטורה

**המסר:** אותו נתון עובר בשלושה מסלולים בעלי מטרות שונות.

> אני קורא את התרשים מימין לשמאל. <bdi dir="ltr"><code>Alpaca</code></bdi> ו־<bdi dir="ltr"><code>SEC</code></bdi> הם המקורות. שירותי <bdi dir="ltr"><code>Python</code></bdi>
> מאחדים את המידע לחוזים ברורים. <bdi dir="ltr"><code>Kafka</code></bdi> מפריד בין היצרן לצרכנים, ולכן כל צרכן
> יכול להתקדם בקצב שלו ואפשר לבצע <bdi dir="ltr"><code>Replay</code></bdi>. ‏<bdi dir="ltr"><code>Spark</code></bdi> מעבד את המידע, ו־<bdi dir="ltr"><code>MariaDB Gold</code></bdi>
> מגיש אותו למוצר דרך <bdi dir="ltr"><code>API</code></bdi>.
>
> במקביל, האירוע נשמר ב־<bdi dir="ltr"><code>MinIO Bronze</code></bdi> כמקור גולמי ובלתי משתנה. עבודות <bdi dir="ltr"><code>Batch</code></bdi>
> מנקות ומנרמלות אותו ל־<bdi dir="ltr"><code>Silver</code></bdi>, מפעילות בדיקות איכות, ורק אז מפרסמות <bdi dir="ltr"><code>Gold</code></bdi>
> מאושר. <bdi dir="ltr"><code>Airflow</code></bdi> מתזמן את העבודות האלה, אבל אינו מפעיל את שירותי ה־<bdi dir="ltr"><code>Streaming</code></bdi>.
> הדפדפן מתקשר רק עם ה־<bdi dir="ltr"><code>API</code></bdi> ולעולם לא ישירות עם <bdi dir="ltr"><code>MariaDB</code></bdi> או <bdi dir="ltr"><code>MinIO</code></bdi>.

**מה הסוקר צריך להבין:** יש הפרדה בין תעבורה, חישוב, אחסון גולמי, שכבת הגשה
ותזמור. כל רכיב מקבל אחריות מוגדרת.

### שקף 5 — <bdi dir="ltr"><code>Provisional</code></bdi> לעומת <bdi dir="ltr"><code>Certified</code></bdi>

**המסר:** מהירות ואמינות אינן אותה הבטחה.

> המסלול החי נותן תמונת מצב מהירה ומסמן אותה כ־<bdi dir="ltr"><code>Provisional</code></bdi>. לאחר סגירת יום
> המסחר, <bdi dir="ltr"><code>Spark Batch</code></bdi> בונה את היום מחדש מהמקור הגולמי ומפעיל בדיקות איכות.
> רק תוצאה שעברה את השערים מתפרסמת כ־<bdi dir="ltr"><code>Certified</code></bdi>. כך המערכת אינה מעמידה פנים
> שנתון חי כבר עבר בדיקה מלאה.

### שקף 6 — בחירת הטכנולוגיות

**המסר:** הטכנולוגיות נבחרו לפי כשלים שהמערכת צריכה למנוע.

> לא בחרתי רכיבים כדי להציג רשימת טכנולוגיות. לכל רכיב יש סיבה. <bdi dir="ltr"><code>Kafka</code></bdi> מפריד
> בין מקור הנתונים לצרכנים ומאפשר <bdi dir="ltr"><code>Replay</code></bdi>. ‏<bdi dir="ltr"><code>Spark</code></bdi> נותן מנוע משותף לעיבוד חי
> ולחישוב חוזר. <bdi dir="ltr"><code>MinIO</code></bdi> שומר את המקור הגולמי מחוץ למסד שמשרת את האפליקציה.
> <bdi dir="ltr"><code>MariaDB</code></bdi> נותן ל־<bdi dir="ltr"><code>API</code></bdi> מודל <bdi dir="ltr"><code>SQL</code></bdi> מהיר. <bdi dir="ltr"><code>Airflow</code></bdi> מנהל תלויות ו־<bdi dir="ltr"><code>Retry</code></bdi> של עבודות
> שמתחילות ומסתיימות. <bdi dir="ltr"><code>Docker Compose</code></bdi> מנהל את השירותים שצריכים להישאר פעילים.
>
> אפשר היה לכתוב סקריפט אחד גדול, אבל אז תקלה ברכיב אחד הייתה מצמידה את כל
> המערכת, והיינו מאבדים <bdi dir="ltr"><code>Replay</code></bdi>, גבולות אחריות ויכולת התאוששות מסודרת.

### שקף 7 — המסך הראשי

**המסר:** המורכבות ההנדסית משרתת חוויה פשוטה.

> זהו מסך המחקר הראשי. המשתמש רואה מחיר, נפח, אינדיקטורים, דיווחי חברה
> וטריות במקום אחד. כל תוצאה מגיעה דרך <bdi dir="ltr"><code>Backend API</code></bdi> וכוללת מצב פרסום. אפשר
> להתחיל מהמספר שעל המסך ולרדת עד האירוע המקורי ששמור ב־<bdi dir="ltr"><code>Bronze</code></bdi>.

### שקף 8 — <bdi dir="ltr"><code>Opportunity Center</code></bdi>

**המסר:** המלצה טובה מציגה גם את התנאים שבהם היא מפסיקה להיות נכונה.

> המערכת אינה מציגה מחיר קסם. היא מציגה <bdi dir="ltr"><code>Buy Zone</code></bdi>, ‏<bdi dir="ltr"><code>Stop</code></bdi>, שני יעדים, יחס
> <bdi dir="ltr"><code>Risk/Reward</code></bdi> וגודל פוזיציה לפי מגבלות התיק. ההסבר בעברית מפרט למה התרחיש
> קיבל את הציון שלו. המודל נמצא ב־<bdi dir="ltr"><code>Shadow Mode</code></bdi>, ולכן הוא אוסף ראיות ואינו
> מסומן כ־<bdi dir="ltr"><code>Actionable</code></bdi>.

### שקף 9 — בדיקה היסטורית

**המסר:** ניסוי אמין חשוב יותר מתשואה יפה.

> ה־<bdi dir="ltr"><code>Backtest</code></bdi> משתמש רק בנתוני <bdi dir="ltr"><code>Certified Gold</code></bdi>. אות שנוצר בנר מסוים משפיע רק
> מהנר הבא, כדי שלא להשתמש במידע עתידי. החישוב כולל עלויות ו־<bdi dir="ltr"><code>Slippage</code></bdi> ומשווה
> מול <bdi dir="ltr"><code>SPY</code></bdi>. גם תוצאה חלשה היא שימושית, משום שהיא מונעת מאיתנו לקדם רעיון שלא
> עמד בבדיקה.

### שקף 10 — האתגרים

**המסר:** האתגרים הפכו לעקרונות תכנון שניתנים להגנה.

> שני האתגרים המרכזיים היו אמון והתאוששות. כדי לשלב מהירות עם אמינות הפרדתי
> בין <bdi dir="ltr"><code>Provisional</code></bdi> ל־<bdi dir="ltr"><code>Certified</code></bdi>. כדי להפוך <bdi dir="ltr"><code>Retry</code></bdi> לבטוח השתמשתי ב־<bdi dir="ltr"><code>Checkpoint</code></bdi>,
> <bdi dir="ltr"><code>Business Keys</code></bdi> ו־<bdi dir="ltr"><code>Upsert</code></bdi>. בהשלמה היסטורית לא כתבתי ישירות למסד. הנתונים עברו
> דרך <bdi dir="ltr"><code>Kafka</code></bdi>, ‏<bdi dir="ltr"><code>Bronze</code></bdi> ושערי האיכות כדי לשמור על אותו <bdi dir="ltr"><code>Lineage</code></bdi> כמו הנתונים החיים.

### שקף 11 — המשך הדרך

**המסר:** יש מוצר עובד, אך קיימים תנאים ברורים לפני שימוש רחב יותר.

> היום קיימת מערכת מקומית מלאה עם מסלול חי, מסלול מאושר, נתונים היסטוריים
> וממשק <bdi dir="ltr"><code>Web</code></bdi>. לפני פתיחת <bdi dir="ltr"><code>Decision Support</code></bdi> פעיל נדרשים 20 ימי <bdi dir="ltr"><code>Shadow Mode</code></bdi>,
> בדיקת <bdi dir="ltr"><code>Calibration</code></bdi> ואישור אנושי. השלב הבא יכול לכלול <bdi dir="ltr"><code>SIP</code></bdi>, מעבר ל־<bdi dir="ltr"><code>S3</code></bdi>,
> <bdi dir="ltr"><code>Observability</code></bdi> ואבטחת <bdi dir="ltr"><code>Production</code></bdi>. אלה שלבי המשך ולא יכולות שאני טוען שכבר
> מימשתי.

### שקף 12 — מעבר לדמו

> עד עכשיו הסברתי את ההיגיון. עכשיו אראה את אותה שרשרת במערכת עצמה: נתחיל
> במסך העסקי, נעבור לאירוע ב־<bdi dir="ltr"><code>Kafka</code></bdi>, נראה את המקור ב־<bdi dir="ltr"><code>MinIO</code></bdi> ואת ריצת האישור
> ב־<bdi dir="ltr"><code>Airflow</code></bdi>, ונסיים בתרחיש ההחלטה ובבדיקה ההיסטורית.

---

## חלק ב: הדמו החי

### מה באמת חי בדמו

הדמו חי משום שהדפדפן מבצע שאילתות אמיתיות ל־<bdi dir="ltr"><code>Backend API</code></bdi>,
ה־<bdi dir="ltr"><code>API</code></bdi> קורא את <bdi dir="ltr"><code>MariaDB Gold</code></bdi>, וממשקי
<bdi dir="ltr"><code>Kafka</code></bdi>, ‏<bdi dir="ltr"><code>MinIO</code></bdi> ו־<bdi dir="ltr"><code>Airflow</code></bdi>
מציגים את מצב המערכת האמיתי. מחוץ לשעות המסחר שירותי הקליטה וה־<bdi dir="ltr"><code>Streaming</code></bdi>
ממשיכים לפעול וממתינים לאירוע חדש. אין צורך לייצר אירוע מלאכותי מול הקהל.

### תחנה 1 — המסך הראשי

**פתח:** <bdi dir="ltr"><code>http://localhost:3000/</code></bdi>

**פעולה:** בחר <bdi dir="ltr"><code>AAPL</code></bdi>, החלף בין <bdi dir="ltr"><code>7D</code></bdi>
ל־<bdi dir="ltr"><code>30D</code></bdi>, והצבע על קו המחיר ועל <bdi dir="ltr"><code>SMA 20</code></bdi>.

> שינוי הטווח מפעיל שאילתה חדשה דרך ה־<bdi dir="ltr"><code>API</code></bdi>. ב־7 ימים אנחנו רואים 5 ימי מסחר
> ו־1,950 נרות. ב־30 ימים אנחנו רואים 21 ימי מסחר ו־8,190 נרות. קו <bdi dir="ltr"><code>SMA 20</code></bdi>
> מחליק רעש קצר ומאפשר לראות את כיוון המחיר ביחס לממוצע של 20 נרות.

**מעבר:** “עכשיו נרד מן הגרף אל האירוע שהגיע למערכת.”

### תחנה 2 — <bdi dir="ltr"><code>Kafka UI</code></bdi>

**פתח:** <bdi dir="ltr"><code>http://localhost:8085/</code></bdi>

**הצג:** <bdi dir="ltr"><code>market.bars.1m.v1</code></bdi>, מפתח, מחיצה, מיקום וגוף
<bdi dir="ltr"><code>JSON</code></bdi> של הודעה אחת.

> <bdi dir="ltr"><code>Kafka</code></bdi> משמש שכבת תעבורה ויומן אירועים. ה־<bdi dir="ltr"><code>Partition</code></bdi> וה־<bdi dir="ltr"><code>Offset</code></bdi> מזהים את מיקום
> ההודעה. כך <bdi dir="ltr"><code>Spark Streaming</code></bdi> וה־<bdi dir="ltr"><code>Raw Archive</code></bdi> יכולים לצרוך באופן עצמאי, ואפשר
> לחזור לאירועים במקרה של עיבוד מחדש.

### תחנה 3 — <bdi dir="ltr"><code>MinIO Bronze</code></bdi>

**פתח:** <bdi dir="ltr"><code>http://localhost:9001/</code></bdi>

**הצג:** אובייקט מתוך <bdi dir="ltr"><code>marketpilot-bronze</code></bdi>, כולל הנתיב והשדות
<bdi dir="ltr"><code>event_id</code></bdi>, ‏<bdi dir="ltr"><code>event_time_utc</code></bdi>,
‏<bdi dir="ltr"><code>ingested_at_utc</code></bdi> ו־<bdi dir="ltr"><code>schema_version</code></bdi>.

> זהו העותק הגולמי. הוא נשמר לפני אישור ההודעה לצרכן, והנתיב שומר גם את
> מיקום <bdi dir="ltr"><code>Kafka</code></bdi>. אם בעתיד אתקן קוד או ארצה לבצע <bdi dir="ltr"><code>Replay</code></bdi>, איני תלוי רק בתוצאה
> שכבר פורסמה ל־<bdi dir="ltr"><code>Gold</code></bdi>.

### תחנה 4 — <bdi dir="ltr"><code>Airflow</code></bdi>

**פתח:** <bdi dir="ltr"><code>http://localhost:8080/</code></bdi>

**הצג:** ריצה מוצלחת ואת סדר המשימות. אין להפעיל ריצה חדשה בזמן ההצגה.

> <bdi dir="ltr"><code>Airflow</code></bdi> מנהל עבודות תחומות בזמן. כאן אפשר לראות את הסדר, התלויות והסטטוס.
> הוא שולח עבודות <bdi dir="ltr"><code>Batch</code></bdi> ל־<bdi dir="ltr"><code>Spark</code></bdi>, אבל אינו מנהל את חיי <bdi dir="ltr"><code>Kafka</code></bdi> או <bdi dir="ltr"><code>Spark Streaming</code></bdi>.
> בריצת ההשלמה האחרונה עובדו 21 ימי מסחר, ולאחר מכן חושבו האינדיקטורים וה־<bdi dir="ltr"><code>Backtest</code></bdi>.

### תחנה 5 — <bdi dir="ltr"><code>Opportunity Center</code></bdi>

**פתח:** <bdi dir="ltr"><code>http://localhost:3000/opportunities.html</code></bdi>

**הצג:** רשימת המעקב, טווח הכניסה, נקודת הביטול, היעדים, יחס הסיכון וגודל
הפוזיציה.

> כאן שכבות הנתונים הופכות לכלי החלטה. התרחיש משלב ניתוח טכני, מידע
> פונדמנטלי ומגבלות סיכון. אפשר לראות למה התקבלה התוצאה ומה יגרום לתזה
> להתבטל. <bdi dir="ltr"><code>Shadow Mode</code></bdi> מונע מהמערכת להציג ביטחון שלא נצבר עדיין.

### תחנה 6 — <bdi dir="ltr"><code>Backtesting Lab</code></bdi>

**פתח:** <bdi dir="ltr"><code>http://localhost:3000/backtesting.html</code></bdi>

**הצג:** הריצה המפורסמת, עקומת ההון, המדדים וההשוואה ל־<bdi dir="ltr"><code>SPY</code></bdi>.

> זו אינה תחזית. זהו ניסוי היסטורי שחזורי. אפשר לראות את טווח הקלט, גרסת
> האסטרטגיה, מספר התצפיות, העלויות והתוצאה מול <bdi dir="ltr"><code>Benchmark</code></bdi>. המערכת שומרת את
> הפרטים כדי שאפשר יהיה להריץ מחדש ולהסביר את התוצאה.

### משפט הסיום

> <bdi dir="ltr"><code>MarketPilot</code></bdi> מחברת בין מהירות לאמון. היא מתחילה באירוע גולמי, שומרת אותו,
> בודקת ומאשרת אותו, ומציגה למשתמש תרחיש שאפשר להסביר ולשחזר. מבחינתי זה
> ההבדל בין גרף מעניין לבין מוצר <bdi dir="ltr"><code>Data Engineering</code></bdi> שאפשר לבנות עליו.

## אם משהו לא עובד

- אם המסך הראשי אינו זמין, הצג את צילום המסך בשקף 7.
- אם <bdi dir="ltr"><code>Kafka UI</code></bdi> אינו זמין, עבור לאובייקט <bdi dir="ltr"><code>Bronze</code></bdi> והסבר שהנתיב מכיל את מיקום ההודעה.
- אם <bdi dir="ltr"><code>MinIO</code></bdi> אינו זמין, הצג את שקף 4 ואת צילום המסך המוכן.
- אם <bdi dir="ltr"><code>Airflow</code></bdi> אינו זמין, הצג את מסמך האימות ואת סדר המשימות בשקף.
- אם הנתון החי ישן, אמור זאת בכנות. שירות בריא ונתון טרי הן שתי בדיקות שונות.
- אל תתחיל תיקון ארוך מול הקהל. עבור לראיה החלופית והמשך לדבר.

## שלושה מושגים שחובה לדעת

### <bdi dir="ltr"><code>Checkpoint</code></bdi>

מצב שמאפשר ל־<bdi dir="ltr"><code>Streaming</code></bdi> להמשיך מהמקום שבו נעצר לאחר הפעלה
מחדש. הוא שומר התקדמות ומיקומי קריאה. מחיקה שלו ללא תוכנית <bdi dir="ltr"><code>Replay</code></bdi>
עלולה ליצור עיבוד חוזר או אובדן מצב.

### <bdi dir="ltr"><code>SMA 20</code></bdi>

ממוצע נע פשוט של 20 נרות. בכל נקודה מחברים את 20 מחירי הסגירה האחרונים
ומחלקים ב־20. הוא מחליק רעש ועוזר לראות כיוון, אך הוא מפגר אחרי המחיר ואינו
אות קנייה בפני עצמו.

### <bdi dir="ltr"><code>Idempotency</code></bdi>

היכולת להריץ פעולה שוב בלי ליצור תוצאה עסקית כפולה. ב־<bdi dir="ltr"><code>MarketPilot</code></bdi>
משתמשים במפתחות עסקיים, מזהים דטרמיניסטיים ו־<bdi dir="ltr"><code>Upsert</code></bdi>. המטרה
אינה למנוע כל <bdi dir="ltr"><code>Retry</code></bdi>, אלא להפוך אותו לבטוח.

## המשפט לזכור אם אינך יודע תשובה

> אני לא רוצה להמציא. אסביר מה מימשתי ומה בדקתי, ואת הפרט המדויק אוכל לאמת
> במסמך או בקוד.

</div>
