# Rotem Shani — Robotic Parking Simulation

סימולציית חניון רובוטי לפרויקט "רותם שני", נבנתה מתוך תכנון DXF/DWG אמיתי.

## תוכן

- `simulation/rotem-shani.html` — הסימולציה (Three.js, נפתחת בדפדפן)
- `simulation/serve.py` — שרת מקומי פשוט להרצה
- `simulation/models/` — מודלים תלת-ממדיים (`.glb`), מנוהלים דרך **Git LFS**
- `simulation/*.json` — נתוני פריסה, חיישנים ותצורה
- `dxf_out/rotem.dxf` — התכנון המקורי

## הרצה

```bash
cd simulation
python serve.py
```

> ⚠️ הקבצים הגדולים (`*.glb`) מנוהלים ב-Git LFS. לפני clone ודאו ש-Git LFS מותקן:
> ```bash
> git lfs install
> git clone https://github.com/boazeng/rotem-shani.git
> ```
