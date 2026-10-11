"""
Wardrobe endpoints (Phase 2).

POST   /wardrobe/items         — upload image, classify, persist, return GarmentResponse
GET    /wardrobe/items         — list the current user's garments
PATCH  /wardrobe/items/{id}    — correct a misclassified field
DELETE /wardrobe/items/{id}    — remove a garment

All routes are auth-protected via the `get_current_user` dependency.
"""
from __future__ import annotations

import io
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.routers.classify import get_classifier
from app.schemas.wardrobe import GarmentPatchRequest, GarmentResponse, WardrobeListResponse
from app.services.classification import FashionClassifier
from app.services.color_extraction import extract_dominant_colors
from app.services.wardrobe_service import (
    create_garment,
    delete_garment,
    get_garment,
    get_garments_for_user,
    patch_garment,
)

router = APIRouter(prefix="/wardrobe", tags=["wardrobe"])


def _save_image(image: Image.Image, upload_dir: Path) -> str:
    """
    Persist the image to LOCAL_UPLOAD_DIR and return a relative URL
    path (e.g. "/uploads/<uuid>.jpg") that the frontend can resolve.
    """
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}.jpg"
    filepath = upload_dir / filename
    image.save(filepath, format="JPEG", quality=85)
    return f"/uploads/{filename}"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/items", response_model=GarmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_garment(
    file: UploadFile = File(...),
    include_embedding: bool = False,
    current_user: User = Depends(get_current_user),
    classifier: FashionClassifier = Depends(get_classifier),
    db: Session = Depends(get_db),
):
    """
    Upload a garment image: classify it with Fashion-CLIP, persist the result,
    and return the new Garment record.

    The image is saved locally (LOCAL_UPLOAD_DIR from config). Pass
    ?include_embedding=true to also store the Fashion-CLIP embedding in the
    DB for use by the Phase 4 compatibility head.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Could not read image file")



    # --- Classify ---
    category, category_confidence = classifier.classify_category(image)
    pattern, _ = classifier.classify_pattern(image)
    formality, _ = classifier.classify_formality(image)
    dominant_colors = extract_dominant_colors(image)
    embedding = classifier.get_embedding(image) if include_embedding else None

    # --- Persist image to disk ---
    upload_dir = Path(settings.LOCAL_UPLOAD_DIR)
    image_url = _save_image(image, upload_dir)

    # --- Persist to DB ---
    garment = create_garment(
        db,
        user_id=str(current_user.id),
        category=category,
        category_confidence=round(category_confidence, 4),
        pattern=pattern,
        formality=formality,
        dominant_colors=dominant_colors,
        image_url=image_url,
        embedding=embedding,
    )

    return GarmentResponse(
        id=str(garment.id),
        category=garment.category,
        category_confidence=garment.category_confidence,
        pattern=garment.pattern,
        formality=garment.formality,
        dominant_colors=garment.dominant_colors,
        image_url=garment.image_url,
        created_at=garment.created_at,
    )


@router.get("/items", response_model=WardrobeListResponse)
def list_garments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all garments belonging to the current user, newest first."""
    garments = get_garments_for_user(db, str(current_user.id))
    items = [
        GarmentResponse(
            id=str(g.id),
            category=g.category,
            category_confidence=g.category_confidence,
            pattern=g.pattern,
            formality=g.formality,
            dominant_colors=g.dominant_colors,
            image_url=g.image_url,
            created_at=g.created_at,
        )
        for g in garments
    ]
    return WardrobeListResponse(items=items, total=len(items))


@router.patch("/items/{garment_id}", response_model=GarmentResponse)
def update_garment(
    garment_id: str,
    payload: GarmentPatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Correct a misclassified field. Only `category`, `pattern`, and `formality`
    are patchable — the user can't change colours or the embedding this way.
    """
    garment = get_garment(db, garment_id, str(current_user.id))
    if garment is None:
        raise HTTPException(status_code=404, detail="Garment not found")

    updated = patch_garment(db, garment, payload.model_dump(exclude_none=True))
    return GarmentResponse(
        id=str(updated.id),
        category=updated.category,
        category_confidence=updated.category_confidence,
        pattern=updated.pattern,
        formality=updated.formality,
        dominant_colors=updated.dominant_colors,
        image_url=updated.image_url,
        created_at=updated.created_at,
    )


@router.delete("/items/{garment_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_garment(
    garment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a garment from the user's wardrobe."""
    garment = get_garment(db, garment_id, str(current_user.id))
    if garment is None:
        raise HTTPException(status_code=404, detail="Garment not found")
    delete_garment(db, garment)


@router.post("/synthetic-closet", response_model=WardrobeListResponse, status_code=status.HTTP_201_CREATED)
def generate_synthetic_closet(
    replace: bool = False,
    count: int = 16,
    current_user: User = Depends(get_current_user),
    classifier: FashionClassifier = Depends(get_classifier),
    db: Session = Depends(get_db),
):
    """
    Generate a synthetic digital closet using clothing images from the clothing dataset.
    Every image is passed through the exact same classification & feature extraction pipeline
    (FashionClassifier, color extraction, local disk persistence) as user uploads.
    """
    from app.services.synthetic_closet import seed_synthetic_closet

    created = seed_synthetic_closet(
        db=db,
        user_id=str(current_user.id),
        classifier=classifier,
        replace=replace,
        max_items=count,
    )
    items = [
        GarmentResponse(
            id=str(g.id),
            category=g.category,
            category_confidence=g.category_confidence,
            pattern=g.pattern,
            formality=g.formality,
            dominant_colors=g.dominant_colors,
            image_url=g.image_url,
            created_at=g.created_at,
        )
        for g in created
    ]
    return WardrobeListResponse(items=items, total=len(items))

