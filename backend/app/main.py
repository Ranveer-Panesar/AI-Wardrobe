from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine
from app.routers import auth, classify, health
from app.routers import wardrobe, outfits, render

# Importing app.models registers all model classes with Base's metadata
# so create_all() below knows what tables to create.
import app.models  # noqa: F401

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

_cors_origins = [settings.FRONTEND_ORIGIN]
if settings.DEBUG:
    # Allow localhost variants during local development.
    # Never enabled in production.
    _cors_origins += [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(classify.router)
app.include_router(wardrobe.router)   # Phase 2 — wardrobe CRUD
app.include_router(outfits.router)    # Phase 3 — outfit generation
app.include_router(render.router)     # Phase 6 — VTON render jobs

# StaticFiles must be mounted at app-definition time (before routing begins),
# not inside on_startup. We mkdir here so the directory always exists when the
# mount is registered, even on a fresh checkout with no uploads yet.
_upload_dir = Path(settings.LOCAL_UPLOAD_DIR)
_upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_upload_dir)), name="uploads")

# Serve VTON render output images at /renders/<job_id>.jpg
_render_dir = Path("./renders")
_render_dir.mkdir(parents=True, exist_ok=True)
app.mount("/renders", StaticFiles(directory=str(_render_dir)), name="renders")


@app.on_event("startup")
def on_startup():
    # Dev convenience: auto-create tables against SQLite.
    # Once you're on Postgres, replace this with proper Alembic migrations
    # so schema changes are tracked instead of silently auto-applied.
    Base.metadata.create_all(bind=engine)
