<div dir="rtl" align="right">

# <bdi dir="ltr"><code>MarketPilot</code></bdi> — חזרות ותרחישי תקלה

## תכנית חזרות

### חזרה 1 - הבנה ללא מסכים

- הסבר בקול את <bdi dir="ltr">Live</bdi>, <bdi dir="ltr">Raw</bdi>, <bdi dir="ltr">Certified</bdi>, <bdi dir="ltr">Historical</bdi> ו־<bdi dir="ltr">SEC</bdi> ללא פתיחת מחשב.
- הגדר <bdi dir="ltr">Kafka</bdi>, <bdi dir="ltr">Spark</bdi>, <bdi dir="ltr">Airflow</bdi>, <bdi dir="ltr">Bronze</bdi>, <bdi dir="ltr">Gold</bdi> ו־<bdi dir="ltr">idempotency</bdi> במשפט אחד כל אחד.
- אם נתקעת, חזור לחוברת המסביר; אל תשנן את תסריט הלחיצות.

### חזרה 2 - מסלול איטי

- בצע את כל המסלול בלי טיימר.
- רשום לכל מעבר את ה־<bdi dir="ltr">URL</bdi>, האובייקט או ה־<bdi dir="ltr">DAG</bdi> המדויק.
- ודא שאינך מחפש נתון מול הקהל.

### חזרה 3 - 15 דקות מוקלטות

- הפעל טיימר והקלט מסך וקול.
- מטרה ראשונה: 14:15 עד 15:45.
- סמן משפטים ארוכים, מסכים מיותרים ומונחים שלא הסברת.

### חזרה 4 - תקלה מכוונת

- סגור מראש <bdi dir="ltr">UI</bdi> אחד שאינו קריטי.
- המשך באמצעות <bdi dir="ltr">verification file</bdi> או <bdi dir="ltr">Project Story</bdi>.
- אמור בקול: "זהו <bdi dir="ltr">snapshot</bdi> מתוארך; איני מציג אותו כמצב חי."

### חזרה 5 - שאלות

- בקש ממישהו לשאול עשר שאלות מ־<bdi dir="ltr"><bdo dir="ltr"><code>qa-bank.md</code></bdo></bdi> בסדר אקראי.
- תשובה ישירה צריכה להתחיל בתוך חמש שניות.
- אם אינך יודע: ציין מה ידוע, מה לא נמדד ואיך היית בודק.

## תנאי מוכנות

- שתי ריצות רצופות של 15 דקות בטווח של 45 שניות.
- חמשת המסלולים מוסברים ללא הערות.
- עשר שאלות החובה נענות ישירות.
- מעבר ל־<bdi dir="ltr">fallback</bdi> אחד בלי לחץ ובלי שינוי נתונים.
- שלוש מגבלות נאמרות יחד עם דרך ההרחבה שלהן.
- משפט פתיחה ומשפט סיום נאמרים באופן טבעי.

## בדיקה מקדימה (<bdi dir="ltr">Preflight</bdi>) ביום ההצגה

### טכני

