<div dir="rtl" align="right">

# <bdi dir="ltr"><code>MarketPilot</code></bdi> — מילון ומודלים מחשבתיים

| מונח | הסבר פשוט | איך לזכור |
|---|---|---|
| <bdi dir="ltr"><code>Event</code></bdi> | עובדה שקרתה בזמן מסוים | מעטפה עם זהות, זמן ותוכן |
| <bdi dir="ltr"><code>Schema</code></bdi> | המבנה והטיפוסים של הנתון | חוזה בין מי ששולח למי שקורא |
| <bdi dir="ltr"><code>Producer</code></bdi> | שירות שמפרסם <bdi dir="ltr"><code>events</code></bdi> | שולח מכתבים לסניף הדואר |
| <bdi dir="ltr"><code>Consumer</code></bdi> | שירות שקורא <bdi dir="ltr"><code>events</code></bdi> | נמען עצמאי עם סימנייה משלו |
| <bdi dir="ltr"><code>Topic</code></bdi> | ערוץ <bdi dir="ltr"><code>events</code></bdi> ב־<bdi dir="ltr"><code>Kafka</code></bdi> | תיקייה לוגית של הודעות מאותו סוג |
| <bdi dir="ltr"><code>Partition</code></bdi> | חלוקה סדורה בתוך <bdi dir="ltr"><code>Topic</code></bdi> | מסילה שבה נשמר סדר מקומי |
| <bdi dir="ltr"><code>Offset</code></bdi> | מספר המיקום ב־<bdi dir="ltr"><code>Partition</code></bdi> | מספר סידורי של הודעה על המסילה |
| <bdi dir="ltr"><code>Consumer group</code></bdi> | צרכנים שחולקים עבודה | צוות שמתחלק במחיצות |
| <bdi dir="ltr"><code>Streaming</code></bdi> | עיבוד מתמשך של <bdi dir="ltr"><code>events</code></bdi> נכנסים | פס ייצור שעובד כל הזמן |
| <bdi dir="ltr"><code>Micro-batch</code></bdi> | קבוצת <bdi dir="ltr"><code>events</code></bdi> קטנה בעיבוד <bdi dir="ltr"><code>Streaming</code></bdi> | סל קטן שמתרוקן כל כמה שניות |
| <bdi dir="ltr"><code>Batch</code></bdi> | <bdi dir="ltr"><code>Job</code></bdi> עם קלט תחום וסוף ברור | סגירת יום וחישוב מחדש |
| <bdi dir="ltr"><code>Checkpoint</code></bdi> | מצב ההתקדמות של <bdi dir="ltr"><code>Streaming</code></bdi> | סימנייה עמידה לאחר <bdi dir="ltr"><code>restart</code></bdi> |
| <bdi dir="ltr"><code>Watermark</code></bdi> | גבול התקדמות או פרסום | חותמת עד היכן הנתונים תקפים |
| <bdi dir="ltr"><code>Idempotency</code></bdi> | <bdi dir="ltr"><code>retry</code></bdi> בלי תוצאה כפולה | לחיצה כפולה שמייצרת הזמנה אחת |
| <bdi dir="ltr"><code>Business key</code></bdi> | זהות עסקית של רשומה | מה הופך <bdi dir="ltr"><code>bar</code></bdi> אחד לייחודי |
| <bdi dir="ltr"><code>Upsert</code></bdi> | <bdi dir="ltr"><code>Insert</code></bdi> או <bdi dir="ltr"><code>Update</code></bdi> לפי <bdi dir="ltr"><code>key</code></bdi> | צור אם חסר, עדכן אם קיים |
| <bdi dir="ltr"><code>Bronze</code></bdi> | חומר גלם בלתי משתנה (<bdi dir="ltr"><code>immutable</code></bdi>) | המקור שלא מתקנים בדיעבד |
| <bdi dir="ltr"><code>Silver</code></bdi> | נתון נקי וקנוני | חומר גלם שעבר ניקוי ואחידות |
| <bdi dir="ltr"><code>Gold</code></bdi> | נתון מוכן ליישום | מוצר מדף לשאילתות ול־<bdi dir="ltr"><code>Dashboard</code></bdi> |
| <bdi dir="ltr"><code>Parquet</code></bdi> | פורמט עמודתי דחוס | קובץ יעיל לסריקות <bdi dir="ltr"><code>Analytics</code></bdi> |
| <bdi dir="ltr"><code>Provisional</code></bdi> | נתון חי שטרם אושר סופית | מה ידוע עכשיו |
| <bdi dir="ltr"><code>Certified</code></bdi> | נתון של יום סגור שעבר <bdi dir="ltr"><code>DQ</code></bdi> | מה מאושר לאחר הבדיקה |
| <bdi dir="ltr"><code>Data Quality</code></bdi> | כללים שחוסמים פרסום שגוי | שער לפני <bdi dir="ltr"><code>Gold Certified</code></bdi> |
| <bdi dir="ltr"><code>Lineage</code></bdi> | שרשרת המקור והעיבוד | תעודת המסע של הרשומה |
| <bdi dir="ltr"><code>Replay</code></bdi> | עיבוד חוזר של היסטוריה | להריץ שוב מהמקור הגולמי |
| <bdi dir="ltr"><code>Backfill</code></bdi> | מילוי או תיקון טווח היסטורי | <bdi dir="ltr"><code>Replay</code></bdi> ממוקד לפי תאריכים וסמלים |
| <bdi dir="ltr"><code>Orchestration</code></bdi> | ניהול סדר ותלויות של <bdi dir="ltr"><code>jobs</code></bdi> | מנהל העבודה, לא העובד עצמו |
| <bdi dir="ltr"><code>Healthcheck</code></bdi> | בדיקה ששירות מסוגל לפעול | דופק טכני של <bdi dir="ltr"><code>container</code></bdi> |
| <bdi dir="ltr"><code>Freshness</code></bdi> | כמה עדכני הנתון | הזמן מאז האירוע האחרון |
| <bdi dir="ltr"><code>DLQ</code></bdi> | מקום ל־<bdi dir="ltr"><code>events</code></bdi> שנכשלו | תיבת חריגים עם סיבה |
| <bdi dir="ltr"><code>Manifest</code></bdi> | רשימת תוכן וראיות לארכיון | תעודת משלוח עם <bdi dir="ltr"><code>counts</code></bdi> ו־<bdi dir="ltr"><code>hashes</code></bdi> |
| <bdi dir="ltr"><code>SHA-256</code></bdi> | טביעת אצבע קריפטוגרפית | שינוי קטן בקובץ משנה את החתימה |
| <bdi dir="ltr"><code>API boundary</code></bdi> | השער היחיד של ממשק המשתמש לנתונים | הדפדפן מדבר עם פקיד, לא עם הכספת |
| <bdi dir="ltr"><code>ADR</code></bdi> | מסמך החלטה ארכיטקטונית | למה בחרנו כך ומה המחיר |
| <bdi dir="ltr"><code>Content-addressed object</code></bdi> | אובייקט ששמו נגזר מה־<bdi dir="ltr"><code>hash</code></bdi> של התוכן | אותה תשובה (<bdi dir="ltr"><code>response</code></bdi>) מקבלת אותה זהות |
| <bdi dir="ltr"><code>Bronze barrier</code></bdi> | תנאי שמוכיח שכל מיקום ב־<bdi dir="ltr"><code>Kafka</code></bdi> נשמר ב־<bdi dir="ltr"><code>Bronze</code></bdi> | לא מעבדים לפני שהמידע הגולמי בטוח |
| <bdi dir="ltr"><code>XNYS session</code></bdi> | יום ושעות מסחר לפי לוח <bdi dir="ltr"><code>NYSE</code></bdi> | לא מניחים שכל יום חול הוא יום מסחר |
| <bdi dir="ltr"><code>IEX feed</code></bdi> | נתוני מסחר מבורסה אחת דרך <bdi dir="ltr"><code>Alpaca</code></bdi> | נתון אמיתי, אך לא שוק מאוחד מלא |
| <bdi dir="ltr"><code>Backtest</code></bdi> | סימולציה של כללי אסטרטגיה על היסטוריה | ניסוי היסטורי, לא ביצוע מסחר |
| <bdi dir="ltr"><code>Look-ahead bias</code></bdi> | שימוש במידע עתידי בהחלטה היסטורית | האות של עכשיו משפיע רק מהרשומה הבאה |
| <bdi dir="ltr"><code>Benchmark</code></bdi> | נקודת השוואה לתוצאה | <bdi dir="ltr"><code>SPY</code></bdi> משמש כהקשר, לא כיעד מובטח |
| <bdi dir="ltr"><code>Slippage</code></bdi> | פער משוער בין מחיר תיאורטי לביצוע | חיכוך שמקטין תשואה מדומה |

