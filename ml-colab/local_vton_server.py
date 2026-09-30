"""
Local CatVTON Server for AI Wardrobe
====================================
Runs CatVTON diffusion try-on directly on the local NVIDIA GPU (RTX 5060 Ti).

Exposes the same API as the Colab notebook:
  POST /try-on      — garment_image (file), person_image (file), garment_category (form)
  POST /mannequin   — garment_image (file), garment_category (form)
  GET  /health      — returns {"status": "ok", "device": "cuda", ...}

Default port: 8001
"""
import io
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Add local CatVTON repository to python path
CATVTON_DIR = Path(__file__).resolve().parent / "CatVTON"
if str(CATVTON_DIR) not in sys.path:
    sys.path.insert(0, str(CATVTON_DIR))

import cv2
import numpy as np
import torch
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from huggingface_hub import snapshot_download
from PIL import Image

from model.SCHP import SCHP
from model.pipeline import CatVTONPipeline
from utils import resize_and_crop, resize_and_padding

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("local_vton")

TARGET_W, TARGET_H = 768, 1024
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if torch.cuda.is_available() else torch.float32

# ─── Optional background remover (rembg) ──────────────────────────────────────
try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
    log.info("rembg loaded — garment backgrounds will be auto-removed for cleaner try-on.")
except ImportError:
    REMBG_AVAILABLE = False
    log.warning("rembg not installed — garment images will be used as-is.")


def remove_garment_bg(img: Image.Image) -> Image.Image:
    """Remove background from a garment image and return it on a pure white background."""
    if not REMBG_AVAILABLE:
        return img.convert("RGB")
    try:
        rgba = rembg_remove(img.convert("RGBA"))
        white_bg = Image.new("RGB", rgba.size, (255, 255, 255))
        white_bg.paste(rgba, mask=rgba.split()[3])
        return white_bg
    except Exception as e:
        log.warning(f"rembg background removal failed, using original: {e}")
        return img.convert("RGB")


def crop_garment_to_bbox(img: Image.Image, padding_pct: float = 0.03) -> Image.Image:
    """
    Crop garment image tightly to its bounding box so it fills the 3:4 frame
    like in standard VTON benchmarks, preventing small square uploads from having
    80%+ white empty margins that wash out colors and details.
    """
    arr = np.array(img)
    if arr.shape[-1] == 4:
        mask = arr[..., 3] > 20
    else:
        mask = np.any(arr < 240, axis=-1)

    if not np.any(mask):
        return img

    y_indices, x_indices = np.where(mask)
    min_y, max_y = np.min(y_indices), np.max(y_indices)
    min_x, max_x = np.min(x_indices), np.max(x_indices)

    h = max_y - min_y
    w = max_x - min_x
    pad_y = int(h * padding_pct)
    pad_x = int(w * padding_pct)

    min_y = max(0, min_y - pad_y)
    max_y = min(arr.shape[0], max_y + pad_y)
    min_x = max(0, min_x - pad_x)
    max_x = min(arr.shape[1], max_x + pad_x)

    return img.crop((min_x, min_y, max_x, max_y))


# ─── Global Models ────────────────────────────────────────────────────────────
pipe: CatVTONPipeline | None = None
schp_parser: SCHP | None = None


def load_models():
    global pipe, schp_parser
    if pipe is not None and schp_parser is not None:
        return pipe, schp_parser

    log.info(f"Loading CatVTON pipeline onto {DEVICE} ({DTYPE})...")
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        log.info(f"Using GPU: {gpu_name} ({vram_gb:.1f} GB VRAM)")

    repo_path = snapshot_download("zhengchong/CatVTON")
    base_ckpt = "booksforcharlie/stable-diffusion-inpainting"

    log.info("Loading SCHP human parsing model on GPU...")
    schp_parser = SCHP(
        ckpt_path=os.path.join(repo_path, "SCHP", "exp-schp-201908301523-atr.pth"),
        device=DEVICE,
    )

    log.info("Loading CatVTON diffusion pipeline on GPU...")
    pipe = CatVTONPipeline(
        base_ckpt=base_ckpt,
        attn_ckpt=repo_path,
        attn_ckpt_version="mix",
        weight_dtype=DTYPE,
        device=DEVICE,
        skip_safety_check=True,
        use_tf32=True,
    )
    log.info("All VTON models successfully loaded and ready for inference!")
    return pipe, schp_parser