- [ ] מחשב מחובר לחשמל ומצב שינה מבוטל.
- [ ] <bdi dir="ltr"><code>docker compose ps</code></bdi> מציג את השירותים הנדרשים כבריאים.
- [ ] <bdi dir="ltr">Project Story</bdi>, <bdi dir="ltr">Presenter Console</bdi>, <bdi dir="ltr">Dashboard</bdi>, <bdi dir="ltr">Opportunity Center</bdi> ו־<bdi dir="ltr">Backtesting Lab</bdi> מחזירים <bdi dir="ltr">HTTP 200</bdi>.
- [ ] <bdi dir="ltr">Opportunity Center</bdi> מציג בנפרד <bdi dir="ltr">Historical Evidence</bdi> ו־<bdi dir="ltr">Live Shadow Mode</bdi>.
- [ ] ברשימת המעקב מופיעים 11 סימולים; <bdi dir="ltr"><code>META</code></bdi> ו־<bdi dir="ltr"><code>AAPL</code></bdi> נבדקו מראש.
- [ ] מונה <bdi dir="ltr"><code>Shadow Mode</code></bdi> נקרא מהמסך בזמן אמת; אין לשנן מספר ישן.
- [ ] שני <bdi dir="ltr"><code>Kafka Topics</code></bdi>, אובייקט <bdi dir="ltr"><code>Bronze</code></bdi> וריצת <bdi dir="ltr"><code>Airflow</code></bdi> ירוקה פתוחים מראש.
- [ ] <bdi dir="ltr"><code>Backtesting Lab</code></bdi> מציג ריצה במצב <bdi dir="ltr"><code>Published</code></bdi>, טווח של כמה שבועות ו־<bdi dir="ltr"><code>Lineage</code></bdi> מלא.
- [ ] <bdi dir="ltr"><code>Opportunity Center</code></bdi> מציג <bdi dir="ltr"><bdo dir="ltr"><code>76 sessions</code></bdo></bdi>, <bdi dir="ltr"><bdo dir="ltr"><code>2/20</code></bdo></bdi> ו־<bdi dir="ltr"><code>RULES ACTIVE · MODEL FALLBACK</code></bdi>.
- [ ] ריצת <bdi dir="ltr"><bdo dir="ltr"><code>repair__2026-09-16__20260917</code></bdo></bdi> ב־<bdi dir="ltr"><code>Airflow</code></bdi> ירוקה.
- [ ] זום הדפדפן ו־<bdi dir="ltr">resolution</bdi> מאפשרים קריאה מרחוק.
- [ ] התראות, <bdi dir="ltr">Teams</bdi>, <bdi dir="ltr">WhatsApp</bdi> ודואר מושתקים.

### אבטחה

- [ ] <bdi dir="ltr"><bdo dir="ltr"><code>.env</code></bdo></bdi> וטרמינלים עם סודות סגורים.
- [ ] <bdi dir="ltr">Adminer</bdi> אינו שומר סיסמה גלויה.
- [ ] אין <bdi dir="ltr">clipboard</bdi> עם <bdi dir="ltr">API keys</bdi>.
- [ ] אין כוונה להריץ <bdi dir="ltr">UPDATE</bdi>, <bdi dir="ltr">purge</bdi> או <bdi dir="ltr">credential rotation</bdi>.

### הצגה

- [ ] מצב 15 דקות נבחר ב־<bdi dir="ltr">Presenter Console</bdi>.
- [ ] טיימר מאופס.
- [ ] משפט הפתיחה והסיום נמצאים בכרטיס הראשון והאחרון.
- [ ] מסמך הארכיטקטורה ו־<bdi dir="ltr"><bdo dir="ltr"><code>docs/phase12-verification.md</code></bdo></bdi> זמינים כגיבוי.

## תרחישי תקלה ודרך התאוששות

### <bdi dir="ltr">Dashboard</bdi> אינו עולה

1. אל תתחיל <bdi dir="ltr">debugging</bdi> ממושך מול הקהל.
2. הראה את <bdi dir="ltr">Project Story</bdi> ואת <bdi dir="ltr">Phase 7/9 verification</bdi>.
3. הסבר את גבול <bdi dir="ltr">Browser</bdi> -> <bdi dir="ltr">API</bdi> -> <bdi dir="ltr">MariaDB</bdi>.
4. אם יש זמן, בדוק לאחר מכן <bdi dir="ltr"><bdo dir="ltr"><code>docker compose ps web-app backend-api mariadb</code></bdo></bdi>.

### אין נתונים בטווח

1. עבור ל־<bdi dir="ltr"><bdo dir="ltr"><code>7D</code></bdo></bdi> או <bdi dir="ltr">Symbol</bdi> אחר שהוכן מראש.
2. אל תיצור <bdi dir="ltr">event</bdi> ידני לצורך ההצגה.
3. הראה <bdi dir="ltr">Evidence</bdi> מתוארך וציין שהוא <bdi dir="ltr">snapshot</bdi>.

