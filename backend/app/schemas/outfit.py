"""
Pydantic schemas for the outfit generation endpoints (Phase 3).
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class OutfitGenerateRequest(BaseModel):
    count: int = Field(default=5, ge=1, le=20, description="Max outfits to return")


class OutfitItem(BaseModel):
    """A single scored outfit combo, as returned by the API and persisted to DB."""
    id: str
    garment_ids: list[str]
    score: float = Field(..., ge=0, le=1)
    # Probability-style breakdown over four style axes (values sum to ~1).
    style_tags: dict[str, float]

    model_config = {"from_attributes": True}


class OutfitGenerateResponse(BaseModel):
    outfits: list[OutfitItem]


class SavedOutfitsResponse(BaseModel):
    outfits: list[OutfitItem]
    total: int
