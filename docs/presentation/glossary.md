<div dir="rtl" align="right">

# <bdi dir="ltr"><code>MarketPilot</code></bdi> — מילון מונחים פשוט

המילון נועד להכנה, לא להקראה. בכל תשובה התחל במשמעות הפשוטה ורק אחר כך
הוסף את הפרט הטכני. המונחים באנגלית מוצגים בשורה עצמאית משמאל לימין;
ההסבר העברי שמתחתיהם נשאר מיושר לימין.

## נתונים וארכיטקטורה

<h3 dir="ltr" align="left"><code>Kafka</code></h3>

- **במילים פשוטות:** יומן אירועים שמאפשר לכמה צרכנים לקרוא אותו מידע בקצב שלהם.
- **בפרויקט:** מפריד את מפיק נתוני השוק משירות ה־<bdi dir="ltr"><code>Streaming</code></bdi> ומהארכיון הגולמי.

<h3 dir="ltr" align="left"><code>Topic</code></h3>

- **במילים פשוטות:** ערוץ בעל שם בתוך <bdi dir="ltr"><code>Kafka</code></bdi>.
- **בפרויקט:** מפריד בין אירועים חיים, אירועי עבר ונתונים שנדחו.

<h3 dir="ltr" align="left"><code>Partition</code></h3>

- **במילים פשוטות:** חלוקה פנימית וסדורה של <bdi dir="ltr"><code>Topic</code></bdi>.
- **בפרויקט:** מאפשרת לשמור סדר ולצרוך מידע במקביל.

<h3 dir="ltr" align="left"><code>Offset</code></h3>

- **במילים פשוטות:** מספר המיקום של הודעה בתוך מחיצה.
- **בפרויקט:** משמש לעקיבות, לחידוש קריאה ול־<bdi dir="ltr"><code>Replay</code></bdi>.

<h3 dir="ltr" align="left"><code>Checkpoint</code></h3>

- **במילים פשוטות:** נקודת התקדמות שמורה של תהליך רציף.
- **בפרויקט:** מאפשר ל־<bdi dir="ltr"><code>Spark Streaming</code></bdi> להמשיך מן המקום האחרון לאחר הפעלה מחדש, בלי להתחיל הכול מהתחלה.

<h3 dir="ltr" align="left"><code>Streaming</code></h3>

- **במילים פשוטות:** שירות ארוך־חיים שמעבד אירועים כשהם מגיעים.
- **בפרויקט:** מפרסם תמונה מהירה במצב <bdi dir="ltr"><code>PROVISIONAL</code></bdi>.

<h3 dir="ltr" align="left"><code>Batch</code></h3>

- **במילים פשוטות:** עבודה תחומה שיש לה התחלה וסיום.
- **בפרויקט:** בונה מחדש יום מסחר סגור ומפרסמת נתונים במצב <bdi dir="ltr"><code>CERTIFIED</code></bdi>.

<h3 dir="ltr" align="left"><code>Airflow DAG</code></h3>

- **במילים פשוטות:** גרף משימות שמגדיר סדר ותלויות.
- **בפרויקט:** מתזמן ומנטר עבודות תחומות; הוא אינו מנהל את שירותי ה־<bdi dir="ltr"><code>Streaming</code></bdi>.

<h3 dir="ltr" align="left"><code>SparkSubmitOperator</code></h3>

- **במילים פשוטות:** רכיב של <bdi dir="ltr"><code>Airflow</code></bdi> ששולח עבודת <bdi dir="ltr"><code>Spark</code></bdi> לביצוע.
- **בפרויקט:** משאיר את החישוב ב־<bdi dir="ltr"><code>Spark</code></bdi> ואת התזמון והניטור ב־<bdi dir="ltr"><code>Airflow</code></bdi>.

<h3 dir="ltr" align="left"><code>Docker Compose</code></h3>

- **במילים פשוטות:** קובץ שמגדיר ומפעיל סביבת קונטיינרים מקומית שלמה.
- **בפרויקט:** מנהל את מחזור החיים של השירותים הארוכים.

<h3 dir="ltr" align="left"><code>Idempotency</code></h3>

- **במילים פשוטות:** אפשר להריץ פעולה שוב בלי ליצור תוצאה עסקית כפולה.
- **בפרויקט:** נשענת על מזהים דטרמיניסטיים, מפתחות עסקיים ו־<bdi dir="ltr"><code>Upsert</code></bdi>.

<h3 dir="ltr" align="left"><code>Lineage</code></h3>

- **במילים פשוטות:** היכולת לעקוב מתוצאה בחזרה למקור, לריצה ולגרסה.
- **בפרויקט:** מאפשרת להסביר, לחקור ולשחזר כל נתון שפורסם.