### סימול מציג <bdi dir="ltr"><code>INSUFFICIENT DATA</code></bdi>

1. אל תציג זאת כתקלה ואל תשנה נתונים מול הקהל.
2. אמור שהמערכת חסמה מסקנה מפני שהיסטוריית המחיר או הנתונים הפונדמנטליים אינם מספיקים.
3. עבור אל <bdi dir="ltr"><code>META</code></bdi> כדי להראות תרחיש מלא, ואז חזור והדגש את שער האיכות.

### מונה <bdi dir="ltr"><code>Shadow Mode</code></bdi> עדיין נמוך

1. הצג את המספר האמיתי שמופיע במסך.
2. הסבר ש־<bdi dir="ltr"><code>Backfill</code></bdi> אינו מקדם אותו, משום שהוא יודע את העבר מראש.
3. ציין שכשל בריצה היומית אינו נספר כהצלחה; רק יום חי שאושר מקצה לקצה מקדם את המונה.

### מודל <bdi dir="ltr"><bdo dir="ltr"><code>v2</code></bdo></bdi> מציג <bdi dir="ltr"><code>FALLBACK</code></bdi>

1. אל תנסה להסתיר את המצב ואל תפעיל אימון מול הקהל.
2. אמור שאין עדיין 24 חודשי ראיות ומדגם אימון שעומד בשער.
3. הסבר שכללי <bdi dir="ltr"><bdo dir="ltr"><code>v1</code></bdo></bdi> פעילים, והשדות ההסתברותיים נשארים ריקים במקום להציג מספר לא אמין.

### <bdi dir="ltr">Kafka UI</bdi> אינו זמין

1. פתח <bdi dir="ltr">Bronze object</bdi> שהוכן מראש.
2. הצג <bdi dir="ltr">topic/partition/offset</bdi> בנתיב ואת חוזה <bdi dir="ltr">MarketBarV1</bdi>.
3. השתמש ב־<bdi dir="ltr">Phase 3/6 verification</bdi> להוכחת <bdi dir="ltr">publish</bdi> ו־<bdi dir="ltr">consumption</bdi>.

### <bdi dir="ltr">MinIO</bdi> אינו זמין

1. הצג את מסלול <bdi dir="ltr">Raw</bdi> ב־<bdi dir="ltr">Project Story</bdi>.
2. פתח <bdi dir="ltr"><bdo dir="ltr"><code>docs/project-context.md</code></bdo></bdi> או <bdi dir="ltr">PDF</bdi> הארכיטקטורה והסבר <bdi dir="ltr">Bronze immutable</bdi>.
3. הצג את <bdi dir="ltr">Phase 8 archive manifest evidence</bdi> אם נדרש.

### <bdi dir="ltr">Airflow</bdi> אינו זמין

1. הראה את תרשים <bdi dir="ltr">Certified</bdi> ואת <bdi dir="ltr"><bdo dir="ltr"><code>docs/architecture/execution-model.md</code></bdo></bdi>.
2. פתח <bdi dir="ltr">Phase 5 verification</bdi> עם סדר המשימות וה־<bdi dir="ltr">run</bdi> המתועד.
3. הדגש שכשל <bdi dir="ltr">Airflow</bdi> אינו עוצר את <bdi dir="ltr">Streaming</bdi>.

### <bdi dir="ltr">Spark UI</bdi> אינו זמין

1. הראה את <bdi dir="ltr">Airflow DAG</bdi> ואת <bdi dir="ltr">verification</bdi> של <bdi dir="ltr">Spark Batch/Streaming</bdi>.
2. הסבר ש־<bdi dir="ltr">UI</bdi> הוא כלי תצפית; הנתונים, <bdi dir="ltr">checkpoint</bdi> וה־<bdi dir="ltr">run evidence</bdi> הם ההוכחה.

