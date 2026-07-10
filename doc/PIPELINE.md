# צנרת הבנייה — איך נבנתה הסימולציה

מסמך זה מתאר **איך המבנה נגזר מה-DWG** ו**איך מוסיפים מודלי רכב** — נחוץ רק אם רוצים לבנות מחדש / להרחיב, לא להרצה רגילה.

## 1. מ-DWG לגאומטריה

### כלים
- **ODA File Converter** (חינמי, של Open Design Alliance) — להמרת DWG → DXF.
- **Python** עם `ezdxf`, `matplotlib`, `numpy` (`pip install ezdxf matplotlib numpy`).

### שלבים
1. **DWG → DXF:**
   ```bash
   # דרך ODA File Converter (GUI או CLI):
   #   inFolder outFolder ACAD2018 DXF 0 1 *.dwg
   ```
   התוצאה: `dxf_out/rotem.dxf`.

2. **חילוץ גאומטריה** (עם `ezdxf`):
   - זוהתה מערכת **Parkolay** — שכבות `PMX25-RAIL/CAR/LIFTS/SDP`, קירות `A_Walls conc`, `X_ref_Pit`.
   - **קו המתאר** = הפוליליין הסגור החיצוני ב-`A_Walls conc` (15 קודקודים, ~21×26מ׳).
   - **מגשים** = בלוקי `*U79`/`*U85` (5.05×2.15מ׳) — מיקום + זווית.
   - **צלחת/מעלית** = טקסט מקודד (היצג-מקלדת עברי) שפוענח: "צלחת סיבוב", "קו מעלית".
   - **יחידות** = ס"מ (אומת מריווח המגשים 530/215).

3. **נרמול ל-`rotem_layout.json`:** תרגום ל-(east, north) מטרים, origin בפינה המינימלית, שמירת `bbox_m`.

4. **`plan_overlay.png`:** רינדור קווי ה-DXF (LINE/LWPOLYLINE/CIRCLE) עם `matplotlib` על רקע שקוף, בגבולות **מדויקים** של `bbox_m` — כך שהתמונה מתמפה 1:1 כטקסטורה על הרצפה.

> **אשכולות קואורדינטות:** ב-DXF היו כמה עותקים/גיליונות. האשכול המכני (PMX25) סביב x≈62000–65000; ממנו חולצה הגאומטריה.

## 2. הזזת קירות

הזזת קיר = עריכת **קודקודי ה-`outline`** ב-`rotem_layout.json`, **בלי לשנות `bbox_m`** (כדי לא להזיז את כל המגשים/השרטוט).
- קיר ישר (למשל north=0): הזזת שני הקודקודים בציר north.
- קיר מוטה: הזזת שני הקודקודים לאורך הנורמל של הקיר (ניצב).
- תמיד לגבות תחילה (`rotem_layout.backup*.json`).

## 3. הוספת מודלי רכב

### 3.0 מאיפה הגיעו המודלים (מקור מול בשימוש)

יש **שתי תיקיות** עם תפקידים שונים:

```
parking systems/new 3d car model/    ← מקור גולמי (הורדות), מחוץ לגיט, נשאר רק במחשב הבנייה (18 קבצים)
        │  (11 מהם הועתקו + שמם קוצר)
        ▼
rotem shani/simulation/models/cars/  ← בתוך הריפו/LFS → עובר לכל מחשב עם git pull (12 קבצים)
        └─ 11 מ"new 3d car model" + ferrari_plain.glb (ממקור מוקדם יותר)
```

> **תיקיית `new 3d car model` אינה בגיט** ולא מסתנכרנת. הסימולציה קוראת **רק** מ-`simulation/models/cars/`. לכן כל מה שהמחשב השני צריך מגיע דרך הריפו — כולל הפרארי.

**מיפוי מקור → שם בסימולציה** (הותאם לפי גודל בייטים מדויק):

| קובץ מקור (`new 3d car model`) | → בסימולציה (`models/cars/`) |
|---|---|
| `130.glb` | `car130.glb` |
| `1970_plymouth_barracuda_440-6.glb` | `barracuda.glb` |
| `1971_plymouth_hemi_cuda.glb` | `hemicuda.glb` |
| `2011_mini_john_cooper_works_r56.glb` | `mini.glb` |
| `2015_mercedes-benz_s65_amg_coupe.glb` | `mercedes.glb` |
| `2016_volkswagen_golf_gti_clubsport_mk7.glb` | `golf.glb` |
| `2020_chevrolet_corvette_c8_stingray_convertible.glb` | `corvette.glb` |
| `65_chevy_malibu.glb` | `malibu.glb` |
| `ford_mustang_1965.glb` | `mustang.glb` |
| `hyundai_kona.glb` | `kona.glb` |
| `mersedes-benz_sl63_amg_free.glb` | `sl63.glb` |
| *(אין מקור בתיקייה)* | `ferrari_plain.glb` — fallback, קיים רק בריפו |