## שכבות הנתונים

<h3 dir="ltr" align="left"><code>Bronze</code></h3>

העותק הגולמי והבלתי־משתנה כפי שהתקבל. בפרויקט הוא נשמר ב־<bdi dir="ltr"><code>MinIO</code></bdi>.

<h3 dir="ltr" align="left"><code>Silver</code></h3>

נתונים נקיים, בעלי טיפוסים אחידים ומנורמלים, הנשמרים בקובצי <bdi dir="ltr"><code>Parquet</code></bdi>.

<h3 dir="ltr" align="left"><code>Gold</code></h3>

טבלאות מוכנות לצריכת המוצר ב־<bdi dir="ltr"><code>MariaDB</code></bdi>.

<h3 dir="ltr" align="left"><code>PROVISIONAL</code></h3>

נתון מהיר שטרם עבר את כל בדיקות סוף היום.

<h3 dir="ltr" align="left"><code>CERTIFIED</code></h3>

נתון שנבנה מחדש מן המקור ועבר את שערי האיכות.

<h3 dir="ltr" align="left"><code>Backfill</code></h3>

רכישה יזומה של תקופה היסטורית שחסרה במערכת.

<h3 dir="ltr" align="left"><code>Replay</code></h3>

עיבוד מחדש של אירועים שכבר נשמרו בארכיון הגולמי.

<h3 dir="ltr" align="left"><code>Freshness</code></h3>

גיל הנתון ביחס לזמן שבו היה צפוי להגיע.

<h3 dir="ltr" align="left"><code>Data Quality Gate</code></h3>

בדיקה חוסמת של שלמות, כפילויות, ערכים חסרים, תקינות מבנה <bdi dir="ltr"><code>OHLC</code></bdi> וטריות. אם הבדיקה נכשלת, הנתון אינו מקודם לשכבה המאושרת.

## מקורות שוק וחברות

<h3 dir="ltr" align="left"><code>IEX</code></h3>

מקור נתוני השוק החינמי של הפרויקט. הוא מייצג בורסה אחת בלבד, ולכן הכיסוי שלו חלקי.

<h3 dir="ltr" align="left"><code>SIP</code></h3>

הזנת השוק המאוחדת והרשמית של הבורסות האמריקאיות. היא מלאה יותר, אך בדרך כלל דורשת הרשאה בתשלום.

<h3 dir="ltr" align="left"><code>SEC EDGAR</code></h3>

המקור הרשמי לדיווחים של חברות ציבוריות בארצות הברית.

<h3 dir="ltr" align="left"><code>Company Facts / XBRL</code></h3>

נתונים חשבונאיים מובנים מתוך דיווחי החברה, למשל הכנסות, רווח, מזומן וחוב.

<h3 dir="ltr" align="left"><code>Corporate Action</code></h3>

אירוע כגון פיצול מניה או דיבידנד, שמשפיע על ניתוח היסטורי של המחיר.

<h3 dir="ltr" align="left"><code>XNYS session</code></h3>

יום מסחר תקף לפי לוח הבורסה של ניו יורק, כולל חגים וסגירות מוקדמות.

## ניתוח טכני וסיכון

<h3 dir="ltr" align="left"><code>SMA 20</code></h3>

ממוצע פשוט של עשרים מחירי הסגירה האחרונים. הוא מחליק רעש, אך מגיב באיחור לשינוי במחיר.

<h3 dir="ltr" align="left"><code>EMA 20 / 50</code></h3>

ממוצע שנותן משקל גדול יותר למחירים חדשים, ולכן מגיב מהר יותר מממוצע פשוט.

<h3 dir="ltr" align="left"><code>RSI</code></h3>

מדד מומנטום בסולם <bdi dir="ltr"><bdo dir="ltr"><code>0–100</code></bdo></bdi>. ערך קיצוני הוא אות לבדיקה, לא פקודת מסחר.

<h3 dir="ltr" align="left"><code>MACD</code></h3>

מדד מגמה ומומנטום שמבוסס על הפער בין ממוצעים מעריכיים.

<h3 dir="ltr" align="left"><code>ATR</code></h3>

מדד תנודתיות שמעריך כמה המחיר נע בדרך כלל. הוא אינו מנבא כיוון.

<h3 dir="ltr" align="left"><code>Buy Zone</code></h3>

טווח כניסה אפשרי המבוסס על תמיכה, ממוצעים ותנודתיות. זהו טווח תרחיש, לא מחיר קסם.

<h3 dir="ltr" align="left"><code>Stop</code></h3>

