"""
Pydantic schemas for the wardrobe endpoints (Phase 2).

GarmentResponse    — what the API returns for a single garment item.
GarmentPatchRequest — what the user sends to correct a misclassified field.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class GarmentResponse(BaseModel):
    """Matches the API contract shape for POST /wardrobe/items and GET /wardrobe/items."""
    id: str
    category: str
    category_confidence: float = Field(..., ge=0, le=1)
    pattern: str
    formality: str
    dominant_colors: list[str]
    image_url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class GarmentPatchRequest(BaseModel):
    """All fields optional — user sends only what they want to correct."""
    category: str | None = None
    pattern: str | None = None
    formality: str | None = None


class WardrobeListResponse(BaseModel):
    items: list[GarmentResponse]
    total: int
