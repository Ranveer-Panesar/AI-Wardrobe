from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import classify, health

# Importing app.models registers all model classes with Base's metadata
# so create_all() below knows what tables to create.
import app.models  # noqa: F401

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(classify.router)
# Auth, wardrobe, and render routers get added here in later phases:
# app.include_router(auth.router, prefix="/auth", tags=["auth"])


@app.on_event("startup")
def on_startup():
    # Dev convenience: auto-create tables against SQLite.
    # Once you're on Postgres, replace this with proper Alembic migrations
    # so schema changes are tracked instead of silently auto-applied.
    Base.metadata.create_all(bind=engine)
