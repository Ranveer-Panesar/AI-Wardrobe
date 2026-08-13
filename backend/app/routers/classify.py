import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.schemas.garment import ClassificationResponse
from app.services.classification import FashionClassifier
from app.services.color_extraction import extract_dominant_colors

router = APIRouter(prefix="/classify", tags=["classification"])


def get_classifier() -> FashionClassifier:
    """FastAPI dependency — overridden with a mock in tests so the test
    suite doesn't need to actually load Fashion-CLIP."""
    return FashionClassifier.get_instance()


@router.post("", response_model=ClassificationResponse)
async def classify_garment(
    file: UploadFile = File(...),
    include_embedding: bool = False,
    classifier: FashionClassifier = Depends(get_classifier),
):
    """
    Classify a single garment photo: category, pattern, formality, and
    dominant colors. Pass ?include_embedding=true to also get the raw
    Fashion-CLIP embedding (needed later for outfit compatibility scoring
    and similarity search, not needed just to show the user what was detected).

    NOTE: this endpoint does not persist anything to the database — it's a
    pure classify-and-return step. Saving the result onto a Garment record
    happens in the wardrobe upload flow (Phase 2, wired up once the Garment
    model exists), which will call this same service internally.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Could not read image file")

    category, category_confidence = classifier.classify_category(image)
    pattern, _ = classifier.classify_pattern(image)
    formality, _ = classifier.classify_formality(image)
    dominant_colors = extract_dominant_colors(image)

    embedding = classifier.get_embedding(image) if include_embedding else None

    return ClassificationResponse(
        category=category,
        category_confidence=round(category_confidence, 4),
        pattern=pattern,
        formality=formality,
        dominant_colors=dominant_colors,
        embedding=embedding,
    )