⚠️ **הפרארי חסר בתיקיית המקור.** הוא מוגן כל עוד הריפו קיים (ב-LFS), אבל בנייה מחדש **רק** מ-`new 3d car model` תשאיר אותו חסר. שווה לשמור עותק מקור שלו בנפרד.

**7 קבצי מקור שלא שובצו** (נשארים רק ב-`new 3d car model`, ~495MB, נדחו — ראה טבלת המלכודות למטה): `1968_volkswagen_beetle_lp`, `1975_triumph_tr6`, `1986_bmw_e30_fl_lp`, `gaz_13_chaika` (137MB), `mercedes_e_class_w212` (83MB), `oldsmobile_cutlass_supreme_sedan_71`, `renault_logan_2004` (125MB).

> השיבוץ המדויק של דגם→מספר חנייה מתועד ב-[FEATURES.md](FEATURES.md#מודלי-רכב).

### פורמט מועדף: **GLB** (קובץ יחיד, טקסטורות מוטמעות).

### שלבים
1. הורד `.glb` (למשל מ-Sketchfab; הורדה ישירה: GLB עם texture 1k/2k). שים ב-`simulation/models/cars/`.
2. הוסף ל-`MODEL_FILES` ו-`TRAY_MODEL` בקוד (`rotem-shani.html`):
   ```js
   const MODEL_FILES = { ..., myカ: { file: 'mycar.glb' } };
   const TRAY_MODEL  = { ..., 7: 'mycar', 18: 'mycar' };  // איזה מגש → איזה דגם
   ```
3. **נרמול אוטומטי** (`loadCarGLB`): מזהה ציר-גובה (הממד הקטן ביותר), מיישר את האורך לציר X של המגש, מתאים לגודל המגש (אורך ורוחב), ומניח על הרצפה. **אין צורך בכוונון ידני** לרוב.

### מלכודות במודלים (נתקלנו בהן!)
| בעיה | דוגמה | פתרון |
|---|---|---|
| **דחיסת Draco** | ה-Ferrari של three.js | פרוק offline: `gltf-transform` (עם `draco3dgltf`) → GLB רגיל. |
| **שני רכבים בקובץ** | beetle, bmw_e30 | לא ניתן לנרמל אוטומטית — נדחו. חפש גרסת "single mesh". |
| **כיפת-סביבה ענקית** | oldsmobile (278מ׳) | הרכב זעיר בתוך כיפה — נדחה. |
| **קובץ ענק** | logan 120MB, gaz_chaika 131MB/3.8M משולשים | כבד מדי לביצועים — נדחה. שאף ל-<30MB, <500k משולשים. |
| **צבע דהוי** | חומרי OBJ אפורים | הרכב מוצג עם טקסטורות מקוריות; ה-Ferrari נצבע פר-רכב. |

### המרות (אם צריך)
- **Draco → רגיל:** `npm i @gltf-transform/core @gltf-transform/extensions draco3dgltf`, ואז סקריפט שקורא וכותב בלי ה-extension.
- **OBJ → GLB:** `npx obj2gltf -i model.obj -o model.glb` (רק אם ל-OBJ יש MTL+טקסטורות תקינים).
- **FBX/3DS/DAE → GLB:** Blender (ייבוא → ייצוא GLB) או assimp. (`.max`/`.c4d` דורשים 3ds Max/Cinema4D.)

## 4. Git LFS (קבצים גדולים)

קבצי `.glb` מנוהלים ב-**Git LFS** (`.gitattributes`: `*.glb filter=lfs ...`).
```bash
git lfs install          # פעם אחת פר-מחשב
git lfs track "*.glb"    # כבר מוגדר
```
בלי LFS, ה-`.glb` יגיעו כ-pointers ריקים.

## 5. תלויות CDN (בהרצה)

Three.js r128 ותוספות נטענות מ-jsdelivr/cdnjs. אם רוצים אופליין מלא — הורד מקומית:
- `three.min.js`, `GLTFLoader.js`, `DRACOLoader.js` (+ decoder), `RoomEnvironment.js`
- עדכן את תגי ה-`<script>` בראש `rotem-shani.html`.
