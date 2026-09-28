"""
render service package — exposes get_render_provider() factory.
"""
from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.services.render.base import RenderProvider


def get_render_provider() -> RenderProvider:
    """
    Factory: returns the appropriate provider based on config.

    - RENDER_PROVIDER=mock   → MockProvider (default, no external deps)
    - RENDER_PROVIDER=colab  → ColabProvider (needs COLAB_RENDER_URL in .env)
    """
    render_dir = Path("./renders")

    if settings.RENDER_PROVIDER == "colab" and settings.COLAB_RENDER_URL:
        from app.services.render.colab import ColabProvider
        return ColabProvider(settings.COLAB_RENDER_URL, render_dir)

    # Default / fallback
    from app.services.render.mock import MockProvider
    return MockProvider(render_dir)
