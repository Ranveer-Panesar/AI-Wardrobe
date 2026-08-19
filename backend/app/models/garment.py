"""
DB models for Phase 2/3.

Garment — one clothing item belonging to a user, populated at upload time
          by the classification pipeline.
Outfit  — a scored combination of garments produced by the outfit engine;
          persisted so the VTON render endpoints (Phase 6) can reference
          outfits by ID without the client having to re-send garment lists.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.types import JSON

from app.database import Base
from app.models.user import GUID  # reuse the cross-DB UUID type defined in user.py


class Garment(Base):
    __tablename__ = "garments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Classification fields (set at upload, patchable by user) ---
    category = Column(String, nullable=False)
    category_confidence = Column(Float, nullable=False)
    pattern = Column(String, nullable=False)
    formality = Column(String, nullable=False)

    # Stored as a JSON array of "#rrggbb" hex strings.
    dominant_colors = Column(JSON, nullable=False, default=list)

    # 512-float Fashion-CLIP embedding — stored for Phase 4 ML compatibility
    # head; NULL if the caller didn't request it at upload time (they can
    # always re-upload to get it, or we backfill later).
    embedding = Column(JSON, nullable=True)

    # Relative path for local storage (e.g. "uploads/<uuid>.jpg") or a full
    # HTTPS URL once cloud storage is wired up in a later phase.
    image_url = Column(String, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Outfit(Base):
    __tablename__ = "outfits"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Ordered list of garment UUIDs (as strings) that make up this outfit.
    garment_ids = Column(JSON, nullable=False, default=list)

    # Composite score from the outfit engine (0–1).
    score = Column(Float, nullable=False)

    # Heuristic style probability breakdown, e.g.
    # {"casual": 0.7, "bold": 0.1, "formal": 0.05, "retro": 0.15}
    style_tags = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
