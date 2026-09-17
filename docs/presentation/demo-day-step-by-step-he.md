<div dir="rtl" align="right">

# מדריך ההצגה והדמו של <bdi dir="ltr"><code dir="ltr">MarketPilot</code></bdi>

זהו המסמך המרכזי ליום ההצגה. הוא בנוי למסלול של כ־<bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">15</code></bdo></bdi> דקות:
כ־<bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">9</code></bdo></bdi> דקות למצגת וכ־<bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">6</code></bdo></bdi> דקות לדמו החי. אין צורך לשנן את הנוסח. צריך להבין את
הרעיון של כל תחנה ולדבר במילים טבעיות.

מונח טכני שאינו מובן מאליו מוסבר בסוגריים מיד אחרי הופעתו הראשונה. לאחר
מכן משתמשים בו בקיצור, כדי שהטקסט יישאר טבעי ולא יישמע כמו מילון. בסוף
המדריך מופיע גם מילון מורחב לחזרה לפני ההצגה.

## הסיפור המרכזי

המטרה של הפרויקט היא לגשר בין המספר שהסוחר רואה לבין היכולת להבין אם אפשר
לסמוך עליו. המערכת אוספת נתוני שוק ודיווחי חברות, שומרת את המקור הגולמי,
בודקת איכות, מחשבת אינדיקטורים ומציגה תרחיש החלטה עם סיכון, הסבר והיסטוריה
שניתנת לשחזור.

המערכת היא כלי מחקר ותמיכה בהחלטות. היא אינה שולחת פקודות מסחר ואינה מבטיחה
תשואה.

## מה מפעילים לפני ההצגה

פתח חלון <bdi dir="ltr"><code dir="ltr">PowerShell</code></bdi> ועבור לתיקיית הפרויקט:

<div dir="ltr" align="left">

```powershell
Set-Location "C:\Users\Amichai\Documents\naya_college_de\final_project\MarketPilot"
docker compose up -d
.\scripts\demo-preflight.ps1 -OpenPages
```

</div>

הפקודה האחרונה בודקת את תצורת <bdi dir="ltr"><code dir="ltr">Docker Compose</code></bdi> (כלי שמגדיר
ומפעיל יחד את כל הקונטיינרים של המערכת), את שירותי הליבה ואת ממשקי ההדגמה.
היא בודקת גם את מצב <bdi dir="ltr"><code dir="ltr">Shadow Mode</code></bdi> (תקופת צל שבה המערכת
מייצרת תרחישים ומודדת אותם, אך עדיין אינה מציגה אותם כהמלצה מעשית) ואת
זמינות ה־<bdi dir="ltr"><code dir="ltr">DAG</code></bdi> היומי (תרשים משימות עם סדר ותלויות
שמופעל ב־<bdi dir="ltr"><code dir="ltr">Airflow</code></bdi>). דפי הדמו נפתחים רק כאשר כל
בדיקות ההכנה עברו.

אם הפקודה אינה מזוהה, הסיבה בדרך כלל היא שהטרמינל נמצא בתיקיית המשתמש ולא
בתיקיית הפרויקט. הרץ קודם את פקודת <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">Set-Location</code></bdo></bdi> שמופיעה למעלה.

## הכנה לפני כניסת הקהל

