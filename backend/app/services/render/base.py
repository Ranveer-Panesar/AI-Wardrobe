"""
Abstract base class for all VTON render providers.

Concrete implementations:
  MockProvider  — returns a placeholder image instantly (dev/testing)
  ColabProvider — forwards to IDM-VTON running on Colab behind ngrok
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class RenderProvider(ABC):
    """
    A provider takes a garment image and a person image and returns
    a URL path to the rendered output image saved on disk.

    Both inputs are PIL-readable image bytes. The provider is responsible
    for writing the output image to LOCAL_RENDER_DIR and returning its
    relative URL ("/renders/<uuid>.jpg").
    """

    @abstractmethod
    def try_on(
        self,
        garment_image_path: str,
        person_image_bytes: bytes,
        job_id: str,
    ) -> str:
        """
        Run a try-on render.

        Args:
            garment_image_path: Absolute path to the garment image on disk.
            person_image_bytes: Raw bytes of the person/user photo.
            job_id:             UUID string — used as the output filename stem.

        Returns:
            Relative URL of the saved output, e.g. "/renders/<job_id>.jpg".
        """

    @abstractmethod
    def mannequin(
        self,
        garment_image_path: str,
        job_id: str,
    ) -> str:
        """
        Render the garment on the built-in mannequin photo.

        Args:
            garment_image_path: Absolute path to the garment image on disk.
            job_id:             UUID string — used as the output filename stem.

        Returns:
            Relative URL of the saved output, e.g. "/renders/<job_id>.jpg".
        """