מחיר שמבטל את התזה ומגדיר מראש את הסיכון המרבי המתוכנן לעסקה.

<h3 dir="ltr" align="left"><code>Target 1 / 2</code></h3>

יעדי מימוש המבוססים על רמות התנגדות ועל מכפלות סיכון.

<h3 dir="ltr" align="left"><code>Risk/Reward</code></h3>

היחס בין הרווח המתוכנן להפסד המתוכנן. היחס אינו הסתברות להצלחה.

<h3 dir="ltr" align="left"><code>Position Sizing</code></h3>

חישוב מספר המניות לפי גודל התיק, מחיר העצירה ומגבלות החשיפה.

## בדיקה היסטורית ומודל

<h3 dir="ltr" align="left"><code>Backtest</code></h3>

ניסוי של כללי אסטרטגיה על נתוני עבר מאושרים.

<h3 dir="ltr" align="left"><code>Benchmark</code></h3>

נקודת ייחוס להשוואה. בפרויקט משתמשים ב־<bdi dir="ltr"><code>SPY</code></bdi>.

<h3 dir="ltr" align="left"><code>Look-ahead Bias</code></h3>

טעות שבה המודל משתמש במידע שלא היה ידוע בזמן ההחלטה.

<h3 dir="ltr" align="left"><code>Slippage</code></h3>

פער בין מחיר הביצוע המתוכנן למחיר שהיה אפשר לקבל בפועל.

<h3 dir="ltr" align="left"><code>Drawdown</code></h3>

הירידה משיא בתיק או באסטרטגיה אל השפל שבא אחריו.

<h3 dir="ltr" align="left"><code>Rule Score</code></h3>

ציון שקוף של הראיות הטכניות והפונדמנטליות. הוא אינו סיכוי לרווח.

<h3 dir="ltr" align="left"><code>Data Confidence</code></h3>

ציון של איכות הנתונים, הכיסוי, הטריות והמקור. גם הוא אינו סיכוי לרווח.

<h3 dir="ltr" align="left"><code>Model Probability</code></h3>

הסתברות מכוילת להגיע ל־<bdi dir="ltr"><bdo dir="ltr"><code>Target 1</code></bdo></bdi> לפני <bdi dir="ltr"><code>Stop</code></bdi>, ורק לאחר כניסה תקפה.

<h3 dir="ltr" align="left"><code>Expected R</code></h3>

תוחלת מתמטית ביחידות סיכון, לאחר שקלול הסתברות, רווח, הפסד ועלויות.

<h3 dir="ltr" align="left"><code>Calibration</code></h3>

בדיקה אם תחזיות של, למשל, <bdi dir="ltr"><bdo dir="ltr"><code>60%</code></bdo></bdi> מצליחות בערך בשישה מכל עשרה מקרים דומים.

<h3 dir="ltr" align="left"><code>Walk-Forward Validation</code></h3>

אימון על העבר ובדיקה על תקופה מאוחרת יותר, שוב ושוב ובסדר כרונולוגי.

<h3 dir="ltr" align="left"><code>NO_ENTRY</code></h3>

התרחיש פורסם, אך המחיר לא נכנס לטווח בזמן התוקף. התוצאה אינה נחשבת הפסד מסחר.

<h3 dir="ltr" align="left"><code>PREVIEW</code></h3>

תחזית מודל שמוצגת למחקר, אך אינה משנה את פעולת כללי <bdi dir="ltr"><bdo dir="ltr"><code>v1</code></bdo></bdi>.

<h3 dir="ltr" align="left"><code>ACTIVE</code></h3>

מודל שעבר שערי איכות, תקופת צל ואישור אנושי, ולכן רשאי להשפיע על הדירוג.

<h3 dir="ltr" align="left"><code>FALLBACK</code></h3>

מצב בטוח שבו אין מודל תקף. כללי <bdi dir="ltr"><bdo dir="ltr"><code>v1</code></bdo></bdi> נשארים פעילים, ולא מוצגת הסתברות ישנה או מומצאת.

## ארבע הבחנות שכדאי לזכור

- <bdi dir="ltr"><code>Fresh</code></bdi> אינו בהכרח <bdi dir="ltr"><code>Certified</code></bdi>.
- <bdi dir="ltr"><code>Confidence</code></bdi> אינו <bdi dir="ltr"><code>Probability</code></bdi>.
- <bdi dir="ltr"><code>Backfill</code></bdi> אינו <bdi dir="ltr"><code>Backtest</code></bdi>.
- <bdi dir="ltr"><code>FALLBACK</code></bdi> אינו כשל שקט; הוא סירוב מודע להציג מודל שלא הוכח.

</div>
