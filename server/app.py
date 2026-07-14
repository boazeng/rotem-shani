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
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # read server/.env before shared-auth reads os.environ

from fastapi import Depends, FastAPI, Request                       # noqa: E402
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


# ---- static apps (behind the auth middleware) ----
# the simulation (HTML + JSON + PNG + the .glb models) and the ops dashboard
app.mount("/dashboard", StaticFiles(directory=str(DASH_DIR), html=True), name="dashboard")
app.mount("/sim", StaticFiles(directory=str(SIM_DIR), html=True), name="sim")
