# ארכיטקטורה — מבנה הקוד ומודל הנתונים

## סקירה

הכל בקובץ יחיד: **`simulation/rotem-shani.html`** (~1335 שורות). מבנה: HTML/CSS למעלה (HUD, סרגלים, תפריט), ואז `<script>` אחד גדול עם כל הלוגיקה בתוך IIFE אסינכרוני (`(async function(){ ... })()`).

הספריות נטענות מ-CDN (Three.js **r128**):
```html
<script src=".../three.js/r128/three.min.js"></script>
<script src=".../GLTFLoader.js"></script>
<script src=".../DRACOLoader.js"></script>
<script src=".../environments/RoomEnvironment.js"></script>
```

## מערכת הקואורדינטות (חשוב!)

- **נתונים** נשמרים ב-**(east, north) במטרים**, כאשר הראשית (0,0) היא הפינה עם ה-north/east המינימליים בתכנון ה-DXF.
- **יחידות:** מטרים. (מקור ב-DXF היה ס"מ; מגש = 505×215 ס"מ → 5.05×2.15 מ׳.)
- **`bbox_m = [21.24, 26.1]`** — רוחב (east) × עומק (north) של הבור. **אסור לשנות** — ממנו נגזרים cx/cn שמיישרים את הכל.
- **מיפוי לעולם Three.js:**
  ```js
  const cx = W/2, cn = D/2;          // W=bbox_m[0]=21.24, D=bbox_m[1]=26.1
  px = (east)  => east - cx;          // worldX
  pz = (north) => -(north - cn);      // worldZ  (צפון = -Z)
  // Y = מעלה (גובה)
  ```
  כלומר **+north = -Z בעולם**. ⚠️ המצפן של המשתמש הפוך מציר ה-north הפנימי (מה שהמשתמש קורא "צפון" הוא north=0, הקצה התחתון).

- **סיבוב:** במידע `rot` במעלות (סגנון DXF, CCW סביב north-up). בעולם: `rotation.y = -rot * π/180`.

## קבצי הנתונים

### `rotem_layout.json` — גאומטריית הבסיס (המבנה)
```jsonc
{
  "units": "meters",
  "outline": [[east,north], ...],   // מצולע קו-המתאר של הבור (15 קודקודים)
  "bbox_m": [21.24, 26.1],          // אסור לשנות
  "trays": [ {"pos":[e,n], "rot":deg, "num":N}, ... ],  // 22 מגשים (פריסת מקור)
  "lift": {"pos":[e,n], "rot":deg},
  "turntable": {"pos":[e,n]},
  "floor_height_m": 3.0
}
```
> נערך פעמיים כדי **להזיז קירות** (הזזת קודקודי ה-`outline`, בלי לגעת ב-`bbox_m`). גיבויים: `rotem_layout.backup.json` (לפני הקיר הראשון), `.backup2.json` (לפני הקיר השני).

### `rotem_saved.json` — הפריסה השמורה (עריכות המשתמש)
נטען **בעדיפות** על פני הבסיס. מכיל את מיקומי כל האובייקטים הניתנים לעריכה:
```jsonc
{
  "version": 1,
  "trays":     [{"pos":[e,n],"rot":deg,"num":N}, ...],
  "lift":      {"pos":[e,n],"rot":deg},
  "turntable": {"pos":[e,n],"rot":deg},
  "e1":        [e, n],
  "walls":     [{"pos":[e,n],"rot":deg,"len":m}, ...],   // קירות שהמשתמש בנה
  "fixtures":  [{"pos":[e,n],"rot":deg}, ...]            // גופי פלורוסנט
}
```
נכתב ע"י `POST /save` (דרך `serve.py`).

### קבצים נלווים
- **`plan_overlay.png`** — שכבת השרטוט (קווי ה-DXF ב-blueprint שקוף), מיושרת מדויק ל-`bbox_m`. ממופה כטקסטורה על הרצפה.
- **`sensors_6cat.json`** — מיקומי חיישנים (מהסימולציה המקורית של beit-el; לא בשימוש פעיל כרגע).
- **`models/cars/*.glb`** — מודלי הרכב (Git LFS).

## מבנה הקוד (סדר ב-`<script>`)

