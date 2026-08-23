"""
Wardrobe CRUD service — thin helpers between the router and SQLAlchemy.
No business logic lives here: just persistence + retrieval.
"""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.garment import Garment


# ---------------------------------------------------------------------------
# Garment helpers
# ---------------------------------------------------------------------------

def create_garment(
    db: Session,
    *,
    user_id: str,
    category: str,
    category_confidence: float,
    pattern: str,
    formality: str,
    dominant_colors: list[str],
    image_url: str,
    embedding: list[float] | None = None,
) -> Garment:
    garment = Garment(
        id=uuid.uuid4(),
        user_id=user_id,
        category=category,
        category_confidence=category_confidence,
        pattern=pattern,
        formality=formality,
        dominant_colors=dominant_colors,
        embedding=embedding,
        image_url=image_url,
    )
    db.add(garment)
    db.commit()
    db.refresh(garment)
    return garment


def get_garments_for_user(db: Session, user_id: str) -> list[Garment]:
    return (
        db.query(Garment)
        .filter(Garment.user_id == str(user_id))
        .order_by(Garment.created_at.desc())
        .all()
    )


def get_garment(db: Session, garment_id: str, user_id: str) -> Garment | None:
    """Returns the garment only if it belongs to the requesting user."""
    return (
        db.query(Garment)
        .filter(Garment.id == garment_id, Garment.user_id == str(user_id))
        .first()
    )


def patch_garment(db: Session, garment: Garment, updates: dict) -> Garment:
    """Apply a partial update dict to a garment and commit."""
    for field, value in updates.items():
        if value is not None:
            setattr(garment, field, value)
    db.commit()
    db.refresh(garment)
    return garment


def delete_garment(db: Session, garment: Garment) -> None:
    db.delete(garment)
    db.commit()