1. פתח את המצגת: [<bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">MarketPilot-Final-Presentation.pptx</code></bdo></bdi>](output/MarketPilot-Final-Presentation.pptx).
2. התחבר מראש ל־<bdi dir="ltr"><code dir="ltr">MinIO</code></bdi> ול־<bdi dir="ltr"><code dir="ltr">Airflow</code></bdi>.
3. סגור את קובץ <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">.env</code></bdo></bdi> וכל חלון שעלול לחשוף סיסמה או מפתח.
4. במסך הראשי בחר <bdi dir="ltr"><code dir="ltr">AAPL</code></bdi> וטווח <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">7D</code></bdo></bdi>.
5. ודא שבגרף מופיעים לפחות <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">5</code></bdo></bdi> ימי מסחר, שהפערים מחוץ לשעות המסחר נשארים גלויים ושכיסוי <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">SMA 20</code></bdo></bdi> גבוה מ־<bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">80%</code></bdo></bdi>.
6. פתח מראש הודעה אחת ב־<bdi dir="ltr"><code dir="ltr">Kafka UI</code></bdi> ואובייקט אחד ב־<bdi dir="ltr"><code dir="ltr">MinIO Bronze</code></bdi>.
7. ב־<bdi dir="ltr"><code dir="ltr">Airflow</code></bdi> פתח את ריצת התיקון הירוקה <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">repair__2026-09-16__20260917</code></bdo></bdi> של <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">historical_market_backfill</code></bdo></bdi>.
8. במעבדת הבדיקה ההיסטורית בחר ריצה במצב <bdi dir="ltr"><code dir="ltr">Published</code></bdi> שמכסה כמה שבועות; אין להסתמך על מזהה קבוע.
9. במרכז ההזדמנויות ודא שמופיעים <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">2/20</code></bdo></bdi>, <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">76 certified sessions</code></bdo></bdi> ו־<bdi dir="ltr"><code dir="ltr">RULES ACTIVE · MODEL FALLBACK</code></bdi>.

## ניהול הזמן

- <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">00:00–02:00</code></bdo></bdi> — שקפים <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">1–3</code></bdo></bdi>: הבעיה והערך לסוחר.
- <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">02:00–05:05</code></bdo></bdi> — שקפים <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">4–6</code></bdo></bdi>: הארכיטקטורה ובחירות הטכנולוגיה.
- <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">05:05–08:55</code></bdo></bdi> — שקפים <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">7–11</code></bdo></bdi>: המוצר, האתגרים והמשך הדרך.
- <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">08:55–09:10</code></bdo></bdi> — שקף <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">12</code></bdo></bdi>: מעבר לדמו.
- <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">09:10–15:00</code></bdo></bdi> — דמו חי: הוכחה מקצה לקצה.

אם הזמן מתקצר, אל תוותר על הבעיה, הארכיטקטורה והדמו. קצר את פירוט הטכנולוגיות
ואת מפת הדרכים.

---

## חלק א: מה לומר במצגת

### שקף <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">1</code></bdo></bdi> — פתיחה

**המסר:** המערכת מחברת מידע גולמי לתרחיש החלטה שניתן להסביר.

> שלום. הפרויקט התחיל משאלה פשוטה: כשסוחר רואה מחיר
> או איתות, איך הוא יודע אם אפשר באמת לסמוך עליו? כדי לבחון מניה אני רוצה
> לדעת מה קורה במחיר, מה השתנה בחברה, מה הסיכון והאם הרעיון עבד גם בעבר.
> לכן בניתי סביבת מחקר שמרכזת את כל התמונה ומאפשרת לרדת מכל תוצאה עד מקור
> הנתון. המערכת אינה מבצעת מסחר. היא עוזרת לקבל החלטה שקופה ומודעת יותר.

**מעבר:** “כדי להבין למה צריך מערכת כזאת, נתחיל מהבעיה.”

### שקף <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">2</code></bdo></bdi> — הבעיה

**המסר:** מחיר לבדו חסר הקשר ואמון.

> הבעיה אינה מחסור במידע. להפך — יש גרפים, חדשות, דיווחים והמון מספרים,
> אבל הם מפוזרים בין כמה מקומות. המשתמש מבזבז זמן בחיפוש ובהצלבה, ועדיין
> לא תמיד יודע מה טרי ומה אמין. ארבע השאלות בשקף הפכו לדרישות המוצר: מה
> קורה עכשיו, האם הנתון אמין, מה השתנה בחברה, ומה קרה כשבדקנו את הרעיון
> על נתוני עבר.

### שקף <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">3</code></bdo></bdi> — הערך למשתמש

**המסר:** המערכת בונה אמון בשלבים לפני שהיא מציגה תרחיש.

> הערך למשתמש הוא לא עוד גרף. במקום לעבור בין כמה מקורות ולחבר הכול לבד,
> הוא מקבל סביבת מחקר אחת: נתוני שוק, מידע רשמי על החברה, בדיקות איכות
> וניתוח היסטורי. בסוף מוצג תרחיש עם טווח כניסה, נקודת ביטול, יעדים ויחס
> סיכון־סיכוי. כך נחסך זמן מחקר, והסיבה לכל תוצאה נשארת גלויה. ההחלטה
> והביצוע נשארים בידי המשתמש.

### שקף <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">4</code></bdo></bdi> — הארכיטקטורה

**המסר:** אותו נתון עובר בשלושה מסלולים נפרדים: מסלול חי למהירות, מסלול גולמי
לשמירת ראיות ומסלול אצווה לאישור. שכבת ההחלטה משתמשת בתוצרים שלהם ואינה
עוקפת אותם.

<blockquote dir="rtl" align="right">
<p><strong>אני קורא את התרשים מימין לשמאל.</strong></p>

<p><strong>ראשית, המקורות:</strong> <bdi dir="ltr"><code dir="ltr">Alpaca</code></bdi> מספקת
נתוני שוק, ובפרויקט היא משמשת לנתונים בלבד. <bdi dir="ltr"><code dir="ltr">SEC</code></bdi>
היא רשות ניירות הערך האמריקאית, שמפרסמת את הדיווחים הרשמיים של החברות.
שירותים שנכתבו ב־<bdi dir="ltr"><code dir="ltr">Python</code></bdi> מאחדים את המידע לחוזי
נתונים ברורים — מבנה מוסכם שמגדיר אילו שדות וסוגי ערכים חייבים להופיע בכל
אירוע.</p>

<p><strong>במסלול החי:</strong> <bdi dir="ltr"><code dir="ltr">Kafka</code></bdi> משמש יומן
אירועים מסודר ומפריד בין מי שמייצר את ההודעה לבין מי שצורך אותה. כך כל צרכן
מתקדם בקצב שלו, ואפשר לבצע <bdi dir="ltr"><code dir="ltr">Replay</code></bdi> — לקרוא ולעבד
מחדש אירועים שכבר נשמרו. <bdi dir="ltr"><code dir="ltr">Spark Streaming</code></bdi> מעבד
את האירועים ברצף ומפרסם תוצאה זמינה במהירות.</p>

<p><strong>במסלול הראיות:</strong> אותו אירוע נשמר גם ב־<bdi dir="ltr"><code dir="ltr">MinIO Bronze</code></bdi>.
זוהי שכבת אחסון אובייקטים מקומית, ובה נשמר המקור הגולמי
והבלתי משתנה. אם צריך לבדוק תקלה או לשחזר עיבוד, אפשר לחזור לראיה המקורית
במקום להסתמך רק על התוצאה הסופית.</p>

<p><strong>במסלול המאושר:</strong> עבודות <bdi dir="ltr"><code dir="ltr">Batch</code></bdi> —
עבודות שמטפלות בכמות נתונים מוגדרת ואז מסתיימות — מנקות ומנרמלות את הנתונים
לשכבת <bdi dir="ltr"><code dir="ltr">Silver</code></bdi>. לאחר בדיקות איכות הן מפרסמות אותם
לשכבת <bdi dir="ltr"><code dir="ltr">Gold</code></bdi>, שמכילה מידע עסקי מוכן לשאילתות
ולמסכים.</p>

<p><strong>לבסוף, ההגשה למשתמש:</strong> <bdi dir="ltr"><code dir="ltr">MariaDB</code></bdi>
מחזיקה את נתוני <bdi dir="ltr"><code dir="ltr">Gold</code></bdi> שהאפליקציה צריכה.
הדפדפן מבקש אותם דרך <bdi dir="ltr"><code dir="ltr">API</code></bdi> — ממשק תוכנה מבוקר —
ולעולם אינו מתחבר ישירות למסד הנתונים או ל־<bdi dir="ltr"><code dir="ltr">MinIO</code></bdi>.</p>

<p><bdi dir="ltr"><code dir="ltr">Airflow</code></bdi> מתזמן ומנטר רק עבודות שמתחילות
ומסתיימות. שירותי ה־<bdi dir="ltr"><code dir="ltr">Streaming</code></bdi> אינם מופעלים על ידו,
מפני שהם צריכים לפעול ברצף ומנוהלים בידי
<bdi dir="ltr"><code dir="ltr">Docker Compose</code></bdi>.</p>
</blockquote>

**מה הסוקר צריך להבין:** יש הפרדה בין תעבורה, חישוב, אחסון גולמי, שכבת הגשה
ותזמור. כל רכיב מקבל אחריות מוגדרת.

### שקף <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">5</code></bdo></bdi> — <bdi dir="ltr"><code dir="ltr">Provisional</code></bdi> לעומת <bdi dir="ltr"><code dir="ltr">Certified</code></bdi>

**המסר:** מהירות ואמינות אינן אותה הבטחה.

> המסלול החי נותן תמונת מצב מהירה ומסמן אותה כ־<bdi dir="ltr"><code dir="ltr">Provisional</code></bdi>
> (תוצאה זמנית שעדיין לא עברה את כל בדיקות סוף היום). לאחר סגירת יום
> המסחר, <bdi dir="ltr"><code dir="ltr">Spark Batch</code></bdi> בונה את היום מחדש מהמקור הגולמי ומפעיל בדיקות איכות.
> רק תוצאה שעברה את השערים מתפרסמת כ־<bdi dir="ltr"><code dir="ltr">Certified</code></bdi>
> (תוצאה מאושרת שנבנתה מחדש ועברה בדיקות איכות). כך המערכת אינה מעמידה פנים
> שנתון חי כבר עבר בדיקה מלאה.

### שקף <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">6</code></bdo></bdi> — בחירת הטכנולוגיות

**המסר:** הכלים מוכרים מהקורס, אבל כל אחד נבחר לתפקיד שמתאים לחוזקות שלו.

> בחרתי בכוונה לעבוד עם הכלים שלמדנו ונחשפנו אליהם בקורס. עם זאת, לא חיברתי
> אותם רק כדי להציג רשימת טכנולוגיות. לכל כלי נתתי אחריות ברורה.
>
> <bdi dir="ltr"><code dir="ltr">Kafka</code></bdi> נבחר במקום חיבור ישיר בין המקור לצרכנים, כדי שהצרכנים יוכלו
> לעבוד בקצב עצמאי וכדי שאפשר יהיה לחזור לאירועים. <bdi dir="ltr"><code dir="ltr">Spark</code></bdi> נבחר כדי להשתמש
> במנוע חישוב אחד גם במסלול החי וגם בעיבוד החוזר, במקום לתחזק שתי לוגיקות
> שונות.
>
> <bdi dir="ltr"><code dir="ltr">Airflow</code></bdi> נבחר במקום אוסף תזמונים וסקריפטים ידניים, משום שהוא מציג תלויות,
> ניסיונות חוזרים והיסטוריית ריצות. <bdi dir="ltr"><code dir="ltr">MinIO</code></bdi> נבחר במקום לשמור חומר גולמי
> בתיקיות מקומיות או במסד ההגשה; הוא מתאים לאובייקטים ולמעבר עתידי לענן.
>
> <bdi dir="ltr"><code dir="ltr">MariaDB</code></bdi> נבחר לשכבת ההגשה משום שהאפליקציה צריכה שאילתות ואינדקסים,
> ולא אחסון אובייקטים. <bdi dir="ltr"><code dir="ltr">Docker Compose</code></bdi> מתאים להיקף המקומי של הפרויקט:
> הוא מאפשר להרים את אותה סביבה בצורה עקבית, בלי המורכבות של מערכת תזמור
> קונטיינרים ארגונית.

**מה לא צריך לומר:** אין צורך לטעון שכל אחד מהכלים הוא “הטוב ביותר”. הבחירה
נכונה להיקף, למטרות הלמידה ולארכיטקטורה של הפרויקט. במערכת גדולה או בענן
ייתכן שהיינו בוחרים שירותים מנוהלים או חלופות אחרות.

### שקף <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">7</code></bdo></bdi> — המסך הראשי

**המסר:** המורכבות ההנדסית משרתת חוויה פשוטה.

> זהו מסך המחקר הראשי. המשתמש רואה מחיר, נפח, אינדיקטורים, דיווחי חברה
> וטריות במקום אחד. כל תוצאה מגיעה דרך <bdi dir="ltr"><code dir="ltr">Backend API</code></bdi> וכוללת מצב פרסום. אפשר
> להתחיל מהמספר שעל המסך ולרדת עד האירוע המקורי ששמור ב־<bdi dir="ltr"><code dir="ltr">Bronze</code></bdi>.

### שקף <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">8</code></bdo></bdi> — <bdi dir="ltr"><code dir="ltr">Opportunity Center</code></bdi>

**המסר:** המלצה טובה מציגה גם את התנאים שבהם היא מפסיקה להיות נכונה.

> המערכת אינה מציגה מחיר קסם. היא מפרקת את התרחיש לרכיבים שאפשר להסביר:
>
> - <bdi dir="ltr"><code dir="ltr">Buy Zone</code></bdi> — טווח מחירים שבו תנאי הכניסה נחשבים סבירים.
> - <bdi dir="ltr"><code dir="ltr">Stop</code></bdi> — המחיר שבו התזה נפסלת ומתכננים מראש את היציאה.
> - שני יעדי רווח — נקודות מימוש אפשריות, ולא הבטחה לתשואה.
> - <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">Risk/Reward</code></bdo></bdi> — כמה רווח מתוכנן ביחס לכל יחידת סיכון.
> - גודל הפוזיציה — הכמות שמתאימה למגבלות התיק.
>
> חשוב להפריד בין שלושה מדדים:
>
> - <bdi dir="ltr"><code dir="ltr">Rule Score</code></bdi> — סיכום הראיות לפי הכללים.
> - <bdi dir="ltr"><code dir="ltr">Data Confidence</code></bdi> — איכות, כיסוי וטריות הנתונים.
> - <bdi dir="ltr"><code dir="ltr">Model Probability</code></bdi> — הסתברות מכוילת שתופיע רק לאחר אימון ואימות.
>
> כרגע כללי <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">v1</code></bdo></bdi> פעילים, ומונה הצל
> עומד על <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">2/20</code></bdo></bdi>. מודל
> <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">v2</code></bdo></bdi> נמצא במצב
> <bdi dir="ltr"><code dir="ltr">FALLBACK</code></bdi>. לכן אין הסתברות על המסך — זו
> התנהגות בטוחה, לא חוסר מקרי.
>
> בדמו אראה שלושה מצבים אמיתיים: <bdi dir="ltr"><code dir="ltr">META</code></bdi> שנמצאת כרגע בתוך
> <bdi dir="ltr"><code dir="ltr">BUY ZONE</code></bdi>, <bdi dir="ltr"><code dir="ltr">AAPL</code></bdi> שמסומנת
> <bdi dir="ltr"><code dir="ltr">WATCH BREAKOUT</code></bdi>, וסימול שמסומן
> <bdi dir="ltr"><code dir="ltr">INSUFFICIENT DATA</code></bdi>. המצב האחרון אינו תקלה; הוא מוכיח ששערי
> האיכות יכולים לעצור מסקנה כשאין בסיס מספק.

### שקף <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">9</code></bdo></bdi> — בדיקה היסטורית

**המסר:** ניסוי אמין חשוב יותר מתשואה יפה.

> ה־<bdi dir="ltr"><code dir="ltr">Backtest</code></bdi> (ניסוי של כללי האסטרטגיה על נתוני עבר)
> משתמש רק בנתוני <bdi dir="ltr"><code dir="ltr">Certified Gold</code></bdi>. אות שנוצר בנר מסוים משפיע רק
> מהנר הבא, כדי שלא להשתמש במידע עתידי. החישוב כולל עלויות ו־<bdi dir="ltr"><code dir="ltr">Slippage</code></bdi>
> (הפער האפשרי בין המחיר שתכננו לקבל לבין מחיר הביצוע בפועל) ומשווה מול
> <bdi dir="ltr"><code dir="ltr">SPY</code></bdi> (קרן סל שעוקבת אחר מדד השוק האמריקאי
> <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">S&amp;P 500</code></bdo></bdi> ומשמשת נקודת ייחוס). גם תוצאה חלשה היא שימושית, משום שהיא מונעת מאיתנו לקדם רעיון שלא
> עמד בבדיקה.

### שקף <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">10</code></bdo></bdi> — האתגרים

**המסר:** האתגרים הפכו לעקרונות תכנון שניתנים להגנה.

> שני האתגרים המרכזיים היו אמון והתאוששות. כל אתגר הפך להחלטת תכנון ברורה:
>
> - הפרדתי בין <bdi dir="ltr"><code dir="ltr">Provisional</code></bdi> לבין
>   <bdi dir="ltr"><code dir="ltr">Certified</code></bdi>, כדי לא לבלבל מהירות עם אישור.
> - השתמשתי ב־<bdi dir="ltr"><code dir="ltr">Checkpoint</code></bdi>, כדי שהעיבוד הרציף
>   ימשיך מהמקום שבו נעצר.
> - השתמשתי ב־<bdi dir="ltr"><code dir="ltr">Business Keys</code></bdi>, כדי לזהות כל
>   רשומה עסקית באופן ייחודי.
> - השתמשתי ב־<bdi dir="ltr"><code dir="ltr">Upsert</code></bdi>, כדי שניסיון חוזר יעדכן
>   רשומה קיימת ולא ייצור כפילות.
> - נתונים היסטוריים עוברים דרך <bdi dir="ltr"><code dir="ltr">Kafka</code></bdi>, שכבת
>   <bdi dir="ltr"><code dir="ltr">Bronze</code></bdi> ושערי האיכות — לא נכתבים ישירות למסד.
>
> כך נשמר <bdi dir="ltr"><code dir="ltr">Lineage</code></bdi>: היכולת לעקוב מהתוצאה הסופית
> אל המקור, הריצה, גרסת הקוד וגרסת הנתונים.

### שקף <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">11</code></bdo></bdi> — המשך הדרך

**המסר:** יש מוצר עובד, אך קיימים תנאים ברורים לפני שימוש רחב יותר.

> היום קיימת מערכת מקומית מלאה עם מסלול חי, מסלול מאושר, נתונים היסטוריים
> וממשק <bdi dir="ltr"><code dir="ltr">Web</code></bdi>. לפני פתיחת מצב פעיל של
> <bdi dir="ltr"><code dir="ltr">Decision Support</code></bdi> נדרשים שלושה תנאים:
>
> - <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">20</code></bdo></bdi> ימי
>   <bdi dir="ltr"><code dir="ltr">Shadow Mode</code></bdi> אמיתיים.
> - בדיקת <bdi dir="ltr"><code dir="ltr">Calibration</code></bdi>, שמוודאת שרמת הביטחון
>   תואמת לשיעור ההצלחה שנמדד.
> - אישור אנושי מפורש.
>
> מפת ההמשך כוללת ארבעה כיוונים אפשריים:
>
> - <bdi dir="ltr"><code dir="ltr">SIP</code></bdi> — הזנת שוק מאוחדת ומלאה יותר מהזנת
>   <bdi dir="ltr"><code dir="ltr">IEX</code></bdi> החלקית שבה משתמשים כעת.
> - <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">S3</code></bdo></bdi> — חלופה עננית לתפקיד
>   שממלא כיום <bdi dir="ltr"><code dir="ltr">MinIO</code></bdi>.
> - <bdi dir="ltr"><code dir="ltr">Observability</code></bdi> — מדדים, לוגים והתראות
>   להבנת בריאות המערכת.
> - אבטחת <bdi dir="ltr"><code dir="ltr">Production</code></bdi> — הקשחה להפעלה אמיתית
>   עבור משתמשים.
>
> אלה שלבי המשך, ולא יכולות שאני טוען שכבר מימשתי.

> בנוסף יישמתי את תשתית <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">Phase 15</code></bdo></bdi>:
>
> - יצירת <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">Point-in-time features</code></bdo></bdi>.
> - יצירת <bdi dir="ltr"><code dir="ltr">Labels</code></bdi> לתוצאות התרחישים.
> - אימון והשוואת מודלים.
> - אימות כרונולוגי מסוג <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">Walk-Forward Validation</code></bdo></bdi>.
> - רישום גרסאות של קובצי המודל.
>
> כרגע אין <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">24</code></bdo></bdi> חודשי נתונים
> ואין לפחות <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">300</code></bdo></bdi> כניסות תקפות.
> לכן המערכת מסרבת לאמן או לפרסם הסתברות ועוברת למצב
> <bdi dir="ltr"><code dir="ltr">FALLBACK</code></bdi>.

### שקף <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">12</code></bdo></bdi> — מעבר לדמו

> עד עכשיו הסברתי את ההיגיון. עכשיו אראה את אותה שרשרת במערכת עצמה: נתחיל
> במסך העסקי, נעבור לאירוע ב־<bdi dir="ltr"><code dir="ltr">Kafka</code></bdi>, נראה את המקור ב־<bdi dir="ltr"><code dir="ltr">MinIO</code></bdi> ואת ריצת האישור
> ב־<bdi dir="ltr"><code dir="ltr">Airflow</code></bdi>, ונסיים בתרחיש ההחלטה ובבדיקה ההיסטורית.

---

## חלק ב: הדמו החי

### מה באמת חי בדמו

הדמו אינו סרטון ואינו אוסף צילומי מסך. כל תחנה מציגה רכיב אמיתי במערכת שרצה
באותו רגע:

- הדפדפן פונה בזמן אמת ל־<bdi dir="ltr"><code dir="ltr">Backend API</code></bdi>.
- ה־<bdi dir="ltr"><code dir="ltr">API</code></bdi> קורא נתונים אמיתיים מ־<bdi dir="ltr"><code dir="ltr">MariaDB Gold</code></bdi>.
- <bdi dir="ltr"><code dir="ltr">Kafka UI</code></bdi> מציג את יומן האירועים הפעיל.
- <bdi dir="ltr"><code dir="ltr">MinIO</code></bdi> מציג את האובייקטים שנשמרו בפועל.
- <bdi dir="ltr"><code dir="ltr">Airflow</code></bdi> מציג את הריצות והתלויות האמיתיות.

חשוב לומר זאת בצורה מדויקת: מחוץ לשעות המסחר אין בהכרח נר חדש שמגיע בכל
דקה. השירותים החיים פועלים ומחכים לנתונים חדשים; בדמו אנו משתמשים גם
בנתונים ההיסטוריים שהוזרמו ועברו את מסלול העיבוד המלא. זה עדיין דמו חי,
מפני שכל מסך נטען מהמערכת שרצה אצלך באותו רגע — לא מקובץ מצגת.

### איך לנהל את הדמו בלי להילחץ

בכל תחנה אל תנסה להסביר כל שדה. בחר דבר אחד שאפשר לראות בעיניים, הסבר למה
הוא קיים, ואז עבור הלאה. המטרה היא שהקהל יבין את הסיבה לשרשרת:

<div dir="ltr" align="left">

```text
Dashboard → Kafka → MinIO Bronze → Airflow → Opportunity Center → Backtest
```

</div>

המסלול מתחיל במה שהמשתמש רואה, יורד למקור הנתון כדי להוכיח אמינות, וחוזר
בסוף לערך העסקי. אם דף נטען לאט, המשך לדבר על מה שכבר פתוח במקום לחכות בשקט.

### תחנה <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">1</code></bdo></bdi> — המסך הראשי

**פתח:** <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">http://localhost:3000/</code></bdo></bdi>

**מה לעשות על המסך:**

1. בחר את <bdi dir="ltr"><code dir="ltr">AAPL</code></bdi> בבורר המניות.
2. לחץ על <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">7D</code></bdo></bdi>. המתן שהגרף ייטען והצבע על תגית מספר התוצאות ועל טווח התאריכים.
3. לחץ על <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">30D</code></bdo></bdi>. הצבע על כך שהטווח והגרף השתנו, ולא רק הכותרת.
4. הצבע על קו המחיר ועל הקו המקווקו של <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">SMA 20</code></bdo></bdi>
   (ממוצע פשוט של <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">20</code></bdo></bdi> מחירי הסגירה האחרונים, שמחליק תנודות קצרות). אין צורך
   לנסות לנבא מה יקרה למחיר.

**מה הקהל צריך לראות:** הנתונים אינם תמונה קבועה. החלפת הטווח יוצרת קריאה
חדשה ל־<bdi dir="ltr"><code dir="ltr">API</code></bdi>, והגרף, סטטוס הנתונים והממוצע הנע מתעדכנים בהתאם.

**מה לומר, במילים טבעיות:**

> אני מתחיל בכוונה מהמסך שהמשתמש פוגש. כאן אפשר לבחור מניה ולראות אותה גם
> בטווח קצר וגם בטווח רחב יותר. ב־<bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">7</code></bdo></bdi> ימים יש אצלנו <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">5</code></bdo></bdi> ימי מסחר ו־<bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">1,950</code></bdo></bdi> נרות
> של דקה. ב־<bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">30</code></bdo></bdi> ימים יש <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">21</code></bdo></bdi> ימי מסחר ו־<bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">8,190</code></bdo></bdi> נרות. זה נותן לי הקשר: האם מה
> שאני רואה עכשיו הוא תנועה של כמה דקות, או חלק מתמונה רחבה יותר.
>
> הקו המקווקו הוא הממוצע הנע של עשרים הסגירות האחרונות. הוא לא אומר לי
> “קנה”. הוא פשוט מוריד קצת מהרעש של כל דקה ועוזר לראות את הכיוון הכללי.

**למה זה קיים:** בלעדיו המשתמש היה רואה אוסף מחירים גולמיים, בלי דרך מהירה
להבין הקשר ומגמה. אבל זה רק קצה השרשרת; עכשיו נבדוק מאיפה הגיע אחד הנתונים.

**מעבר:** “עכשיו נרד מן הגרף אל האירוע שהגיע למערכת.”

### תחנה <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">2</code></bdo></bdi> — <bdi dir="ltr"><code dir="ltr">Kafka UI</code></bdi>

**פתח את הקישור הזה:** <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">http://localhost:8085/</code></bdo></bdi>

**המטרה בתחנה הזאת:** להראות שהנתון לא “קפץ” ישר לגרף. קודם הוא נכתב
כיומן אירועים מסודר, שאפשר לאתר בו כל הודעה.

**מה לעשות על המסך:**

1. אם מופיעה בחירת קלאסטר, בחר את <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">marketpilot-local</code></bdo></bdi>.
2. לחץ על <bdi dir="ltr"><code dir="ltr">Topics</code></bdi>.
3. פתח את <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">market.bars.1m.v1</code></bdo></bdi>.
4. לחץ על <bdi dir="ltr"><code dir="ltr">Messages</code></bdi>.
5. בחר הודעות אחרונות ולחץ על כפתור הטעינה, אם הוא מופיע.
6. פתח הודעה אחת בלבד.
7. הצבע על השדה <bdi dir="ltr"><code dir="ltr">key</code></bdi> (מפתח שמאפשר לנתב אירועים
   הקשורים לאותה ישות, למשל אותה מניה, לאותה מחיצה).
8. הצבע על השדה <bdi dir="ltr"><code dir="ltr">partition</code></bdi> (מחיצה: רצף מסודר אחד
   בתוך הנושא, שמאפשר לחלק עומס בלי לאבד סדר בתוך המחיצה).
9. הצבע על השדה <bdi dir="ltr"><code dir="ltr">offset</code></bdi> (מספר סידורי עולה שמציין
   את המיקום המדויק של ההודעה בתוך המחיצה).
10. פתח את גוף ה־<bdi dir="ltr"><code dir="ltr">JSON</code></bdi> (פורמט טקסט מובנה של שמות
    שדות וערכים) והצבע על שם המניה ועל זמן האירוע.

**אם אינך רואה הודעה:**

1. פתח את <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">market.bars.1m.backfill.v1</code></bdo></bdi>.
2. אמור: “זהו הנושא של הנתונים ההיסטוריים שהזרמתי לצורך השלמת ההיסטוריה.”
3. אל תציג את ההודעה כאילו היא הגיעה עכשיו מהשוק.

**מה הקהל צריך לראות:** לפני שהנתון הופך לשורה במסד או לנקודה בגרף, הוא
מופיע כאירוע עצמאי עם כתובת מדויקת בתוך יומן האירועים.

**מה לומר, במילים טבעיות:**

> כאן הנתון נכנס למערכת בפעם הראשונה. שכבת ההודעות אינה המסד שממנו
> הדשבורד קורא. היא יומן מסודר של הודעות.
>
> לכל הודעה יש מחיצה ומספר מיקום. אני אוהב לחשוב עליהם כמו על מדף ומספר
> סידורי. לכן אפשר
> לאתר את אותה הודעה גם אחרי זמן רב.
>
> מכאן שני רכיבים קוראים את אותו אירוע בלי להפריע זה לזה: מסלול אחד מעבד
> אותו מהר עבור המערכת החיה, ומסלול שני שומר עותק גולמי. זה בדיוק מה שנותן
> לנו גם מהירות וגם אפשרות לחזור אחורה במקרה של תקלה.

**למה זה קיים:** בלי שכבת האירועים, היצרן היה תלוי ישירות במסד הנתונים או
בכל שירות צרכן. תקלה בצרכן אחד הייתה עלולה לגרום לאובדן מידע. כאן אפשר
להפריד אחריות וגם לחזור לאירוע בעת עיבוד מחדש.

**מעבר:** “עכשיו אראה את העותק הגולמי שנשמר עבור ביקורת ושחזור.”

### תחנה <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">3</code></bdo></bdi> — <bdi dir="ltr"><code dir="ltr">MinIO Bronze</code></bdi>

**פתח:** <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">http://localhost:9001/</code></bdo></bdi>

**מה לעשות על המסך — בדיוק לפי הסדר:**

1. במסך הבית לחץ על ה־<bdi dir="ltr"><code dir="ltr">Bucket</code></bdi> (מכל לוגי לאובייקטים,
   בדומה לתיקייה ראשית בענן) בשם <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">marketpilot-bronze</code></bdo></bdi>.
2. לחץ על התיקייה <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">source=alpaca</code></bdo></bdi>. המשמעות: מקור האירוע הוא ספק נתוני השוק <bdi dir="ltr"><code dir="ltr">Alpaca</code></bdi>.
3. פתח <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">event=market_bar_1m</code></bdo></bdi>. זהו אירוע של נר שוק באורך דקה.
4. המשך בנתיב התאריך: <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">year=... / month=... / day=...</code></bdo></bdi>.
5. פתח מניה, למשל <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">symbol=AAPL</code></bdo></bdi>, ואז <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">topic=market.bars.1m.v1</code></bdo></bdi>.
6. פתח <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">partition=0</code></bdo></bdi>, ואז קובץ אחד שמתחיל ב־<bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">offset=</code></bdo></bdi> ומסתיים ב־<bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">.json</code></bdo></bdi>.
7. בתוך הקובץ הצבע רק על השדות הבאים:
   - <bdi dir="ltr"><code dir="ltr">symbol</code></bdi> — סימול המניה.
   - <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">event_time_utc</code></bdo></bdi> — המועד שבו הנר התרחש בשוק לפי שעון עולמי.
   - <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">open/high/low/close</code></bdo></bdi> — מחירי הפתיחה, הגבוה, הנמוך והסגירה.
   - <bdi dir="ltr"><code dir="ltr">volume</code></bdi> — כמות המניות שנסחרה.
   - <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">ingested_at_utc</code></bdo></bdi> — המועד שבו המערכת קלטה את האירוע.
   - <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">schema_version</code></bdo></bdi> — גרסת מבנה הנתונים, שמאפשרת לשנות את החוזה באופן מבוקר.

אם הגעת לנתון היסטורי, ייתכן שתראה שם אירוע או נושא של <bdi dir="ltr"><code dir="ltr">Backfill</code></bdi>
(טעינה תחומה של נתוני עבר כדי להשלים תקופה חסרה). זה בסדר:
הסבר שמדובר בנתונים שהשלמנו לצורך ההיסטוריה והבדיקה; אל תציג אותם כאילו הם
נקלטו ברגע זה.

**מה הקהל צריך לראות:** הן הנתיב והן תוכן הקובץ מתעדים את מקור הנתון. אפשר
לראות לאיזו מניה הוא שייך, מתי קרה בשוק, מתי נקלט במערכת, ובאיזה מבנה נתונים.

**מה לומר, במילים טבעיות:**

> זה החלק שחשוב לי במיוחד מבחינת אמון. זה לא עוד גרף ולא עוד טבלה. זה העותק
> הגולמי שנשמר לפני העיבוד המאושר. הנתיב עצמו מספר סיפור: הנתון הגיע מספק
> נתוני השוק,
> הוא נר של דקה, הוא שייך לתאריך ולמניה מסוימים, והוא נכתב מתוך נושא ומיקום
> מוגדרים ביומן האירועים.
>
> בתוך הקובץ אני רואה שני זמנים שונים: זמן האירוע הוא הזמן שבו הוא קרה
> בשוק; זמן הקליטה הוא הזמן שבו המערכת שמרה אותו. ההבחנה הזו מאפשרת לי לבדוק
> גם טריות ולא רק מחיר. גרסת החוזה אומרת באיזה מבנה נתונים השתמשנו, כדי
> ששינוי עתידי במבנה לא ישבור את העיבוד בשקט.

**למה זה קיים:** אם תתגלה תקלה בקוד או שתרצה לבדוק מחדש מסקנה, יש לך מקור
שאפשר לחזור אליו. לא צריך לסמוך רק על השורה המעובדת שכבר נמצאת ב־<bdi dir="ltr"><code dir="ltr">Gold</code></bdi>.
זה גם מאפשר <bdi dir="ltr"><code dir="ltr">Replay</code></bdi>: להריץ שוב את אותו מידע גולמי דרך גרסה חדשה של הלוגיקה.

**מעבר:** “העותק נשמר; עכשיו נראה מי מנהל את העיבוד המאושר שלו.”

### תחנה <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">4</code></bdo></bdi> — <bdi dir="ltr"><code dir="ltr">Airflow</code></bdi>

**פתח:** <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">http://localhost:8080/</code></bdo></bdi>

**מה לעשות על המסך:**

1. פתח את רשימת ה־<bdi dir="ltr"><code dir="ltr">DAGs</code></bdi> (תהליכים שמוגדרים
   כמשימות עם סדר ותלויות; משימה מאוחרת אינה מתחילה לפני שקודמתה הצליחה).
2. בחר את ריצת התיקון הירוקה <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">repair__2026-09-16__20260917</code></bdo></bdi> של <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">historical_market_backfill</code></bdo></bdi>.
   אל תבחר את הריצה האחרונה באופן אוטומטי; בדוק קודם שהסטטוס שלה ירוק.
3. פתח את תצוגת <bdi dir="ltr"><code dir="ltr">Grid</code></bdi> (טבלת ריצות ומשימות) או
   <bdi dir="ltr"><code dir="ltr">Graph</code></bdi> (תרשים התלויות) והצבע על סדר המשימות הירוקות.
4. אל תלחץ על <bdi dir="ltr"><code dir="ltr">Trigger DAG</code></bdi> מול הקהל. ריצה מוצלחת קיימת היא הראיה הבטוחה יותר.

**מה הקהל צריך לראות:** העבודה המאושרת אינה כפתור קסם. יש לה שלבים, תלויות
ותוצאת הצלחה או כישלון שניתן לבדוק.

**מה לומר, במילים טבעיות:**

> מנהל התזמור הוא מנהל העבודה של התהליכים שמתחילים ומסתיימים. כאן רואים בדיוק
> מה קרה ובאיזה סדר: מעבדים את המקור הגולמי לשכבה נקייה, בודקים איכות,
> מפרסמים לשכבת ההגשה ורק אחר כך ממשיכים לחישובי הניתוח. ריצת התיקון המוצגת
> רכשה מחדש את <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">16</code></bdo></bdi> בספטמבר, העבירה <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">11</code></bdo></bdi> סימולים דרך שער הכיסוי ופרסמה אותם כ־<bdi dir="ltr"><code dir="ltr">CERTIFIED</code></bdi>.
>
> חשוב להדגיש מה מנהל התזמור לא עושה: הוא לא מפעיל את שירות ההודעות, לא
> מפעיל את העיבוד הרציף ולא מנהל את חיי הדשבורד. אלה שירותים ארוכי־חיים.
> את ההפעלה שלהם מנהל <bdi dir="ltr"><code dir="ltr">Docker Compose</code></bdi>. ההפרדה הזאת מונעת מצב שבו תזמון
> של עבודת אצווה עוצר בטעות את המסלול החי.

**למה זה קיים:** בלי תזמור, קשה לדעת אם כל השלבים רצו לפי הסדר ואם נתון עבר
בדיקות איכות לפני שפורסם. <bdi dir="ltr"><code dir="ltr">Airflow</code></bdi> נותן היסטוריית ריצות, סטטוס ותלויות.

**מעבר:** “אחרי שהנתונים עברו מסלול מבוקר, אפשר לתת להם ערך למשתמש.”

### תחנה <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">5</code></bdo></bdi> — <bdi dir="ltr"><code dir="ltr">Opportunity Center</code></bdi>

**פתח:** <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">http://localhost:3000/opportunities.html</code></bdo></bdi>

**מה לעשות על המסך:**

1. ודא שמופיעים <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">11</code></bdo></bdi> סימולים ברשימת המעקב.
2. בחר את <bdi dir="ltr"><code dir="ltr">META</code></bdi> והראה תרחיש <bdi dir="ltr"><code dir="ltr">BUY ZONE</code></bdi>.
3. עבור אל <bdi dir="ltr"><code dir="ltr">AAPL</code></bdi> והראה מדוע מחיר מעל טווח הכניסה הופך את הפעולה ל־<bdi dir="ltr"><code dir="ltr">WATCH BREAKOUT</code></bdi> ולא ל־<bdi dir="ltr"><code dir="ltr">BUY</code></bdi> עיוור.
4. בחר סימול שמציג <bdi dir="ltr"><code dir="ltr">INSUFFICIENT DATA</code></bdi> (אין מספיק
   נתונים טריים ומאושרים כדי לחשב תרחיש אמין) והסבר מדוע עצירת מסקנה היא תוצאה תקינה.
5. הצבע על הסטטוס שמופיע בפועל:
   - <bdi dir="ltr"><code dir="ltr">PROVISIONAL</code></bdi> — תוצאה חיה וזמנית.
   - <bdi dir="ltr"><code dir="ltr">CERTIFIED</code></bdi> — תוצאה שנבנתה מחדש ועברה בדיקות.
   - <bdi dir="ltr"><code dir="ltr">STALE</code></bdi> — הנתון קיים אך עבר את מגבלת הטריות.
   - <bdi dir="ltr"><code dir="ltr">INSUFFICIENT DATA</code></bdi> — אין בסיס נתונים מספק לתרחיש.
6. עבור על כרטיס התרחיש לפי הסדר:
   - <bdi dir="ltr"><code dir="ltr">Buy Zone</code></bdi> — טווח הכניסה.
   - <bdi dir="ltr"><code dir="ltr">Stop</code></bdi> — נקודת ביטול התזה.
   - <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">Target 1</code></bdo></bdi> — היעד הראשון.
   - <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">Target 2</code></bdo></bdi> — היעד השני.
   - <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">Risk/Reward</code></bdo></bdi> — היחס בין הסיכון לרווח המתוכנן.
   - גודל הפוזיציה — הכמות שמתאימה למגבלות התיק.
7. הצבע על שלושת המדדים הנפרדים:
   - <bdi dir="ltr"><code dir="ltr">Rule Score</code></bdi> — חוזק התרחיש לפי הכללים.
   - <bdi dir="ltr"><code dir="ltr">Model Probability</code></bdi> — הסתברות מודל, רק לאחר אימון ואישור.
   - <bdi dir="ltr"><code dir="ltr">Data Confidence</code></bdi> — איכות, כיסוי וטריות הנתונים.
8. פתח את ההסבר בעברית, ובחר סיבה אחת טכנית וסיבה אחת פונדמנטלית בלבד.

**מה הקהל צריך לראות:** המוצר לא זורק “קנה” עם מספר אחד. הוא מראה תרחיש,
הנחות, סיכון, תנאי ביטול וסטטוס אמינות.

**מה לומר, במילים טבעיות:**

> כאן הנתונים הופכים לכלי עזר להחלטה. אני לא מציג מחיר יעד קסום, כי אין דבר
> כזה. במקום זה יש טווח כניסה, נקודה שבה הרעיון כבר לא תקף, ושני יעדים אפשריים.
> יחס הסיכון־סיכוי וגודל הפוזיציה מחזירים את השיחה לניהול סיכון ולא רק לפוטנציאל
> רווח.
>
> חשוב גם מה שהמערכת לא עושה: היא לא מבצעת פקודת קנייה. היא נמצאת במצב
> צל, כלומר אוספת ומודדת את איכות התרחישים לפני שמציגים אותם כהמלצה מעשית. האדם
> נשאר מקבל ההחלטה.
>
> נכון לבדיקת ההכנה יש <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">76</code></bdo></bdi> ימי מסחר היסטוריים מאושרים, אך מונה הצל של
> <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">v1</code></bdo></bdi> הוא <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">2/20</code></bdo></bdi>.
> ההיסטוריה אינה נספרת כזמן חי. המונה עולה רק
> אחרי יום מסחר אמיתי שבו כל ריצת האישור היומית הסתיימה בהצלחה. אם הריצה
> נכשלת, היום אינו נספר — זו התנהגות בטוחה ומכוונת.
>
> מודל <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">v2</code></bdo></bdi> מוצג כ־<bdi dir="ltr"><code dir="ltr">FALLBACK</code></bdi>
> מפני שאין עדיין בסיס אימון שעומד בדרישות. כללי <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">v1</code></bdo></bdi>
> עדיין מחשבים את הטווחים והסיכון, אבל השדות <bdi dir="ltr"><code dir="ltr">Model Probability</code></bdi>
> ו־<bdi dir="ltr"><code dir="ltr">Expected R</code></bdi> נשארים ריקים. כך המערכת אינה הופכת
> ציון איכות להבטחת הצלחה.

**למה זה קיים:** זה מחבר בין המידע ההנדסי לבין פעולה אחראית. אם אין מספיק
נתונים או שהמידע ישן, המערכת אמורה לומר “להמתין” ולא להעמיד פנים שהיא יודעת.

**מעבר:** “ולפני שסומכים על רעיון כזה, צריך לבדוק איך הוא התנהג בעבר.”

### תחנה <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">6</code></bdo></bdi> — <bdi dir="ltr"><code dir="ltr">Backtesting Lab</code></bdi>

**פתח:** <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">http://localhost:3000/backtesting.html</code></bdo></bdi>

**מה לעשות על המסך:**

1. בחר ריצה במצב <bdi dir="ltr"><code dir="ltr">Published</code></bdi> שמכסה כמה שבועות. העדף את הריצה הארוכה ביותר שמופיעה במסך; מזהה הריצה עשוי להשתנות.
2. ודא שהמסך מציג את טווח הנתונים, מספר התצפיות ואת עקומת ההון (שינוי הערך
   המצטבר של האסטרטגיה לאורך הניסוי).
3. הצבע על מדדי התוצאה ועל ההשוואה ל־<bdi dir="ltr"><code dir="ltr">SPY</code></bdi>
   (מדד הייחוס שבודק אם האסטרטגיה הוסיפה ערך לעומת השוק הרחב).
4. אם יש פירוט אסטרטגיה או עלויות, הצבע עליו ואמור שהן נכללות בניסוי ולא הוסתרו.

**מה הקהל צריך לראות:** זו ריצה מתועדת שאפשר לחזור עליה: יש קלטים, גרסה,
מדדים, עקומה והשוואה למדד ייחוס.

**מה לומר, במילים טבעיות:**

> זה לא גרף שמוכיח שאפשר להרוויח. זה ניסוי היסטורי שנועד להעמיד את הרעיון
> למבחן. אות שנוצר בנר מסוים מופעל רק מהנר הבא, כדי לא להשתמש בעתיד בלי לשים
> לב. התוצאה כוללת עלויות והחלקה במחיר, ואנחנו משווים אותה למדד השוק הרחב, כדי שלא
> נתרשם מתוצאה שנובעת רק מעלייה כללית של השוק.
>
> מבחינתי גם תוצאה חלשה היא מידע חשוב. היא אומרת לי לא לקדם רעיון לפני שהוא
> הוכיח שהוא מחזיק מים בתנאים הוגנים.

**למה זה קיים:** בלי בדיקה כזו קל מאוד לראות דפוס יפה בגרף ולהאמין שהוא
אסטרטגיה. הבדיקה מכריחה אותנו לשמור גרסה, קלטים, עלויות ומדדי השוואה.

### משפט הסיום

> המערכת מחברת בין מהירות לאמון. היא מתחילה באירוע גולמי, שומרת אותו,
> בודקת ומאשרת אותו, ומציגה למשתמש תרחיש שאפשר להסביר ולשחזר.
>
> מבחינתי, זה ההבדל בין גרף מעניין לבין מוצר הנדסת נתונים שאפשר לסמוך עליו.

## אם משהו לא עובד

- אם המסך הראשי אינו זמין, הצג את צילום המסך בשקף <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">7</code></bdo></bdi>.
- אם <bdi dir="ltr"><code dir="ltr">Kafka UI</code></bdi> אינו זמין, עבור לאובייקט <bdi dir="ltr"><code dir="ltr">Bronze</code></bdi> והסבר שהנתיב מכיל את מיקום ההודעה.
- אם <bdi dir="ltr"><code dir="ltr">MinIO</code></bdi> אינו זמין, הצג את שקף <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">4</code></bdo></bdi> ואת צילום המסך המוכן.
- אם <bdi dir="ltr"><code dir="ltr">Airflow</code></bdi> אינו זמין, הצג את מסמך האימות ואת סדר המשימות בשקף.
- אם הנתון החי ישן, אמור זאת בכנות. שירות בריא ונתון טרי הן שתי בדיקות שונות.
- אל תתחיל תיקון ארוך מול הקהל. עבור לראיה החלופית והמשך לדבר.

## מילון מושגים שכדאי לדעת לפני ההצגה

אין צורך להקריא את החלק הזה בדמו. הוא נועד כדי שתוכל לענות בביטחון אם הסוקר
עוצר ושואל מה משמעותו של מושג שמופיע במסך או במצגת.

<h3 dir="ltr" align="left"><bdi dir="ltr"><code dir="ltr">IEX</code> vs. <code dir="ltr">SIP</code></bdi></h3>

הזנת <bdi dir="ltr"><code dir="ltr">IEX</code></bdi> מבוססת על בורסה אמריקאית אחת. בחבילת
הנתונים החינמית של <bdi dir="ltr"><code dir="ltr">Alpaca</code></bdi> היא מציגה רק חלק
מהעסקאות בשוק.

לעומתה, מנגנון <bdi dir="ltr"><code dir="ltr">SIP</code></bdi> מאחד רשמית את נתוני הבורסות
האמריקאיות. הוא מרכז עסקאות וציטוטי קנייה ומכירה מכל זירות המסחר המשתתפות,
ולכן הוא מלא יותר — אך בדרך כלל דורש הרשאה או תשלום. בפרויקט הנוכחי הנתונים
החיים נשארים ב־<bdi dir="ltr"><code dir="ltr">IEX</code></bdi>, והמערכת מורידה את רמת הביטחון בהתאם.

<h3 dir="ltr" align="left"><bdi dir="ltr"><code dir="ltr">Bronze</code> · <code dir="ltr">Silver</code> · <code dir="ltr">Gold</code></bdi></h3>

שכבת <bdi dir="ltr"><code dir="ltr">Bronze</code></bdi> היא העותק הגולמי שנשמר כפי שהתקבל.

שכבת <bdi dir="ltr"><code dir="ltr">Silver</code></bdi> מכילה מידע שנוקה, נורמל ואורגן למבנה אחיד.

שכבת <bdi dir="ltr"><code dir="ltr">Gold</code></bdi> מכילה מידע מוכן לצריכה עסקית, למשל גרף,
אינדיקטור או תרחיש החלטה. ההפרדה בין השכבות מאפשרת לחזור למקור גם אם בעתיד
נשנה את לוגיקת העיבוד.

<h3 dir="ltr" align="left"><bdi dir="ltr"><code dir="ltr">Streaming</code> vs. <code dir="ltr">Batch</code></bdi></h3>

עיבוד <bdi dir="ltr"><code dir="ltr">Streaming</code></bdi> פועל כשירות ארוך־חיים שמחכה לאירועים
ומעבד אותם ברצף כדי לתת תוצאה מהירה.

עבודת <bdi dir="ltr"><code dir="ltr">Batch</code></bdi> מתחילה, מעבדת טווח ידוע ומסתיימת,
למשל יום מסחר שלם. המסלול החי נותן מהירות; המסלול האצוותי בונה מחדש את התוצאה
ומוסיף בדיקות איכות סמכותיות.

<h3 dir="ltr" align="left"><bdi dir="ltr"><code dir="ltr">Provisional</code> vs. <code dir="ltr">Certified</code></bdi></h3>

סטטוס <bdi dir="ltr"><code dir="ltr">Provisional</code></bdi> פירושו “מהיר אך זמני”: התוצאה זמינה
למשתמש, אך עוד לא עברה את כל בדיקות סוף היום.

סטטוס <bdi dir="ltr"><code dir="ltr">Certified</code></bdi> פירושו “מאושר”: התוצאה חושבה מחדש
מהמקור הגולמי ועברה את שערי האיכות. זהו לא הבדל עיצובי, אלא הבטחה שונה לגבי
רמת האמון בנתון.

<h3 dir="ltr" align="left"><bdi dir="ltr"><code dir="ltr">Backfill</code> / <code dir="ltr">Replay</code></bdi></h3>

תהליך <bdi dir="ltr"><code dir="ltr">Backfill</code></bdi> מביא באופן יזום נתוני עבר לתקופה חסרה.

פעולת <bdi dir="ltr"><code dir="ltr">Replay</code></bdi> מעבדת מחדש אירועים שכבר נשמרו.
בפרויקט הנתונים ההיסטוריים אינם “נשתלים” ישירות במסד: הם עוברים דרך אותו
מסלול אירועים, אחסון ובדיקות, כדי לשמור על התנהגות ועל עקיבות זהות לנתונים החיים.

<h3 dir="ltr" align="left"><bdi dir="ltr"><code dir="ltr">Checkpoint</code></bdi></h3>

מצב שמאפשר ל־<bdi dir="ltr"><code dir="ltr">Streaming</code></bdi> להמשיך מהמקום שבו נעצר
לאחר הפעלה מחדש. הוא שומר התקדמות ומיקומי קריאה. מחיקה שלו ללא תוכנית
<bdi dir="ltr"><code dir="ltr">Replay</code></bdi> עלולה ליצור עיבוד חוזר או אובדן מצב.

<h3 dir="ltr" align="left"><bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">SMA 20</code></bdo></bdi></h3>

ממוצע נע פשוט של <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">20</code></bdo></bdi> נרות. בכל נקודה מחברים את
<bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">20</code></bdo></bdi> מחירי הסגירה האחרונים ומחלקים ב־<bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">20</code></bdo></bdi>.
הוא מחליק רעש ועוזר לראות כיוון, אך מפגר אחרי המחיר ואינו אות קנייה בפני עצמו.

<h3 dir="ltr" align="left"><bdi dir="ltr"><code dir="ltr">EMA</code> · <code dir="ltr">RSI</code> · <code dir="ltr">MACD</code> · <code dir="ltr">ATR</code></bdi></h3>

מדד <bdi dir="ltr"><code dir="ltr">EMA</code></bdi> (ממוצע נע מעריכי) דומה לממוצע נע, אך נותן
משקל גבוה יותר למחירים האחרונים ולכן מגיב מהר יותר לשינוי.

מדד <bdi dir="ltr"><code dir="ltr">RSI</code></bdi> (מדד עוצמה יחסית) מודד מומנטום בסולם
<bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">0–100</code></bdo></bdi>. ערך קיצוני הוא סימן לבדיקה, לא פקודת קנייה
או מכירה אוטומטית.

מדד <bdi dir="ltr"><code dir="ltr">MACD</code></bdi> (מדד מגמה ומומנטום המבוסס על הפער בין שני
ממוצעים מעריכיים) עוזר לזהות שינוי בעוצמת המגמה.

מדד <bdi dir="ltr"><code dir="ltr">ATR</code></bdi> (טווח אמיתי ממוצע) מודד תנודתיות — כמה המחיר
נע בדרך כלל — ולא את כיוון התנועה. המערכת נעזרת בו כדי להתאים מרחקי עצירה
ויעדים לתנודתיות של כל מניה.

<h3 dir="ltr" align="left"><bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">Risk/Reward</code></bdo></bdi></h3>

היחס בין הרווח המתוכנן לבין ההפסד המתוכנן. לדוגמה, אם הסיכון עד מחיר העצירה
הוא <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">10</code></bdo></bdi> שקלים והיעד מציע <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">20</code></bdo></bdi>
שקלים, היחס הוא <bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">2:1</code></bdo></bdi>. היחס אינו חוזה שהיעד יושג;
הוא מאפשר לבדוק מראש אם פוטנציאל התרחיש מצדיק את הסיכון שלו.

<h3 dir="ltr" align="left"><bdi dir="ltr"><code dir="ltr">Lineage</code></bdi></h3>

עקיבות מלאה של הנתון: מאיזה מקור ואירוע הגיע, איזו ריצה עיבדה אותו, באיזו
גרסת קוד ובאיזו גרסת נתונים. כך אפשר להסביר תוצאה, לשחזר אותה ולברר תקלה בלי לנחש.

<h3 dir="ltr" align="left"><bdi dir="ltr"><code dir="ltr">Freshness</code></bdi></h3>

מדד לגיל הנתון ביחס לזמן שבו ציפינו לקבלו. שירות יכול להיות בריא ועדיין
להציג נתון ישן, למשל כאשר השוק סגור או כשהמקור הפסיק לשלוח מידע. לכן המערכת
בודקת בנפרד זמינות שירותים וטריות נתונים.

<h3 dir="ltr" align="left"><bdi dir="ltr"><code dir="ltr">Slippage</code> · <code dir="ltr">Drawdown</code> · <code dir="ltr">Benchmark</code></bdi></h3>

המונח <bdi dir="ltr"><code dir="ltr">Slippage</code></bdi> מתאר את ההפרש בין מחיר הביצוע שתוכנן לבין
המחיר שבו היה אפשר לבצע בפועל. מוסיפים אותו לבדיקה כדי לא להציג תוצאה אופטימית מדי.

המדד <bdi dir="ltr"><code dir="ltr">Drawdown</code></bdi> מתאר את שיעור הירידה משיא מקומי לשפל שבא
אחריו. הוא עוזר להבין כמה כאב וסיכון היו בדרך, גם אם התשואה הסופית חיובית.

המונח <bdi dir="ltr"><code dir="ltr">Benchmark</code></bdi> מציין מדד ייחוס. בפרויקט זהו
<bdi dir="ltr"><code dir="ltr">SPY</code></bdi>, כדי להשוות את האסטרטגיה לחלופה פשוטה של
חשיפה לשוק הרחב.

<h3 dir="ltr" align="left"><bdi dir="ltr"><code dir="ltr">Idempotency</code></bdi></h3>

היכולת להריץ פעולה שוב בלי ליצור תוצאה עסקית כפולה. ב־<bdi dir="ltr"><code dir="ltr">MarketPilot</code></bdi>
משתמשים במפתחות עסקיים, מזהים דטרמיניסטיים ו־<bdi dir="ltr"><code dir="ltr">Upsert</code></bdi>.
המטרה אינה למנוע כל <bdi dir="ltr"><code dir="ltr">Retry</code></bdi>, אלא להפוך אותו לבטוח.

<h3 dir="ltr" align="left"><bdi dir="ltr"><code dir="ltr">Calibration</code></bdi></h3>

בדיקה האם ציון הביטחון של המערכת מתאים למה שקרה בפועל. אם תרחישים עם
<bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">80%</code></bdo></bdi> ביטחון מצליחים רק בחצי מהמקרים, הציון אינו
מכויל היטב. זו אחת הסיבות לתקופת הצל: קודם אוספים מספיק תוצאות אמיתיות,
ורק אחר כך מחליטים אם אפשר להציג את התרחישים כתמיכה פעילה בהחלטה.

<h3 dir="ltr" align="left"><bdi dir="ltr"><code dir="ltr">Rule Score</code> · <code dir="ltr">Model Probability</code> · <code dir="ltr">Data Confidence</code></bdi></h3>

ציון <bdi dir="ltr"><code dir="ltr">Rule Score</code></bdi> מסכם באופן שקוף את הראיות
הטכניות והפונדמנטליות לפי נוסחה קבועה.

השדה <bdi dir="ltr"><code dir="ltr">Model Probability</code></bdi> מציג הסתברות מכוילת להגיע ליעד
הראשון לפני מחיר העצירה. היא מוצגת רק כאשר קיים מודל מאומן שעבר בדיקות מחוץ למדגם.

ציון <bdi dir="ltr"><code dir="ltr">Data Confidence</code></bdi> מתאר את איכות המקור, הכיסוי
והטריות. הוא אינו סיכוי לרווח.

<h3 dir="ltr" align="left"><bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">Walk-Forward Validation</code></bdo></bdi></h3>

בדיקה כרונולוגית שבה מאמנים רק על העבר ובודקים על תקופה מאוחרת יותר. לאחר
כל חלון מזיזים את נקודת הזמן קדימה. כך מדמים שימוש אמיתי ונמנעים מערבוב
אקראי שמאפשר למודל ללמוד מידע מהעתיד.

<h3 dir="ltr" align="left"><bdi dir="ltr"><code dir="ltr">FALLBACK</code></bdi></h3>

מצב בטוח שבו שכבת המודל אינה זמינה או טרם הוכחה, ולכן המערכת חוזרת לכללי
<bdi dir="ltr"><bdo dir="ltr"><code dir="ltr">v1</code></bdo></bdi> השקופים. במקרה זה לא מוצגת הסתברות ישנה או
מומצאת. זהו מנגנון הגנה מתוכנן, לא תקלה שמנסים להסתיר.

## המשפט לזכור אם אינך יודע תשובה

> אני לא רוצה להמציא. אסביר מה מימשתי ומה בדקתי, ואת הפרט המדויק אוכל לאמת
> במסמך או בקוד.

</div>
