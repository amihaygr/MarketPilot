# MarketPilot - חזרות ותרחישי תקלה

## תכנית חזרות

### חזרה 1 - הבנה ללא מסכים

- הסבר בקול את Live, Raw, Certified, Historical ו-SEC ללא פתיחת מחשב.
- הגדר Kafka, Spark, Airflow, Bronze, Gold ו-idempotency במשפט אחד כל אחד.
- אם נתקעת, חזור לחוברת המסביר; אל תשנן את תסריט הלחיצות.

### חזרה 2 - מסלול איטי

- בצע את כל המסלול בלי טיימר.
- רשום לכל מעבר את ה-URL, האובייקט או ה-DAG המדויק.
- ודא שאינך מחפש נתון מול הקהל.

### חזרה 3 - 15 דקות מוקלטות

- הפעל טיימר והקלט מסך וקול.
- מטרה ראשונה: 14:15 עד 15:45.
- סמן משפטים ארוכים, מסכים מיותרים ומונחים שלא הסברת.

### חזרה 4 - תקלה מכוונת

- סגור מראש UI אחד שאינו קריטי.
- המשך באמצעות verification file או Project Story.
- אמור בקול: "זהו snapshot מתוארך; איני מציג אותו כמצב חי."

### חזרה 5 - שאלות

- בקש ממישהו לשאול עשר שאלות מ-`qa-bank.md` בסדר אקראי.
- תשובה ישירה צריכה להתחיל בתוך חמש שניות.
- אם אינך יודע: ציין מה ידוע, מה לא נמדד ואיך היית בודק.

## תנאי מוכנות

- שתי ריצות רצופות של 15 דקות בטווח של 45 שניות.
- חמשת המסלולים מוסברים ללא הערות.
- עשר שאלות החובה נענות ישירות.
- מעבר ל-fallback אחד בלי לחץ ובלי שינוי נתונים.
- שלוש מגבלות נאמרות יחד עם דרך ההרחבה שלהן.
- משפט פתיחה ומשפט סיום נאמרים באופן טבעי.

## Preflight ביום ההצגה

### טכני

- [ ] מחשב מחובר לחשמל ומצב שינה מבוטל.
- [ ] `docker compose ps` מציג את השירותים הנדרשים כבריאים.
- [ ] Project Story, Presenter Console, Dashboard ו-Backtesting Lab מחזירים HTTP 200.
- [ ] נבחר Symbol עם נתונים.
- [ ] שני Kafka Topics, Bronze object וה-Airflow run הסופי פתוחים מראש.
- [ ] Backtesting Lab מציג 20 sessions, 23,349 observations ו-555 trades.
- [ ] זום הדפדפן ו-resolution מאפשרים קריאה מרחוק.
- [ ] התראות, Teams, WhatsApp ודואר מושתקים.

### אבטחה

- [ ] `.env` וטרמינלים עם סודות סגורים.
- [ ] Adminer אינו שומר סיסמה גלויה.
- [ ] אין clipboard עם API keys.
- [ ] אין כוונה להריץ UPDATE, purge או credential rotation.

### הצגה

- [ ] מצב 15 דקות נבחר ב-Presenter Console.
- [ ] טיימר מאופס.
- [ ] משפט הפתיחה והסיום נמצאים בכרטיס הראשון והאחרון.
- [ ] מסמך הארכיטקטורה ו-`docs/phase12-verification.md` זמינים כגיבוי.

## Failure playbook

### Dashboard אינו עולה

1. אל תתחיל debugging ממושך מול הקהל.
2. הראה את Project Story ואת Phase 7/9 verification.
3. הסבר את גבול Browser -> API -> MariaDB.
4. אם יש זמן, בדוק לאחר מכן `docker compose ps web-app backend-api mariadb`.

### אין נתונים בטווח

1. עבור ל-`7D` או Symbol אחר שהוכן מראש.
2. אל תיצור event ידני לצורך ההצגה.
3. הראה Evidence מתוארך וציין שהוא snapshot.

### Kafka UI אינו זמין

1. פתח Bronze object שהוכן מראש.
2. הצג topic/partition/offset בנתיב ואת חוזה MarketBarV1.
3. השתמש ב-Phase 3/6 verification להוכחת publish ו-consumption.

### MinIO אינו זמין

1. הצג את מסלול Raw ב-Project Story.
2. פתח `docs/project-context.md` או PDF הארכיטקטורה והסבר Bronze immutable.
3. הצג את Phase 8 archive manifest evidence אם נדרש.

### Airflow אינו זמין

1. הראה את תרשים Certified ואת `docs/architecture/execution-model.md`.
2. פתח Phase 5 verification עם סדר המשימות וה-run המתועד.
3. הדגש שכשל Airflow אינו עוצר את Streaming.

### Spark UI אינו זמין

1. הראה את Airflow DAG ואת verification של Spark Batch/Streaming.
2. הסבר ש-UI הוא כלי תצפית; הנתונים, checkpoint וה-run evidence הם ההוכחה.

### Adminer אינו זמין

1. השתמש ב-Backend API docs או Dashboard.
2. הצג את טבלת Gold במסמך הארכיטקטורה.
3. ציין ש-Adminer אינו חלק מזרימת המשתמש, אלא כלי פיתוח מקומי.

### Backend API אינו זמין

1. Project Story עדיין מציג ראיות מתוארכות ומסמן live proof כ-unavailable.
2. הצג Phase 7 verification ואת גבול ה-SELECT-only identity.
3. אל תעקוף את ה-API באמצעות חיבור UI ישיר למסד.

### Backtesting Lab אינו עולה או מציג run ישן

1. אל תריץ Backtest חדש מול הקהל.
2. פתח את טבלת `Final published results` ב-`docs/phase12-verification.md`.
3. ציין את run ID `48cf39e5-ccb0...`, את code version `bed1fb7` ואת תאריך האימות.
4. הסבר שה-UI הוא read model; ה-Parquet וה-manifest הם ראיית השחזור המלאה.

## ניסוחים טובים בזמן תקלה

- "הממשק המקומי הזה אינו זמין כרגע, ולכן אעבור לראיית verification מתוארכת."
- "אני מפריד בין מצב חי לבין תוצאה שנמדדה; איני מציג snapshot כ-live."
- "הכשל ב-UI אינו משנה את הגבול הארכיטקטוני שאותו אני מסביר."
- "לא אבצע שינוי נתונים כדי לתקן דמו; אשתמש במסלול הגיבוי שהוכן מראש."

## ניסוחים שכדאי להימנע מהם

- "זה אמור לעבוד" ללא ראיה.
- "זה exactly once" כשאין הבטחה כזו.
- "זה production ready" בלי authentication, TLS ו-capacity testing.
- "Airflow מריץ את כל המערכת" - הוא מריץ רק bounded workflows.
- "MariaDB שומר הכול" - Raw, Silver ו-Archive נמצאים ב-object storage.