# ─── Anatomical Agnostic Mask Generation ──────────────────────────────────────
# ATR Label index map:
# 0: Background, 1: Hat, 2: Hair, 3: Sunglasses, 4: Upper-clothes, 5: Skirt,
# 6: Pants, 7: Dress, 8: Belt, 9: Left-shoe, 10: Right-shoe, 11: Face,
# 12: Left-leg, 13: Right-leg, 14: Left-arm, 15: Right-arm, 16: Bag, 17: Scarf

_LOWER_BODY_CATEGORIES = {
    "trousers", "pants", "shorts", "skirt", "jeans", "leggings",
    "lower_body", "lower body", "bottom", "joggers", "formal trousers", "casual trousers"
}
_FULL_BODY_CATEGORIES = {
    "dress", "suit", "jumpsuit", "overalls", "romper", "full_body", "full body"
}


def generate_agnostic_mask(person_img: Image.Image, category: str) -> Image.Image:
    """
    Generate an anatomical inpainting mask using SCHP.
    Strictly isolates the target garment area and preserves background,
    face, shoes, and non-target clothing.
    """
    _, parser = load_models()
    person_resized = resize_and_crop(person_img, (TARGET_W, TARGET_H))
    atr = np.array(parser(person_resized))

    cat = category.lower().strip()
    is_lower = any(k in cat for k in _LOWER_BODY_CATEGORIES)
    is_full = any(k in cat for k in _FULL_BODY_CATEGORIES)

    if is_lower:
        log.info(f"Generating anatomical LOWER_BODY mask for '{category}'")
        # Inpaint: skirts (5), pants (6), legs (12, 13)
        mask = np.isin(atr, [5, 6, 12, 13]).astype(np.uint8) * 255
        # Guard: zero out head and upper torso region
        mask[:int(TARGET_H * 0.48), :] = 0
    elif is_full:
        log.info(f"Generating anatomical FULL_BODY mask for '{category}'")
        # Inpaint: upper clothes (4), skirt (5), pants (6), dress (7), legs (12,13), arms (14,15)
        mask = np.isin(atr, [4, 5, 6, 7, 12, 13, 14, 15]).astype(np.uint8) * 255
        mask[:int(TARGET_H * 0.17), :] = 0
    else:
        log.info(f"Generating anatomical UPPER_BODY mask for '{category}'")
        # Inpaint: upper clothes (4), dress/torso (7), arms (14, 15)
        mask = np.isin(atr, [4, 7, 14, 15]).astype(np.uint8) * 255
        # Include neck & upper chest (part of label 11) between row 0.17 and 0.35 of height
        # This allows collared shirts, polo collars, crew necks, and button-ups to close naturally
        # over previous V-necks or bare skin
        neck_area = (atr == 11) & (np.arange(TARGET_H)[:, None] >= int(TARGET_H * 0.17)) & (np.arange(TARGET_H)[:, None] <= int(TARGET_H * 0.35))
        mask[neck_area] = 255
        # Guard: zero out head and face
        mask[:int(TARGET_H * 0.17), :] = 0
        # Guard: zero out waistband and pants
        mask[int(TARGET_H * 0.56):, :] = 0

    # Fallback guard if SCHP didn't find the expected parts
    if np.sum(mask > 0) < 500:
        log.warning("SCHP detected minimal body parts, using silhouette fallback")
        non_bg = (atr != 0).astype(np.uint8) * 255
        if is_lower:
            non_bg[:int(TARGET_H * 0.48), :] = 0
            mask = non_bg
        elif is_full:
            non_bg[:int(TARGET_H * 0.18), :] = 0
            mask = non_bg
        else:
            non_bg[:int(TARGET_H * 0.18), :] = 0
            non_bg[int(TARGET_H * 0.56):, :] = 0
            mask = non_bg

    # Dilate smoothly along the body contours to cover seams, then soft blur
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    mask = cv2.dilate(mask, kernel, iterations=2)
    mask = cv2.GaussianBlur(mask, (21, 21), 0)

    return Image.fromarray(mask)


