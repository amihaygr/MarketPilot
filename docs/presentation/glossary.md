<div dir="rtl" align="right">

# <bdi dir="ltr"><code>MarketPilot</code></bdi> — מילון מונחים פשוט

המילון נועד להכנה, לא להקראה. בכל תשובה התחל במשמעות הפשוטה ורק אחר כך הוסף את הפרט הטכני.

## נתונים וארכיטקטורה

| מונח | הסבר פשוט | התפקיד בפרויקט |
|---|---|---|
| <bdi dir="ltr"><code>Kafka</code></bdi> | יומן אירועים שמאפשר לכמה צרכנים לקרוא אותו מידע בקצב שלהם | מפריד את מפיק נתוני השוק מ־<bdi dir="ltr"><code>Streaming</code></bdi> ומהארכיון הגולמי |
| <bdi dir="ltr"><code>Topic</code></bdi> | ערוץ בשם מסוים בתוך <bdi dir="ltr"><code>Kafka</code></bdi> | מפריד בין אירועים חיים, אירועי עבר ונתונים שנדחו |
| <bdi dir="ltr"><code>Partition</code></bdi> | חלוקה פנימית וסדורה של <bdi dir="ltr"><code>Topic</code></bdi> | מאפשרת סדר וצריכה מקבילית |
| <bdi dir="ltr"><code>Offset</code></bdi> | מספר המיקום של הודעה בתוך מחיצה | משמש עקיבות, חידוש קריאה ו־<bdi dir="ltr"><code>Replay</code></bdi> |
| <bdi dir="ltr"><code>Checkpoint</code></bdi> | מצב שמור של תהליך רציף | מאפשר ל־<bdi dir="ltr"><code>Spark Streaming</code></bdi> להמשיך לאחר הפעלה מחדש |
| <bdi dir="ltr"><code>Streaming</code></bdi> | שירות ארוך־חיים שמעבד אירועים כשהם מגיעים | מפרסם תמונה מהירה במצב <bdi dir="ltr"><code>PROVISIONAL</code></bdi> |
| <bdi dir="ltr"><code>Batch</code></bdi> | עבודה תחומה עם התחלה וסיום | בונה מחדש יום סגור ומפרסם <bdi dir="ltr"><code>CERTIFIED</code></bdi> |
| <bdi dir="ltr"><code>Airflow DAG</code></bdi> | גרף משימות עם סדר ותלויות | מתזמן ומנטר עבודות תחומות; אינו מנהל שירותי <bdi dir="ltr"><code>Streaming</code></bdi> |
| <bdi dir="ltr"><code>SparkSubmitOperator</code></bdi> | רכיב של <bdi dir="ltr"><code>Airflow</code></bdi> ששולח עבודת <bdi dir="ltr"><code>Spark</code></bdi> | שומר את החישוב ב־<bdi dir="ltr"><code>Spark</code></bdi> ואת התזמון ב־<bdi dir="ltr"><code>Airflow</code></bdi> |
| <bdi dir="ltr"><code>Docker Compose</code></bdi> | תיאור והפעלה של סביבת קונטיינרים מקומית | מנהל את מחזור החיים של השירותים הארוכים |
| <bdi dir="ltr"><code>Idempotency</code></bdi> | הפעלה חוזרת שאינה יוצרת תוצאה עסקית כפולה | נשענת על מזהים דטרמיניסטיים, מפתחות עסקיים ו־<bdi dir="ltr"><code>Upsert</code></bdi> |
| <bdi dir="ltr"><code>Lineage</code></bdi> | היכולת לעקוב מתוצאה בחזרה למקור, לריצה ולגרסה | מאפשר הסבר, חקירה ושחזור |

## שכבות הנתונים