### <bdi dir="ltr">Adminer</bdi> אינו זמין

1. השתמש ב־<bdi dir="ltr">Backend API docs</bdi> או <bdi dir="ltr">Dashboard</bdi>.
2. הצג את טבלת <bdi dir="ltr">Gold</bdi> במסמך הארכיטקטורה.
3. ציין ש־<bdi dir="ltr">Adminer</bdi> אינו חלק מזרימת המשתמש, אלא כלי פיתוח מקומי.

### <bdi dir="ltr">Backend API</bdi> אינו זמין

1. <bdi dir="ltr">Project Story</bdi> עדיין מציג ראיות מתוארכות ומסמן <bdi dir="ltr">live proof</bdi> כ־<bdi dir="ltr">unavailable</bdi>.
2. הצג <bdi dir="ltr">Phase 7 verification</bdi> ואת גבול ה־<bdi dir="ltr">SELECT-only identity</bdi>.
3. אל תעקוף את ה־<bdi dir="ltr">API</bdi> באמצעות חיבור <bdi dir="ltr">UI</bdi> ישיר למסד.

### <bdi dir="ltr">Backtesting Lab</bdi> אינו עולה או מציג <bdi dir="ltr">run</bdi> ישן

1. אל תריץ <bdi dir="ltr">Backtest</bdi> חדש מול הקהל.
2. פתח את טבלת <bdi dir="ltr"><code>Final published results</code></bdi> ב־<bdi dir="ltr"><bdo dir="ltr"><code>docs/phase12-verification.md</code></bdo></bdi>.
3. ציין את <bdi dir="ltr">run ID</bdi> <bdi dir="ltr"><bdo dir="ltr"><code>48cf39e5-ccb0...</code></bdo></bdi>, את <bdi dir="ltr">code version</bdi> <bdi dir="ltr"><bdo dir="ltr"><code>bed1fb7</code></bdo></bdi> ואת תאריך האימות.
4. הסבר שה־<bdi dir="ltr">UI</bdi> הוא <bdi dir="ltr">read model</bdi>; ה־<bdi dir="ltr">Parquet</bdi> וה־<bdi dir="ltr">manifest</bdi> הם ראיית השחזור המלאה.

## ניסוחים טובים בזמן תקלה

- "הממשק המקומי הזה אינו זמין כרגע, ולכן אעבור לראיית <bdi dir="ltr">verification</bdi> מתוארכת."
- "אני מפריד בין מצב חי לבין תוצאה שנמדדה; איני מציג <bdi dir="ltr">snapshot</bdi> כ־<bdi dir="ltr">live</bdi>."
- "הכשל ב־<bdi dir="ltr">UI</bdi> אינו משנה את הגבול הארכיטקטוני שאותו אני מסביר."
- "לא אבצע שינוי נתונים כדי לתקן דמו; אשתמש במסלול הגיבוי שהוכן מראש."

## ניסוחים שכדאי להימנע מהם

- "זה אמור לעבוד" ללא ראיה.
- "זה <bdi dir="ltr">exactly once</bdi>" כשאין הבטחה כזו.
- "זה <bdi dir="ltr">production ready</bdi>" בלי <bdi dir="ltr">authentication</bdi>, <bdi dir="ltr">TLS</bdi> ו־<bdi dir="ltr">capacity testing</bdi>.
- "<bdi dir="ltr">Airflow</bdi> מריץ את כל המערכת" - הוא מריץ רק <bdi dir="ltr">bounded workflows</bdi>.
- "<bdi dir="ltr">MariaDB</bdi> שומר הכול" - <bdi dir="ltr">Raw</bdi>, <bdi dir="ltr">Silver</bdi> ו־<bdi dir="ltr">Archive</bdi> נמצאים ב־<bdi dir="ltr">object storage</bdi>.

</div>
