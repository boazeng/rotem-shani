# התקנה והרצה — מעבר למחשב אחר

## דרישות

| כלי | לשם מה | חובה? |
|---|---|---|
| **Python 3** | שרת מקומי (`serve.py`) | כן |
| **Git + Git LFS** | שכפול הפרויקט (המודלים גדולים, ב-LFS) | כן, למעבר בין מחשבים |
| דפדפן מודרני (Chrome/Edge/Firefox) | הרצת הסימולציה (WebGL) | כן |
| חיבור אינטרנט | ספריות Three.js נטענות מ-CDN | כן (בהרצה) |
| **ODA File Converter** | רק אם רוצים להמיר מחדש DWG→DXF | לא (רק לבנייה מחדש) |
| **Node.js** | רק אם רוצים לעבד/להמיר מודלי GLB מחדש | לא |

> הסימולציה טוענת את Three.js, GLTFLoader, DRACOLoader ו-RoomEnvironment מ-CDN (jsdelivr/cdnjs). לכן נדרש אינטרנט בהרצה. אם רוצים עבודה לגמרי-אופליין, צריך להוריד את הספריות מקומית ולעדכן את תגי ה-`<script>`.

## מעבר למחשב חדש (מומלץ — דרך Git)

הפרויקט כבר ב-GitHub: **`github.com/boazeng/rotem-shani`**, עם **Git LFS** לקבצי `.glb`.

```bash
# פעם אחת במחשב החדש:
git lfs install

# שכפול:
git clone https://github.com/boazeng/rotem-shani.git
cd rotem-shani/simulation
python serve.py
```

⚠️ **חובה `git lfs install` לפני ה-clone** — אחרת קבצי ה-`.glb` יגיעו כ-pointers ריקים והרכבים לא ייטענו (יהיו קופסאות).

### לשמור עבודה חזרה ל-GitHub
```bash
git add -A
git commit -m "תיאור השינוי"
git push
```

## מעבר ידני (בלי Git)

העתק את **כל תיקיית `rotem shani`**. הקבצים ההכרחיים להרצה:
```
simulation/rotem-shani.html      ← הסימולציה
simulation/serve.py              ← השרת
simulation/rotem_layout.json     ← גאומטריית הבסיס (מבנה)
simulation/rotem_saved.json      ← הפריסה השמורה שלך (מיקומי רכבים/קירות/פלורוסנטים)
simulation/plan_overlay.png      ← שכבת שרטוט ה-DWG
simulation/models/cars/*.glb     ← מודלי הרכב (~164MB)
```
(שאר הקבצים — `dxf_out/`, ה-DWG, backups — נחוצים רק לבנייה מחדש, לא להרצה.)

## הרצה

```bash
cd simulation
python serve.py            # ברירת מחדל פורט 8010
#   או פורט אחר:  python serve.py 8020
```
פתח בדפדפן: **http://localhost:8010/rotem-shani.html**

### חשוב — למה `serve.py` ולא סתם `http.server`?
`serve.py` הוא שרת קטן (רב-תהליכי) שמוסיף שני endpoints:
- `POST /save` — כותב את הפריסה ל-`rotem_saved.json` (קובץ אחד קבוע).
- `POST /reset` — מוחק את `rotem_saved.json`.

אם תריץ `python -m http.server` רגיל, כפתור **💾 שמור** לא יוכל לכתוב לקובץ — הוא ייפול חזרה לשמירה ב-`localStorage` של הדפדפן (עדיין נשמר ברענון, אבל לא לקובץ, ולא עובר בין מחשבים).

## בעיות נפוצות

| תסמין | סיבה | פתרון |
|---|---|---|
| הרכבים קופסאות אפורות | קבצי `.glb` לא ירדו (LFS) | `git lfs install` ואז `git lfs pull` |
| שמירה לא נשמרת לקובץ | רץ `http.server` במקום `serve.py` | הרץ `python serve.py` |
| הסצנה ריקה/שגיאה | אין אינטרנט (CDN) | ודא חיבור, או הורד ספריות מקומית |
| השרת נתקע | חיבור keep-alive של הדפדפן | `serve.py` כבר רב-תהליכי; אתחל אותו |
