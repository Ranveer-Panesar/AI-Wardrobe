"""
Pydantic schemas for the outfit generation endpoints (Phase 3).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class OutfitGenerateRequest(BaseModel):
    count: int = Field(default=6, ge=1, le=20, description="Max outfits to return")
    occasion: str = Field(default="casual", description="Target occasion: casual, business, formal, evening, wedding, sport")
    style: str | None = Field(default=None, description="Style preference: Classic, Minimalist, Streetwear, Vintage, Bohemian, Athleisure")
    season: str | None = Field(default=None, description="Season preference: Spring, Summer, Autumn, Winter")
    fit: str | None = Field(default=None, description="Fit preference: Slim Fit, Regular, Oversized, Relaxed")


class OutfitItem(BaseModel):
    """A single scored outfit combo, as returned by the API and persisted to DB."""
    id: str
    garment_ids: list[str]
    score: float = Field(..., ge=0, le=1)
    style_tags: dict[str, Any] = Field(default_factory=dict)
    name: str | None = None
    reasoning: str | None = None
    occasion: str | None = None

    model_config = {"from_attributes": True}



class OutfitGenerateResponse(BaseModel):
    outfits: list[OutfitItem]


class SavedOutfitsResponse(BaseModel):
    outfits: list[OutfitItem]
    total: int
