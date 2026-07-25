"""Rotem Shani — parking app server.

A small FastAPI app that puts the parking simulation behind Google sign-in
(via the shared-auth module), adds a system-management screen with user
management (admin only), and persists layout edits to disk.

Run locally:
    cd server
    cp .env.example .env          # fill in secrets (or set AUTH_DISABLED=true)
    pip install -r requirements.txt
    pip install -e ../../shared-auth
    uvicorn app:app --reload --port 8100
"""
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # read server/.env before shared-auth reads os.environ

from fastapi import Depends, FastAPI, File, Request, UploadFile      # noqa: E402
from fastapi.responses import HTMLResponse, RedirectResponse         # noqa: E402
from fastapi.staticfiles import StaticFiles                          # noqa: E402

from shared_auth import install_auth, current_user                  # noqa: E402

# ---- paths ----
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                     # the repo root (parking sim)
SIM_DIR = ROOT / "simulation"
DASH_DIR = ROOT / "admin"              # the parking operations dashboard (built earlier)
SAVED_FILE = SIM_DIR / "rotem_saved.json"
TEMPLATES = HERE / "templates"
RECORDINGS_DIR = ROOT / "recordings"   # saved videos (untracked; served behind auth)
RECORDINGS_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Rotem Shani — Parking", docs_url=None, redoc_url=None)

# ---- authentication (Google sign-in + roles + user management) ----
auth = install_auth(
    app,
    db_path=os.getenv("AUTH_DB_PATH", str(ROOT / "database" / "auth.db")),
    redirect_uri=os.getenv("AUTH_REDIRECT_URI",
                           "https://parking.newavera.co.il/auth/callback"),
    initial_users=[{"email": "boazen@gmail.com", "role": "admin"}],
)
require_role = auth["require_role"]


def _page(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


# ============================ app routes ============================

@app.get("/", include_in_schema=False)
async def home(request: Request):
    """Logged-in landing: straight into the simulation."""
    return RedirectResponse("/sim/rotem-shani.html")


# --- layout persistence: same /save + /reset API the local serve.py exposes, so
#     the simulation's 💾 button works unchanged — but now writes to the server
#     and is gated to admins by the auth middleware + role check. ---
@app.post("/save", include_in_schema=False)
async def save_layout(request: Request, _admin: dict = Depends(require_role("admin"))):
    data = await request.json()
    SAVED_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"ok": True}


@app.post("/reset", include_in_schema=False)
async def reset_layout(_admin: dict = Depends(require_role("admin"))):
    if SAVED_FILE.exists():
        SAVED_FILE.unlink()
    return {"ok": True}


# --- system management screen (admin only) + user management UI ---
@app.get("/manage", response_class=HTMLResponse, include_in_schema=False)
async def manage(_admin: dict = Depends(require_role("admin"))):
    # user CRUD is served by shared-auth at /auth/users; this page is its UI
    return _page("manage.html")


# --- a page ONLY the system admin can see ---
@app.get("/admin-only", response_class=HTMLResponse, include_in_schema=False)
async def admin_only(user: dict = Depends(require_role("admin"))):
    return _page("admin_only.html").replace("{{EMAIL}}", user["email"])


# --- video recordings: the sim uploads a WebM here; we transcode to MP4 (H.264)
#     with ffmpeg so it plays anywhere, and save it on the server. ---
@app.post("/rec/upload", include_in_schema=False)
async def rec_upload(file: UploadFile = File(...), _admin: dict = Depends(require_role("admin"))):
    ts = time.strftime("%Y%m%d-%H%M%S")
    tmp = RECORDINGS_DIR / f".upload-{ts}.webm"
    with tmp.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        out = RECORDINGS_DIR / f"rotem-{ts}.mp4"
        try:
            subprocess.run(
                [ffmpeg, "-y", "-i", str(tmp), "-c:v", "libx264", "-preset", "veryfast",
                 "-crf", "23", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(out)],
                check=True, capture_output=True, timeout=600)
            tmp.unlink(missing_ok=True)
            return {"ok": True, "name": out.name, "url": f"/rec/files/{out.name}", "mp4": True}
        except Exception as exc:  # conversion failed -> keep the webm so nothing is lost
            keep = RECORDINGS_DIR / f"rotem-{ts}.webm"
            tmp.rename(keep)
            return {"ok": True, "name": keep.name, "url": f"/rec/files/{keep.name}",
                    "mp4": False, "warn": f"mp4 conversion failed: {exc}"}
    keep = RECORDINGS_DIR / f"rotem-{ts}.webm"
    tmp.rename(keep)
    return {"ok": True, "name": keep.name, "url": f"/rec/files/{keep.name}", "mp4": False,
            "warn": "ffmpeg not installed — saved as webm"}


@app.get("/rec/list", include_in_schema=False)
async def rec_list(_admin: dict = Depends(require_role("admin"))):
    files = sorted(
        (p for p in RECORDINGS_DIR.iterdir()
         if p.suffix in (".mp4", ".webm") and not p.name.startswith(".")),
        key=lambda p: p.stat().st_mtime, reverse=True)
    return {"files": [{"name": p.name, "url": f"/rec/files/{p.name}",
                       "size": p.stat().st_size, "mtime": int(p.stat().st_mtime)} for p in files]}


@app.post("/rec/delete", include_in_schema=False)
async def rec_delete(body: dict, _admin: dict = Depends(require_role("admin"))):
    name = os.path.basename(body.get("name", ""))   # prevent path traversal
    p = RECORDINGS_DIR / name
    if p.exists() and p.suffix in (".mp4", ".webm"):
        p.unlink()
    return {"ok": True}


@app.get("/rec", response_class=HTMLResponse, include_in_schema=False)
async def rec_page(_admin: dict = Depends(require_role("admin"))):
    return _page("recordings.html")


# ---- static apps (behind the auth middleware) ----
# the simulation (HTML + JSON + PNG + the .glb models) and the ops dashboard
app.mount("/rec/files", StaticFiles(directory=str(RECORDINGS_DIR)), name="rec-files")
app.mount("/dashboard", StaticFiles(directory=str(DASH_DIR), html=True), name="dashboard")
# the sim's "מרכז ניהול" button opens ./admin/index.html (relative to /sim/rotem-shani.html) — serve the
# dashboard there too so that link resolves. MUST be registered before /sim so it matches first.
app.mount("/sim/admin", StaticFiles(directory=str(DASH_DIR), html=True), name="sim-admin")
app.mount("/sim", StaticFiles(directory=str(SIM_DIR), html=True), name="sim")
