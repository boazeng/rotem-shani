# פריסה ל-AWS — S3 + CloudFront + פריסה אוטומטית

הסימולציה מתארחת כאתר סטטי על **S3 מאחורי CloudFront** (HTTPS), ומתעדכנת **אוטומטית** בכל דחיפה ל-main דרך GitHub Actions.

## 🌐 כתובת האתר (חי)

**https://dmfotw8kwayzt.cloudfront.net/rotem-shani/rotem-shani.html**

(הכתובת הבסיסית `https://dmfotw8kwayzt.cloudfront.net/` מפנה אוטומטית לסימולציה.)

## מבנה ב-AWS (חשבון 824980746386, region us-east-1)

| משאב | ערך |
|---|---|
| **S3 bucket** | `parking-sim-frontend-824980746386` (פרטי — נגיש רק דרך CloudFront) |
| מבנה תיקיות | `rotem-shani/` (HTML, JSON, PNG) · `rotem-shani/models/` (מודלי `.glb`) |
| **CloudFront** | distribution `E2QO66F9BFH2JK` → `dmfotw8kwayzt.cloudfront.net` |
| גישה ל-S3 | Origin Access Control (OAC) `E3OU890K99DNEA` + bucket policy |
| **תפקיד פריסה (OIDC)** | `arn:aws:iam::824980746386:role/parking-sim-github-deploy` |

> "parking sim" = ה-bucket (הפרויקט); תחתיו התיקייה `rotem-shani/`, ובתוכה `models/` — כפי שהתבקש.

## פריסה אוטומטית (CI/CD)

הקובץ [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) רץ בכל **push ל-main** שנוגע ב-`simulation/**`:

1. אימות ל-AWS דרך **GitHub OIDC** (ללא מפתחות AWS שמורים בריפו).
2. **סנכרון החכם של המודלים:** קבצי ה-`.glb` (LFS, ~183MB) נמשכים ומסונכרנים **רק אם הם השתנו** בדחיפה. עריכות HTML/JSON רגילות **לא** מושכות LFS — חוסך רוחב-פס.
3. `aws s3 sync` של קבצי האתר → `s3://.../rotem-shani/`.
4. `cloudfront create-invalidation` — מרענן את המטמון מיד.

**כלומר:** אתה עורך, `git push` (או `.\sync.ps1`), וכעבור 1–2 דקות האתר החי מתעדכן לבד. אפשר גם להריץ ידנית מלשונית **Actions → Run workflow**.

## עדכון ידני (אם צריך, בלי לחכות ל-CI)

```bash
aws s3 sync simulation/ "s3://parking-sim-frontend-824980746386/rotem-shani/" --delete \
  --exclude "*.backup*.json" --exclude "serve.py" --exclude "SUMMARY.md"
aws cloudfront create-invalidation --distribution-id E2QO66F9BFH2JK --paths "/*"
```

## הערות

- **שמירה (💾):** באירוח סטטי אין שרת (`serve.py`), לכן כפתור השמירה נופל חזרה ל-`localStorage` של הדפדפן (נשמר בדפדפן, לא בקובץ המשותף). הפריסה מיועדת לצפייה/הדגמה; לעריכה-ושמירה-לקובץ הרץ מקומית עם `python serve.py` (ראה [SETUP.md](SETUP.md)).
- **תלויות CDN:** Three.js נטען מ-jsdelivr/cdnjs (HTTPS) — עובד היטב מאחורי CloudFront.
- **עלות:** CloudFront PriceClass_100 (US/EU), S3 ~200MB. עלות זניחה לתעבורה נמוכה.
- **רוחב-פס LFS:** כל פריסה שכוללת שינוי מודלים מושכת ~183MB LFS ב-Actions. שינויי מודלים נדירים, אז זה בגבולות המכסה החינמית (1GB/חודש). שינויי קוד/פריסה רגילים לא נספרים.
