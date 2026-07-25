# פריסה — שרת מאובטח (FastAPI + כניסת Google)

מיולי 2026 הסימולציה מתארחת כ**אפליקציית FastAPI מאחורי כניסת Google**, על שרת קטן ותמידי ב-AWS Lightsail. זה מחליף את האירוח הסטטי הישן ב-S3/CloudFront (ראה [למטה](#האירוח-הישן-s3cloudfront--הוצא-משירות)).

## 🌐 הכתובת החיה

**https://parkin-sim-rotem.newavera.co.il**

הכניסה מפנה ל-`/sim/rotem-shani.html`. כל האתר (סימולציה, דשבורד, ניהול) **מאחורי כניסת Google** — רק אימייל שמנהל הוסיף רשאי להיכנס.

## מפת הנתיבים

| נתיב | גישה | תוכן |
|---|---|---|
| `/` | מחובר | → הסימולציה |
| `/sim/rotem-shani.html` | מחובר | הסימולציה (סטטי, כולל המודלים) |
| `/dashboard/` · `/sim/admin/` | מחובר | לוח בקרה תפעולי |
| `/manage` | **admin** | ניהול מערכת + ניהול משתמשים |
| `/admin-only` | **admin** | עמוד שרק מנהל רואה |
| `/rec` · `/rec/files/*` | **admin** | סרטונים שמורים (MP4) |
| `/save` · `/reset` | **admin** | שמירת/איפוס הפריסה לדיסק (כפתור 💾) |
| `/login` `/auth/callback` `/auth/users` `/logout` … | (shared-auth) | כניסת Google + CRUD משתמשים |

## הרכיבים (חשבון AWS 824980746386)

| רכיב | ערך |
|---|---|
| **Lightsail instance** | `parking-sim-rotem` — Ubuntu 24.04, `micro_3_0` (1GB RAM), us-east-1 |
| **IP סטטי** | `44.223.250.97` |
| **פורטים** | 22 (SSH), 80/443 (Caddy) |
| **קוד** | git clone ב-`/opt/rotem` (repo `boazeng/rotem-shani`) |
| **אפליקציה** | systemd service `rotem` — `uvicorn app:app` על `127.0.0.1:8100`, WorkingDirectory `/opt/rotem/server` |
| **HTTPS** | **Caddy** — reverse-proxy ל-:8100 + תעודת Let's Encrypt אוטומטית (`/etc/caddy/Caddyfile`) |
| **אימות** | מודול [`shared-auth`](https://github.com/boazeng/shared-auth) (FastAPI, Google OIDC) — מותקן מ-`/opt/shared-auth` |
| **DB משתמשים** | SQLite ב-`/opt/rotem/database/auth.db` |
| **וידאו** | `ffmpeg` (המרה ל-MP4), נשמר ב-`/opt/rotem/recordings/` |
| **super-admin** | `boazen@gmail.com` (תמיד admin, לא ניתן להסרה) |

## SSH לשרת

```bash
ssh -i "C:\Users\User\Aiprojects\env\parking-sim-rotem-key.pem" ubuntu@44.223.250.97
```

## עדכון השרת מהריפו

יש סקריפט `update.sh` על השרת (`/opt/rotem/update.sh`, לא מנוהל בגיט) — מגבה כל פריסה שנשמרה חי, מושך את הקוד העדכני מ-main, ומפעיל מחדש:

```bash
sudo /opt/rotem/update.sh
```

מה שהוא עושה: אם `simulation/rotem_saved.json` שונה בזמן ריצה (כפתור 💾) — מגבה אותו ל-`rotem_saved.server-<זמן>.json` ומשחזר לגרסת git כדי ש-`git pull --ff-only` יעבור נקי; מושך; ואם היה שינוי — `systemctl restart rotem`.

> ⚠️ להריץ git ישירות בשרת **עם sudo** (הסקריפט עושה זאת), אחרת `.git/FETCH_HEAD` נשאר בבעלות root וריצה כ-ubuntu תיכשל בהרשאות.

## תלויות שמותקנות בשרת (מעבר ל-`requirements.txt`)

- **`python-multipart`** — נדרש להעלאת הווידאו (`/rec/upload`).
- **`ffmpeg`** (חבילת מערכת: `sudo apt install ffmpeg`) — המרת WebM → MP4.
- **Caddy** (מ-repo הרשמי של Caddy).

## הגדרות סביבה — `server/.env` (בשרת בלבד, לא בגיט)

הסודות מגיעים מתוך ה-`.env` הראשי (`C:\Users\User\Aiprojects\env\.env`) — הועתקו **רק** מפתחות ה-auth:

| משתנה | תפקיד |
|---|---|
| `GOOGLE_OAUTH_CLIENT_ID` / `_SECRET` | ה-OAuth client הקיים (משותף עם bookkeeping) |
| `AUTH_SESSION_SECRET` | חתימת עוגיית ה-session |
| `AUTH_EMERGENCY_TOKEN` | כניסת חירום `/emergency-login?token=…` |
| `AUTH_SUPER_ADMIN_EMAIL` | `boazen@gmail.com` |
| `AUTH_REDIRECT_URI` | `https://parkin-sim-rotem.newavera.co.il/auth/callback` |
| `AUTH_DB_PATH` | `/opt/rotem/database/auth.db` |
| `AUTH_DISABLED` | `true` = כיבוי אימות לגמרי (כולם admin) — **לפיתוח בלבד**; ב-production `false` |

## DNS ו-Google (חד-פעמי)

- **DNS (Cloudflare):** רשומת `A` — `parkin-sim-rotem` → `44.223.250.97`, במצב **DNS-only (ענן אפור)**. אם Proxied (כתום) — Caddy לא יוכל להנפיק תעודת HTTPS.
- **Google Cloud Console:** ב-OAuth client, תחת *Authorized redirect URIs*, יש `https://parkin-sim-rotem.newavera.co.il/auth/callback`.

## הקמה מאפס (אם צריך לשחזר את השרת)

1. Lightsail: instance Ubuntu 24.04 `micro_3_0` + IP סטטי + פורטים 22/80/443.
2. `apt install python3-venv git git-lfs ffmpeg caddy`; `git lfs install`.
3. `git clone …/rotem-shani.git /opt/rotem` → `git lfs pull`.
4. venv ב-`/opt/rotem/server`; `pip install -r requirements.txt` + `pip install /opt/shared-auth`.
5. `server/.env` עם הסודות (ראה למעלה).
6. systemd unit `rotem` (uvicorn על 8100) + `Caddyfile` (reverse_proxy לדומיין).
7. DNS + Google redirect כנ"ל.

## האירוח הישן (S3/CloudFront) — הוצא משירות

הפריסה הישנה הייתה אתר **סטטי ציבורי** ב-S3 מאחורי CloudFront (`dmfotw8kwayzt.cloudfront.net`), שהתעדכן ב-GitHub Actions בכל push. **workflow הפריסה הוסר** (commit "retire the S3/CloudFront deploy workflow"), ולכן push **לא** מפרס יותר ל-CloudFront. הפריסה כיום היא רק שרת ה-Lightsail דרך `update.sh`.

> אם ה-bucket/distribution הישנים עדיין קיימים — אפשר להשאירם לצפייה ציבורית ללא אימות, או למחוק. שקול למחוק כדי שלא יישאר עותק לא-מאובטח שעוקף את הכניסה.