| מונח | משמעות בפרויקט |
|---|---|
| <bdi dir="ltr"><code>Bronze</code></bdi> | העותק הגולמי והבלתי־משתנה כפי שהתקבל; נשמר ב־<bdi dir="ltr"><code>MinIO</code></bdi> |
| <bdi dir="ltr"><code>Silver</code></bdi> | נתונים נקיים, טיפוסיים ומנורמלים בקובצי <bdi dir="ltr"><code>Parquet</code></bdi> |
| <bdi dir="ltr"><code>Gold</code></bdi> | טבלאות מוכנות לצריכת המוצר ב־<bdi dir="ltr"><code>MariaDB</code></bdi> |
| <bdi dir="ltr"><code>PROVISIONAL</code></bdi> | נתון מהיר שטרם עבר את כל בדיקות סוף היום |
| <bdi dir="ltr"><code>CERTIFIED</code></bdi> | נתון שנבנה מחדש מן המקור ועבר שערי איכות |
| <bdi dir="ltr"><code>Backfill</code></bdi> | רכישה יזומה של תקופה היסטורית חסרה |
| <bdi dir="ltr"><code>Replay</code></bdi> | עיבוד מחדש של אירועים שכבר נשמרו |
| <bdi dir="ltr"><code>Freshness</code></bdi> | גיל הנתון ביחס לזמן שבו היה צפוי להגיע |
| <bdi dir="ltr"><code>Data Quality Gate</code></bdi> | בדיקה חוסמת של שלמות, כפילויות, ערכים חסרים, מבנה <bdi dir="ltr"><code>OHLC</code></bdi> וטריות |

## מקורות שוק וחברות

| מונח | הסבר |
|---|---|
| <bdi dir="ltr"><code>IEX</code></bdi> | מקור נתוני השוק החינמי של הפרויקט; הוא מייצג בורסה אחת ולכן חלקי |
| <bdi dir="ltr"><code>SIP</code></bdi> | הזנת השוק המאוחדת הרשמית של הבורסות האמריקאיות; מלאה יותר ובדרך כלל דורשת הרשאה בתשלום |
| <bdi dir="ltr"><code>SEC EDGAR</code></bdi> | המקור הרשמי לדיווחי חברות ציבוריות בארצות הברית |
| <bdi dir="ltr"><bdo dir="ltr"><code>Company Facts / XBRL</code></bdo></bdi> | נתונים חשבונאיים מובנים מתוך דיווחי החברה, למשל הכנסות, רווח, מזומן וחוב |
| <bdi dir="ltr"><code>Corporate Action</code></bdi> | אירוע כמו פיצול מניה או דיבידנד שמשפיע על ניתוח היסטורי |
| <bdi dir="ltr"><code>XNYS session</code></bdi> | יום מסחר תקף לפי לוח הבורסה של ניו יורק, כולל חגים וסגירות מוקדמות |

## ניתוח טכני וסיכון

| מונח | הסבר פשוט |
|---|---|
| <bdi dir="ltr"><bdo dir="ltr"><code>SMA 20</code></bdo></bdi> | ממוצע פשוט של עשרים מחירי הסגירה האחרונים; מחליק רעש אך מפגר אחרי המחיר |
| <bdi dir="ltr"><bdo dir="ltr"><code>EMA 20 / 50</code></bdo></bdi> | ממוצע שנותן משקל גדול יותר למחירים חדשים ולכן מגיב מהר יותר |
| <bdi dir="ltr"><code>RSI</code></bdi> | מדד מומנטום בסולם <bdi dir="ltr"><bdo dir="ltr"><code>0–100</code></bdo></bdi>; ערך קיצוני הוא אות לבדיקה, לא פקודה |
| <bdi dir="ltr"><code>MACD</code></bdi> | מדד מגמה ומומנטום שמבוסס על הפער בין ממוצעים מעריכיים |
| <bdi dir="ltr"><code>ATR</code></bdi> | מדד תנודתיות שמעריך כמה המחיר נע בדרך כלל; אינו מנבא כיוון |
| <bdi dir="ltr"><code>Buy Zone</code></bdi> | טווח כניסה אפשרי המבוסס על תמיכה, ממוצעים ותנודתיות; אינו מחיר קסם |
| <bdi dir="ltr"><code>Stop</code></bdi> | מחיר שמבטל את התזה ומגדיר את הסיכון מראש |
| <bdi dir="ltr"><bdo dir="ltr"><code>Target 1 / 2</code></bdo></bdi> | יעדי מימוש המבוססים על התנגדות ומכפלות סיכון |
| <bdi dir="ltr"><bdo dir="ltr"><code>Risk/Reward</code></bdo></bdi> | היחס בין הרווח המתוכנן להפסד המתוכנן; אינו הסתברות הצלחה |
| <bdi dir="ltr"><code>Position Sizing</code></bdi> | חישוב מספר המניות לפי גודל התיק, מחיר העצירה ומגבלות החשיפה |

