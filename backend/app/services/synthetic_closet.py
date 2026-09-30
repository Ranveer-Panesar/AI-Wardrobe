"""
Service for generating a synthetic / sample digital closet for testing the AI stylist.
Images pass through the exact same classification & feature extraction pipeline
(FashionClassifier, color extraction, local disk persistence) as user-uploaded garments.
"""
from __future__ import annotations

import io
import logging
import uuid
from pathlib import Path

import requests
from PIL import Image
from sqlalchemy.orm import Session

from app.config import settings
from app.models.garment import Garment, Outfit
from app.services.classification import FashionClassifier
from app.services.color_extraction import extract_dominant_colors
from app.services.wardrobe_service import create_garment

logger = logging.getLogger(__name__)

# Fallback public dataset image URLs if local assets are missing
_REMOTE_DATASET_FALLBACK: list[tuple[str, str]] = [
    ("t-shirt", "https://raw.githubusercontent.com/alexeygrigorev/clothing-dataset-small/master/train/t-shirt/00003aeb-ace5-43bf-9a0c-dc31a03e9cd2.jpg"),
    ("t-shirt", "https://raw.githubusercontent.com/alexeygrigorev/clothing-dataset-small/master/train/t-shirt/00805d0e-7fe5-4251-b577-86065e4f6587.jpg"),
    ("shorts", "https://raw.githubusercontent.com/alexeygrigorev/clothing-dataset-small/master/train/shorts/00f4bb77-5cbd-4c81-98b5-42647b8d0c64.jpg"),
    ("shorts", "https://raw.githubusercontent.com/alexeygrigorev/clothing-dataset-small/master/train/shorts/028223d5-e408-4b02-b1a1-2cc641fb9500.jpg"),
    ("pants", "https://raw.githubusercontent.com/alexeygrigorev/clothing-dataset-small/master/train/pants/0098b991-e36e-4ef1-b5ee-4154b21e2a92.jpg"),
    ("pants", "https://raw.githubusercontent.com/alexeygrigorev/clothing-dataset-small/master/train/pants/027c81f2-c6e1-498a-8f69-823ce631438e.jpg"),
    ("shirt", "https://raw.githubusercontent.com/alexeygrigorev/clothing-dataset-small/master/train/shirt/005d3a4d-b8cc-4f14-a288-8065ab797974.jpg"),
    ("shirt", "https://raw.githubusercontent.com/alexeygrigorev/clothing-dataset-small/master/train/shirt/006a85bc-8a95-4cd3-8c8c-215b53753abe.jpg"),
    ("outwear", "https://raw.githubusercontent.com/alexeygrigorev/clothing-dataset-small/master/train/outwear/00149032-3dd6-426e-9bc0-d53032536a42.jpg"),
    ("dress", "https://raw.githubusercontent.com/alexeygrigorev/clothing-dataset-small/master/train/dress/009b3c31-fb62-45c0-be9a-37a5c238cb88.jpg"),
]


def _save_image(image: Image.Image, upload_dir: Path) -> str:
    """Save PIL Image to upload directory and return relative path."""
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}.jpg"
    filepath = upload_dir / filename
    image.save(filepath, format="JPEG", quality=85)
    return f"/uploads/{filename}"


def get_synthetic_image_sources() -> list[tuple[str, Path | str]]:
    """
    Returns list of (label_hint, file_path_or_url) representing balanced clothing items.
    Prefers local cached assets; falls back to remote dataset URLs.
    """
    # Check local backend assets folder
    local_dir = Path(settings.BASE_DIR if hasattr(settings, "BASE_DIR") else ".") / "assets" / "synthetic_dataset"
    if not local_dir.exists():
        # Try relative to this file
        local_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "synthetic_dataset"

    if local_dir.exists():
        local_files = sorted(local_dir.glob("*.jpg"))
        if local_files:
            by_cat: dict[str, list[Path]] = {}
            for f in local_files:
                cat = f.stem.split("_")[0]
                by_cat.setdefault(cat, []).append(f)

            # Interleave to ensure an impeccably balanced capsule wardrobe:
            # T-shirts, shorts, pants, shirts, blazers, polos, hoodies, outerwear, dresses
            interleaved: list[tuple[str, Path]] = []
            max_len = max(len(v) for v in by_cat.values()) if by_cat else 0
            order = ("t-shirt", "shorts", "pants", "shirt", "blazer", "polo", "hoodie", "outwear", "dress")
            for idx in range(max_len):
                for cat in order:
                    if cat in by_cat and idx < len(by_cat[cat]):
                        interleaved.append((cat, by_cat[cat][idx]))
            return interleaved

    # Fallback to remote URLs
    return [(label, url) for label, url in _REMOTE_DATASET_FALLBACK]


def seed_synthetic_closet(
    db: Session,
    user_id: str,
    classifier: FashionClassifier,
    replace: bool = False,
    max_items: int = 16,
) -> list[Garment]:
    """
    Populate a user's digital wardrobe with synthetic clothing dataset items.
    Every item is run through FashionClassifier and color extraction exactly like a user upload.
    """
    if replace:
        # Delete existing outfits first (due to foreign references/associations)
        db.query(Outfit).filter(Outfit.user_id == user_id).delete()
        # Delete existing garments
        db.query(Garment).filter(Garment.user_id == user_id).delete()
        db.commit()

    sources = get_synthetic_image_sources()
    # If we have more than max_items, select a balanced subset
    selected_sources = sources[:max_items]

    upload_dir = Path(settings.LOCAL_UPLOAD_DIR)
    created_garments: list[Garment] = []

    for hint, src in selected_sources:
        try:
            if isinstance(src, Path) and src.exists():
                image = Image.open(src).convert("RGB")
            elif isinstance(src, str) and src.startswith("http"):
                resp = requests.get(src, timeout=12)
                if resp.status_code != 200:
                    continue
                image = Image.open(io.BytesIO(resp.content)).convert("RGB")
            else:
                continue

            # Run through the EXACT same classification pipeline as upload_garment:
            category, category_confidence = classifier.classify_category(image)
            pattern, _ = classifier.classify_pattern(image)
            formality, _ = classifier.classify_formality(image)
            dominant_colors = extract_dominant_colors(image)

            # Persist image to disk
            image_url = _save_image(image, upload_dir)

            # Persist to database
            garment = create_garment(
                db,
                user_id=user_id,
                category=category,
                category_confidence=round(category_confidence, 4),
                pattern=pattern,
                formality=formality,
                dominant_colors=dominant_colors,
                image_url=image_url,
            )
            created_garments.append(garment)

        except Exception as e:
            logger.warning(f"Error processing synthetic garment {src}: {e}")
            continue

    return created_garments
