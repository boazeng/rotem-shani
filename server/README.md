# Rotem Shani — parking app server

FastAPI app that puts the parking simulation behind **Google sign-in** (via the
[`shared-auth`](https://github.com/boazeng/shared-auth) module), with a
**system-management screen** (user management, admin only) and an **admin-only
page**. Layout edits are saved to the server (no more local-only saving).

## Routes

| Path | Access | What |
|---|---|---|
| `/` | logged-in | → the simulation |
| `/sim/rotem-shani.html` | logged-in | the parking simulation (static) |
| `/dashboard/` | logged-in | the parking operations dashboard |
| `/manage` | **admin** | system management + user management UI |
| `/admin-only` | **admin** | a page only the admin can see |
| `/save`, `/reset` | **admin** | persist / clear the layout (the 💾 button) |
| `/login` `/auth/callback` `/logout` `/auth/users` … | (shared-auth) | Google sign-in + user CRUD |

Everything except the sign-in routes requires a logged-in Google account that an
admin has added under **/manage**.

## Run locally

```bash
cd server
python -m venv .venv && . .venv/Scripts/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e ../../shared-auth                       # the auth module
cp .env.example .env                                   # fill in the secrets
uvicorn app:app --reload --port 8100
```

To try it **without Google** (local only): set `AUTH_DISABLED=true` in `.env`
(the three required secrets can be dummy values) — every request is treated as
admin. Turn it off for anything real.

## Deploy (Lightsail/EC2 — Phase 2)

1. Small always-on instance; clone this repo (with Git LFS for the `.glb` models).
2. `pip install -r server/requirements.txt` + `pip install "git+https://github.com/boazeng/shared-auth.git"`.
3. Real `server/.env` (Google client id/secret from the existing bookkeeping
   client, a fresh `AUTH_SESSION_SECRET`, `AUTH_REDIRECT_URI=https://parking.newavera.co.il/auth/callback`).
4. Run under systemd: `uvicorn app:app --host 127.0.0.1 --port 8100`.
5. **Caddy** (or nginx) in front for automatic HTTPS on `parking.newavera.co.il`.
6. DNS: `parking.newavera.co.il` → the instance IP.
7. Google Cloud Console: add `https://parking.newavera.co.il/auth/callback` to
   the OAuth client's authorized redirect URIs.
