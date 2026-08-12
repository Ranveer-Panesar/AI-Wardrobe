from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Basic liveness check — is the API process up."""
    return {"status": "ok"}


@router.get("/health/db")
def health_check_db(db: Session = Depends(get_db)):
    """Readiness check — can we actually reach the database."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
