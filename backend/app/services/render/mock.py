"""
MockProvider — instantly returns a placeholder render image.

Used during development and CI so the render flow can be tested
end-to-end without a running Colab notebook.

The placeholder is a simple composite: garment image pasted onto a
grey silhouette background, annotated with "MOCK RENDER".
"""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.services.render.base import RenderProvider


class MockProvider(RenderProvider):

    def __init__(self, render_dir: Path):
        self.render_dir = render_dir
        self.render_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_placeholder(self, garment_path: str, label: str) -> Image.Image:
        """
        Create a 512×768 placeholder image:
        - Light grey background
        - Garment image composited in the centre
        - "MOCK RENDER" label at the top
        """
        canvas = Image.new("RGB", (512, 768), color="#e8e8e8")

        # Draw a simple body silhouette outline
        draw = ImageDraw.Draw(canvas)
        # Head circle
        draw.ellipse([196, 40, 316, 160], outline="#bbbbbb", width=3)
        # Body rectangle
        draw.rectangle([156, 160, 356, 560], outline="#bbbbbb", width=3)
        # Legs
        draw.rectangle([156, 560, 246, 730], outline="#bbbbbb", width=3)
        draw.rectangle([266, 560, 356, 730], outline="#bbbbbb", width=3)

        # Paste garment over torso area
        try:
            garment = Image.open(garment_path).convert("RGBA")
            garment.thumbnail((180, 220))
            gx = (512 - garment.width) // 2
            gy = 170
            canvas.paste(garment, (gx, gy), garment)
        except Exception:
            pass  # garment image unreadable — silhouette only

        # Label
        draw.rectangle([0, 0, 512, 36], fill="#555555")
        draw.text((8, 8), f"MOCK RENDER — {label}", fill="#ffffff")

        return canvas

    def _save(self, img: Image.Image, job_id: str) -> str:
        out_path = self.render_dir / f"{job_id}.jpg"
        img.convert("RGB").save(str(out_path), format="JPEG", quality=88)
        return f"/renders/{job_id}.jpg"

    # ------------------------------------------------------------------
    # RenderProvider interface
    # ------------------------------------------------------------------

    def try_on(self, garment_image_path: str, person_image_bytes: bytes, job_id: str) -> str:
        img = self._make_placeholder(garment_image_path, "try-on")
        return self._save(img, job_id)

    def mannequin(self, garment_image_path: str, job_id: str) -> str:
        img = self._make_placeholder(garment_image_path, "mannequin")
        return self._save(img, job_id)
