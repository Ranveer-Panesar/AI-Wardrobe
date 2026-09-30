"""
ColabProvider — forwards render requests to CatVTON running on Google Colab
behind a public ngrok tunnel.

The Colab notebook (ml-colab/idm_vton_server.py) starts a FastAPI server
and exposes two endpoints:
  POST /try-on      — person image + garment image → rendered image (bytes)
  POST /mannequin   — garment image → rendered image (bytes, uses Colab's internal mannequin)

Mannequin renders use the local dummy reference image (backend/Dummy/) sent as
person_image to /try-on — so the backend controls the mannequin, not Colab.

When the notebook is running you copy the ngrok URL into your .env as:
  COLAB_RENDER_URL=https://xxxx-xx-xxx.ngrok-free.app

If COLAB_RENDER_URL is empty or the notebook is not running, fall back to MockProvider.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path

import requests
from PIL import Image

from app.services.render.base import RenderProvider
from app.services.render.mock import MockProvider

log = logging.getLogger(__name__)

# Timeout for a single render request — CatVTON takes ~90-180s on free T4
# (longer for large garment images — 2MB+ can push 2-3 min)
_REQUEST_TIMEOUT_S = 300

# Default mannequin reference — backend/Dummy/male-mannequins-500x500.png
# Change this path (or add more dummies) without touching Colab at all.
_DUMMY_DIR = Path(__file__).resolve().parents[3] / "Dummy"
_DEFAULT_MANNEQUIN = (
    _DUMMY_DIR / "Base_model_VTON.png"
    if (_DUMMY_DIR / "Base_model_VTON.png").exists()
    else _DUMMY_DIR / "default_model.jpg"
    if (_DUMMY_DIR / "default_model.jpg").exists()
    else _DUMMY_DIR / "male-mannequins-500x500.png"
)


# Target resolution for Colab inference — matches CatVTON's native size.
# Sending larger images wastes ngrok bandwidth and doesn't improve quality.
_INFER_W, _INFER_H = 768, 1024
_GARMENT_QUALITY   = 82   # JPEG quality for garment uploads (~200 KB vs 2+ MB raw)


def _prepare_image(img: Image.Image, max_w: int = _INFER_W, max_h: int = _INFER_H,
                   quality: int = _GARMENT_QUALITY) -> bytes:
    """
    Resize image to fit within (max_w × max_h) keeping aspect ratio,
    then encode as JPEG at the given quality.
    Typical reduction: 2.2 MB raw → ~200 KB — 10x faster upload over ngrok.
    """
    img = img.convert("RGB")
    img.thumbnail((max_w, max_h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    size_kb = len(buf.getvalue()) // 1024
    log.debug("Image prepared: %dx%d  %d KB", img.width, img.height, size_kb)
    return buf.getvalue()


def _prepare_garment_file(path: str) -> bytes:
    """Load a garment from disk and prepare it for Colab upload."""
    return _prepare_image(Image.open(path))


def _read_mannequin(path: Path | None = None) -> bytes:
    """
    Read the mannequin reference image, resize to inference dimensions,
    and return as JPEG bytes. Falls back gracefully if the file is missing.
    """
    target = path or _DEFAULT_MANNEQUIN
    if target.exists():
        return _prepare_image(Image.open(target), quality=90)
    log.warning("Mannequin reference not found at %s — using blank fallback", target)
    img = Image.new("RGB", (_INFER_W, _INFER_H), "#d0ccc8")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


class ColabProvider(RenderProvider):
    """
    Sends render requests to the CatVTON FastAPI server running on Colab.
    Falls back to MockProvider if the Colab URL is unreachable.
    """

    def __init__(self, colab_url: str, render_dir: Path):
        self.base_url = colab_url.rstrip("/")
        self.render_dir = render_dir
        self.render_dir.mkdir(parents=True, exist_ok=True)
        # Pre-load mannequin bytes once at startup
        self._mannequin_bytes = _read_mannequin()
        log.info(
            "ColabProvider ready — target=%s  mannequin=%s (%d KB)",
            self.base_url,
            _DEFAULT_MANNEQUIN.name,
            len(self._mannequin_bytes) // 1024,
        )
        # Quick connectivity check
        try:
            import requests as _r
            _r.get(f"{self.base_url}/health", timeout=3)
            log.info("VTON server at %s is reachable ✓", self.base_url)
        except Exception as _e:
            log.warning("VTON server at %s not reachable yet: %s — will retry on first render", self.base_url, _e)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _save_response_image(self, content: bytes, job_id: str) -> str:
        """Save raw image bytes from Colab response and return relative URL."""
        out_path = self.render_dir / f"{job_id}.jpg"
        img = Image.open(io.BytesIO(content)).convert("RGB")
        img.save(str(out_path), format="JPEG", quality=90)
        return f"/renders/{job_id}.jpg"

    # ------------------------------------------------------------------
    # RenderProvider interface
    # ------------------------------------------------------------------

    def try_on(self, garment_image_path: str, person_image_bytes: bytes, job_id: str, garment_category: str = "upper_body") -> str:
        """
        POST multipart to Colab /try-on:
          - garment_image: garment file (pre-resized to 768×1024, ~200 KB)
          - person_image:  user/person photo bytes
          - garment_category: used by VTON server to pick the correct mask
        """
        url = f"{self.base_url}/try-on"
        garment_bytes = _prepare_garment_file(garment_image_path)
        log.info("try_on: garment=%d KB  person=%d KB  category=%s",
                 len(garment_bytes) // 1024, len(person_image_bytes) // 1024, garment_category)
        files = {
            "garment_image": ("garment.jpg", garment_bytes,      "image/jpeg"),
            "person_image":  ("person.jpg",  person_image_bytes, "image/jpeg"),
        }
        data = {"garment_category": garment_category}
        resp = requests.post(url, files=files, data=data, timeout=_REQUEST_TIMEOUT_S)
        resp.raise_for_status()
        return self._save_response_image(resp.content, job_id)

    def mannequin(self, garment_image_path: str, job_id: str, garment_category: str = "upper_body") -> str:
        """
        Render a garment on the local mannequin dummy.

        Sends the dummy PNG (backend/Dummy/male-mannequins-500x500.png) as
        person_image to Colab /try-on — so the mannequin is fully controlled
        by the backend, not by whatever the Colab script has hardcoded.
        Both images are pre-resized to 768×1024 before upload for faster inference.
        """
        url = f"{self.base_url}/try-on"
        garment_bytes = _prepare_garment_file(garment_image_path)
        log.info("mannequin: garment=%d KB  mannequin=%d KB  category=%s",
                 len(garment_bytes) // 1024, len(self._mannequin_bytes) // 1024, garment_category)
        files = {
            "garment_image": ("garment.jpg",   garment_bytes,        "image/jpeg"),
            "person_image":  ("mannequin.jpg",  self._mannequin_bytes, "image/jpeg"),
        }
        data = {"garment_category": garment_category}
        resp = requests.post(url, files=files, data=data, timeout=_REQUEST_TIMEOUT_S)
        resp.raise_for_status()
        return self._save_response_image(resp.content, job_id)
