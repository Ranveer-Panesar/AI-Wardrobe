"""
Outfit generation endpoints (Phase 3).

POST  /outfits/generate   — run the engine over the user's wardrobe, persist + return top N outfits
GET   /outfits/saved      — retrieve previously generated outfits for the user

The engine itself (outfit_engine.py) is pure Python with no DB imports,
so only this file touches SQLAlchemy when persisting the results.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.garment import Outfit
from app.models.user import User
from app.schemas.outfit import (
    OutfitGenerateRequest,
    OutfitGenerateResponse,
    OutfitItem,
    SavedOutfitsResponse,
)
from app.services.outfit_engine import GarmentData, generate_outfits
from app.services.wardrobe_service import get_garments_for_user

router = APIRouter(prefix="/outfits", tags=["outfits"])


def _garments_to_engine_data(garments) -> list[GarmentData]:
    """Convert ORM Garment objects to the engine's lightweight GarmentData DTOs."""
    return [
        GarmentData(
            id=str(g.id),
            category=g.category,
            pattern=g.pattern,
            formality=g.formality,
            dominant_colors=g.dominant_colors or [],
        )
        for g in garments
    ]


def _extract_meta(style_tags: dict | None) -> tuple[dict, dict]:
    """Separate _meta (name, reasoning, occasion) from the style percentage dictionary."""
    if not isinstance(style_tags, dict):
        return {}, {}
    meta = style_tags.get("_meta", {}) if isinstance(style_tags.get("_meta"), dict) else {}
    clean_tags = {k: v for k, v in style_tags.items() if k != "_meta"}
    return meta, clean_tags


def _persist_outfits(db: Session, user_id: str, scored_outfits) -> list[Outfit]:
    """Bulk-insert the scored outfits returned by the engine and return ORM objects."""
    orm_outfits = []
    for o in scored_outfits:
        stored_tags = dict(o.style_tags) if isinstance(o.style_tags, dict) else {}
        stored_tags["_meta"] = {
            "name": getattr(o, "name", ""),
            "reasoning": getattr(o, "reasoning", ""),
            "occasion": getattr(o, "occasion", ""),
        }
        outfit = Outfit(
            id=uuid.uuid4(),
            user_id=user_id,
            garment_ids=o.garment_ids,
            score=o.score,
            style_tags=stored_tags,
        )
        db.add(outfit)
        orm_outfits.append(outfit)
    db.commit()
    for o in orm_outfits:
        db.refresh(o)
    return orm_outfits


@router.post("/generate", response_model=OutfitGenerateResponse)
def generate(
    payload: OutfitGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run the rule-based outfit engine over the user's wardrobe and return
    the top `count` scored outfit combinations.

    Each outfit is persisted to the `outfits` table so it can be referenced
    by the VTON render endpoints (Phase 6) without the client re-sending the
    garment list.

    Returns 422 if the user's wardrobe has fewer than 2 items, and 200 with
    an empty list if no valid combinations can be found (e.g. all tops, no
    bottoms).
    """
    garments = get_garments_for_user(db, str(current_user.id))

    if len(garments) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Add at least 2 garments to your wardrobe before generating outfits",
        )

    engine_garments = _garments_to_engine_data(garments)
    scored = generate_outfits(
        engine_garments,
        count=payload.count,
        occasion=payload.occasion,
        style=payload.style,
        season=payload.season,
        fit=payload.fit,
    )

    if not scored:
        # Wardrobe exists but has no combinable items (e.g. all outerwear)
        return OutfitGenerateResponse(outfits=[])

    orm_outfits = _persist_outfits(db, str(current_user.id), scored)

    outfits = []
    for orm_o, sc_o in zip(orm_outfits, scored):
        meta, clean_tags = _extract_meta(orm_o.style_tags)
        outfits.append(
            OutfitItem(
                id=str(orm_o.id),
                garment_ids=orm_o.garment_ids,
                score=orm_o.score,
                style_tags=clean_tags,
                name=sc_o.name or meta.get("name"),
                reasoning=sc_o.reasoning or meta.get("reasoning"),
                occasion=sc_o.occasion or meta.get("occasion"),
            )
        )
    return OutfitGenerateResponse(outfits=outfits)


@router.get("/saved", response_model=SavedOutfitsResponse)
def list_saved_outfits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all previously generated outfits for the current user, newest first."""
    orm_outfits = (
        db.query(Outfit)
        .filter(Outfit.user_id == str(current_user.id))
        .order_by(Outfit.created_at.desc())
        .all()
    )

    outfits = []
    for o in orm_outfits:
        meta, clean_tags = _extract_meta(o.style_tags)
        outfits.append(
            OutfitItem(
                id=str(o.id),
                garment_ids=o.garment_ids,
                score=o.score,
                style_tags=clean_tags,
                name=meta.get("name"),
                reasoning=meta.get("reasoning"),
                occasion=meta.get("occasion"),
            )
        )
    return SavedOutfitsResponse(outfits=outfits, total=len(outfits))