## הבדלים שקל להתבלבל בהם

- **<bdi dir="ltr"><code>Kafka</code></bdi> מול <bdi dir="ltr"><code>MinIO</code></bdi>:** ‏<bdi dir="ltr"><code>Kafka</code></bdi> מעביר ושומר <bdi dir="ltr"><code>log</code></bdi> לפי <bdi dir="ltr"><code>offset</code></bdi>; ‏<bdi dir="ltr"><code>MinIO</code></bdi> שומר אובייקטים לטווח ארוך.
- **<bdi dir="ltr"><code>Spark</code></bdi> מול <bdi dir="ltr"><code>Airflow</code></bdi>:** ‏<bdi dir="ltr"><code>Spark</code></bdi> מבצע חישוב; ‏<bdi dir="ltr"><code>Airflow</code></bdi> מחליט מתי ובאיזה סדר להריץ <bdi dir="ltr"><code>Batch</code></bdi>.
- **<bdi dir="ltr"><code>MinIO</code></bdi> מול <bdi dir="ltr"><code>MariaDB</code></bdi>:** ‏<bdi dir="ltr"><code>MinIO</code></bdi> שומר <bdi dir="ltr"><code>Raw</code></bdi>, ‏<bdi dir="ltr"><code>Parquet</code></bdi> וארכיון; ‏<bdi dir="ltr"><code>MariaDB</code></bdi> מגיש נתוני <bdi dir="ltr"><code>Gold</code></bdi>.
- **<bdi dir="ltr"><code>Health</code></bdi> מול <bdi dir="ltr"><code>Freshness</code></bdi>:** שירות יכול להיות תקין (<bdi dir="ltr"><code>healthy</code></bdi>) אבל להציג נתונים ישנים.
- **<bdi dir="ltr"><code>Backup</code></bdi> מול <bdi dir="ltr"><code>Archive</code></bdi>:** גיבוי משחזר מערכת; ארכיון משמר מערך נתונים סגור ומאומת.
- **<bdi dir="ltr"><code>Retry</code></bdi> מול <bdi dir="ltr"><code>Duplicate</code></bdi>:** ניסיון חוזר הוא פעולה חוזרת; <bdi dir="ltr"><code>Idempotency</code></bdi> מונע תוצאה עסקית כפולה.
- **<bdi dir="ltr"><code>Event time</code></bdi> מול <bdi dir="ltr"><code>Ingestion time</code></bdi>:** הראשון הוא זמן האירוע במקור; השני הוא זמן הקליטה במערכת.
- **<bdi dir="ltr"><code>Live</code></bdi> מול <bdi dir="ltr"><code>Certified</code></bdi>:** הראשון ממקסם מהירות; השני ממקסם אמון במחיצה סגורה.
- **<bdi dir="ltr"><code>Backfill</code></bdi> מול <bdi dir="ltr"><code>Backtest</code></bdi>:** הראשון משיג ומאשר היסטוריה; השני בוחן אסטרטגיה על ההיסטוריה המאושרת.
- **<bdi dir="ltr"><code>IEX</code></bdi> מול <bdi dir="ltr"><code>SIP</code></bdi>:** ‏<bdi dir="ltr"><code>IEX</code></bdi> הוא מקור חלקי מבורסה אחת; ‏<bdi dir="ltr"><code>SIP</code></bdi> הוא מקור מאוחד שדורש הרשאה מתאימה.

</div>