# ─── Inference Helper ─────────────────────────────────────────────────────────

def _run_inference(person_img: Image.Image, garment_img: Image.Image, mask: Image.Image) -> Image.Image:
    pipeline, _ = load_models()
    person_img = resize_and_crop(person_img, (TARGET_W, TARGET_H))
    garment_tight = crop_garment_to_bbox(garment_img)
    garment_img = resize_and_padding(garment_tight, (TARGET_W, TARGET_H))

    with torch.inference_mode():
        result = pipeline(
            image=person_img,
            condition_image=garment_img,
            mask=mask,
            num_inference_steps=35,
            guidance_scale=2.5,
            height=TARGET_H,
            width=TARGET_W,
            generator=torch.Generator(DEVICE).manual_seed(42),
        )[0]
    return result


# ─── FastAPI Application ──────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        load_models()
    except Exception as exc:
        log.warning(f"Deferred model loading on first request: {exc}")
    yield

app = FastAPI(title="Local CatVTON Server", version="2.0.0", lifespan=lifespan)


@app.get("/health")
def health():
    gpu_info = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    return {
        "status": "ok",
        "model": "CatVTON",
        "masker": "SCHP",
        "device": DEVICE,
        "gpu": gpu_info,
        "dtype": str(DTYPE),
        "pipeline_loaded": pipe is not None,
        "rembg_available": REMBG_AVAILABLE,
    }


@app.post("/try-on")
async def try_on(
    garment_image: UploadFile = File(...),
    person_image: UploadFile = File(...),
    garment_category: str = Form(default="upper_body"),
):
    try:
        g_bytes = await garment_image.read()
        p_bytes = await person_image.read()

        garment_img = Image.open(io.BytesIO(g_bytes))
        person_img = Image.open(io.BytesIO(p_bytes))

        log.info(
            f"Received try-on job: garment {garment_img.size}, person {person_img.size}, "
            f"category='{garment_category}'"
        )

        garment_img = remove_garment_bg(garment_img)
        mask = generate_agnostic_mask(person_img, garment_category)

        rendered = _run_inference(person_img, garment_img, mask)

        buf = io.BytesIO()
        rendered.save(buf, format="JPEG", quality=92)
        return Response(content=buf.getvalue(), media_type="image/jpeg")

    except Exception as exc:
        log.error(f"Try-on error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/mannequin")
async def mannequin(
    garment_image: UploadFile = File(...),
    garment_category: str = Form(default="upper_body"),
):
    try:
        g_bytes = await garment_image.read()
        garment_img = Image.open(io.BytesIO(g_bytes))

        dummy_dir = Path(__file__).resolve().parents[1] / "backend" / "Dummy"
        dummy_path = (
            dummy_dir / "Base_model_VTON.png"
            if (dummy_dir / "Base_model_VTON.png").exists()
            else dummy_dir / "default_model.jpg"
            if (dummy_dir / "default_model.jpg").exists()
            else dummy_dir / "male-mannequins-500x500.png"
        )
        if dummy_path.exists():
            person_img = Image.open(dummy_path)
        else:
            person_img = Image.new("RGB", (TARGET_W, TARGET_H), color="#c8bfb6")

        garment_img = remove_garment_bg(garment_img)
        mask = generate_agnostic_mask(person_img, garment_category)

        rendered = _run_inference(person_img, garment_img, mask)

        buf = io.BytesIO()
        rendered.save(buf, format="JPEG", quality=92)
        return Response(content=buf.getvalue(), media_type="image/jpeg")

    except Exception as exc:
        log.error(f"Mannequin render error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