## בדיקה היסטורית ומודל

| מונח | הסבר פשוט |
|---|---|
| <bdi dir="ltr"><code>Backtest</code></bdi> | ניסוי של כללי אסטרטגיה על נתוני עבר מאושרים |
| <bdi dir="ltr"><code>Benchmark</code></bdi> | נקודת ייחוס; בפרויקט משתמשים ב־<bdi dir="ltr"><code>SPY</code></bdi> |
| <bdi dir="ltr"><bdo dir="ltr"><code>Look-ahead Bias</code></bdo></bdi> | טעות שבה המודל משתמש במידע שלא היה ידוע בזמן ההחלטה |
| <bdi dir="ltr"><code>Slippage</code></bdi> | פער בין מחיר הביצוע המתוכנן למחיר שהיה אפשר לקבל בפועל |
| <bdi dir="ltr"><code>Drawdown</code></bdi> | הירידה משיא לשפל שבא אחריו |
| <bdi dir="ltr"><code>Rule Score</code></bdi> | ציון שקוף של הראיות הטכניות והפונדמנטליות; הוא אינו סיכוי לרווח |
| <bdi dir="ltr"><code>Data Confidence</code></bdi> | ציון איכות, כיסוי, טריות ומקור הנתונים; גם הוא אינו סיכוי לרווח |
| <bdi dir="ltr"><code>Model Probability</code></bdi> | הסתברות מכוילת להגיע ל־<bdi dir="ltr"><bdo dir="ltr"><code>Target 1</code></bdo></bdi> לפני <bdi dir="ltr"><code>Stop</code></bdi>, רק לאחר כניסה תקפה |
| <bdi dir="ltr"><code>Expected R</code></bdi> | תוחלת מתמטית ביחידות סיכון לאחר הסתברות, רווח, הפסד ועלויות |
| <bdi dir="ltr"><code>Calibration</code></bdi> | בדיקה האם תחזיות של, למשל, <bdi dir="ltr"><bdo dir="ltr"><code>60%</code></bdo></bdi> מצליחות בערך בשישה מכל עשרה מקרים דומים |
| <bdi dir="ltr"><bdo dir="ltr"><code>Walk-Forward Validation</code></bdo></bdi> | אימון על העבר ובדיקה על תקופה מאוחרת יותר, שוב ושוב בסדר כרונולוגי |
| <bdi dir="ltr"><bdo dir="ltr"><code>NO_ENTRY</code></bdo></bdi> | התרחיש פורסם, אך המחיר לא נכנס לטווח בזמן התוקף; אינו הפסד מסחר |
| <bdi dir="ltr"><code>PREVIEW</code></bdi> | תחזית מודל שמוצגת למחקר אך אינה משנה את פעולת <bdi dir="ltr"><bdo dir="ltr"><code>v1</code></bdo></bdi> |
| <bdi dir="ltr"><code>ACTIVE</code></bdi> | מודל שעבר שערים, תקופת צל ואישור אנושי, ולכן רשאי להשפיע על הדירוג |
| <bdi dir="ltr"><code>FALLBACK</code></bdi> | מצב בטוח שבו אין מודל תקף; כללי <bdi dir="ltr"><bdo dir="ltr"><code>v1</code></bdo></bdi> נשארים פעילים ולא מוצגת הסתברות ישנה או מומצאת |

## ארבע הבחנות שכדאי לזכור

- <bdi dir="ltr"><code>Fresh</code></bdi> אינו בהכרח <bdi dir="ltr"><code>Certified</code></bdi>.
- <bdi dir="ltr"><code>Confidence</code></bdi> אינו <bdi dir="ltr"><code>Probability</code></bdi>.
- <bdi dir="ltr"><code>Backfill</code></bdi> אינו <bdi dir="ltr"><code>Backtest</code></bdi>.
- <bdi dir="ltr"><code>FALLBACK</code></bdi> אינו כשל שקט; הוא סירוב מודע להציג מודל שלא הוכח.

</div>