1. **טעינת `L`** — `fetch('rotem_layout.json')`.
2. **Scene / camera / renderer** — `NoToneMapping`, `outputEncoding=sRGB`.
   - `carEnv` — env map ל**רכבים בלבד** (PMREM מ-RoomEnvironment). לא `scene.environment` (זה הלבין הכל).
3. **מסגרת קואורדינטות** — `px/pz`, `cx/cn`, `H` (גובה קומה).
4. **תאורה** — `hemi`, `amb`, `key` (directional חלש לצל). + `makeFixture()` לגופי פלורוסנט.
5. **בניית הבור** — רצפה/קירות/תקרה מ-`outline`; `planMesh` (overlay); `grid`.
6. **מגשים + רכבים** — `makeTray`, `makeCar` (מודל אמיתי או fallback קופסה), `labelMaterial` (מספר), `makeCenterMarker`.
7. **טעינת פריסה שמורה** — `rotem_saved.json` → `localStorage` → בסיס.
8. **בניית המגשים** מ-`sourceTrays`.
9. **טעינת מודלי רכב** (אסינכרוני, לא-חוסם) והחלפת הקופסאות.
10. **פלורוסנטים** (movable), **צלחת**, **E1**, **קירות משתמש**, **מעלית**, **קווי עזר**.
11. **HUD + toggles** + החלת ברירות מחדל.
12. **מניפולציה** — בחירה/גרירה/סיבוב/מחיקה; מצב עריכה (`editMode`); בניית קירות.
13. **שמירה/טעינה/איפוס** — `saveLayout`, `resetSim`, `resetLayout`, `captureInitial`.
14. **מנוע תרחישים** — תור-משימות (`runTasks`, `advanceAnim`), `playCar`, בלוק 1/2, פותר חידה.
15. **שליטת מצלמה** (orbit) + מצפן + לולאת רינדור.

## אובייקטים ניתנים לעריכה (`movables`)

מערך `movables` מכיל את כל מה שאפשר לבחור/לגרור/לסובב/למחוק:
- **מגשים** (`isTray`, `num`)
- **מעלית** (`isLift`) — פלטת המעלית (`liftPlatform`) עולה בנפרד מהעמודים
- **צלחת סיבוב** (`isTurntable`)
- **E1** (`isEntry`)
- **קירות** (`isWall`, `len`)
- **פלורוסנטים** (`isFixture`)

בחירה = raycast מול `movables`; גרירה במישור y=0 (משנה x/z); סיבוב Q/E; מחיקה Delete. הכל דורש **מצב עריכה** (`editMode`, כפתור 🔒 עדכן).

## מנוע האנימציה (תור-משימות)

- `runTasks([task,...])` — מריץ רצף משימות ברצף.
- כל **task** = `{ tray, steps:[...], end }`.
- סוגי **step**: `move` (X/Z), `spin` (סיבוב מלא), `turn` (סיבוב לזווית), `liftup` (עלייה ב-Y + פלטת מעלית).
- `advanceAnim(dt)` מקדם את המשימה הנוכחית; בסיום → `startNextTask`.
- זמנים נשלטים מ-`CFG` (`travel`, `spin`, `lift`) בתפריט ⚙.

## מודל התאורה

- **ברירת מחדל = חושך מוחלט** (`tDark` דלוק): `hemi/amb/key = 0`, רקע שחור, ו-`envMapIntensity=0` על הרכבים — כך שרק הפלורוסנטים מאירים.
- כשמכבים "חושך מוחלט": `hemi=0.16, amb=0.06, key=0.25`, ו-env חוזר לרכבים.
- **גופי פלורוסנט** = קבוצת `fixtures`; כל אחד = פס `MeshBasic` זוהר + `PointLight`. `tFluor` מכבה/מדליק (הסתרת הקבוצה מדלגת גם על אורות-הילדים ברינדור).
- **צבע רכב:** גוף = `MeshLambert` (חי, בלי ברק/env). זכוכית/כרום = חומרים מקוריים + `carEnv`. חשוב: `ACESFilmicToneMapping` **הלבין** צבעים (אדום→ורוד) — הוחלף ל-`NoToneMapping`.
