"""
Central app configuration, loaded from environment variables (.env file).
Using pydantic-settings so every value is typed and validated at startup
instead of failing later with a cryptic KeyError.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "AI Wardrobe API"
    ENV: str = "development"  # development | production
    DEBUG: bool = True

    # --- Database ---
    # Defaults to a local SQLite file so the app runs with zero setup.
    # Swap to a Postgres URL (e.g. postgresql+psycopg://user:pass@host/db)
    # once you move to Supabase/Neon/Render Postgres.
    DATABASE_URL: str = "sqlite:///./wardrobe.db"

    # --- Auth / JWT ---
    JWT_SECRET: str = "change-me-in-.env"  # MUST be overridden in production
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # --- CORS ---
    # The frontend origin(s) allowed to call this API.
    FRONTEND_ORIGIN: str = "http://localhost:5173"  # Vite's default dev port

    # --- Storage (filled in during Phase 2) ---
    STORAGE_MODE_DEFAULT: str = "local"  # "local" | "cloud"
    LOCAL_UPLOAD_DIR: str = "./uploads"

    # --- Render provider (filled in during Phase 6) ---
    RENDER_PROVIDER: str = "mock"  # "mock" | "colab" | "vendor_api"
    COLAB_RENDER_URL: str = ""
    VENDOR_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Import this singleton anywhere you need config: `from app.config import settings`
settings = Settings()
